from collections import defaultdict
from tuber import app, config
from flask import send_file, request, jsonify, Response, stream_with_context
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from sqlalchemy import and_, or_, not_, func
from sqlalchemy.orm import joinedload, selectinload
import datetime
import os
from tuber.api.util import *
from .room_matcher import rematch_hotel_block, clear_hotel_block
import time

@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/room/<int:room_id>/remove_roommates", methods=["POST"])
def remove_roommates(event, hotel_block, room_id):
    if not check_permission(f'hotel_block.{hotel_block}.write', event=event):
        return "", 403
    db.query(RoomNightAssignment).filter(RoomNightAssignment.event == event,
                                         RoomNightAssignment.hotel_room == room_id, RoomNightAssignment.badge.in_(g.data['roommates'])).delete()
    reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event ==
                                             event, HotelRoomRequest.badge.in_(g.data['roommates'])).all()
    for req in reqs:
        db.add(req)
    db.commit()
    return "null", 200


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/room/<int:room_id>/add_roommates", methods=["POST"])
def add_roommates(event, hotel_block, room_id):
    if not check_permission(f'hotel_block.{hotel_block}.write', event=event):
        return "", 403
    reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event ==
                                             event, HotelRoomRequest.badge.in_(g.data['roommates'])).all()
    room_nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).order_by(HotelRoomNight.date).all()
    room_nights = {x.id: x for x in room_nights}
    for req in reqs:
        for night in req.room_night_requests:
            assign = False
            if night.requested:
                assign = True
            for assignment in req.room_night_assignments:
                if assignment.room_night == night.room_night:
                    assign = False
                    break
            if assign:
                db.add(RoomNightAssignment(event=event, badge=req.badge,
                       room_night=night.room_night, hotel_room=room_id))
    for req in reqs:
        db.add(req)
    db.commit()
    return "null", 200


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/rematch_all", methods=["POST"])
def rematch_block(event, hotel_block):
    if not check_permission(f"hotel_block.{hotel_block}.write", event=event):
        return "", 403
    if rematch_hotel_block(db, event, hotel_block):
        return "[]", 200
    return "", 500


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/clear_matches", methods=["POST"])
def clear_matches(event, hotel_block):
    if not check_permission(f"hotel_block.{hotel_block}.write", event=event):
        return "", 403
    clear_hotel_block(db, event, hotel_block)
    return "[]", 200


@app.route("/api/event/<int:event>/hotel/room_details", methods=["GET"])
def room_details(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403

    rooms = [int(x) for x in g.data['rooms'].split(",")]

    rnas = db.query(RoomNightAssignment, Badge.public_name).join(Badge, Badge.id ==
                                                                 RoomNightAssignment.badge).filter(RoomNightAssignment.hotel_room.in_(rooms)).all()

    badges = []
    request_groups = {}

    details = {}
    for rna, public_name in rnas:
        if not rna.badge in badges:
            badges.append(rna.badge)
        if not rna.hotel_room in details:
            details[rna.hotel_room] = {
                "room_nights": [],
                "roommates": {},
                "empty_slots": 0
            }
            request_groups[rna.hotel_room] = {}
        if not rna.room_night in details[rna.hotel_room]['room_nights']:
            details[rna.hotel_room]['room_nights'].append(rna.room_night)

        if not rna.badge in details[rna.hotel_room]['roommates']:
            details[rna.hotel_room]['roommates'][rna.badge] = {
                "id": rna.badge,
                "name": public_name,
                "errors": set(),
                "room_night_assignments": {}
            }
            request_groups[rna.hotel_room][rna.badge] = []
        details[rna.hotel_room]['roommates'][rna.badge]['room_night_assignments'][rna.room_night] = rna.id

    all_rnas = db.query(RoomNightAssignment).filter(
        RoomNightAssignment.badge.in_(badges)).all()
    rnas_by_badge = defaultdict(list)
    for rna in all_rnas:
        rnas_by_badge[rna.badge].append(rna)

    gender_prefs = {}

    room_nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).order_by(HotelRoomNight.date).all()
    room_nights = {x.id: x for x in room_nights}
    hotel_rooms = db.query().with_entities(
        HotelRoom,
        HotelRoomRequest
    ).join(
        RoomNightAssignment, HotelRoom.id == RoomNightAssignment.hotel_room
    ).join(
        HotelRoomRequest, HotelRoomRequest.badge == RoomNightAssignment.badge
    ).filter(HotelRoom.id.in_(rooms)).distinct().options(
        selectinload(HotelRoomRequest.roommate_requests).load_only(
            Badge.id, Badge.public_name)
    ).options(
        selectinload(
            HotelRoomRequest.roommate_anti_requests).load_only(Badge.id, Badge.public_name)
    ).options(
        selectinload(HotelRoomRequest.room_night_requests).load_only(
            RoomNightRequest.room_night, RoomNightRequest.requested)
    ).options(
        selectinload(HotelRoomRequest.room_night_approvals).load_only(
            RoomNightApproval.room_night, RoomNightApproval.approved
        )
    ).options(
        selectinload(HotelRoom.roommates).load_only(
            Badge.id, Badge.public_name)
    ).all()

    for hotel_room, request in hotel_rooms:
        if not hotel_room.id in gender_prefs:
            gender_prefs[hotel_room.id] = set()
        gender_prefs[hotel_room.id].add(
            config.gender_map.get(request.preferred_gender, "Unknown"))
    for hotel_room, request in hotel_rooms:
        for roommate_request in request.roommate_requests:
            if not roommate_request.id in request_groups[hotel_room.id][request.badge]:
                request_groups[hotel_room.id][request.badge].append(
                    roommate_request.id)
            if not roommate_request in hotel_room.roommates:

                details[hotel_room.id]['roommates'][request.badge]['errors'].add(
                    f'Requested {roommate_request.public_name}')
        for antiroommate_request in request.roommate_anti_requests:
            if antiroommate_request in hotel_room.roommates:
                details[hotel_room.id]['roommates'][request.badge]['errors'].add(
                    'Anti-requested Roommate')
        nights = set()
        for night_request in request.room_night_requests:
            if night_request.requested:
                if room_nights[night_request.room_night].restricted:
                    for approval in request.room_night_approvals:
                        if approval.room_night == night_request.room_night and approval.approved:
                            nights.add(night_request.room_night)
                else:
                    nights.add(night_request.room_night)
        assigned_nights = [x.room_night for x in rnas_by_badge[request.badge]]
        missing_nights = nights.difference(set(assigned_nights))
        extra_nights = set(details[hotel_room.id]
                           ['room_nights']).difference(nights)
        if extra_nights:
            details[hotel_room.id]['roommates'][request.badge]['errors'].add(
                f'Extra Room Night ({", ".join([room_nights[x].name[:2] for x in extra_nights])})')
        if missing_nights:
            details[hotel_room.id]['roommates'][request.badge]['errors'].add(
                f'Missing Room Night ({", ".join([room_nights[x].name[:2] for x in missing_nights])})')
        if request.prefer_single_gender and len(gender_prefs[hotel_room.id]) > 1:
            details[hotel_room.id]['roommates'][request.badge]['errors'].add(
                f'Gender Mismatch ({request.preferred_gender}) ({", ".join(gender_prefs[hotel_room.id])})')
        details[hotel_room.id]['roommates'][request.badge]['errors'] = list(
            details[hotel_room.id]['roommates'][request.badge]['errors'])
        details[hotel_room.id]['empty_slots'] += len(
            set(details[hotel_room.id]['room_nights']).difference(nights))

    for room, detail in details.items():
        groups = request_groups[room]
        combined = []
        for member, requests in groups.items():
            for cgroup in combined:
                if member in cgroup['requested'] or any([x in requests for x in cgroup['members']]):
                    cgroup['members'].append(member)
                    cgroup['requested'].extend(requests)
                    break
            else:
                combined.append({
                    "members": [member, ],
                    "requested": requests
                })
        detail['groups'] = [{y: detail['roommates'][y]
                             for y in x['members']} for x in combined]
    return jsonify(details)


@app.route("/api/event/<int:event>/hotel/matching_roommates", methods=["GET"])
def matching_roommates(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403

    room_nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).order_by(HotelRoomNight.date).all()
    room_nights = {x.id: x for x in room_nights}

    badges = db.query(Badge).join(HotelRoomRequest, HotelRoomRequest.badge == Badge.id).filter(
        or_(HotelRoomRequest.declined == False, HotelRoomRequest.declined == None)
    ).filter(Badge.event == event, Badge.search_name.contains(g.data.get('search', "").lower())).order_by(Badge.public_name).limit(20).all()

    results = []
    for badge in badges:
        missing = []
        for night in badge.room_night_requests:
            assign = False
            if night.requested:
                if room_nights[night.room_night].restricted:
                    for approval in badge.room_night_approvals:
                        if approval.room_night == night.room_night and approval.approved:
                            assign = True
                            break
                else:
                    assign = True
            for assignment in badge.room_night_assignments:
                if assignment.room_night == night.room_night:
                    assign = False
                    break
            if assign:
                missing.append(night.room_night)
        if missing:
            results.append({
                "missing_nights": missing,
                "id": badge.id,
                "name": badge.public_name,
            })

    return jsonify(results[:10])


@app.route("/api/event/<int:event>/hotel/room_search", methods=["GET"])
def room_search(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    count = db.query(HotelRoom).filter(HotelRoom.event == event).filter(
        HotelRoom.roommates.any(Badge.search_name.contains(g.data['search'].lower()))).count()
    offset = int(g.data.get('offset', '0'))
    rooms = db.query(HotelRoom).filter(HotelRoom.event == event).filter(
        HotelRoom.roommates.any(Badge.search_name.contains(g.data['search'].lower()))).order_by(HotelRoom.name).offset(offset).limit(10).all()

    # .join(RoomNightAssignment, RoomNightAssignment.hotel_room == HotelRoom.id).join(
    #    Badge, Badge.id == RoomNightAssignment.badge).filter(Badge.search_name.contains(g.data['search'].lower())).order_by(Badge.search_name).all()
    return jsonify(hotel_rooms=HotelRoom.serialize(rooms, serialize_relationships=True), count=count), 200


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/request_search", methods=["GET"])
def request_search(event, hotel_block):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    
    assigned_nights = db.query(RoomNightRequest.id).filter(RoomNightRequest.requested).join(
        RoomNightAssignment, and_(RoomNightAssignment.badge == RoomNightRequest.badge,
                                  RoomNightAssignment.room_night == RoomNightRequest.room_night)
    ).subquery()

    reqs = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.event == event,
        HotelRoomRequest.hotel_block == hotel_block,
        or_(HotelRoomRequest.declined == False, HotelRoomRequest.declined == None),
        HotelRoomRequest.room_night_requests.any(and_(RoomNightRequest.requested, not_(RoomNightRequest.id.in_(assigned_nights))))
    ).join(Badge, Badge.id == HotelRoomRequest.badge)
    if g.data['search_term']:
        reqs = reqs.filter(
            or_(Badge.search_name.contains(g.data['search_term'].lower()), func.lower(
                HotelRoomRequest.notes).contains(g.data['search_term'].lower()))
        )
    count = reqs.count()
    
    if g.data['sort'] == "notes":
        sort = HotelRoomRequest.notes
    else:
        sort = Badge.search_name
    if g.data['order'] == "desc":
        sort = sort.desc()
    reqs = reqs.order_by(sort).offset(int(g.data['offset'])).limit(int(g.data['limit'])).all()
    return jsonify(requests=HotelRoomRequest.serialize(reqs, serialize_relationships=True, deep=True), count=count), 200


@app.route("/api/event/<int:event>/hotel/submitted_requests", methods=["GET"])
def submitted_requests(event):
    if request.method == "GET":
        if not check_permission("hotel_request.*.read"):
            return "", 403
        subquery = db.query(RoomNightRequest.badge).filter(
            RoomNightRequest.event == event, RoomNightRequest.requested == True).distinct().subquery().select()
        rows = db.query(HotelRoomRequest.id, HotelRoomRequest.declined, HotelRoomRequest.notes, Badge.id, Badge.public_name).filter(
            HotelRoomRequest.event == event, HotelRoomRequest.badge.in_(subquery)).join(HotelRoomRequest, HotelRoomRequest.badge == Badge.id).all()
        results = []
        for ID, declined, notes, BID, public_name in rows:
            if not declined:
                results.append({
                    "id": ID,
                    "badge": BID,
                    "public_name": public_name,
                    "notes": notes
                })
        return jsonify(results)
    return "", 406


@app.route("/api/event/<int:event>/hotel/block_assignments", methods=["GET", "POST"])
def block_assignments(event):
    if request.method == "GET":
        if not check_permission("hotel_block.*.read", event=event):
            return "", 403
        subquery = db.query(RoomNightRequest.badge).filter(
            RoomNightRequest.event == event, RoomNightRequest.requested == True).distinct().subquery().select()
        query = db.query(Badge, HotelRoomRequest.declined, HotelRoomRequest.hotel_block, HotelRoomRequest.id, HotelRoomRequest.notes).options(joinedload(
            Badge.departments)).filter(HotelRoomRequest.event == event, HotelRoomRequest.badge.in_(subquery)).join(HotelRoomRequest, HotelRoomRequest.badge == Badge.id)
        if request.args.get("sort", "") == "notes":
            if request.args.get("order", "asc") == "asc":
                query = query.order_by(HotelRoomRequest.notes)
            else:
                query = query.order_by(HotelRoomRequest.notes.desc())
        if request.args.get("search_field", "") == "hotel_block":
            if request.args.get("search", "") == "-1":
                query = query.filter(HotelRoomRequest.hotel_block == None)
            else:
                query = query.filter(HotelRoomRequest.hotel_block == int(
                    request.args.get("search", "")))
        elif request.args.get("search_field", "") == "notes":
            query = query.filter(func.lower(HotelRoomRequest.notes).contains(
                request.args.get("search", "").lower()))
        query = paginate(query, Badge, event)
        count = request.args.get(
            "count", False, type=lambda x: x.lower() == 'true')
        if count:
            return jsonify(query.count())
        rows = query.all()
        badge_dicts = []
        for badge, declined, block, hrr, notes in rows:
            if not declined:
                badge_dicts.append({
                    "id": badge.id,
                    "notes": notes,
                    "public_name": badge.public_name,
                    "departments": [x.id for x in badge.departments],
                    "department_names": [x.name for x in badge.departments],
                    "badge_type": badge.badge_type,
                    "hotel_block": block,
                    "hotel_room_request": hrr
                })
        return jsonify(badge_dicts)
    elif request.method == "POST":
        if not check_permission("hotel_block.*.write", event=event):
            return "", 403
        room_requests = {x['id']: x['hotel_block'] for x in g.data['updates']}
        hotel_room_requests = db.query(HotelRoomRequest).filter(HotelRoomRequest.id.in_(
            room_requests.keys()), HotelRoomRequest.event == event).all()
        for hotel_room_request in hotel_room_requests:
            updated = room_requests[hotel_room_request.id]
            if updated == -1:
                updated = None
            hotel_room_request.hotel_block = updated
        db.commit()
        return "null", 200
    return "", 406


@app.route("/api/event/<int:event>/hotel/requests/<int:department>", methods=["GET"])
def hotel_requests(event, department):
    requests = db.query(Badge, HotelRoomRequest).join(BadgeToDepartment, BadgeToDepartment.badge == Badge.id).filter(
        BadgeToDepartment.department == department).join(HotelRoomRequest, HotelRoomRequest.badge == BadgeToDepartment.badge).all()
    res = []
    for req in requests:
        badge, roomrequest = req
        if not check_permission("hotel_request.*.approve", event=event, department=department):
            continue
        room_nights = db.query(RoomNightRequest, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.badge == RoomNightRequest.badge, RoomNightApproval.room_night ==
                                                                                                 RoomNightRequest.room_night, RoomNightApproval.department == department), isouter=True).filter(RoomNightRequest.badge == badge.id).all()
        res.append({
            "id": badge.id,
            "name": badge.public_name,
            "justification": roomrequest.room_night_justification,
            "room_nights": {
                btr.room_night: {
                    "id": btr.id,
                    "requested": btr.requested,
                    "room_night": btr.room_night,
                    "approved": rna.approved if rna else None
                } for btr, rna in room_nights}
        })
    res = sorted(res, key=lambda x: x['name'])
    return jsonify(res)


@app.route("/api/event/<int:event>/hotel/approve/<int:department>", methods=["POST"])
def hotel_approve(event, department):
    if check_permission("hotel_request.*.approve", event=event, department=department):
        room_night_request = db.query(RoomNightRequest).filter(
            RoomNightRequest.room_night == request.json['room_night'], RoomNightRequest.badge == request.json['badge']).one_or_none()
        if not room_night_request:
            return "Could not find corresponding request.", 404
        approval = db.query(RoomNightApproval).filter(RoomNightApproval.badge ==
                                                      request.json['badge'], RoomNightApproval.room_night == request.json['room_night'], RoomNightApproval.department == department).one_or_none()
        if request.json['approved'] is None:
            if approval:
                db.delete(approval)
        else:
            if not approval:
                approval = RoomNightApproval(
                    event=event, badge=request.json['badge'], department=department)
            approval.approved = request.json['approved']
            approval.room_night = request.json['room_night']
            db.add(approval)
        hotel_room_request = db.query(HotelRoomRequest).filter(
            HotelRoomRequest.badge == room_night_request.badge).one()
        db.add(room_night_request)
        db.commit()
        return "null", 200
    return "", 403


@app.route('/hotels/request_complete.png')
def request_complete():
    if not 'id' in request.args:
        resp = send_file(os.path.join(
            config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    id = request.args['id']
    badge = db.query(Badge).filter(Badge.uber_id == id).one_or_none()
    if not badge:
        resp = send_file(os.path.join(
            config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    req = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.badge == badge.id).one_or_none()
    if req:
        room_nights = db.query(RoomNightRequest).filter(
            RoomNightRequest.event == badge.event, RoomNightRequest.badge == badge.id).all()
        if room_nights:
            if (req.first_name and req.last_name and any([x.requested for x in room_nights])) or req.declined:
                return send_file(os.path.join(config.static_path, "checkbox_checked.png"))
    resp = send_file(os.path.join(
        config.static_path, "checkbox_unchecked.png"))
    resp.cache_control.max_age = 10
    return resp


@app.route("/api/event/<int:event>/hotel/request/<int:request_id>", methods=["GET", "PATCH"])
def hotel_request_single_api(event, request_id):
    if not check_permission("rooming.*.manage", event=event) and not check_permission(f"hotel_room_request.{request_id}.write", event=event):
        return "", 403
    if request.method == "GET":
        hotel_request = db.query(HotelRoomRequest).filter(
            HotelRoomRequest.id == request_id).one_or_none()
        if not hotel_request:
            return "Could not locate hotel room request", 404
        room_nights = []
        requested = db.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night ==
                                                                    HotelRoomNight.id).filter(RoomNightRequest.badge == hotel_request.badge).all()
        for req, night in requested:
            if check_permission("rooming.*.manage", event=event) or not night.hidden:
                room_nights.append({
                    "id": night.id,
                    "requested": req.requested,
                    "date": night.date,
                    "name": night.name,
                    "restricted": night.restricted,
                    "restriction_type": night.restriction_type,
                })
        all_room_nights = db.query(HotelRoomNight).filter(
            HotelRoomNight.event == event).all()
        for room_night in all_room_nights:
            for existing in room_nights:
                if existing['id'] == room_night.id:
                    break
            else:
                if check_permission("rooming.*.manage", event=event) or not room_night.hidden:
                    room_nights.append({
                        "id": room_night.id,
                        "requested": False,
                        "date": room_night.date,
                        "name": room_night.name,
                        "restricted": room_night.restricted,
                        "restriction_type": room_night.restriction_type
                    })
        room_nights.sort(key=lambda x: x['date'])
        return jsonify({
            "event": hotel_request.event,
            "badge": hotel_request.badge,
            "first_name": hotel_request.first_name or "",
            "last_name": hotel_request.last_name or "",
            "declined": hotel_request.declined,
            "prefer_department": hotel_request.prefer_department,
            "preferred_department": hotel_request.preferred_department,
            "notes": hotel_request.notes or "",
            "prefer_single_gender": hotel_request.prefer_single_gender,
            "preferred_gender": hotel_request.preferred_gender or "",
            "noise_level": hotel_request.noise_level or "",
            "smoke_sensitive": hotel_request.smoke_sensitive,
            "sleep_time": hotel_request.sleep_time or "",
            "room_night_justification": hotel_request.room_night_justification or "",
            "requested_roommates": [x.id for x in hotel_request.roommate_requests],
            "antirequested_roommates": [x.id for x in hotel_request.roommate_anti_requests],
            "room_nights": room_nights
        })
    elif request.method == "PATCH":
        hotel_request = db.query(HotelRoomRequest).filter(
            HotelRoomRequest.id == request_id).one_or_none()
        if not hotel_request:
            return "Could not locate hotel room request", 404
        hotel_request.first_name = g.data['first_name']
        hotel_request.last_name = g.data['last_name']
        hotel_request.declined = g.data['declined']
        hotel_request.prefer_department = g.data['prefer_department']
        hotel_request.preferred_department = g.data['preferred_department']
        hotel_request.notes = g.data['notes']
        hotel_request.prefer_single_gender = g.data['prefer_single_gender']
        hotel_request.preferred_gender = g.data['preferred_gender']
        hotel_request.noise_level = g.data['noise_level']
        hotel_request.smoke_sensitive = g.data['smoke_sensitive']
        hotel_request.sleep_time = g.data['sleep_time']
        hotel_request.room_night_justification = g.data['room_night_justification']
        hotel_request.roommate_requests = db.query(Badge).filter(
            Badge.id.in_(g.data['requested_roommates'])).all()
        hotel_request.roommate_anti_requests = db.query(Badge).filter(
            Badge.id.in_(g.data['antirequested_roommates'])).all()
        db.add(hotel_request)
        requested = db.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night ==
                                                                    HotelRoomNight.id).filter(RoomNightRequest.badge == hotel_request.badge).all()
        night_status = {}
        for req, night in requested:
            night_status[night.id] = req
        for room_night_request in g.data['room_nights']:
            if room_night_request['id'] in night_status:
                night_status[room_night_request['id']
                             ].requested = room_night_request['requested']
                db.add(night_status[room_night_request['id']])
            else:
                requested_night = RoomNightRequest(
                    event=event, badge=hotel_request.badge, requested=room_night_request['requested'], room_night=room_night_request['id'])
                db.add(requested_night)
        db.commit()
        return "null", 200


@app.route("/api/event/<int:event>/hotel/request", methods=["GET", "PATCH"])
def hotel_request_api(event):
    if not check_permission("rooming.*.request", event=event):
        return "", 403
    if g.user:
        badge = db.query(Badge).filter(Badge.event == event,
                                       Badge.user == g.user.id).one_or_none()
    elif g.badge:
        badge = g.badge
    if not badge:
        return "Could not locate badge", 404
    hotel_request = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.badge == badge.id).one_or_none()
    if not hotel_request:
        return "Could not locate hotel room request", 404
    return hotel_request_single_api(event, hotel_request.id)


@app.route("/api/event/<int:event>/hotel/export_passkey", methods=["GET"])
def export_passkey(event):
    if not check_permission("rooming.*.assignment", event=event):
        return "", 403

    fields = [
            'Block', 'First Name', 'Last Name', 'Guest Email Address for confirmation purposes', 'Special Requests',
            'Arrival', 'Departure', 'City', 'State', 'Zip', 'GUEST COUNTRY', 'Telephone',
            'Payment Type', 'Card #', 'Exp.',
            'BILLING ADDRESS', 'BILLING CITY', 'BILLING STATE', 'BILLING ZIP CODE', 'BILLING COUNTRY',
            'Additional Guest First Name-2', 'Additional Guest Last Name-2',
            'Additional Guest First Name-3', 'Additional Guest Last Name3',  # No, this is not a typo
            'Additional Guest First Name-4', 'Additional Guest Last Name-4',
            'Notes', 'Emails',
        ]

    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    room_nights = {x.id: x for x in room_nights}
    completed_rooms = db.query(HotelRoom).filter(HotelRoom.completed == True, HotelRoom.event == event).all()
    hotel_blocks = db.query(HotelRoomBlock).filter(HotelRoomBlock.event == event).all()
    hotel_blocks = {x.id: x for x in hotel_blocks}

    result = ",".join(fields)+"\n"
    for room in completed_rooms:
        rnas = room.room_night_assignments
        if not rnas:
            continue
        fnames = ["","","",""]
        lnames = ["","","",""]
        emails = []
        arrival = room_nights[rnas[0].room_night].date
        departure = room_nights[rnas[0].room_night].date
        for rna in rnas:
            if room_nights[rna.room_night].date < arrival:
                arrival = room_nights[rna.room_night].date
            if room_nights[rna.room_night].date > departure:
                departure = room_nights[rna.room_night].date
        departure += datetime.timedelta(days=1)
        for idx, roommate in enumerate(room.roommates[:4]):
            if roommate.room_night_requests:
                if roommate.hotel_room_request[0].first_name:
                    fnames[idx] = roommate.hotel_room_request[0].first_name
                else:
                    fnames[idx] = roommate.first_name
                if roommate.hotel_room_request[0].last_name:
                    lnames[idx] = roommate.hotel_room_request[0].last_name
                else:
                    lnames[idx] = roommate.last_name
            else:
                fnames[idx] = roommate.first_name
                lnames[idx] = roommate.last_name
            emails.append(roommate.email)
        notes = room.notes
        result += f'"{hotel_blocks[room.hotel_block].name}","{fnames[0]}","{lnames[0]}","{emails[0]}",,"{arrival.strftime("%m/%d/%Y")}","{departure.strftime("%m/%d/%Y")}",,,,,,,,,,,,,,"{fnames[1]}","{lnames[1]}","{fnames[2]}","{lnames[2]}","{fnames[3]}","{lnames[3]}","{notes}","{",".join(emails)}"\n'

    headers = {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=rooms.csv",
    }
    return Response(result, headers=headers)
