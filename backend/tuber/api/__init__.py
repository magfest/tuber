from functools import partial
from flask import request, jsonify, g
from sqlalchemy.orm import joinedload
from tuber.models import *
from tuber.permissions import *
from tuber.errors import *
from tuber import app
from tuber.database import db
import inspect
import time

READ_PERMS = {"read", "write", "*", "searchname"}
WRITE_PERMS = {"write", "*"}

def crud_group(model, event=None, department=None):
    start = time.time()
    if request.method == "GET":
        count = request.args.get("count", False, type=lambda x: x.lower()=='true')
        sort = request.args.get("sort", "")
        order = request.args.get("order", "asc")
        limit = request.args.get("limit", 0, type=int)
        offset = request.args.get("offset", 0, type=int)
        page = request.args.get("page", 0, type=int)
        full = request.args.get("full", False, type=lambda x: x.lower()=='true')
        deep = request.args.get("deep", False, type=lambda x: x.lower()=='true')
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
        if full:
            columns, relationships = model.get_fields()
            for relation in relationships:
                rows = rows.options(joinedload(relation.key))
        if count:
            return json.dumps(rows.count()), 200
        if hasattr(model, sort):
            if order == "asc":
                rows = rows.order_by(getattr(model, sort))
            else:
                rows = rows.order_by(getattr(model, sort).desc())
        if limit:
            rows = rows.offset(offset).limit(limit)
        elif offset:
            rows = rows.offset(offset).limit(10)
        rows = rows.all()
        now = time.time()
        print(f"{request.path} Load time {now - start}s")
        data = model.serialize(rows, serialize_relationships=full, deep=deep)
        print(f"{request.path} Serialize time {time.time() - now}s")
        if not data:
            return "[]", 404
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
            full = request.args.get("full", False, type=lambda x: x.lower()=='true')
            instance = db.query(model).filter(model.id == id).one_or_none()
            return jsonify(model.serialize(instance, serialize_relationships=full))
        raise PermissionDenied()
    elif request.method == "PATCH":
        if WRITE_PERMS.intersection(perms['*']) or (id in perms and WRITE_PERMS.intersection(perms[id])):
            g.data['id'] = id
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
            instance_data = None
            if hasattr(instance, 'onchange_cb'):
                instance_data = model.serialize(instance, serialize_relationships=True)
            db.delete(instance)
            if hasattr(instance, 'onchange_cb'):
                db.flush()
                for cb in instance.onchange_cb:
                    cb(db, instance, deleted=instance_data)
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
