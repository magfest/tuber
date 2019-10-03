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
        session = db.session.query(Session).filter(Session.secret == request.cookies.get('session')).one_or_none()
        if session:
            if datetime.datetime.now() < session.last_active + datetime.timedelta(seconds=config['session_duration']):
                session.last_active = datetime.datetime.now()
                g.user = session.user
                g.session = session.secret
                permissions = db.session.query(Grant.department, Role.event, Permission.operation).filter(Grant.user == g.user).join(Role, Grant.role == Role.id).join(Permission, Permission.role == Role.id).all()
                for permission in permissions:
                    g.perms.append({"department": permission.department, "event": permission.event, "operation": permission.operation})
                db.session.add(session)
            else:
                session.delete()
            db.session.commit()

def check_permission(operation="", event="", department=""):
    for i in g.perms:
        if event and (not i['event'] is None) and (i['event'] != event):
            continue
        if department and (not i['department'] is None) and (i['department'] != department):
            continue
        perm_entity, perm_op = i['operation'].split(".")
        req_entity, req_op = operation.split(".")
        if perm_entity != "*" and req_entity != perm_entity:
            continue
        if perm_op != "*" and req_op != perm_op:
            continue
        return True
    return False
        