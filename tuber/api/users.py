from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt
import datetime
import uuid
from tuber.api import *
from marshmallow_sqlalchemy import ModelSchema

class UserSchema(ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session
        fields = ['id', 'username', 'email', 'active', 'badges', 'sessions']

register_crud("users", UserSchema(), url_scheme="global")

@app.route("/api/check_initial_setup")
def check_initial_setup():
    if not User.query.first():
        # No users have been created yet, so permissions are disabled for now
        return jsonify({"initial_setup": True})
    return jsonify({"initial_setup": False})

@app.route("/api/initial_setup", methods=["POST"])
def initial_setup():
    if User.query.first():
        raise PermissionDenied("Initial setup has already completed.")
    if request.json['username'] and request.json['email'] and request.json['password']:
        user = User(username=request.json['username'], email=request.json['email'], password=sha256_crypt.encrypt(request.json['password']), active=True)
        role = Role(name="Server Admin", description="Allowed to do anything.")
        db.session.add(user)
        db.session.add(role)
        db.session.flush()
        perm = Permission(operation="*.*", role=role.id)
        grant = Grant(user=user.id, role=role.id)
        db.session.add(perm)
        db.session.add(grant)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/api/login", methods=["POST"])
def login():
    if request.json['username'] and request.json['password']:
        user = db.session.query(User).filter(User.username == request.json['username']).one_or_none()
        if user:
            if sha256_crypt.verify(request.json['password'], user.password):
                session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
                db.session.add(session)
                db.session.commit()
                response = jsonify({"success": True, "session": session.secret})
                response.set_cookie('session', session.secret)
                return response
    return jsonify({"success": False})

@app.route("/api/logout", methods=["POST"])
def logout():
    if g.user:
        sessions = db.session.query(Session).filter(Session.user == g.user).delete()
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/api/check_login")
def check_login():
    if g.user:
        user = db.session.query(User).filter(User.id == g.user).one()
        return jsonify({"success": True, "user": {"email": user.email, "username": user.username, "id": user.id}, "session": g.session})
    return jsonify({"success": False})

@app.route("/api/test_permission")
def test_permission():
    return jsonify({"success": check_permission(**request.json)})

@app.route("/api/user/permissions")
def get_permissions():
    if 'user' in request.args:
        if check_permission("user.read"):
            perms = []
            permissions = db.session.query(Grant.department, Role.event, Permission.operation).filter(Grant.user == request.args['user']).join(Role, Grant.role == Role.id).join(Permission, Permission.role == Role.id).all()
            for permission in permissions:
                perms.append({"department": permission.department, "event": permission.event, "operation": permission.operation})
            return jsonify(success=True, permissions=perms)
        return jsonify(success=False)
    return jsonify({"success": True, "permissions": g.perms})

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
            return jsonify(success=False)
    except:
        return jsonify(success=False)
    result = resp.json()['result'][0]
    if not 'id' in result:
        return jsonify(success=False)
    id = result['id']
    if id != request.json['token']:
        return jsonify(success=False)
    if not result['staffing']:
        return jsonify(success=False)
    user = db.session.query(User).filter(User.password == id).one_or_none()
    if user:
        session = Session(user=user.id, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()))
        db.session.add(session)
    else:
        return jsonify(success=False)
    db.session.commit()
    response = jsonify({"success": True, "session": session.secret})
    response.set_cookie('session', session.secret)
    return response