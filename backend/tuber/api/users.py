from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt
import datetime
import uuid
from tuber.api import *
from marshmallow_sqlalchemy import ModelSchema
import requests

def allow_self_edits(event=0, department=0):
    if set(g.data.keys()) & set(['id', 'active', 'badges', 'sessions']):
        return False
    return g.url_params['id'] == g.user.id

def allow_self_reads(event=0, department=0):
    return g.url_params['id'] == g.user.id

class UserSchema(ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session
        fields = ['id', 'username', 'email', 'active', 'badges', 'sessions', 'grants']

class UserWriteSchema(ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session
        fields = ['id', 'username', 'email', 'active', 'password']

register_crud("users", {UserSchema(): ["GET"], UserWriteSchema(): ["POST", "PATCH", "DELETE"]}, url_scheme="global", permissions={"GET": [[allow_self_reads, "users.read"]], "PATCH": [[allow_self_edits, "users.update"]]})

class GrantSchema(ModelSchema):
    class Meta:
        model = Grant
        sqla_session = db.session
        fields = ['id', 'user', 'role', 'department']

register_crud("grants", GrantSchema(), url_scheme="global")


class RoleSchema(ModelSchema):
    class Meta:
        model = Role
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'event']

register_crud("roles", RoleSchema(), url_scheme="global")


class PermissionSchema(ModelSchema):
    class Meta:
        model = Permission
        sqla_session = db.session
        fields = ['id', 'operation', 'role']

register_crud("permissions", PermissionSchema(), url_scheme="global")

@app.route("/api/change_password", methods=["POST"])
def change_password():
    if not g.user:
        return "", 403
    if not 'password' in g.data:
        return "You must provide a password", 406
    if len(g.data['password']) < 8:
        return "Your password must be at least 8 characters.", 406
    g.user.password = sha256_crypt.hash(g.data['password'])
    db.session.add(g.user)
    db.session.commit()
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
        db.session.add(user)
        db.session.add(role)
        db.session.flush()
        perm = Permission(operation="*.*", role=role.id)
        grant = Grant(user=user.id, role=role.id)
        db.session.add(perm)
        db.session.add(grant)
        db.session.commit()
        return "null", 200
    return "", 406

@app.route("/api/login", methods=["POST"])
def login():
    if request.json['username'] and request.json['password']:
        user = db.session.query(User).filter(User.username == request.json['username']).one_or_none()
        if user:
            if sha256_crypt.verify(request.json['password'], user.password):
                session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
                db.session.add(session)
                db.session.commit()
                response = jsonify(session.secret)
                response.set_cookie('session', session.secret)
                return response
    return "", 406

@app.route("/api/logout", methods=["POST"])
def logout():
    if g.user:
        sessions = db.session.query(Session).filter(Session.user == g.user.id).delete()
        db.session.commit()
    return "null", 200

@app.route("/api/check_login")
def check_login():
    if g.user:
        user = db.session.query(User).filter(User.id == g.user.id).one()
        return jsonify(user={"email": user.email, "username": user.username, "id": user.id}, session=g.session)
    return "", 406

@app.route("/api/test_permission")
def test_permission():
    return jsonify(check_permission(**request.json))

@app.route("/api/user/permissions")
def get_permissions():
    if 'user' in request.args:
        if check_permission("user.read"):
            perms = []
            permissions = db.session.query(Grant.department, Role.event, Permission.operation).filter(Grant.user == request.args['user']).join(Role, Grant.role == Role.id).join(Permission, Permission.role == Role.id).all()
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
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        return "", 403
    db.session.commit()
    response = jsonify(session.secret)
    response.set_cookie('session', session.secret)
    return response