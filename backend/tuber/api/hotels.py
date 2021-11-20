from tuber import app, config
from flask import send_file, request, jsonify, escape
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
import os
from tuber.api import *

@app.route("/api/event/<int:event>/hotel/statistics", methods=["GET"])
def hotel_statistics(event):
    if check_permission("hotel_statistics.*.read", event=request.args['event']):
        num_badges = db.query(Badge).filter(Badge.event == request.args['event']).count()
        num_requests = db.query(Badge, HotelRoomRequest).filter(Badge.id == HotelRoomRequest.badge, Badge.event == request.args['event']).count()
        return jsonify(num_badges=num_badges, num_requests=num_requests)
    return "", 403

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
        print(request.json)
        room_night_request = db.query(RoomNightRequest).filter(RoomNightRequest.room_night == request.json['room_night'], RoomNightRequest.badge == request.json['badge']).one_or_none()
        if not room_night_request:
            return "Could not find corresponding request.", 404
        approval = db.query(RoomNightApproval).filter(RoomNightApproval.badge == request.json['badge'], RoomNightApproval.room_night == request.json['room_night'], RoomNightApproval.department == department).one_or_none()
        if request.json['approved'] is None:
            print("Deleting")
            if approval:
                db.delete(approval)
        else:
            if not approval:
                print("Creating new approval")
                approval = RoomNightApproval(event=event, badge=request.json['badge'], department=department)
            print("Setting approval")
            approval.approved = request.json['approved']
            approval.room_night = request.json['room_night']
            db.add(approval)
        db.commit()
        return "null", 200
    return "", 403

@app.route("/api/event/<int:event>/hotel/room_nights", methods=["GET"])
def hotel_room_nights(event):
    if check_permission("hotel_request.*.approve", event=request.args['event']):
        room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        res = []
        for rn in room_nights:
            res.append({
                "id": rn.id,
                "name": rn.name,
                "restricted": rn.restricted,
                "restriction_type": rn.restriction_type,
                "hidden": rn.hidden
            })
        return jsonify(res)
    return "", 403

@app.route("/api/event/<int:event>/hotel/hotel_room", methods=["GET", "POST", "DELETE"])
def hotel_room(event):
    if request.method == "GET":
        if not check_permission("hotel_settings.*.hotel_room", event=request.args['event']):
            return "", 403
        room_blocks = db.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.args['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        hotel_rooms = db.query(HotelRoom).filter(HotelRoom.hotel_block.in_(room_block_ids)).all()
        res = []
        for rn in hotel_rooms:
            res.append({
                "id": rn.id,
                "name": rn.name,
                "notes": rn.notes,
                "messages": rn.messages,
                "hotel_block": rn.hotel_block,
                "hotel_location": rn.hotel_location,
                "completed": rn.completed,
            })
        return jsonify(res)
    if request.method == "POST":
        if not check_permission("hotel_settings.*.write", event=request.json['event']):
            return "", 403
        room_blocks = db.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.json['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        room_locations = db.query(HotelLocation).filter(HotelLocation.event == request.json['event']).all()
        room_location_ids = [x.id for x in room_locations]
        if 'rooms' in request.json:
            for room in request.json['rooms']:
                rn = db.query(HotelRoom).filter(HotelRoom.id == room['id']).one_or_none()
                if not rn:
                    return "Could not find hotel room {}".format(escape(room['id'])), 404
                if 'hotel_block' in room:
                    if not room['hotel_block'] in room_block_ids:
                        return "Could not find hotel block {}".format(escape(room['hotel_block'])), 404
                if 'hotel_location' in room:
                    if not room['hotel_location'] in room_location_ids:
                        return "Could not find hotel location {}".format(escape(room['hotel_location'])), 404
                for attr in ['name', 'notes', 'messages', 'hotel_block', 'hotel_location', 'completed']:
                    if attr in room:
                        setattr(rn, attr, room[attr])
                db.add(rn)
            db.commit()
            return "null", 200
        if not room_blocks:
            return "No room blocks defined.", 412
        if not room_locations:
            return "No hotel locations defined.", 412
        rn = HotelRoom(hotel_block=room_block_ids[0], hotel_location=room_location_ids[0])
        db.add(rn)
        db.flush()
        db.commit()
        return jsonify({'id': rn.id, 'name': rn.name, 'notes': rn.notes, 'messages': rn.messages, 'hotel_block': rn.hotel_block, 'hotel_location': rn.hotel_location})
    if request.method == "DELETE": 
        if not check_permission("hotel_settings.*.write", event=request.json['event']):
            return "", 403
        for room in request.json['rooms']:
            rnas = db.query(RoomNightAssignment).filter(RoomNightAssignment.hotel_room == room).all()
            for rna in rnas:
                db.delete(rna)
            rn = db.query(HotelRoom).filter(HotelRoom.id == room).one_or_none()
            if not rn:
                return "Could not find hotel room {}".format(escape(room)), 404
            db.delete(rn)
        db.commit()
        return "null", 200

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

@app.route('/api/event/<int:event>/hotel/room_assignments', methods=['GET', 'POST'])
def hotel_room_assignments(event):
    if request.method == "GET":
        if not check_permission('room_assignment.*.read', event=request.args['event']):
            return "", 403
        room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        if 'badge' in request.args:
            badge = db.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
            if not badge:
                return "Could not locate badge {}".format(escape(request.args['badge'])), 404
            if badge.event != request.args['event']:
                return "Permission Denied", 403
            rnas = db.query(RoomNightAssignment).filter(RoomNightAssignment.badge == badge.id).all()
            res = {x.id: [y.hotel_room for y in rnas if y.room_night == x.id] for x in room_nights}
            return jsonify(res)
        badges = db.query(Badge).filter(Badge.event == request.args['event']).all()
        badge_ids = [x.id for x in badges]
        rnas = db.query(RoomNightAssignment).filter(RoomNightAssignment.badge.in_(badge_ids)).all()
        res = {}
        for badge in badge_ids:
            res[badge] = {}
            for room_night in room_nights:
                res[badge][room_night.id] = []
            for rna in rnas:
                if rna.badge == badge:
                    res[rna.badge][rna.room_night].append(rna.hotel_room)
        return jsonify(res)
    if request.method == "POST":
        if not check_permission('room_assignment.*.write', event=request.json['event']):
            return "", 403
        if 'badge' in request.json:
            badges = [request.json['badge']]
        if 'badges' in request.json:
            badges = request.json['badges']
        if not badges:
            return "Either badge or badges must be provided", 406
        for badge in badges:
            rnas = db.query(RoomNightAssignment).filter(RoomNightAssignment.badge==badge, RoomNightAssignment.hotel_room==int(request.json['hotel_room'])).all()
            for rna in rnas:
                db.delete(rna)
            if type(request.json['room_nights']) is list:
                for room_night in request.json['room_nights']:
                    rna = RoomNightAssignment(badge=badge, room_night=room_night, hotel_room=request.json['hotel_room'])
                    db.add(rna)
            else:
                requested = db.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night == HotelRoomNight.id).filter(RoomNightRequest.badge == badge, RoomNightRequest.requested == True).all()
                approvals = db.query(RoomNightApproval, RoomNightRequest).join(RoomNightRequest, RoomNightRequest.id == RoomNightApproval.room_night).filter(RoomNightRequest.badge == badge).all()
                approved = [x[1].room_night for x in approvals if x[0].approved]
                for req, night in requested:
                    if (night.id in approved) or (not night.restricted):
                        rna = RoomNightAssignment(badge=badge, room_night=req.room_night, hotel_room=request.json['hotel_room'])
                        db.add(rna)
        db.commit()
        return "null", 200

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
            "requested_roommates": hotel_request.roommate_requests,
            "antirequested_roommates": hotel_request.roommate_anti_requests,
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