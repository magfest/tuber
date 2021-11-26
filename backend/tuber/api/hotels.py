from tuber import app, config
from flask import send_file, request, jsonify, escape
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
import os
from tuber.api import *
from .room_matcher import rematch_hotel_block

def update_room_request_props(db, reqs, assigned=None, requested=None, approved=None):
    if not reqs:
        return
    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == reqs[0].event).all()
    room_night_lookup = {x.id: x for x in room_nights}
    for req in reqs:
        req.requested = False
        req.approved = False
        if not req.declined:
            for rnr in req.room_night_requests:
                if rnr.requested:
                    req.requested = True
                    if not room_night_lookup[rnr.room_night].restricted:
                        req.approved = True
                    else:
                        for rna in req.room_night_approvals:
                            if rna.room_night == rnr.room_night and rna.approved:
                                req.approved = True

        req.assigned = bool(req.room_night_assignments)
        if not assigned is None:
            req.assigned = assigned
        if not requested is None:
            req.requested = requested
        if not approved is None:
            req.approved = approved

@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/room/<int:room_id>/remove_roommates", methods=["POST"])
def remove_roommates(event, hotel_block, room_id):
    if not check_permission(f'hotel_block.{hotel_block}.write', event=event):
        return "", 403
    db.query(RoomNightAssignment).filter(RoomNightAssignment.event==event, RoomNightAssignment.hotel_room==room_id, RoomNightAssignment.badge.in_(g.data['roommates'])).delete()
    reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event==event, HotelRoomRequest.badge.in_(g.data['roommates'])).all()
    update_room_request_props(db, reqs, assigned=False)
    for req in reqs:
        db.add(req)
    db.commit()
    return "null", 200

@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/room/<int:room_id>/add_roommates", methods=["POST"])
def add_roommates(event, hotel_block, room_id):
    if not check_permission(f'hotel_block.{hotel_block}.write', event=event):
        return "", 403
    reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event==event, HotelRoomRequest.badge.in_(g.data['roommates'])).all()
    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event==event).all()
    room_nights = {x.id: x for x in room_nights}
    for req in reqs:
        for night in req.room_night_requests:
            assign = False
            if night.requested:
                if room_nights[night.room_night].restricted:
                    for approval in req.room_night_approvals:
                        if approval.room_night == night.room_night and approval.approved:
                            assign = True
                            break
                else:
                    assign = True
            for assignment in req.room_night_assignments:
                if assignment.room_night == night.room_night:
                    assign = False
                    break
            if assign:
                db.add(RoomNightAssignment(event=event, badge=req.badge, room_night=night.room_night, hotel_room=room_id))
    update_room_request_props(db, reqs, assigned=True)
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

@app.route("/api/event/<int:event>/hotel/room_details", methods=["GET"])
def room_details(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    rooms = [int(x) for x in g.data['rooms'].split(",")]

    rnas = db.query(RoomNightAssignment, Badge.public_name).join(Badge, Badge.id == RoomNightAssignment.badge).filter(RoomNightAssignment.hotel_room.in_(rooms)).all()

    details = {}
    for rna, public_name in rnas:
        if not rna.hotel_room in details:
            details[rna.hotel_room] = {
                "room_nights": [],
                "roommates": {},
                "empty_slots": 0
            }
        if not rna.room_night in details[rna.hotel_room]['room_nights']:
            details[rna.hotel_room]['room_nights'].append(rna.room_night)

        if not rna.badge in details[rna.hotel_room]['roommates']:
            details[rna.hotel_room]['roommates'][rna.badge] = {
                "id": rna.badge,
                "name": public_name,
                "errors": set()
            }

    gender_prefs = {}

    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    room_nights = {x.id: x for x in room_nights}
    hotel_rooms = db.query(HotelRoom, HotelRoomRequest).join(RoomNightAssignment, HotelRoom.id == RoomNightAssignment.hotel_room).join(HotelRoomRequest, HotelRoomRequest.badge == RoomNightAssignment.badge).filter(HotelRoom.id.in_(rooms)).options(joinedload(HotelRoomRequest.room_night_approvals)).options(joinedload(HotelRoomRequest.room_night_requests)).all()
    for hotel_room, request in hotel_rooms:
        if not hotel_room.id in gender_prefs:
            gender_prefs[hotel_room.id] = set()
        gender_prefs[hotel_room.id].add(config.gender_map.get(request.preferred_gender, "Unknown"))
    for hotel_room, request in hotel_rooms:
        for roommate_request in request.roommate_requests:
            if not roommate_request in hotel_room.roommates:
                details[hotel_room.id]['roommates'][request.badge]['errors'].add('Missing Roommate')
        for antiroommate_request in request.roommate_anti_requests:
            if antiroommate_request in hotel_room.roommates:
                details[hotel_room.id]['roommates'][request.badge]['errors'].add('Anti-requested Roommate')
        nights = set()
        for night_request in request.room_night_requests:
            if night_request.requested:
                if room_nights[night_request.room_night].restricted:
                    for approval in request.room_night_approvals:
                        if approval.room_night == night_request.room_night and approval.approved:
                            nights.add(night_request.room_night)
                else:
                    nights.add(night_request.room_night)
        extra_nights = nights.symmetric_difference(set(details[hotel_room.id]['room_nights']))
        if extra_nights:
            details[hotel_room.id]['roommates'][request.badge]['errors'].add(f'Extra Room Night ({len(extra_nights)})')
        if request.prefer_single_gender and len(gender_prefs[hotel_room.id]) > 1:
            details[hotel_room.id]['roommates'][request.badge]['errors'].add(f'Gender Mismatch ({request.preferred_gender}) ({", ".join(gender_prefs[hotel_room.id])})')
        details[hotel_room.id]['roommates'][request.badge]['errors'] = list(details[hotel_room.id]['roommates'][request.badge]['errors'])
        details[hotel_room.id]['empty_slots'] += len(set(details[hotel_room.id]['room_nights']).difference(nights))
    return jsonify(details)


@app.route("/api/event/<int:event>/hotel/room_search", methods=["GET"])
def room_search(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    rooms = db.query(HotelRoom).filter(HotelRoom.event==event).join(RoomNightAssignment, RoomNightAssignment.hotel_room==HotelRoom.id).join(Badge, Badge.id==RoomNightAssignment.badge).filter(Badge.search_name.contains(g.data['search'].lower())).limit(10).all()
    return jsonify(HotelRoom.serialize(rooms, serialize_relationships=True)), 200

@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/request_search", methods=["GET"])
def request_search(event, hotel_block):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    reqs = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.event == event,
        HotelRoomRequest.hotel_block == hotel_block,
        HotelRoomRequest.approved==True,
        HotelRoomRequest.assigned==False
    ).join(Badge, Badge.id==HotelRoomRequest.badge).filter(
        Badge.search_name.contains(g.data['search_term'])
    ).order_by(g.data['sort']).offset(int(g.data['offset'])).limit(int(g.data['limit'])).all()
    count = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.event == event,
        HotelRoomRequest.hotel_block == hotel_block,
        HotelRoomRequest.approved==True,
        HotelRoomRequest.assigned==False
    ).join(Badge, Badge.id==HotelRoomRequest.badge).filter(
        Badge.search_name.contains(g.data['search_term'])
    ).count()
    return jsonify(requests=HotelRoomRequest.serialize(reqs, serialize_relationships=True, deep=True), count=count), 200

@app.route("/api/event/<int:event>/hotel/submitted_requests", methods=["GET"])
def submitted_requests(event):
    if request.method == "GET":
        if not check_permission("hotel_request.*.read"):
            return "", 403
        subquery = db.query(RoomNightRequest.badge).filter(RoomNightRequest.event == event, RoomNightRequest.requested == True).distinct().subquery().select()
        rows = db.query(HotelRoomRequest.id, HotelRoomRequest.declined, HotelRoomRequest.notes, Badge.id, Badge.public_name).filter(HotelRoomRequest.event == event, HotelRoomRequest.badge.in_(subquery)).join(HotelRoomRequest, HotelRoomRequest.badge == Badge.id).all()
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
        subquery = db.query(RoomNightRequest.badge).filter(RoomNightRequest.event == event, RoomNightRequest.requested == True).distinct().subquery().select()
        rows = db.query(Badge, HotelRoomRequest.declined, HotelRoomRequest.hotel_block, HotelRoomRequest.id, HotelRoomRequest.notes).options(joinedload('departments')).filter(HotelRoomRequest.event == event, HotelRoomRequest.badge.in_(subquery)).join(HotelRoomRequest, HotelRoomRequest.badge == Badge.id).all()
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
        hotel_room_requests = db.query(HotelRoomRequest).filter(HotelRoomRequest.id.in_(room_requests.keys()), HotelRoomRequest.event == event).all()
        for hotel_room_request in hotel_room_requests:
            hotel_room_request.hotel_block = room_requests[hotel_room_request.id]
        db.commit()
        return "null", 200
    return "", 406

@app.route("/api/event/<int:event>/hotel/requests/<int:department>", methods=["GET"])
def hotel_requests(event, department):
    requests = db.query(Badge, HotelRoomRequest).join(BadgeToDepartment, BadgeToDepartment.badge == Badge.id).filter(BadgeToDepartment.department == department).join(HotelRoomRequest, HotelRoomRequest.badge == BadgeToDepartment.badge).all()
    res = []
    for req in requests:
        badge, roomrequest = req
        if not check_permission("hotel_request.*.approve", event=event, department=department):
            continue
        room_nights = db.query(RoomNightRequest, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.badge == RoomNightRequest.badge, RoomNightApproval.room_night == RoomNightRequest.room_night, RoomNightApproval.department == department), isouter=True).filter(RoomNightRequest.badge == badge.id).all()
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
        room_night_request = db.query(RoomNightRequest).filter(RoomNightRequest.room_night == request.json['room_night'], RoomNightRequest.badge == request.json['badge']).one_or_none()
        if not room_night_request:
            return "Could not find corresponding request.", 404
        approval = db.query(RoomNightApproval).filter(RoomNightApproval.badge == request.json['badge'], RoomNightApproval.room_night == request.json['room_night'], RoomNightApproval.department == department).one_or_none()
        if request.json['approved'] is None:
            if approval:
                db.delete(approval)
        else:
            if not approval:
                approval = RoomNightApproval(event=event, badge=request.json['badge'], department=department)
            approval.approved = request.json['approved']
            approval.room_night = request.json['room_night']
            db.add(approval)
        hotel_room_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == room_night_request.badge).one()
        update_room_request_props(db, [hotel_room_request,])
        db.add(room_night_request)
        db.commit()
        return "null", 200
    return "", 403

@app.route('/hotels/request_complete.png')
def request_complete():
    if not 'id' in request.args:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    id = request.args['id']
    badge = db.query(Badge).filter(Badge.uber_id == id).one_or_none()
    if not badge:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    req = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if req:
        room_nights = db.query(RoomNightRequest).filter(RoomNightRequest.event == badge.event, RoomNightRequest.badge == badge.id).all()
        if room_nights:
            if (req.first_name and req.last_name and any([x.requested for x in room_nights])) or req.declined:
                return send_file(os.path.join(config.static_path, "checkbox_checked.png"))
    resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
    resp.cache_control.max_age = 10
    return resp

@app.route("/api/event/<int:event>/hotel/request/<int:request_id>", methods=["GET", "PATCH"])
def hotel_request_single_api(event, request_id):
    if not check_permission("rooming.*.manage", event=event) and not check_permission(f"hotel_room_request.{request_id}.write", event=event):
        return "", 403
    if request.method == "GET":
        hotel_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.id == request_id).one_or_none()
        if not hotel_request:
            return "Could not locate hotel room request", 404
        room_nights = []
        requested = db.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night == HotelRoomNight.id).filter(RoomNightRequest.badge == hotel_request.badge).all()
        for req, night in requested:
            if not night.hidden:
                room_nights.append({
                    "id": night.id,
                    "requested": req.requested,
                    "date": night.date,
                    "name": night.name,
                    "restricted": night.restricted,
                    "restriction_type": night.restriction_type,
                })
        all_room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
        for room_night in all_room_nights:
            for existing in room_nights:
                if existing['id'] == room_night.id:
                    break
            else:
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
        hotel_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.id == request_id).one_or_none()
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
        hotel_request.roommate_requests = db.query(Badge).filter(Badge.id.in_(g.data['requested_roommates'])).all()
        hotel_request.roommate_anti_requests = db.query(Badge).filter(Badge.id.in_(g.data['antirequested_roommates'])).all()
        db.add(hotel_request)
        requested = db.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night == HotelRoomNight.id).filter(RoomNightRequest.badge == hotel_request.badge).all()
        night_status = {}
        for req, night in requested:
            night_status[night.id] = req
        for room_night_request in g.data['room_nights']:
            if room_night_request['id'] in night_status:
                night_status[room_night_request['id']].requested = room_night_request['requested']
                db.add(night_status[room_night_request['id']])
            else:
                requested_night = RoomNightRequest(event=event, badge=hotel_request.badge, requested=room_night_request['requested'], room_night=room_night_request['id'])
                db.add(requested_night)
        db.commit()
        return "null", 200

@app.route("/api/event/<int:event>/hotel/request", methods=["GET", "PATCH"])
def hotel_request_api(event):
    if not check_permission("rooming.*.request", event=event):
        return "", 403
    if not g.badge:
        return "Could not locate badge", 404
    hotel_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == g.badge.id).one_or_none()
    if not hotel_request:
        return "Could not locate hotel room request", 404
    return hotel_request_single_api(event, hotel_request.id)

@app.route("/api/event/<int:event>/hotel/update_requests", methods=["POST"])
def update_requests(event):
    if not check_permission("rooming.*.admin"):
        return "", 403
    updates = {
        "requests": {},
        "badges": {}
    }
    badges = db.query(Badge).filter(Badge.event == event).all()
    for badge in badges:
        if not badge.public_name and badge.printed_name:
            badge.public_name = badge.printed_name
            updates['badges'][badge.id] = badge.public_name
            db.add(badge)
    badgeLookup = {x.id: x for x in badges}

    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    room_night_lookup = {x.id: x for x in room_nights}
    block = db.query(HotelRoomBlock).filter(HotelRoomBlock.event == event).first()

    reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event).options(joinedload('room_night_requests')).all()
    for req in reqs:
        req.requested = False
        req.approved = False
        if not req.declined:
            for rnr in req.room_night_requests:
                if rnr.requested:
                    req.requested = True
                    if not room_night_lookup[rnr.room_night].restricted:
                        req.approved = True
                    else:
                        for rna in req.room_night_approvals:
                            if rna.room_night == rnr.room_night and rna.approved:
                                req.approved = True

        req.assigned = bool(req.room_night_assignments)
        updates['requests'][req.id] = {
            "requested": req.requested,
            "approved": req.approved,
            "assigned": req.assigned
        }

        badge_name = " "
        badge = badgeLookup[req.badge]
        if badge.public_name:
            badge_name = badge.public_name
        elif badge.search_name:
            badge_name = " ".join([x.capitalize() for x in badge.search_name.split(" ")])
        elif badge.legal_name:
            badge_name = badge.legal_name
        elif badge.printed_name:
            badge_name = badge.printed_name

        badge_first_name = badge.first_name
        if not badge_first_name:
            badge_first_name = badge_name.split(" ")[0]

        badge_last_name = badge.last_name
        if not badge_last_name:
            badge_last_name = badge_name.split(" ", 1)[1]

        if not req.first_name:
            if badge_first_name:
                req.first_name = badge_first_name
                updates['requests'][req.id]['first_name'] = req.first_name
        if not req.last_name:
            if badge_last_name:
                req.last_name = badge_last_name
                updates['requests'][req.id]['last_name'] = req.last_name

        if not req.hotel_block:
            req.hotel_block = block.id
        db.add(req)

    

    db.commit()
    return jsonify(updates), 200

@HotelRoom.onchange
@RoomNightRequest.onchange
@RoomNightAssignment.onchange
@RoomNightApproval.onchange
@HotelRoomRequest.onchange
@HotelRoomNight.onchange
def update_room_request(db, instance, deleted=None):
    reqs = []
    if request.method == "DELETE" and type(instance) is HotelRoom:
        print(f"Deleting hotel room {deleted['name']}")
        print(deleted)
        reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge.in_(deleted['roommates'])).all()
    elif type(instance) is RoomNightRequest or type(instance) is RoomNightAssignment or type(instance) is RoomNightApproval:
        reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == instance.badge).all()
    elif type(instance) is HotelRoomRequest:
        reqs = [instance]
    elif type(instance) is HotelRoomNight:
        reqs = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == instance.event).options(joinedload('room_night_requests')).options(joinedload('room_night_approvals')).options(joinedload('room_night_assignments')).all()
    update_room_request_props(db, reqs)
    if not type(instance) is HotelRoomRequest:
        for req in reqs:
            db.add(req)