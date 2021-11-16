from functools import partial
from flask import request, jsonify, g
from tuber.models import *
from tuber.permissions import *
from tuber.errors import *
from tuber import app
from tuber.database import db
import inspect

READ_PERMS = {"read", "write", "*", "searchname"}
WRITE_PERMS = {"write", "*"}

def crud_group(model, event=None, department=None):
    if request.method == "GET":
        limit = request.args.get("limit", 0, type=int)
        offset = request.args.get("offset", 0, type=int)
        page = request.args.get("page", 0, type=int)
        if page:
            offset = page*10
            if limit:
                offset = page*limit
        filters = []
        perms = model_permissions(model.__tablename__.lower())
        if not READ_PERMS.intersection(perms['*']):
            ids = [int(x) for x in perms.keys() if READ_PERMS.intersection(perms[x])]
            if not ids:
                raise PermissionDenied(f"User is not able to read any values in {model.__tablename__}")
            filters.append(model.id.in_(ids))
        if event:
            filters.append(model.event == event)
        if department:
            filters.append(model.department == department)
        for key, val in request.args.items():
            if hasattr(model, key):
                filters.append(getattr(model, key) == val)
        rows = db.query(model).filter(*filters)
        if limit:
            rows = rows.offset(offset).limit(limit)
        elif offset:
            rows = rows.offset(offset).limit(10)
        rows = rows.all()
        data = model.serialize(rows)
        return jsonify(data)
    elif request.method == "POST":
        if event:
            g.data['event'] = event
        if department:
            g.data['department'] = department
        instance = model.deserialize(g.data)
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
            instance = db.query(model).filter(model.id == id).one_or_none()
            return jsonify(model.serialize(instance))
        raise PermissionDenied()
    elif request.method == "PATCH":
        if WRITE_PERMS.intersection(perms['*']) or (id in perms and WRITE_PERMS.intersection(perms[id])):
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
        if WRITE_PERMS.intersection(perms['*']) or (id in perms and WRITE_PERMS.intersection(perms[id])):
            instance = db.query(model).filter(model.id == id).one_or_none()
            if not instance:
                return "", 404
            db.delete(instance)
            if hasattr(instance, 'onchange_cb'):
                db.flush()
                for cb in instance.onchange_cb:
                    cb(db, instance)
            db.commit()
            return "null"
        raise PermissionDenied()
    raise MethodNotAllowed()

from .users import *
from .hotels import *
from .importer import *
from .emails import *
from .shifts import *
from .uber import *

for obj in list(locals().values()):
    if inspect.isclass(obj) and issubclass(obj, Base) and hasattr(obj, "__url__"):
        app.add_url_rule(obj.__url__, f"crud_group_{obj.__tablename__}", partial(crud_group, obj), methods=["GET", "POST"])
        app.add_url_rule(obj.__url__+"/<int:id>", f"crud_single_{obj.__tablename__}", partial(crud_single, obj), methods=["GET", "PATCH", "DELETE"])
