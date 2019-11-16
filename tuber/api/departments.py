from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
import datetime
import uuid

@app.route("/api/departments/list")
def list_departments():
    departments = db.session.query(Department, Event).filter(Department.event_id == Event.id).all()
    filtered = {}
    for department, event in departments:
        if check_permission("event.read", department.event_id):
            if not department.event_id in filtered:
                filtered[department.event_id] = []
            filtered[department.event_id].append({"id": department.id, "name": department.name})
    return jsonify({"success": True, "departments": filtered})