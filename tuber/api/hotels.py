from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
import requests
import datetime
import uuid

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
        if not check_permission('hotel_request.create', event=request.args['event']):
            return jsonify(success=False)
        hotel_request = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == g.badge).one_or_none()
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
            requested_roommates = db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester == g.badge).all()
            antirequested_roommates = db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester == g.badge).all()
            current_request['requested_roommates'] = [x.requested for x in requested_roommates]
            current_request['antirequested_roommates'] = [x.requested for x in antirequested_roommates]
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            current_request['room_nights'] = []
            for room_night in room_nights:
                rn = {
                    "id": room_night.id,
                    "name": room_night.name,
                    "checked": False,
                    "restricted": room_night.restricted,
                    "restriction_type": room_night.restriction_type
                }
                room_night_request = db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.badge == g.badge, BadgeToRoomNight.room_night == room_night.id).one_or_none()
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
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
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
        if not check_permission('hotel_request.create', event=request.json['event']):
            return jsonify(success=False)
        req = request.json['request']
        hotel_request = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == g.badge).one_or_none()
        if not hotel_request:
            hotel_request = HotelRoomRequest(badge=g.badge)
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
        db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester == g.badge).delete()
        db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester == g.badge).delete()
        for roommate in req['requested_roommates']:
            db.session.add(HotelRoommateRequest(requester=g.badge, requested=roommate))
        for roommate in req['antirequested_roommates']:
            db.session.add(HotelAntiRoommateRequest(requester=g.badge, requested=roommate))
        db.session.query(BadgeToRoomNight).filter(BadgeToRoomNight.badge == g.badge).delete()
        for room_night in req['room_nights']:
            db.session.add(BadgeToRoomNight(badge=g.badge, requested=room_night['checked'], room_night=room_night['id']))
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