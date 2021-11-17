from tuber import app, config
from flask import request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from passlib.hash import sha256_crypt
from sqlalchemy.orm import joinedload
import datetime
import uuid
from tuber.api import *
import requests


headers = {
    'X-Auth-Token': config.uber_api_token
}

@app.route("/api/uber_department")
def get_uber_department():
    event = config.uber_event
    if not 'uber_id' in g.data:
        return "You must provide an uber_id", 406
    dept = db.query(Department).filter(Department.uber_id == g.data['uber_id']).one_or_none()
    if dept:
        return Department.serialize(dept)
    return "", 404

def create_attendee(uber_model, event, hotel_eligible=True):
    staff_badge_type = db.query(BadgeType).filter(BadgeType.name == "Staff", BadgeType.event == event).one_or_none()
    if not staff_badge_type:
        staff_badge_type = BadgeType(name="Staff", description="Experienced Volunteers")
        db.flush()
    badge = Badge(
        event=event,
        badge_type=staff_badge_type.id,
        printed_number=uber_model['badge_num'],
        printed_name=uber_model['badge_printed_name'],
        public_name=uber_model['full_name'],
        search_name=uber_model['full_name'].lower(),
        first_name=uber_model['first_name'],
        last_name=uber_model['last_name'],
        legal_name_matches=(not uber_model['legal_name']),
        emergency_contact_name=uber_model['ec_name'],
        emergency_contact_phone=uber_model['ec_phone'],
        phone=uber_model['cellphone'],
        email=uber_model['email'],
        uber_id=uber_model['id']
    )
    db.add(badge)
    db.flush()
    if hotel_eligible:
        hotel_request = HotelRoomRequest(event=event, badge=badge.id)
        db.add(hotel_request)
        db.flush()
    return badge

@app.route("/api/uber_department_sync", methods=["POST"])
def department_sync():
    event = config.uber_event
    req = {"method": "hotel.eligible_attendees"}
    eligible = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
    req = {"method": "dept.list"}
    uber_depts = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
    uber_depts_names = {}
    for dept_id in uber_depts:
        uber_depts_names[uber_depts[dept_id]] = dept_id

    departments = db.query(Department).filter(Department.event == event).all()
    dept_names = {}
    for dept in departments:
        dept_names[dept.name] = dept

    badges = db.query(Badge).filter(Badge.event == event).options(joinedload('departments')).all()
    badgelookup = {badge.uber_id: badge for badge in badges}

    for attendee in eligible:
        req = {
            "method": "attendee.search",
            "params": [
                attendee,
                "full"
            ]
        }
        uber_model = requests.post(config.uber_api_url, headers=headers, json=req).json()['result'][0]
        if uber_model['badge_status_label'] == "Deferred":
            if attendee in badgelookup:
                print(f"Deleting deferred attendee {attendee} ({badgelookup[attendee].public_name})")
                rnrs = badgelookup[attendee].room_night_requests
                if any([x.requested for x in rnrs]):
                    print("WARNING: ATTENDEE REQUESTED ROOM NIGHTS")
                db.delete(badgelookup[attendee])
        else:
            if not attendee in badgelookup:
                print(f"Missing attendee: {attendee}")
                new_badge = create_attendee(uber_model, event)
                badgelookup[attendee] = new_badge

            badge = badgelookup[attendee]
            for dept_name in uber_model['assigned_depts_labels']:
                if not dept_name in dept_names and dept_name in uber_depts_names:
                    new_dept = Department(uber_id=uber_depts_names[dept_name], event=event, name=dept_name)
                    dept_names[dept_name] = new_dept
                    print(f"Creating department {dept_name}")
                    db.add(new_dept)
                if not dept_names[dept_name] in badge.departments:
                    badge.departments.append(dept_names[dept_name])
                    print(f"Adding {badge.public_name} to {dept_name}")

            to_remove = []
            for dept in badge.departments:
                if not dept.name in uber_model['assigned_depts_labels']:
                    to_remove.append(dept)
            for dept in to_remove:
                print(f"Removing {badge.public_name} from {dept.name}")
                badge.departments.remove(dept)
            db.add(badge)
        
    db.commit()
    return "", 200

@app.route("/api/uber_login", methods=["POST"])
def staffer_auth():
    if not User.query.first():
        return "You must set up this server before using this method to log in.", 403
    event = config.uber_event
    req = {
        "method": "attendee.search",
        "params": [
            request.json['token'],
            "full"
        ]
    }
    results = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
    if len(results) == 0:
        return "no result", 403
    result = results[0]
    if not 'id' in result:
        return "no id", 403
    uber_id = result['id']
    if uber_id != request.json['token']:
        return "wrong token", 403
    if result['badge_status_label'] == "Deferred":
        return "Badge is deferred", 403

    badge = db.query(Badge).filter(Badge.uber_id == uber_id).one_or_none()
    hotel_request = None
    if badge:
        hotel_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if not hotel_request or not badge:
        req = {"method": "hotel.eligible_attendees"}
        eligible = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
        if len(eligible) == 0:
            return "Failed to load eligible attendees", 403
        if not uber_id in eligible:
            return "You are not eligible", 403
    if not badge:
        staff_badge_type = db.query(BadgeType).filter(BadgeType.name == "Staff").one_or_none()
        if not staff_badge_type:
            staff_badge_type = BadgeType(name="Staff", description="Experienced Volunteers")
            db.flush()
        badge = Badge(
            event=event,
            badge_type=staff_badge_type.id,
            printed_number=result['badge_num'],
            printed_name=result['badge_printed_name'],
            public_name=result['full_name'],
            search_name=result['full_name'].lower(),
            first_name=result['first_name'],
            last_name=result['last_name'],
            legal_name_matches=(not result['legal_name']),
            emergency_contact_name=result['ec_name'],
            emergency_contact_phone=result['ec_phone'],
            phone=result['cellphone'],
            email=result['email'],
            uber_id=result['id']
        )

        req = {
            "method": "dept.list",
            "params": []
        }
        uber_depts = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
        uber_depts_names = {}
        for dept_id in uber_depts:
            uber_depts_names[uber_depts[dept_id]] = dept_id

        departments = db.query(Department).filter(Department.event == event).all()
        dept_names = {}
        for dept in departments:
            dept_names[dept.name] = dept

        for dept_name in result['assigned_depts_labels']:
            if not dept_name in dept_names and dept_name in uber_depts_names:
                new_dept = Department(uber_id=uber_depts_names[dept_name], event=event, name=dept_name)
                db.add(new_dept)
                badge.departments.append(new_dept)
            elif dept_name in dept_names:
                badge.departments.append(dept_names[dept_name])
        db.add(badge)
        db.flush()
    if not hotel_request:
        hotel_request = HotelRoomRequest(event=event, badge=badge.id)
        db.add(hotel_request)
        db.flush()

    permissions = {
        "event": {
            str(event): [
                "rooming.*.request",
                "badge.*.searchname",
                f"hotel_room_request.{hotel_request.id}.write",
                "hotel_room_block.*.read",
                "hotel_location.*.read",
                "hotel_room_night.*.read",
            ],
            "*": [
                "event.*.read",
                f"badge.{badge.id}.read",
                "department.*.read"
            ]
        },
        "department": {}
    }

    for department in badge.departments:
        req = {
            "method": "dept.members",
            "params": {
                "department_id": department.uber_id
            }
        }
        result = requests.post(config.uber_api_url, headers=headers, json=req).json()
        if 'error' in result:
            print(f"Could not locate {department.name} ({department.uber_id})")
            continue
        uber_dept_members = result['result']
        for attendee in uber_dept_members['checklist_admins']:
            if attendee['id'] == badge.uber_id:
                if not str(event) in permissions["department"]:
                    permissions["department"][str(event)] = {}
                permissions["department"][str(event)][str(department.id)] = [
                    f"department.*.checklist_admin",
                    "hotel_request.*.approve"
                ]

    session = Session(badge=badge.id, secret=str(uuid.uuid4()), permissions=json.dumps(permissions), last_active=datetime.datetime.now())
    db.add(session)
    db.commit()
    response = jsonify(session.secret)
    response.set_cookie('session', session.secret)
    return response