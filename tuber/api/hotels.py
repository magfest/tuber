from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from sqlalchemy import or_
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
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        user = User(username=username, email=email, password=id, active=False)
        db.session.add(user)
        db.session.flush()
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    db.session.commit()
    response = jsonify({"success": True, "session": session.secret})
    response.set_cookie('session', session.secret)
    return response


@app.route("/api/hotels/request", methods=["POST"])
def submit_hotels_request():
    if check_permission("hotels.request.create"):
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
    if not request.json['event']:
        return jsonify({"success": False})
    if check_permission("staff.search_names", event=request.json['event']):
        results = db.session.query(Badge).filter(Badge.search_name.like("%{}%".format(request.json['search'].lower()))).limit(25).all()
        filtered_results = []
        for res in results:
            departments = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == res.id).all()
            filtered_departments = []
            for dept in departments:
                filtered_departments.append(dept.id)
            filtered_results.append({
                "name": "{} {}".format(res.first_name, res.last_name),
                "id": res.id,
                "departments": filtered_departments
            })
        return jsonify({"success": True, "results": filtered_results})