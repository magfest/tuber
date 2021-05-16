from tuber import app, config
from flask import g, request
from tuber.models import Permission, Grant, Role, DepartmentPermission, DepartmentGrant, DepartmentRole, Session, User, Badge
from tuber.database import db
import datetime
import json

@app.url_value_preprocessor
def load_session(endpoint, values):
    g.user = None
    g.badge = None
    g.session = None
    g.event = None
    g.department = None
    g.perms = {}
    g.department_perms = {}
    if not values:
        values = {}
    if 'event' in values:
        g.event = values['event']
    if 'department' in values:
        g.department = values['department']
    if 'session' in request.cookies:
        res = db.query(Session, User).join(User, Session.user == User.id).filter(Session.secret == request.cookies.get('session')).one_or_none()
        if res:
            session, user = res
            if datetime.datetime.now() < session.last_active + datetime.timedelta(seconds=config.session_duration):
                session.last_active = datetime.datetime.now()
                g.session = session
                g.user = user
                if "event" in values:
                    g.badge = db.query(Badge).filter(Badge.user == g.user.id, Badge.event == values['event']).one_or_none()
                permissions = json.loads(session.permissions)
                g.perms = {k: set(v) for k,v in permissions['event'].items()}
                if not '*' in g.perms:
                    g.perms['*'] = set()
                if g.badge:
                    g.department_perms = {k: set(v) for k,v in permissions['department'][g.badge.event].items()}
                if not '*' in g.department_perms:
                    g.department_perms['*'] = set()
                db.add(session)
            else:
                db.delete(session)
            db.commit()

def flush_session_perms(user_id=None):
    if user_id:
        sessions = db.query(Session).filter(Session.user == user_id).all()
    else:
        sessions = db.query(Session).all()
    for session in sessions:
        perms = get_permissions(user_id=session.user)
        session.permissions=json.dumps(perms)
        db.add(session)
    db.commit()

def get_permissions(user=None):
    if not user and g.user:
        user = g.user.id
    perm_cache = {
        "event": {},
        "department": {}
    }
    if not user:
        return perm_cache

    perms = db.query(Permission, Grant, Role).filter(Grant.user == user, Grant.role == Role.id, Permission.role == Role.id).all()
    for permission, grant, role in perms:
        event = grant.event
        if event == None:
            event = "*"
        if not event in perm_cache['event']:
            perm_cache['event'][event] = []
        perm_cache['event'][event].append(permission.operation)

    user_obj = db.query(User).filter(User.id == user).one()
    for badge in user_obj.badges:
        perm_cache['department'][badge.event] = {}
        dep_perms = db.query(DepartmentPermission, DepartmentGrant, DepartmentRole).filter(DepartmentGrant.badge == badge, DepartmentGrant.role == DepartmentRole.id, DepartmentPermission.role == DepartmentRole.id).all()
        for permission, grant, role in dep_perms:
            department = grant.department
            if department == None:
                department = "*"
            if not department in perm_cache['department'][badge.event]:
                perm_cache['department'][badge.event][department] = []
            perm_cache['department'][badge.event][department].append(permission.operation)
    return perm_cache

def check_permission(permission=None, event=None, department=None):
    return True
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
