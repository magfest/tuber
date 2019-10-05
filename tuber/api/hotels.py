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