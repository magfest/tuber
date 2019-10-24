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
    'X-Auth-Token': config['uber_api_token']
}

@app.route("/api/hotels/staffer_auth", methods=["POST"])
def staffer_auth():
    req = {
        "method": "attendee.search",
        "params": [
            request.json['token'],
            "full"
        ]
    }
    resp = requests.post(config['uber_api_url'], headers=headers, json=req)
    if len(resp.json()['result']) == 0:
        return jsonify({"success": False})
    result = resp.json()['result'][0]
    id = result['id']
    if id != request.json['token']:
        return {"success": False}
    if not result['staffing']:
        return {"success": False}
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        return jsonify({"success": False})
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
                    "restriction_type": room_night.restriction_type
                }
                room_night_request = db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.badge == badge.id, BadgeToRoomNight.room_night == room_night.id).one_or_none()
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
                    "restriction_type": room_night.restriction_type
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
        db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.badge == badge.id).delete()
        for room_night in req['room_nights']:
            db.session.add(BadgeToRoomNight(badge=badge.id, requested=room_night['checked'], room_night=room_night['id']))
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

@app.route("/api/hotels/department_membership", methods=["POST"])
def department_membership():
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return jsonify({"success": False})
    if check_permission("staff.search_names", event=request.json['event']):
        user = db.session.query(User).filter(User.id == request.json['user']).one()
        print(user.id, event.id)
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

@app.route("/api/hotels/statistics", methods=["GET"])
def hotel_statistics():
    if check_permission("hotel_statistics.read", event=request.args['event']):
        num_badges = db.session.query(Badge).filter(Badge.event_id == request.args['event']).count()
        num_requests = db.session.query(Badge, HotelRoomRequest).filter(Badge.id == HotelRoomRequest.badge, Badge.event_id == request.args['event']).count()
        return jsonify(success=True, num_badges=num_badges, num_requests=num_requests)
    return jsonify(success=False)

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
                room_nights = db.session.query(BadgeToRoomNight, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.room_night == BadgeToRoomNight.id, RoomNightApproval.department == dept.id), isouter=True).filter(BadgeToRoomNight.badge == badge.id).all()
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
            room_night = db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.id == request.json['room_night_request']).one_or_none()
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
                    "restriction_type": rn.restriction_type
                })
            return jsonify(success=True, room_nights=res)
    return jsonify(success=False)
        
@app.route("/api/hotels/settings", methods=["GET", "POST"])
def hotel_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            res = []
            for rn in room_nights:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "restricted": rn.restricted,
                    "restriction_type": rn.restriction_type
                })
            return jsonify(success=True, room_nights=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.json['event']).all()
            for i in room_nights:
                if [x for x in request.json['room_nights'] if 'id' in x and x['id'] == i.id]:
                    continue
                for j in db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.room_night == i.id).all():
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
                db.session.add(room_night)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/hotels/request_complete.png')
def request_complete():
    if not 'id' in request.args:
        return send_file(os.path.join(config['static_path'], "checkbox_unchecked.png"))
    id = request.args['id']
    badge = db.session.query(Badge).filter(Badge.uber_id == id).one_or_none()
    if not badge:
        return send_file(os.path.join(config['static_path'], "checkbox_unchecked.png"))
    req = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if req:
        return send_file(os.path.join(config['static_path'], "checkbox_checked.png"))
    return send_file(os.path.join(config['static_path'], "checkbox_unchecked.png"))