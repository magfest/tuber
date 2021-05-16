from tuber import app, config
from flask import g, request
from tuber.models import *
from tuber.database import db
import datetime

@app.url_value_preprocessor
def load_session(endpoint, values):
    g.user = None
    g.badge = None
    g.session = None
    g.event = None
    g.department = None
    g.perms = set()
    g.department_perms = set()
    if 'event' in values:
        g.event = values['event']
    if 'department' in values:
        g.department = values['department']
    if 'session' in request.cookies:
        res = db.query(Session, User).join(User, Session.user == User.id).filter(Session.secret == request.cookies.get('session')).one_or_none()
        if res:
            session, user = res
            if datetime.datetime.now() < session.last_active + datetime.timedelta(seconds=config.session_duration):
                g.session.last_active = datetime.datetime.now()
                g.session = session
                g.user = user
                if "event" in values:
                    g.badge = session.query(Badge).filter(Badge.user == g.user.id, Badge.event == values['event']).one_or_none()
                permissions = json.loads(session.permissions)
                g.perms = {k: set(v) for k,v in permissions['event'].items()}
                if not '*' in g.perms:
                    g.perms['*'] = set()
                g.department_perms = {k: set(v) for k,v in permissions['department'].items()}
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

def get_permissions(user_id=None):
    if not user_id and g.user:
        user_id = g.user.id
    perm_cache = {
        "event": {},
        "department": {}
    }
    if not user_id:
        return perm_cache

    perms = db.query(Permission, Grant, Role).filter(Grant.user == user_id, Grant.role == Role.id, Permission.role == Role.id).all()
    for permission, grant, role in perms:
        if not grant.event in perm_cache['event']:
            perm_cache['event'][grant.event] = []
        perm_cache['event'][grant.event].append(permission.operation)

    dep_perms = db.query(DepartmentPermission, DepartmentGrant, DepartmentRole).filter(DepartmentGrant.user == user_id, DepartmentGrant.role == DepartmentRole.id, DepartmentPermission.role == DepartmentRole.id).all()
    for permission, grant, role in dep_perms:
        if not grant.department in perm_cache['department']:
            perm_cache['department'][grant.department] = []
        perm_cache['department'][grant.department].append(permission.operation)
    return perm_cache

def check_permission(permission=None, event=0, department=0):
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
        
def model_permissions(model):
    """
    Retrieves the permissions of the current user on the given model class.
    Returns permissions as a dictionary of sets, with instance IDs as keys
    and sets of permitted actions as values.
    """
    permissions = g.perms['*'] + g.department_perms['*']
    if g.event in g.perms:
        permissions += g.perms[g.event]
    if g.department in g.department_perms:
        permissions += g.department_perms
    model_perms = {}
    for perm in permissions:
        table, instance, action = perm.split(".")
        if table == model.__tablename__:
            if not instance in model_perms:
                model_perms[instance] = set()
            model_perms[instance].add(action)
    return model_perms