from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt
import datetime
import uuid

@app.route("/api/events/list")
def list_events():
    events = db.session.query(Event).all()
    resp_events = []
    for event in events:
        if check_permission("event.read", event.id):
            resp_events.append({"id": event.id, "name": event.name, "description": event.description})
    return jsonify({"success": True, "events": resp_events})

@app.route("/api/events/create", methods=["POST"])
def create_event():
    if check_permission("event.create"):
        if request.json['name'] and request.json['description']:
            event = Event(name=request.json['name'], description=request.json['description'])
            db.session.add(event)
            db.session.flush()
            resp = {"id": event.id, "name": event.name, "description": event.description}
            db.session.commit()
            return jsonify({"success": True, "event": resp})
    return jsonify({"success": False})