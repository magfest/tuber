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
    email = result['email']
    username = id
    if id != request.json['token']:
        return {"success": False}
    if not result['staffing']:
        return {"success": False}
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        role = db.session.query(Role).filter(Role.name == "Default Staff").one_or_none()
        if not role:
            role = Role(name="Default Staff", description="Automatically assigned to staff.")
            db.session.add(role)
            db.session.flush()
            for perm in ['staff.search_names', 'hotel_request.create', 'event.read']:
                permission = Permission(operation=perm, role=role.id)
                db.session.add(permission)
        user = User(username=username, email=email, password=id, active=False)
        db.session.add(user)
        db.session.flush()
        grant = Grant(user=user.id, role = role.id)
        db.session.add(grant)
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    db.session.commit()
    response = jsonify({"success": True, "session": session.secret})
    response.set_cookie('session', session.secret)
    return response


@app.route("/api/hotels/request", methods=["POST"])
def submit_hotels_request():
    if check_permission("hotel_request.create"):
        #if request.json['name'] and request.json['description']:
        #    event = Event(name=request.json['name'], description=request.json['description'])
        #    db.session.add(event)
        #    db.session.flush()
        #    resp = {"id": event.id, "name": event.name, "description": event.description}
        #    db.session.commit()
        resp = {}
        return jsonify({"success": True, "event": resp})
    return jsonify({"success": False})

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