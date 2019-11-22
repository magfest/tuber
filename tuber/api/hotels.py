from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from sqlalchemy import and_
import requests
import datetime
import uuid
import os

headers = {
    'X-Auth-Token': config.uber_api_token
}

@app.route("/api/hotels/staffer_auth", methods=["POST"])
def staffer_auth():
    try:
        req = {
            "method": "attendee.search",
            "params": [
                request.json['token'],
                "full"
            ]
        }
        resp = requests.post(config.uber_api_url, headers=headers, json=req)
        if len(resp.json()['result']) == 0:
            return jsonify(success=False)
    except:
        return jsonify(success=False)
    result = resp.json()['result'][0]
    if not 'id' in result:
        return jsonify(success=False)
    id = result['id']
    if id != request.json['token']:
        return jsonify(success=False)
    if not result['staffing']:
        return jsonify(success=False)
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        return jsonify(success=False)
    db.session.commit()
    response = jsonify({"success": True, "session": session.secret})
    response.set_cookie('session', session.secret)
    return response

@app.route("/api/hotels/request", methods=["GET", "POST"])
def submit_hotels_request():
    if request.method == "GET":
        badge = db.session.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
        if not badge:
            return jsonify(success=False, reason="Badge does not exist.")
        if not check_permission('hotel_request.create', event=badge.event_id):
            return jsonify(success=False, reason="Permission denied.")
        if badge.user_id != g.user:
            if not check_permission('hotel_assignment.read'):
                return jsonify(success=False, reason="Permission denied.")

        hotel_request = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
        if hotel_request:
            current_request = {
                "decline": hotel_request.declined,
                "prefer_department": hotel_request.prefer_department,
                "preferred_department": hotel_request.preferred_department,
                "notes": hotel_request.notes,
                "single_gender": hotel_request.prefer_single_gender,
                "gender": hotel_request.preferred_gender,
                "noise_level": hotel_request.noise_level,
                "smoke_sensitive": hotel_request.smoke_sensitive,
                "sleep_time": hotel_request.sleep_time,
                "justification": hotel_request.room_night_justification
            }
            requested_roommates = db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester == badge.id).all()
            antirequested_roommates = db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester == badge.id).all()
            current_request['requested_roommates'] = [x.requested for x in requested_roommates]
            current_request['antirequested_roommates'] = [x.requested for x in antirequested_roommates]
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == badge.event_id).all()
            current_request['room_nights'] = []
            for room_night in room_nights:
                rn = {
                    "id": room_night.id,
                    "name": room_night.name,
                    "checked": False,
                    "restricted": room_night.restricted,
                    "restriction_type": room_night.restriction_type,
                    "hidden": room_night.hidden
                }
                room_night_request = db.session.query(RoomNightRequest).filter(RoomNightRequest.badge == badge.id, RoomNightRequest.room_night == room_night.id).one_or_none()
                if room_night_request:
                    rn['checked'] = room_night_request.requested
                current_request['room_nights'].append(rn)
            return jsonify(success=True, request=current_request)
        else:
            current_request = {
                "decline": False,
                "requested_roommates": [],
                "antirequested_roommates": [],
                "prefer_department": False,
                "preferred_department": None,
                "notes": '',
                "single_gender": False,
                "gender": '',
                "noise_level": "Moderate - I don't make a lot of noise.",
                "smoke_sensitive": False,
                "sleep_time": '12am-2am',
                "justification": ''
            }
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == badge.event_id).all()
            current_request['room_nights'] = []
            for room_night in room_nights:
                rn = {
                    "id": room_night.id,
                    "name": room_night.name,
                    "checked": False,
                    "restricted": room_night.restricted,
                    "restriction_type": room_night.restriction_type,
                    "hidden": room_night.hidden
                }
                current_request['room_nights'].append(rn)
            return jsonify(success=True, request=current_request)

    if request.method == "POST":
        badge = db.session.query(Badge).filter(Badge.id == request.json['badge']).one_or_none()
        if not badge:
            return jsonify(success=False, reason="Badge does not exist.")
        if not check_permission('hotel_request.create', event=badge.event_id):
            return jsonify(success=False, reason="Permission denied.")
        if badge.user_id != g.user:
            if not check_permission('hotel_assignment.read'):
                return jsonify(success=False, reason="Permission denied.")
        req = request.json['request']
        hotel_request = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
        if not hotel_request:
            hotel_request = HotelRoomRequest(badge=badge.id)
            db.session.add(hotel_request)
            db.session.flush()
        if len(req['notes']) > HotelRoomRequest.notes.type.length:
            return jsonify(success=False, reason="Notes field is too long.")
        if len(req['gender']) > HotelRoomRequest.preferred_gender.type.length:
            return jsonify(success=False, reason="Preferred Gender field is too long.")
        if len(req['justification']) > HotelRoomRequest.room_night_justification.type.length:
            return jsonify(success=False, reason="Notes field is too long.")
        hotel_request.declined = req['decline']
        hotel_request.prefer_department = req['prefer_department']
        hotel_request.preferred_department = req['preferred_department']
        hotel_request.notes = req['notes']
        hotel_request.prefer_single_gender = req['single_gender']
        hotel_request.preferred_gender = req['gender']
        hotel_request.noise_level = req['noise_level']
        hotel_request.smoke_sensitive = req['smoke_sensitive']
        hotel_request.sleep_time = req['sleep_time']
        hotel_request.room_night_justification = req['justification']
        db.session.add(hotel_request)
        db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester == badge.id).delete()
        db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester == badge.id).delete()
        for roommate in req['requested_roommates']:
            db.session.add(HotelRoommateRequest(requester=badge.id, requested=roommate))
        for roommate in req['antirequested_roommates']:
            db.session.add(HotelAntiRoommateRequest(requester=badge.id, requested=roommate))
        nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == badge.event_id).all()
        for night in nights:
            rnr = db.session.query(RoomNightRequest).filter(RoomNightRequest.badge == badge.id, RoomNightRequest.room_night == night.id).one_or_none()
            if not rnr:
                rnr = RoomNightRequest(badge=badge.id, room_night=night.id)
            for room_night in req['room_nights']:
                if room_night['id'] == night.id:
                    rnr.requested = room_night['checked']
                    break
            db.session.add(rnr)
        if badge.id in req['antirequested_roommates']:
            return jsonify(success=False, reason="You cannot anti-request yourself as a roommate. What does that even mean?")
        if badge.id in req['requested_roommates']:
            return jsonify(success=False, reason="You cannot request yourself as a roommate.")
        if [x for x in req['antirequested_roommates'] if x in req['requested_roommates']]:
            return jsonify({"success": False, "reason": "You cannot request and antirequest a roommate."})
        db.session.commit()
        return jsonify({"success": True})

@app.route("/api/hotels/roommate_search", methods=["POST"])
def roommate_search():
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return jsonify({"success": False})
    if check_permission("staff.search_names", event=request.json['event']):
        results = db.session.query(Badge).filter(Badge.event_id == request.json['event'], Badge.search_name.like("%{}%".format(request.json['search'].lower()))).limit(25).all()
        filtered_results = []
        for res in results:
            departments = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == res.id).all()
            filtered_departments = []
            for dept in departments:
                filtered_departments.append(dept.department)
            filtered_results.append({
                "name": "{} {}".format(res.first_name, res.last_name),
                "id": res.id,
                "departments": filtered_departments
            })
        return jsonify({"success": True, "results": filtered_results})
    return jsonify(success=False)

@app.route("/api/hotels/roommate_lookup", methods=["POST"])
def roommate_lookup():
    if check_permission("staff.search_names", event=request.json['event']):
        badge = db.session.query(Badge).filter(Badge.id == request.json['badge']).one_or_none()
        if not badge:
            return jsonify(success=False)
        departments = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == badge.id).all()
        return jsonify(success=True, roommate={
            "name": "{} {}".format(badge.first_name, badge.last_name),
            "id": badge.id,
            "departments": [x.department for x in departments]
        })
    return jsonify(success=False)

@app.route("/api/hotels/department_names", methods=["POST"])
def department_names():
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return jsonify({"success": False})
    if check_permission("staff.search_names", event=request.json['event']):
        departments = db.session.query(Department).filter(Department.event_id == event.id).all()
        filtered = {}
        for dept in departments:
            filtered[dept.id] = {
                "name": dept.name,
                "description": dept.description
            }
        return jsonify({"success": True, "departments": filtered})
    return jsonify(success=False, reason="Permission Denied")

@app.route("/api/hotels/department_membership", methods=["POST"])
def department_membership():
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return jsonify({"success": False})
    if check_permission("staff.search_names", event=request.json['event']):
        user = db.session.query(User).filter(User.id == request.json['user']).one()
        badge = db.session.query(Badge).filter(Badge.user_id == user.id, Badge.event_id == event.id).one_or_none()
        if not badge:
            return jsonify({"success": False})
        membership = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == badge.id).all()
        filtered = []
        for dept in membership:
            department = db.session.query(Department).filter(Department.id == dept.department).one()
            filtered.append({
                "name": department.name,
                "id": department.id
            })
        return jsonify({"success": True, "departments": filtered})
    return jsonify(success=False)

@app.route("/api/hotels/statistics", methods=["GET"])
def hotel_statistics():
    if check_permission("hotel_statistics.read", event=request.args['event']):
        num_badges = db.session.query(Badge).filter(Badge.event_id == request.args['event']).count()
        num_requests = db.session.query(Badge, HotelRoomRequest).filter(Badge.id == HotelRoomRequest.badge, Badge.event_id == request.args['event']).count()
        return jsonify(success=True, num_badges=num_badges, num_requests=num_requests)
    return jsonify(success=False)

@app.route("/api/hotels/all_requests", methods=["GET"])
def hotel_all_requests():
    if request.method == "GET":
        if not check_permission("hotel_request.assign", event=request.args['event']):
            return jsonify(success=False)
        room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        room_night_ids = [x.id for x in room_nights]
        requests = db.session.query(Badge, HotelRoomRequest).join(HotelRoomRequest, Badge.id == HotelRoomRequest.badge).filter(HotelRoomRequest.declined != True).all()
        badges = [x[0].id for x in requests]
        default_room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event'], HotelRoomNight.restricted != True).all()
        default_room_nights = [x.id for x in default_room_nights]
        approvals = db.session.query(RoomNightRequest).join(RoomNightApproval, RoomNightApproval.room_night == RoomNightRequest.id).filter(RoomNightRequest.badge.in_(badges), RoomNightApproval.approved == True).all()
        requested_roommates = db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester.in_(badges)).all()
        antirequested_roommates = db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester.in_(badges)).all()
        department_membership = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge.in_(badges)).all()
        results = {}
        genders = {
            "male": 0,
            "guy": 0,
            "bro": 0,
            "boys": 0,
            "males": 0,
            "female": 1,
            "females": 1,
            "woman": 1,
            "women": 1,
            "he/him": 0,
            "she/her": 1,
            "m": 0,
            "f": 1,
        }
        noise_levels = {
            'Quiet - I am quiet, and prefer quiet.': 0,
            "Moderate - I don't make a lot of noise.": 1,
            "Loud - I'm ok if someone snores or I snore.": 2,
        }
        sleep_times = {
            '8pm-10pm': 0,
            '10pm-12am': 1,
            '12am-2am': 2,
            '2am-4am': 3,
            '4am-6am': 4,
            '6am-8am': 5,
            '8am-10am': 6,
            '10am-12pm': 7,
            '12pm-2pm': 8,
            '2pm-4pm': 9,
            '4pm-6pm': 10,
            '6pm-8pm': 11,
        }
        for badge, req in requests:
            notes = req.notes
            preferred_gender = None
            if req.preferred_gender:
                if req.preferred_gender.lower().strip() in genders.keys():
                    preferred_gender = genders[req.preferred_gender.lower().strip()]
                elif "trans" in req.preferred_gender.lower():
                    preferred_gender = 2
                else:
                    print("Unhandled gender preference: {}".format(req.preferred_gender))
                    notes += "\nRequested to be roomed with ({}) gender.".format(req.preferred_gender)
            noise_level = None
            if req.noise_level in noise_levels:
                noise_level = noise_levels[req.noise_level]
            sleep_time = None
            if req.sleep_time in sleep_times:
                sleep_time = sleep_times[req.sleep_time]
            results[badge.id] = {
                "id": badge.id,
                "name": "{} {}".format(badge.first_name, badge.last_name),
                "justification": req.room_night_justification,
                "room_nights": [x for x in default_room_nights if x in [y.room_night for y in badge.room_night_requests if y.requested]],
                "prefer_department": req.prefer_department,
                "preferred_department": req.preferred_department,
                "notes": notes,
                "prefer_single_gender": req.prefer_single_gender,
                "preferred_gender": preferred_gender,
                "noise_level": noise_level,
                "smoke_sensitive": req.smoke_sensitive,
                "sleep_time": sleep_time,
                "requested_roommates": [],
                "antirequested_roommates": [],
                "departments": []
            }
        for rnr in approvals:
            if not rnr.room_night in results[rnr.badge]["room_nights"]:
                results[rnr.badge]["room_nights"].append(rnr.room_night)
        for req in requested_roommates:
            results[req.requester]['requested_roommates'].append(req.requested)
        for req in antirequested_roommates:
            results[req.requester]['antirequested_roommates'].append(req.requested)
        for membership in department_membership:
            results[membership.badge]['departments'].append(membership.department)
        return jsonify(success=True, requests=results)

@app.route("/api/hotels/requests", methods=["GET", "POST"])
def hotel_requests():
    if request.method == "GET":
        if check_permission("hotel_request.approve", event=request.args['event']):
            requests = db.session.query(Department, Badge, HotelRoomRequest).join(BadgeToDepartment, BadgeToDepartment.department == Department.id).join(HotelRoomRequest, HotelRoomRequest.badge == BadgeToDepartment.badge).join(Badge, Badge.id == BadgeToDepartment.badge).all()
            departments = {}
            for req in requests:
                dept, badge, roomrequest = req
                if not check_permission("hotel_request.approve", event=request.args['event'], department=dept.id):
                    continue
                if not dept.id in departments:
                    departments[dept.id] = {
                        "id": dept.id,
                        "name": dept.name,
                        "requests": []
                    }
                room_nights = db.session.query(RoomNightRequest, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.room_night == RoomNightRequest.id, RoomNightApproval.department == dept.id), isouter=True).filter(RoomNightRequest.badge == badge.id).all()
                departments[dept.id]['requests'].append({
                    "id": badge.id,
                    "name": badge.first_name + " " + badge.last_name,
                    "justification": roomrequest.room_night_justification,
                    "room_nights": {
                        btr.room_night: {
                        "id": btr.id,
                        "requested": btr.requested,
                        "room_night": btr.room_night,
                        "approved": rna.approved if rna else None
                    } for btr, rna in room_nights}
                })
            res = []
            for i in departments:
                res.append(departments[i])
            return jsonify(success=True, departments=res)
        return jsonify(success=False, reason="Permission Denied.")
    return jsonify(success=False)
            
@app.route("/api/hotels/approve", methods=["POST"])
def hotel_approve():
    if request.method == "POST":
        if check_permission("hotel_request.approve", event=request.json['event'], department=request.json['department']):
            room_night = db.session.query(RoomNightRequest).filter(RoomNightRequest.id == request.json['room_night_request']).one_or_none()
            if not room_night:
                return jsonify(success=False, reason="Could not find corresponding request.")
            approval = db.session.query(RoomNightApproval).filter(RoomNightApproval.room_night == room_night.id, RoomNightApproval.department == request.json['department']).one_or_none()
            if request.json['approved'] is None:
                if approval:
                    db.session.delete(approval)
            else:
                if not approval:
                    approval = RoomNightApproval()
                approval.approved = request.json['approved']
                approval.department = request.json['department']
                approval.room_night = room_night.id
                db.session.add(approval)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False, reason="Permission denied.")

@app.route("/api/hotels/room_nights", methods=["GET"])
def hotel_room_nights():
    if request.method == "GET":
        if check_permission("hotel_request.approve", event=request.args['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            res = []
            for rn in room_nights:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "restricted": rn.restricted,
                    "restriction_type": rn.restriction_type,
                    "hidden": rn.hidden
                })
            return jsonify(success=True, room_nights=res)
    return jsonify(success=False)

@app.route("/api/hotels/hotel_room", methods=["GET", "POST", "DELETE"])
def hotel_room():
    if request.method == "GET":
        if not check_permission("hotel_settings.*", event=request.args['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.args['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        hotel_rooms = db.session.query(HotelRoom).filter(HotelRoom.hotel_block.in_(room_block_ids)).all()
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
        return jsonify(success=True, hotel_rooms=res)
    if request.method == "POST":
        if not check_permission("hotel_settings.write", event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.json['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.json['event']).all()
        room_location_ids = [x.id for x in room_locations]
        if 'rooms' in request.json:
            for room in request.json['rooms']:
                rn = db.session.query(HotelRoom).filter(HotelRoom.id == room['id']).one_or_none()
                if not rn:
                    return jsonify(success=False, reason="Could not find hotel room {}".format(room['id']))
                if 'hotel_block' in room:
                    if not room['hotel_block'] in room_block_ids:
                        return jsonify(success=False, reason="Could not find hotel block {}".format(room['hotel_block']))
                if 'hotel_location' in room:
                    if not room['hotel_location'] in room_location_ids:
                        return jsonify(success=False, reason="Could not find hotel location {}".format(room['hotel_location']))
                for attr in ['name', 'notes', 'messages', 'hotel_block', 'hotel_location', 'completed']:
                    if attr in room:
                        setattr(rn, attr, room[attr])
                db.session.add(rn)
            db.session.commit()
            return jsonify(success=True)
        if not room_blocks:
            return jsonify(success=False, reason="No room blocks defined.")
        if not room_locations:
            return jsonify(success=False, reason="No hotel locations defined.")
        rn = HotelRoom(hotel_block=room_block_ids[0], hotel_location=room_location_ids[0])
        db.session.add(rn)
        db.session.flush()
        db.session.commit()
        return jsonify(success=True, room={'id': rn.id, 'name': rn.name, 'notes': rn.notes, 'messages': rn.messages, 'hotel_block': rn.hotel_block, 'hotel_location': rn.hotel_location})
    if request.method == "DELETE": 
        if not check_permission("hotel_settings.write", event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        for room in request.json['rooms']:
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.hotel_room == room).all()
            for rna in rnas:
                db.session.delete(rna)
            rn = db.session.query(HotelRoom).filter(HotelRoom.id == room).one_or_none()
            if not rn:
                return jsonify(success=False, reason="Could not find hotel room {}".format(room))
            db.session.delete(rn)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, reason="Unsupported request method")

@app.route("/api/hotels/settings/room_night", methods=["GET", "POST"])
def hotel_room_night_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            res = []
            for rn in room_nights:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "restricted": rn.restricted,
                    "restriction_type": rn.restriction_type,
                    "hidden": rn.hidden
                })
            return jsonify(success=True, room_nights=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.json['event']).all()
            for i in room_nights:
                if [x for x in request.json['room_nights'] if 'id' in x and x['id'] == i.id]:
                    continue
                for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_nights']:
                room_night = None
                if 'id' in i:
                    room_night = db.session.query(HotelRoomNight).filter(HotelRoomNight.id == i['id']).one_or_none()
                if not room_night:
                    room_night = HotelRoomNight()
                room_night.name = i['name']
                room_night.event = request.json['event']
                room_night.restricted = i['restricted']
                if room_night.restricted:
                    room_night.restriction_type = i['restriction_type']
                else:
                    room_night.restriction_type = ""
                room_night.hidden = i['hidden']
                db.session.add(room_night)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route("/api/hotels/settings/room_block", methods=["GET", "POST"])
def hotel_room_block_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.args['event']).all()
            res = []
            for rn in room_blocks:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "description": rn.description
                })
            return jsonify(success=True, room_blocks=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.json['event']).all()
            for i in room_blocks:
                if [x for x in request.json['room_blocks'] if 'id' in x and x['id'] == i.id]:
                    continue
                #Need to add later
                #for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                #    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_blocks']:
                room_block = None
                if 'id' in i:
                    room_block = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.id == i['id']).one_or_none()
                if not room_block:
                    room_block = HotelRoomBlock()
                room_block.name = i['name']
                room_block.description = i['description']
                room_block.event = request.json['event']
                db.session.add(room_block)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route("/api/hotels/settings/room_location", methods=["GET", "POST"])
def hotel_room_location_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.args['event']).all()
            res = []
            for rn in room_locations:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "address": rn.address
                })
            return jsonify(success=True, room_locations=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.json['event']).all()
            for i in room_locations:
                if [x for x in request.json['room_locations'] if 'id' in x and x['id'] == i.id]:
                    continue
                #Need to add later
                #for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                #    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_locations']:
                room_location = None
                if 'id' in i:
                    room_location = db.session.query(HotelLocation).filter(HotelLocation.id == i['id']).one_or_none()
                if not room_location:
                    room_location = HotelLocation()
                room_location.name = i['name']
                room_location.address = i['address']
                room_location.event = request.json['event']
                db.session.add(room_location)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/hotels/request_complete.png')
def request_complete():
    if not 'id' in request.args:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    id = request.args['id']
    badge = db.session.query(Badge).filter(Badge.uber_id == id).one_or_none()
    if not badge:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    req = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if req:
        return send_file(os.path.join(config.static_path, "checkbox_checked.png"))
    resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
    resp.cache_control.max_age = 10
    return resp

@app.route('/api/hotels/room_assignments', methods=['GET', 'POST'])
def hotel_room_assignments():
    if request.method == "GET":
        if not check_permission('room_assignment.read', event=request.args['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        if 'badge' in request.args:
            badge = db.session.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
            if not badge:
                return jsonify(success=False, reason="Could not locate badge {}".format(request.args['badge']))
            if badge.event_id != request.args['event']:
                return jsonify(success=False, reason="Permission Denied")
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge == badge.id).all()
            res = {x.id: [y.hotel_room for y in rnas if y.room_night == x.id] for x in room_nights}
            return jsonify(success=True, room_assignments=res)
        badges = db.session.query(Badge).filter(Badge.event_id == request.args['event']).all()
        badge_ids = [x.id for x in badges]
        rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge.in_(badge_ids)).all()
        res = {}
        for badge in badge_ids:
            res[badge] = {}
            for room_night in room_nights:
                res[badge][room_night.id] = []
            for rna in rnas:
                if rna.badge == badge:
                    res[rna.badge][rna.room_night].append(rna.hotel_room)
        return jsonify(success=True, room_assignments=res)
    if request.method == "POST":
        if not check_permission('room_assignment.write', event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        if 'badge' in request.json:
            badges = [request.json['badge']]
        if 'badges' in request.json:
            badges = request.json['badges']
        for badge in badges:
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge==badge, RoomNightAssignment.hotel_room==int(request.json['hotel_room'])).all()
            for rna in rnas:
                db.session.delete(rna)
            if type(request.json['room_nights']) is list:
                for room_night in request.json['room_nights']:
                    rna = RoomNightAssignment(badge=badge, room_night=room_night, hotel_room=request.json['hotel_room'])
                    db.session.add(rna)
            else:
                requested = db.session.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night == HotelRoomNight.id).filter(RoomNightRequest.badge == badge, RoomNightRequest.requested == True).all()
                approvals = db.session.query(RoomNightApproval, RoomNightRequest).join(RoomNightRequest, RoomNightRequest.id == RoomNightApproval.room_night).filter(RoomNightRequest.badge == badge).all()
                approved = [x[1].room_night for x in approvals if x[0].approved]
                for req, night in requested:
                    if (night.id in approved) or (not night.restricted):
                        rna = RoomNightAssignment(badge=badge, room_night=req.room_night, hotel_room=request.json['hotel_room'])
                        db.session.add(rna)
            db.session.commit()
            return jsonify(success=True)
        return jsonify(success=False, reason="Either badge or badges must be provided")
            
    return jsonify(success=False, reason="Unsupported method type {}".format(request.method))