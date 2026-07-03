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
from .night_approval import (approved_night_ids, manual_approved_night_ids,
                             shift_hours_totals, shift_satisfied_night_ids)
from .room_matcher import (clear_hotel_block, match_block,
                           rematch_hotel_block, suggest_roommates)
from .uber import export_requests
from .util import paginate
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
    """Clear unaccepted suggestions and produce a fresh batch. Hand-built
       (non-suggested) rooms are never touched."""
    if not check_permission(f"hotel_block.{hotel_block}.write", event=event):
        return "", 403
    created = rematch_hotel_block(db, event, hotel_block)
    return jsonify({"created": created})


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/suggest_rooms", methods=["POST"])
def suggest_rooms(event, hotel_block):
    """Run the matcher over unhoused people, creating persisted suggested
       rooms to accept (PATCH completed=true) or reject (DELETE) one by one."""
    if not check_permission(f"hotel_block.{hotel_block}.write", event=event):
        return "", 403
    created = match_block(db, event, hotel_block)
    return jsonify({"created": created})


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/clear_matches", methods=["POST"])
def clear_matches(event, hotel_block):
    """Delete unaccepted suggested rooms, returning their occupants to the
       matching pool. Hand-built rooms are never touched."""
    if not check_permission(f"hotel_block.{hotel_block}.write", event=event):
        return "", 403
    clear_hotel_block(db, event, hotel_block, suggested_only=True)
    return "[]", 200


@app.route("/api/event/<int:event>/hotel/room/<int:room_id>/suggest_roommates", methods=["GET"])
def hotel_suggest_roommates(event, room_id):
    """Best additions to a room per the matcher's scoring, drawn from people
       not in any completed room."""
    if not check_permission("hotel_block.*.read", event=event):
        return "", 403
    room = db.query(HotelRoom).filter(
        HotelRoom.id == room_id, HotelRoom.event == event).options(
        selectinload(HotelRoom.roommates),
        selectinload(HotelRoom.room_night_assignments)).one_or_none()
    if not room:
        return "Could not locate room", 404
    limit = request.args.get("limit", 10, type=int)
    return jsonify(suggest_roommates(db, event, room, limit=limit))


def _room_details_data(event, rooms):
    """Per-room roommate details, validation errors, and request groups for a
       list of room ids. Shared by the bulk room_details endpoint, the room
       modal endpoint, and the dashboard error sweep."""
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
            Badge.id, Badge.public_name),
        selectinload(
            HotelRoomRequest.roommate_anti_requests).load_only(Badge.id, Badge.public_name),
        selectinload(HotelRoomRequest.room_night_requests).load_only(
            RoomNightRequest.room_night, RoomNightRequest.requested),
        selectinload(HotelRoom.roommates).load_only(
            Badge.id, Badge.public_name),
    ).all()

    approved = approved_night_ids(db, event, badges)

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
                approved_nights = set()
                for roommate in hotel_room.roommates:
                    approved_nights.update(approved[roommate.id])
                if night_request.room_night in approved_nights:
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
    return details


@app.route("/api/event/<int:event>/hotel/room_details", methods=["GET"])
def room_details(event):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    rooms = [int(x) for x in g.data['rooms'].split(",")]
    return jsonify(_room_details_data(event, rooms))


@app.route("/api/event/<int:event>/hotel/room_search", methods=["GET"])
def room_search(event):
    """Filterable, sortable room listing. All parameters are optional:
       search (matches room name or a roommate's name), hotel_block,
       hotel_location, suggested (true/false),
       status (completed|incomplete|locked|unlocked),
       sort (name|created|modified), order (asc|desc), offset, limit."""
    if not check_permission("hotel_block.*.read"):
        return "", 403
    query = db.query(HotelRoom).filter(HotelRoom.event == event)
    if g.data.get('hotel_block'):
        query = query.filter(HotelRoom.hotel_block == int(g.data['hotel_block']))
    if g.data.get('hotel_location'):
        query = query.filter(HotelRoom.hotel_location == int(g.data['hotel_location']))
    if g.data.get('suggested'):
        if g.data['suggested'].lower() == 'true':
            query = query.filter(HotelRoom.suggested == True)
        else:
            query = query.filter(or_(HotelRoom.suggested == False,
                                     HotelRoom.suggested == None))
    status = g.data.get('status')
    if status == 'completed':
        query = query.filter(HotelRoom.completed == True)
    elif status == 'incomplete':
        query = query.filter(or_(HotelRoom.completed == False,
                                 HotelRoom.completed == None))
    elif status == 'locked':
        query = query.filter(HotelRoom.locked == True)
    elif status == 'unlocked':
        query = query.filter(or_(HotelRoom.locked == False,
                                 HotelRoom.locked == None))
    if g.data.get('search'):
        term = g.data['search'].lower()
        query = query.filter(or_(
            func.lower(HotelRoom.name).contains(term),
            HotelRoom.roommates.any(Badge.search_name.contains(term))))
    count = query.count()
    sorts = {
        "name": HotelRoom.name,
        "created": HotelRoom.created,
        "modified": HotelRoom.modified,
    }
    sort = sorts.get(g.data.get('sort'), HotelRoom.name)
    if g.data.get('order') == 'desc':
        sort = sort.desc()
    offset = int(g.data.get('offset', '0'))
    limit = int(g.data.get('limit', '10'))
    rooms = query.order_by(sort).offset(offset).limit(limit).all()
    return jsonify(hotel_rooms=HotelRoom.serialize(rooms, serialize_relationships=True), count=count), 200


@app.route("/api/event/<int:event>/hotel/<int:hotel_block>/request_search", methods=["GET"])
def request_search(event, hotel_block):
    if not check_permission("hotel_block.*.read"):
        return "", 403
    
    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    
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
    if g.data.get('search_term'):
        reqs = reqs.filter(
            or_(Badge.search_name.contains(g.data['search_term'].lower()), func.lower(
                HotelRoomRequest.notes).contains(g.data['search_term'].lower()))
        )
    if g.data.get('night'):
        reqs = reqs.filter(HotelRoomRequest.room_night_requests.any(and_(
            RoomNightRequest.requested,
            RoomNightRequest.room_night == int(g.data['night']))))
    if g.data.get('has_roommates', '').lower() == 'true':
        reqs = reqs.filter(HotelRoomRequest.roommate_requests.any())

    # Base ordering in SQL; computed filters/sorts below preserve it for ties.
    if g.data.get('sort') == "notes":
        sort = HotelRoomRequest.notes
    else:
        sort = Badge.search_name
    if g.data.get('order') == "desc":
        sort = sort.desc()
    reqs = reqs.order_by(sort).all()

    approved = approved_night_ids(db, event, [x.badge for x in reqs])
    requested_map = {req.id: {y.room_night for y in req.room_night_requests if y.requested}
                     for req in reqs}

    # Approval coverage is computed, so it filters after the SQL query.
    approval = g.data.get('approval')
    if approval == 'full':
        reqs = [x for x in reqs if requested_map[x.id] <= approved[x.badge]]
    elif approval == 'partial':
        reqs = [x for x in reqs if requested_map[x.id] - approved[x.badge]]

    if g.data.get('sort') == 'nights':
        reqs.sort(key=lambda x: len(requested_map[x.id]),
                  reverse=g.data.get('order') == 'desc')

    count = len(reqs)
    offset = int(g.data.get('offset', 0))
    limit = int(g.data.get('limit', 25))
    reqs = reqs[offset:offset + limit]

    results = [{
        "id": req.id,
        "approved_nights": {x.id: x.id in approved[req.badge] and x.id in requested_map[req.id] for x in room_nights},
        "requested_nights": {x.id: x.id in requested_map[req.id] for x in room_nights},
        "notes": req.notes,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "public_name": req.badge_obj.public_name,
        "badge": req.badge,
    } for req in reqs]
    return jsonify(requests=results, results=results, count=count), 200


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
    if not check_permission("hotel_request.*.approve", event=event, department=department):
        return "", 403
    requests = db.query(Badge, HotelRoomRequest).join(BadgeToDepartment, BadgeToDepartment.badge == Badge.id).filter(
        BadgeToDepartment.department == department).join(HotelRoomRequest, HotelRoomRequest.badge == BadgeToDepartment.badge).all()
    badge_ids = [badge.id for badge, _ in requests]
    nights = {x.id: x for x in db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).all()}
    shift_satisfied = shift_satisfied_night_ids(db, event, badge_ids)
    manual = manual_approved_night_ids(db, event, badge_ids)
    hours = shift_hours_totals(db, event, badge_ids)
    res = []
    for badge, roomrequest in requests:
        room_nights = db.query(RoomNightRequest, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.badge == RoomNightRequest.badge, RoomNightApproval.room_night ==
                                                                                                 RoomNightRequest.room_night, RoomNightApproval.department == department), isouter=True).filter(RoomNightRequest.badge == badge.id).all()
        night_status = {}
        for btr, rna in room_nights:
            night = nights.get(btr.room_night)
            mode = night.restriction_mode if night else 'none'
            status = {
                "id": btr.id,
                "requested": btr.requested,
                "room_night": btr.room_night,
                "mode": mode,
                "approved_by_anyone": btr.room_night in manual[badge.id],
                "approved_by_shifts": btr.room_night in shift_satisfied[badge.id],
                "approved": rna.approved if rna else None
            }
            if mode == 'shift_hours' and night:
                status["hours_required"] = night.shift_hours_required
                status["hours_assigned"] = round(hours.get(badge.id, 0), 1)
                status["hours_met"] = btr.room_night in shift_satisfied[badge.id]
            night_status[btr.room_night] = status
        res.append({
            "id": badge.id,
            "name": badge.public_name,
            "justification": roomrequest.room_night_justification,
            "room_nights": night_status
        })
    res = sorted(res, key=lambda x: x['name'])
    return jsonify(res)


def _isoz(dt):
    """Naive-UTC datetime -> ISO 8601 with Z suffix (or None)."""
    if not dt:
        return None
    return dt.replace(tzinfo=None).isoformat() + "Z"


@app.route("/api/event/<int:event>/hotel/attendee/approve", methods=["POST"])
def hotel_attendee_approve(event):
    """Toggle an event-level manual approval for a badge's room night.
       Turning approval off removes all approvals for that badge+night."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    badge = int(g.data["badge"])
    room_night = int(g.data["room_night"])
    if g.data["approved"]:
        approval = db.query(RoomNightApproval).filter(
            RoomNightApproval.badge == badge,
            RoomNightApproval.room_night == room_night,
            RoomNightApproval.department == None).one_or_none()
        if not approval:
            approval = RoomNightApproval(
                event=event, badge=badge, room_night=room_night, department=None)
        approval.approved = True
        db.add(approval)
    else:
        db.query(RoomNightApproval).filter(
            RoomNightApproval.badge == badge,
            RoomNightApproval.room_night == room_night).delete()
    db.commit()
    return jsonify({"approved": bool(g.data["approved"])})


@app.route("/api/event/<int:event>/hotel/attendee/request", methods=["POST"])
def hotel_attendee_request(event):
    """Toggle whether a badge has requested a room night."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    badge = int(g.data["badge"])
    room_night = int(g.data["room_night"])
    requested = bool(g.data["requested"])
    night_request = db.query(RoomNightRequest).filter(
        RoomNightRequest.badge == badge,
        RoomNightRequest.room_night == room_night).one_or_none()
    if not night_request:
        night_request = RoomNightRequest(
            event=event, badge=badge, room_night=room_night)
    night_request.requested = requested
    db.add(night_request)
    db.commit()
    return jsonify({"requested": requested})


@app.route("/api/event/<int:event>/hotel/attendee/assign", methods=["POST"])
def hotel_attendee_assign(event):
    """Toggle a room night assignment (without a room) for a badge.
       Turning assignment off removes the badge from any room for that night."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    badge = int(g.data["badge"])
    room_night = int(g.data["room_night"])
    if g.data["assigned"]:
        existing = db.query(RoomNightAssignment).filter(
            RoomNightAssignment.badge == badge,
            RoomNightAssignment.room_night == room_night).count()
        if not existing:
            db.add(RoomNightAssignment(
                event=event, badge=badge, room_night=room_night, hotel_room=None))
    else:
        db.query(RoomNightAssignment).filter(
            RoomNightAssignment.badge == badge,
            RoomNightAssignment.room_night == room_night).delete()
    db.commit()
    return jsonify({"assigned": bool(g.data["assigned"])})


@app.route("/api/event/<int:event>/hotel/attendee/<int:badge_id>", methods=["GET"])
def hotel_attendee_detail(event, badge_id):
    """Everything needed to understand one person's situation: their shift
       schedule, each room night's window and status, their room request, and
       the rooms they're assigned to."""
    if not (check_permission("rooming.*.manage", event=event)
            or check_permission("hotel_block.*.read", event=event)):
        return "", 403
    badge = db.query(Badge).filter(
        Badge.id == badge_id, Badge.event == event).options(
        selectinload(Badge.departments)).one_or_none()
    if not badge:
        return "Could not locate badge", 404
    shift_nights = shift_satisfied_night_ids(db, event, [badge.id])[badge.id]
    manual_nights = manual_approved_night_ids(db, event, [badge.id])[badge.id]
    hours = shift_hours_totals(db, event, [badge.id]).get(badge.id, 0)
    night_requests = {x.room_night: bool(x.requested) for x in db.query(
        RoomNightRequest).filter(RoomNightRequest.badge == badge.id).all()}
    assignments = db.query(RoomNightAssignment).filter(
        RoomNightAssignment.badge == badge.id).all()
    assigned = {x.room_night for x in assignments}
    assigned_rooms = {x.room_night: x.hotel_room for x in assignments}
    nights = []
    for night in db.query(HotelRoomNight).filter(
            HotelRoomNight.event == event).order_by(HotelRoomNight.date).all():
        entry = {
            "id": night.id,
            "name": night.name,
            "date": night.date.strftime("%Y-%m-%d") if night.date else None,
            "restricted": night.restriction_mode != 'none',
            "mode": night.restriction_mode,
            "restriction_type": night.restriction_type,
            "shift_starttime": _isoz(night.shift_starttime),
            "shift_endtime": _isoz(night.shift_endtime),
            "requested": night_requests.get(night.id, False),
            "has_shift": night.id in shift_nights,
            "approved": night.id in manual_nights,
            "assigned": night.id in assigned,
            "assigned_room": assigned_rooms.get(night.id),
        }
        if night.restriction_mode == 'shift_hours':
            entry["hours_required"] = night.shift_hours_required
            entry["hours_assigned"] = round(hours, 1)
        nights.append(entry)
    shifts = []
    for shift, job, department in db.query(Shift, Job, Department).join(
            ShiftAssignment, ShiftAssignment.shift == Shift.id).join(
            Job, Shift.job == Job.id).outerjoin(
            Department, Job.department == Department.id).filter(
            ShiftAssignment.badge == badge.id).order_by(Shift.starttime).all():
        shifts.append({
            "job": job.name,
            "department": department.name if department else None,
            "starttime": _isoz(shift.starttime),
            "duration": shift.duration,
        })
    # The rooms this person occupies, with the nights they hold there and who
    # they share with.
    rooms = []
    room_ids = sorted({x.hotel_room for x in assignments if x.hotel_room})
    if room_ids:
        blocks = {x.id: x.name for x in db.query(HotelRoomBlock).filter(
            HotelRoomBlock.event == event).all()}
        for room in db.query(HotelRoom).filter(
                HotelRoom.id.in_(room_ids)).options(
                selectinload(HotelRoom.roommates)).all():
            rooms.append({
                "id": room.id,
                "name": room.name,
                "hotel_block": room.hotel_block,
                "block_name": blocks.get(room.hotel_block),
                "completed": bool(room.completed),
                "locked": bool(room.locked),
                "suggested": bool(room.suggested),
                "nights": sorted([x.room_night for x in assignments
                                  if x.hotel_room == room.id]),
                "roommates": [{"id": x.id, "name": x.public_name}
                              for x in room.roommates if x.id != badge.id],
            })

    room_request = db.query(HotelRoomRequest).filter(
        HotelRoomRequest.badge == badge.id).one_or_none()
    request_summary = None
    if room_request:
        request_summary = {
            "id": room_request.id,
            "justification": room_request.room_night_justification,
            "notes": room_request.notes,
            "declined": room_request.declined,
            "hotel_block": room_request.hotel_block,
            "prefer_department": room_request.prefer_department,
            "preferred_department": room_request.preferred_department,
            "noise_level": room_request.noise_level,
            "sleep_time": room_request.sleep_time,
            "prefer_single_gender": room_request.prefer_single_gender,
            "preferred_gender": room_request.preferred_gender,
            "smoke_sensitive": room_request.smoke_sensitive,
            "roommate_requests": [{"id": x.id, "name": x.public_name}
                                  for x in room_request.roommate_requests],
            "roommate_anti_requests": [{"id": x.id, "name": x.public_name}
                                       for x in room_request.roommate_anti_requests],
        }
    return jsonify({
        "id": badge.id,
        "name": badge.public_name,
        "email": badge.email,
        "departments": sorted([x.name for x in badge.departments]),
        "nights": nights,
        "shifts": shifts,
        "rooms": rooms,
        "room_request": request_summary,
    })


def _attendees_data(event, mode="all", search=None, block=None):
    """One row per eligible person (anyone with a hotel room request record)
       with request/assignment status and their missing restricted nights."""
    requests = db.query(HotelRoomRequest, Badge).join(
        Badge, HotelRoomRequest.badge == Badge.id).filter(
        HotelRoomRequest.event == event).options(
        selectinload(HotelRoomRequest.room_night_requests),
        selectinload(Badge.departments))
    if block is not None:
        requests = requests.filter(HotelRoomRequest.hotel_block == block)
    if search:
        requests = requests.filter(or_(
            Badge.search_name.contains(search.lower()),
            func.lower(HotelRoomRequest.notes).contains(search.lower())))
    requests = requests.all()

    badge_ids = [badge.id for _, badge in requests]
    nights = {x.id: x for x in db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).all()}
    shift_satisfied = shift_satisfied_night_ids(db, event, badge_ids)
    manual_nights = manual_approved_night_ids(db, event, badge_ids)
    hours = shift_hours_totals(db, event, badge_ids)
    unrestricted = {x.id for x in nights.values() if x.restriction_mode == 'none'}
    assigned_nights = defaultdict(set)
    roomless = set()
    for assignment in db.query(RoomNightAssignment).filter(
            RoomNightAssignment.event == event,
            RoomNightAssignment.badge.in_(badge_ids)).all():
        assigned_nights[assignment.badge].add(assignment.room_night)
        if assignment.hotel_room is None:
            roomless.add(assignment.badge)

    rows = []
    for req, badge in requests:
        requested = {x.room_night for x in req.room_night_requests if x.requested}
        approved = (unrestricted | shift_satisfied[badge.id]
                    | manual_nights[badge.id])
        completed = bool(req.declined or (
            req.first_name and req.last_name and requested))
        missing = []
        for night_id in requested:
            night = nights.get(night_id)
            if not night or night.restriction_mode == 'none':
                continue
            if night_id in shift_satisfied[badge.id]:
                continue
            if night.restriction_mode == 'manual' and night_id in manual_nights[badge.id]:
                continue
            entry = {
                "id": night.id,
                "name": night.name,
                "date": night.date.strftime("%Y-%m-%d") if night.date else None,
                "restriction_type": night.restriction_type,
                "mode": night.restriction_mode,
                "requested": True,
                "approved": night_id in manual_nights[badge.id],
                "assigned": night_id in assigned_nights[badge.id],
            }
            if night.restriction_mode == 'shift_hours':
                entry["hours_required"] = night.shift_hours_required
                entry["hours_assigned"] = round(hours.get(badge.id, 0), 1)
            missing.append(entry)
        missing.sort(key=lambda x: x["date"] or "")

        if mode == "missing_shifts" and not missing:
            continue
        if mode == "complete" and (not completed or req.declined):
            continue
        if mode == "incomplete" and (completed or req.declined):
            continue
        if mode == "declined" and not req.declined:
            continue
        if mode == "roomless" and badge.id not in roomless:
            continue
        if mode == "unassigned_approved" and not (
                requested & approved - assigned_nights[badge.id]):
            continue

        rows.append({
            "badge": badge.id,
            "id": badge.id,
            "name": badge.public_name,
            "email": badge.email,
            "departments": sorted([x.name for x in badge.departments]),
            "hotel_block": req.hotel_block,
            "declined": bool(req.declined),
            "completed": completed,
            "notes": req.notes,
            "request_id": req.id,
            "requested_nights": len(requested),
            "approved_nights": len(requested & approved),
            "assigned_nights": len(assigned_nights[badge.id]),
            "missing_nights": missing,
        })
    rows.sort(key=lambda x: x["name"] or "")
    return rows


ATTENDEE_FILTERS = ("all", "complete", "incomplete", "declined",
                    "missing_shifts", "roomless", "unassigned_approved")


@app.route("/api/event/<int:event>/hotel/attendees", methods=["GET"])
def hotel_attendees(event):
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    mode = request.args.get("filter", "all")
    if mode not in ATTENDEE_FILTERS:
        return "Unknown filter", 400
    block = request.args.get("block", None, type=int)
    rows = _attendees_data(event, mode, request.args.get("search"), block)
    if request.args.get("sort") in ("requested_nights", "assigned_nights",
                                    "approved_nights", "name"):
        rows.sort(key=lambda x: x[request.args["sort"]] or 0
                  if request.args["sort"] != "name" else (x["name"] or ""),
                  reverse=request.args.get("order") == "desc")
    count = len(rows)
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", None, type=int)
    if limit is not None:
        rows = rows[offset:offset + limit]
    return jsonify(results=rows, count=count)


@app.route("/api/event/<int:event>/hotel/attendees/export", methods=["GET"])
def hotel_attendees_export(event):
    """CSV of attendees for the given filter, with emails for outreach."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    mode = request.args.get("filter", "missing_shifts")
    if mode not in ATTENDEE_FILTERS:
        return "Unknown filter", 400
    import csv
    import io
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Name", "Email", "Departments", "Nights Requested",
                     "Nights Assigned", "Nights Missing a Shift"])
    for entry in _attendees_data(event, mode):
        writer.writerow([
            entry["name"],
            entry["email"],
            "; ".join(entry["departments"]),
            entry["requested_nights"],
            entry["assigned_nights"],
            "; ".join([f"{x['name']} ({x['date']})" if x["date"] else x["name"]
                       for x in entry["missing_nights"]]),
        ])
    return Response(out.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f"attachment; filename={mode}_attendees.csv"})


@app.route("/api/event/<int:event>/hotel/room/<int:room_id>/details", methods=["GET"])
def hotel_room_grid(event, room_id):
    """Everything the room modal needs: room fields plus a nights-by-occupant
       grid of requested/approved/assigned status."""
    if not check_permission("hotel_block.*.read", event=event):
        return "", 403
    room = db.query(HotelRoom).filter(
        HotelRoom.id == room_id, HotelRoom.event == event).options(
        selectinload(HotelRoom.roommates)).one_or_none()
    if not room:
        return "Could not locate room", 404
    details = _room_details_data(event, [room_id]).get(room_id, {
        "room_nights": [], "roommates": {}, "empty_slots": 0, "groups": []})
    nights = db.query(HotelRoomNight).filter(
        HotelRoomNight.event == event).order_by(HotelRoomNight.date).all()
    badge_ids = [x.id for x in room.roommates]
    approved = approved_night_ids(db, event, badge_ids)
    requested = defaultdict(set)
    if badge_ids:
        for night_request in db.query(RoomNightRequest).filter(
                RoomNightRequest.badge.in_(badge_ids),
                RoomNightRequest.requested == True).all():
            requested[night_request.badge].add(night_request.room_night)
    assignments = defaultdict(dict)
    if badge_ids:
        for rna in db.query(RoomNightAssignment).filter(
                RoomNightAssignment.badge.in_(badge_ids)).all():
            assignments[rna.badge][rna.room_night] = rna.hotel_room
    blocks = {x.id: x.name for x in db.query(HotelRoomBlock).filter(
        HotelRoomBlock.event == event).all()}
    locations = {x.id: x.name for x in db.query(HotelLocation).filter(
        HotelLocation.event == event).all()}

    occupants = []
    for badge in room.roommates:
        detail = details["roommates"].get(badge.id, {})
        occupants.append({
            "badge": badge.id,
            "name": badge.public_name,
            "errors": detail.get("errors", []),
            "nights": {night.id: {
                "requested": night.id in requested[badge.id],
                "approved": night.id in approved[badge.id],
                "assigned": assignments[badge.id].get(night.id, None) == room.id,
                "assigned_room": assignments[badge.id].get(night.id),
            } for night in nights},
        })
    groups = [[badge_id for badge_id in group]
              for group in details.get("groups", [])]
    return jsonify({
        "id": room.id,
        "name": room.name,
        "notes": room.notes,
        "messages": room.messages,
        "completed": bool(room.completed),
        "locked": bool(room.locked),
        "suggested": bool(room.suggested),
        "hotel_block": {"id": room.hotel_block,
                        "name": blocks.get(room.hotel_block)},
        "hotel_location": {"id": room.hotel_location,
                           "name": locations.get(room.hotel_location)},
        "nights": [{"id": x.id, "name": x.name,
                    "date": x.date.strftime("%Y-%m-%d") if x.date else None}
                   for x in nights],
        "occupants": occupants,
        "groups": groups,
        "empty_slots": details.get("empty_slots", 0),
    })


@app.route("/api/event/<int:event>/hotel/dashboard", methods=["GET"])
def hotel_dashboard(event):
    """Status of the whole rooming system: request completion, night and room
       counts, and the issues that still need attention."""
    if not check_permission("rooming.*.manage", event=event):
        return "", 403
    attendees = _attendees_data(event)
    eligible = len(attendees)
    completed = len([x for x in attendees if x["completed"] and not x["declined"]])
    declined = len([x for x in attendees if x["declined"]])
    pending = eligible - completed - declined

    requested_total = db.query(RoomNightRequest).filter(
        RoomNightRequest.event == event, RoomNightRequest.requested == True).count()
    approved_total = sum(x["approved_nights"] for x in attendees)
    assigned_total = db.query(RoomNightAssignment).filter(
        RoomNightAssignment.event == event).count()
    roomless_total = db.query(RoomNightAssignment).filter(
        RoomNightAssignment.event == event,
        RoomNightAssignment.hotel_room == None).count()

    rooms = db.query(HotelRoom).filter(HotelRoom.event == event).all()
    blocks = {x.id: x.name for x in db.query(HotelRoomBlock).filter(
        HotelRoomBlock.event == event).all()}
    by_block = defaultdict(lambda: {"total": 0, "completed": 0, "suggested_pending": 0})
    for room in rooms:
        stats = by_block[room.hotel_block]
        stats["total"] += 1
        if room.completed:
            stats["completed"] += 1
        elif room.suggested:
            stats["suggested_pending"] += 1
    completed_rooms = [x for x in rooms if x.completed]
    suggested_pending = [x for x in rooms if x.suggested and not x.completed]

    # Error sweep over completed rooms (the ones believed done).
    rooms_with_errors = []
    if completed_rooms:
        details = _room_details_data(event, [x.id for x in completed_rooms])
        for room_id, detail in details.items():
            if any(x["errors"] for x in detail["roommates"].values()):
                rooms_with_errors.append(room_id)

    missing = [x for x in attendees if x["missing_nights"]]
    pending_manual = sum(
        len([n for n in x["missing_nights"]
             if n["mode"] == "manual" and not n["approved"]])
        for x in attendees)
    unassigned_approved = len([
        x for x in attendees
        if x["approved_nights"] > x["assigned_nights"] and not x["declined"]])

    issues = [
        {"kind": "missing_shifts", "count": len(missing),
         "link": {"page": "requests", "filter": "missing_shifts"}},
        {"kind": "pending_manual_approvals", "count": pending_manual,
         "link": {"page": "approvals"}},
        {"kind": "unassigned_approved", "count": unassigned_approved,
         "link": {"page": "requests", "filter": "unassigned_approved"}},
        {"kind": "roomless_assignments", "count": roomless_total,
         "link": {"page": "requests", "filter": "roomless"}},
        {"kind": "rooms_with_errors", "count": len(rooms_with_errors),
         "rooms": rooms_with_errors,
         "link": {"page": "assignments"}},
        {"kind": "incomplete_requests", "count": pending,
         "link": {"page": "requests", "filter": "incomplete"}},
        {"kind": "suggested_rooms_pending", "count": len(suggested_pending),
         "link": {"page": "assignments", "view": "suggested"}},
    ]
    return jsonify({
        "requests": {
            "eligible": eligible,
            "completed": completed,
            "declined": declined,
            "pending": pending,
            "percent_resolved": round(
                (completed + declined) / eligible * 100, 1) if eligible else 0,
        },
        "room_nights": {
            "requested": requested_total,
            "approved": approved_total,
            "assigned": assigned_total,
            "roomless_assignments": roomless_total,
        },
        "rooms": {
            "total": len(rooms),
            "completed": len(completed_rooms),
            "suggested_pending": len(suggested_pending),
            "incomplete": len(rooms) - len(completed_rooms) - len(suggested_pending),
            "by_block": [{"id": block_id, "name": blocks.get(block_id),
                          **stats} for block_id, stats in by_block.items()],
        },
        "issues": [x for x in issues if x["count"]],
    })


@app.route("/api/event/<int:event>/hotel/approve/<int:department>", methods=["POST"])
def hotel_approve(event, department):
    if check_permission("hotel_request.*.approve", event=event, department=department):
        room_night_request = db.query(RoomNightRequest).filter(
            RoomNightRequest.room_night == int(request.json['room_night']), RoomNightRequest.badge == int(request.json['badge'])).one_or_none()
        if not room_night_request:
            return "Could not find corresponding request.", 404
        approval = db.query(RoomNightApproval).filter(RoomNightApproval.badge ==
                                                      int(request.json['badge']), RoomNightApproval.room_night == int(request.json['room_night']), RoomNightApproval.department == department).one_or_none()
        if request.json['approved'] is None:
            if approval:
                db.delete(approval)
        else:
            if not approval:
                approval = RoomNightApproval(
                    event=event, badge=int(request.json['badge']), department=department)
            approval.approved = request.json['approved']
            approval.room_night = int(request.json['room_night'])
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
        
        export_requests(event, [hotel_request,])
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
