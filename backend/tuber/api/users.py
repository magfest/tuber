from tuber import app, config
from flask import request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from passlib.hash import sha256_crypt
import datetime
import uuid
from tuber.api import *

@app.route("/api/change_password/<int:user_id>", methods=["POST"])
def change_password(user_id):
    if not check_permission(f"user.{user_id}.change_password") and not check_permission(f"user.{user_id}.self"):
        return "", 403
    user = db.query(User).filter(User.id == user_id).one()
    if not 'password' in g.data:
        return "You must provide a password", 406
    if len(g.data['password']) < 8:
        return "Your password must be at least 8 characters.", 406
    user.password = sha256_crypt.hash(g.data['password'])
    db.add(user)
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
                badges = db.query(Badge).filter(Badge.user == user.id).all()
                badge = None
                if badges:
                    badge = badges[0].id
                perm_cache = get_permissions(user=user.id)
                session = Session(user=user.id, badge=badge, last_active=datetime.datetime.now(), secret=str(uuid.uuid4()), permissions=json.dumps(perm_cache))
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
        res['badge'] = Badge.serialize(badge, serialize_relationships=True)
        res['session'] = g.session.secret
    if res:
        return jsonify(res)
    return "", 406

@app.route("/api/logout", methods=["POST"])
def logout():
    if g.user:
        db.query(Session).filter(Session.user == g.user.id).delete()
    if 'session' in request.cookies:
        db.query(Session).filter(Session.secret == request.cookies.get('session')).delete()
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
        "department": {str(k): {str(m): n for m, n in v.items()} for k, v in g.perms['department'].items()}
    }
    return jsonify(res)
