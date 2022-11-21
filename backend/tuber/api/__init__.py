from .users import *
from .health import *
from .uber import *
from .shifts import *
from .emails import *
from .importer import *
from .hotels import *
from .util import paginate
from functools import partial
from flask import request, jsonify, g
from sqlalchemy.sql.sqltypes import Boolean, Integer, String
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func
from tuber.models import *
from tuber.permissions import *
from tuber.errors import *
from tuber import app
from tuber.database import db
import inspect
import time

READ_PERMS = {"read", "write", "*", "searchname"}
WRITE_PERMS = {"write", "*"}


def event_is_readonly(event):
    if event is None:
        return False
    db_event = db.query(Event).filter(Event.id == event).one_or_none()
    if not db_event:
        return False
    return db_event.readonly


def crud_group(model, event=None, department=None):
    start = time.time()
    if request.method == "GET":
        full = request.args.get(
            "full", False, type=lambda x: x.lower() == 'true')
        deep = request.args.get(
            "deep", False, type=lambda x: x.lower() == 'true')
        count = request.args.get(
            "count", False, type=lambda x: x.lower() == 'true')
        query = db.query(model)
        rows = paginate(query, model, event, department)
        if count:
            return json.dumps(rows.count()), 200
        rows = rows.all()
        now = time.time()
        print(f"{request.path} Load time {now - start}s")
        data = model.serialize(rows, serialize_relationships=full, deep=deep)
        print(f"{request.path} Serialize time {time.time() - now}s")
        return jsonify(data)
    elif request.method == "POST":
        if event_is_readonly(event):
            return "This event is readonly", 403
        if event:
            g.data['event'] = event
        if department:
            g.data['department'] = department
        print(event, g.data)
        instance = model.deserialize(g.data)
        print(instance)
        db.add(instance)
        if hasattr(instance, 'onchange_cb'):
            db.flush()
            for cb in instance.onchange_cb:
                cb(db, instance)
        db.commit()
        return jsonify(model.serialize(instance))
    raise MethodNotAllowed()


def crud_single(model, event=None, department=None, id=None):
    perms = model_permissions(model.__tablename__.lower())
    if request.method == "GET":
        if READ_PERMS.intersection(perms['*']) or (id in perms and READ_PERMS.intersection(perms[id])):
            full = request.args.get(
                "full", False, type=lambda x: x.lower() == 'true')
            instance = db.query(model).filter(model.id == id).one_or_none()
            return jsonify(model.serialize(instance, serialize_relationships=full))
        raise PermissionDenied()
    elif request.method == "PATCH":
        if event_is_readonly(event):
            return "This event is readonly", 403
        if WRITE_PERMS.intersection(perms['*']) or (id in perms and WRITE_PERMS.intersection(perms[id])):
            g.data['id'] = id
            g.data = {k: v for k, v in g.data.items() if hasattr(model, k)}
            instance = model.deserialize(g.data)
            db.add(instance)
            if hasattr(instance, 'onchange_cb'):
                db.flush()
                for cb in instance.onchange_cb:
                    cb(db, instance)
            db.commit()
            return jsonify(model.serialize(instance))
        raise PermissionDenied()
    elif request.method == "DELETE":
        if event_is_readonly(event):
            return "This event is readonly", 403
        if model is Event:
            if event_is_readonly(id):
                return "This event is readonly", 403
        if WRITE_PERMS.intersection(perms['*']) or (id in perms and WRITE_PERMS.intersection(perms[id])):
            instance = db.query(model).filter(model.id == id).one_or_none()
            if not instance:
                return "", 404
            instance_data = None
            if hasattr(instance, 'onchange_cb'):
                instance_data = model.serialize(
                    instance, serialize_relationships=True)
            db.delete(instance)
            if hasattr(instance, 'onchange_cb'):
                db.flush()
                for cb in instance.onchange_cb:
                    cb(db, instance, deleted=instance_data)
            db.commit()
            return "null"
        raise PermissionDenied()
    raise MethodNotAllowed()


for obj in list(locals().values()):
    if inspect.isclass(obj) and issubclass(obj, Base) and hasattr(obj, "__url__"):
        app.add_url_rule(obj.__url__, f"crud_group_{obj.__tablename__}", partial(
            crud_group, obj), methods=["GET", "POST"])
        app.add_url_rule(obj.__url__+"/<int:id>", f"crud_single_{obj.__tablename__}", partial(
            crud_single, obj), methods=["GET", "PATCH", "DELETE"])
