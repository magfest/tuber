from tuber import app, config
from flask import request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from passlib.hash import sha256_crypt
import datetime
import uuid
from tuber.api import *
import requests

@app.route("/api/change_password", methods=["POST"])
def change_password():
    if not g.user:
        return "", 403
    if not 'password' in g.data:
        return "You must provide a password", 406
    if len(g.data['password']) < 8:
        return "Your password must be at least 8 characters.", 406
    g.user.password = sha256_crypt.hash(g.data['password'])
    db.add(g.user)
    db.commit()
    return "null", 200

@app.route("/api/check_initial_setup")
def check_initial_setup():
    if not User.query.first():
        # No users have been created yet, so permissions are disabled for now
        return jsonify(True)
    return jsonify(False)

@app.route("/api/initial_setup", methods=["POST"])
def initial_setup():
    if User.query.first():
        return "Initial setup has already completed.", 403
    if request.json['username'] and request.json['email'] and request.json['password']:
        user = User(username=request.json['username'], email=request.json['email'], password=sha256_crypt.hash(request.json['password']), active=True)
        role = Role(name="Server Admin", description="Allowed to do anything.")
        db.add(user)
        db.add(role)
        db.flush()
        perm = Permission(operation="*.*.*", role=role.id)
        grant = Grant(user=user.id, role=role.id)
        db.add(perm)
        db.add(grant)
        db.commit()
        return "null", 200
    return "", 406

@app.route("/api/login", methods=["POST"])
def login():
    if request.json['username'] and request.json['password']:
        user = db.query(User).filter(User.username == request.json['username']).one_or_none()
        if user:
            if sha256_crypt.verify(request.json['password'], user.password):
                perm_cache = get_permissions(user=user.id)
                session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()), permissions=json.dumps(perm_cache))
                db.add(session)
                db.commit()
                response = jsonify(session.secret)
                response.set_cookie('session', session.secret)
                return response
    return "", 406

@app.route("/api/check_login")
def check_login():
    res = {}
    if g.user:
        user = db.query(User).filter(User.id == g.user.id).one()
        res['user'] = User.serialize(user)
        res['session'] = g.session.secret
    if g.badge:
        badge = db.query(Badge).filter(Badge.id == g.badge.id).one()
        res['badge'] = Badge.serialize(badge)
        res['session'] = g.session.secret
    if res:
        return jsonify(res)
    return "", 406

@app.route("/api/logout", methods=["POST"])
def logout():
    if g.user:
        db.query(Session).filter(Session.user == g.user.id).delete()
        db.commit()
    return "null", 200

@app.route("/api/user/permissions")
def get_user_permissions():
    if 'user' in request.args:
        if check_permission("user." + request.args['user'] + ".read"):
            return jsonify(get_permissions(user=request.args['user']))
        return "", 403
    res = {
        "event": {str(k): v for k, v in g.perms['event'].items()},
        "department": {str(k): {str(m): n for m, n in v.items()} for k, v in g.perms['department']}
    }
    return jsonify(res)

headers = {
    'X-Auth-Token': config.uber_api_token
}

@app.route("/api/uber_login", methods=["POST"])
def staffer_auth():
    if not User.query.first():
        return "You must set up this server before using this method to log in.", 403
    event = config.uber_event
    try:
        req = {
            "method": "attendee.search",
            "params": [
                request.json['token'],
                "full"
            ]
        }
        results = requests.post(config.uber_api_url, headers=headers, json=req).json()['result']
        if results == 0:
            return "no result", 403
    except:
        return "exception", 403
    result = results[0]
    if not 'id' in result:
        return "no id", 403
    uber_id = result['id']
    if uber_id != request.json['token']:
        return "wrong token", 403

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

    session = Session(badge=badge.id, secret=str(uuid.uuid4()), permissions=json.dumps(permissions), last_active=datetime.datetime.now())
    db.add(session)
    db.commit()
    response = jsonify(session.secret)
    response.set_cookie('session', session.secret)
    return response