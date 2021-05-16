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
        return "", 200
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
    if g.user:
        user = db.query(User).filter(User.id == g.user.id).one()
        return jsonify(user={"email": user.email, "username": user.username, "id": user.id}, session=g.session.secret)
    return "", 406

@app.route("/api/logout", methods=["POST"])
def logout():
    if g.user:
        db.query(Session).filter(Session.user == g.user.id).delete()
        db.commit()
    return "", 200

@app.route("/api/user/permissions")
def get_user_permissions():
    if 'user' in request.args:
        if check_permission("user.read"):
            perms = []
            permissions = db.query(Grant.department, Role.event, Permission.operation).filter(Grant.user == request.args['user']).join(Role, Grant.role == Role.id).join(Permission, Permission.role == Role.id).all()
            for permission in permissions:
                perms.append({"department": permission.department, "event": permission.event, "operation": permission.operation})
            return jsonify(perms)
        return "", 403
    return jsonify(g.perms)

headers = {
    'X-Auth-Token': config.uber_api_token
}

@app.route("/api/uber_login", methods=["POST"])
def staffer_auth():
    try:
        req = {
            "method": "attendee.search",
            "params": [
                request.json['token'],
                "full"
            ]
        }
        resp = requests.post(config.uber_api_url, headers=headers, json=req)
        if len(resp.json()['result']) == 0:
            return "", 403
    except:
        return "", 403
    result = resp.json()['result'][0]
    if not 'id' in result:
        return "", 403
    id = result['id']
    if id != request.json['token']:
        return "", 403
    if not result['staffing']:
        return "", 403
    user = db.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.add(session)
    else:
        return "", 403
    db.commit()
    response = jsonify(db.secret)
    response.set_cookie('db', db.secret)
    return response