from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.worker import worker_conn
from sqlalchemy import or_
from rq import Queue
import requests
import datetime
import uuid
import csv
import io

def get_uber_csv(session, model, url):
    data = session.post(url+"/devtools/export_model", data={"selected_model": model}).text
    stream = io.StringIO(data)
    reader = csv.DictReader(stream)
    return list(reader)

def run_staff_import(email, password, url, event):
    session = requests.Session()
    session.post(url+"/accounts/login", data={"email": email, "password": password, "original_location": "homepage"})
    attendees = get_uber_csv(session, "Attendee", url)
    num_staff = 0
    print("Retrieved export")

    role = db.session.query(Role).filter(Role.name == "Default Staff").one_or_none()
    if not role:
        role = Role(name="Default Staff", description="Automatically assigned to staff.", event=event)
        db.session.add(role)
        db.session.flush()
        for perm in ['staff.search_names', 'hotel_request.create', 'event.read']:
            permission = Permission(operation=perm, role=role.id)
            db.session.add(permission)

    dh_role = db.session.query(Role).filter(Role.name == "Department Head").one_or_none()
    if not dh_role:
        dh_role = Role(name="Department Head", description="Automatically assigned to department heads.", event=event)
        db.session.add(dh_role)
        db.session.flush()
        for perm in ['department.write', 'hotel_request.approve']:
            permission = Permission(operation=perm, role=dh_role.id)
            db.session.add(permission)

    print("Adding attendees...")
    for attendee in attendees:
        if attendee['hotel_eligible'].lower() == "true":
            num_staff += 1
            user = db.session.query(User).filter(User.password == attendee['id']).one_or_none()
            if not user:
                user = User(username=attendee['id'], email=attendee['id'], password=attendee['id'], active=False)
                db.session.add(user)
                db.session.flush()
            grant = db.session.query(Grant).filter(Grant.user == user.id, Grant.role == role.id).one_or_none()
            if not grant:
                grant = Grant(user=user.id, role=role.id)
                db.session.add(grant)
            badge = db.session.query(Badge).filter(Badge.event_id == event, Badge.uber_id == attendee['id']).one_or_none()
            if not badge:
                badge = Badge(
                    uber_id = attendee['id'],
                    event_id = event,
                    printed_number = attendee['badge_num'],
                    printed_name = attendee['badge_printed_name'],
                    search_name = "{} {}".format(attendee['first_name'].lower(), attendee['last_name'].lower()),
                    first_name = attendee['first_name'],
                    last_name = attendee['last_name'],
                    legal_name = attendee['legal_name'],
                    legal_name_matches = bool(attendee['legal_name']),
                    email = attendee['email'],
                    user_id = user.id
                )
                db.session.add(badge)

    print("Adding departments...")
    departments = get_uber_csv(session, "Department", url)
    for department in departments:
        current = db.session.query(Department).filter(Department.event_id == event, Department.uber_id == department['id']).one_or_none()
        if not current:
            dept = Department(
                uber_id = department['id'],
                name = department['name'],
                description = department['description'],
                event_id = event
            )
            db.session.add(dept)
            
    print("Adding staffers to departments...")
    deptmembers = get_uber_csv(session, "DeptMembership", url)
    for dm in deptmembers:
        badge = db.session.query(Badge).filter(Badge.event_id == event, Badge.uber_id == dm['attendee_id']).one_or_none()
        if not badge:
            print("Could not find badge {} to place in department {}.".format(dm['attendee_id'], dm['department_id']))
            continue
        department = db.session.query(Department).filter(Department.event_id == event, Department.uber_id == dm['department_id']).one_or_none()
        if not department:
            print("Could not find department {} for attendee {}.".format(dm['department_id'], dm['attendee_id']))
            continue
        existing = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == badge.id, BadgeToDepartment.department == department.id).one_or_none()
        if not existing:
            department_member = BadgeToDepartment(
                badge = badge.id,
                department = department.id
            )
            db.session.add(department_member)
        grant = db.session.query(Grant).filter(Grant.user == badge.user_id, Grant.role == dh_role.id, Grant.department==department.id).one_or_none()
        if (dm['is_dept_head'].lower() == "true") or (dm['is_checklist_admin'].lower() == "true"):
            if not grant:
                grant = Grant(user=badge.user_id, role=dh_role.id, department=department.id)
                db.session.add(grant)
        elif grant:
            db.session.delete(grant)
    print("Committing changes...")
    db.session.commit()
    print("Done.")

@app.route("/api/importer/uber_staff", methods=["POST"])
def import_uber_staff():
    print("Importing staff...")
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return jsonify({"success": False})
    if not check_permission("import.staff", event=request.json['event']):
        return jsonify({"success": False})

    email = request.json['email']
    password = request.json['password']
    url = request.json['uber_url']

    if config.background_tasks:
        worker_queue = Queue(connection=worker_conn)
        worker_queue.enqueue(run_staff_import, email, password, url, event.id, job_timeout=1800)
    else:
        run_staff_import(email, password, url, event.id)
    return jsonify({"success": True})
