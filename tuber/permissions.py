from tuber import app, db, config
from flask import jsonify, g, request, url_for, redirect
from tuber.models import *
import datetime

class PermissionDenied(Exception):
    status_code = 403

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(PermissionDenied)
def handle_permission_denied(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.before_request
def get_user():
    g.user = None
    g.perms = []
    if 'session' in request.cookies:
        res = db.session.query(Session, User).join(User, Session.user == User.id).filter(Session.secret == request.cookies.get('session')).one_or_none()
        if res:
            session, g.user = res
            if datetime.datetime.now() < session.last_active + datetime.timedelta(seconds=config.session_duration):
                session.last_active = datetime.datetime.now()
                g.session = session.secret
                permissions = db.session.query(Grant.department, Role.event, Permission.operation).filter(Grant.user == g.user.id).join(Role, Grant.role == Role.id).join(Permission, Permission.role == Role.id).all()
                for permission in permissions:
                    g.perms.append({"department": permission.department, "event": permission.event, "operation": permission.operation})
                db.session.add(session)
                event = None
                if request.method == "GET":
                    if "event" in request.args:
                        event = request.args['event']
                if request.method == "POST":
                    if "event" in request.json:
                        event = request.json['event']
            else:
                db.session.delete(session)
            db.session.commit()

def check_permission(permission=None, event=0, department=0):
    if isinstance(permission, list):
        if len(permission) > 1:
            return check_permission(permission[0], event, department) or check_permission(permission[1:], event, department)
        permission = permission[0]
    if callable(permission):
        return permission(event, department)
    for i in g.perms:
        if int(event) and (not (i['event'] is None)) and (i['event'] != int(event)):
            continue
        if int(department) and (not i['department'] is None) and (i['department'] != int(department)):
            continue
        perm_entity, perm_op = i['operation'].split(".")
        req_entity, req_op = permission.split(".")
        if perm_entity != "*" and req_entity != perm_entity:
            continue
        if perm_op != "*" and req_op != perm_op:
            continue
        return True
    return False
        