from functools import partial
from flask import send_from_directory, send_file, request, jsonify, g, _request_ctx_stack
from tuber.models import *
from tuber.permissions import *
from tuber.csrf import validate_csrf
from tuber import app, db
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import ModelSchema
import inspect
import json
import time
import sqlalchemy
from multiprocessing.pool import ThreadPool
pool = ThreadPool(processes=1)

all_permissions = []

def check_matches(matches, row, env):
    for match in matches:
        if getattr(row, match) != env[match]:
            return False
    return True

def crud(schema, permissions, matches=[], event=0, badge=0, department=0, id=None, onchange=None):
    g.url_params = {"event": event, "badge": badge, "department": department, "id": id}
    if isinstance(schema, dict):
        for key, val in schema.items():
            if request.method in val:
                schema = key
    for perm in permissions[request.method]:
        if not check_permission(perm, event=event, department=department):
            return "", 403
    model = schema.opts.model
    filters = []
    for match in matches:
        filters.append(getattr(model, match) == locals()[match])

    if id is None:
        if request.method == "GET":
            get_filters = []
            for param in g.data:
                if hasattr(model, param):
                    get_filters.append(getattr(model, param) == g.data[param])
            get_filters.extend(filters)
            limit = 0
            offset = 0
            if 'limit' in g.data:
                limit = int(g.data['limit'])
            if 'page' in g.data:
                if not limit:
                    limit = 10
                offset = int(g.data['page']) * limit
            if 'offset' in g.data:
                if not limit:
                    limit = 10
                offset = int(g.data['offset'])
            if 'full' in g.data and g.data['full'].lower() == "true":
                rows = db.session.query(model).filter(*get_filters)
                if limit:
                    rows = rows.offset(offset).limit(limit)
                rows = rows.all()
                return jsonify(schema.dump(rows, many=True))
            rows = db.session.query(model.id).filter(*get_filters)
            if limit:
                rows = rows.offset(offset).limit(limit)
            rows = rows.all()
            return jsonify([x.id for x in rows])
        if request.method == "POST":
            row = schema.load(data={key:val for key, val in g.data.items() if key in schema.Meta.fields})
            for match in matches:
                setattr(row, match, locals()[match])
            db.session.add(row)
            if callable(onchange):
                db.session.flush()
                res = onchange(db, row)
                if res:
                    return res
            db.session.commit()
            return jsonify(schema.dump(row))
    else:
        if request.method == "GET":
            row = schema.get_instance({"id": id})
            if check_matches(matches, row, locals()):
                return jsonify(schema.dump(row))
        if request.method == "PATCH":
            row = schema.get_instance({"id": id})
            if not check_matches(matches, row, locals()):
                return "", 403
            for attr in g.data:
                if hasattr(row, attr) and attr in schema.Meta.fields:
                    setattr(row, attr, g.data[attr])
            if check_matches(matches, row, locals()):
                db.session.add(row)
                if callable(onchange):
                    db.session.flush()
                    res = onchange(db, row)
                    if res:
                        return res
                db.session.commit()
                return jsonify(schema.dump(row))
            return "",  403
        if request.method == "DELETE":
            row = schema.get_instance({"id": id})
            if not check_matches(matches, row, locals()):
                return "", 403
            db.session.delete(row)
            if callable(onchange):
                db.session.flush()
                res = onchange(db, row)
                if res:
                    return res
            db.session.commit()
            return jsonify(schema.dump(row))

def register_crud(name, schema, methods=["GET", "POST", "PATCH", "DELETE"], permissions={}, url_scheme="event", onchange=None):
    default_permissions = {
        "GET": [name+".read"],
        "POST": [name+".create"],
        "PATCH": [name+".update"],
        "DELETE": [name+".delete"],
    }
    default_permissions.update(permissions)

    url_schemes = {
        "event": {
            "base_url": f"/api/events/<int:event>/{name}",
            "matches": ['event'],
        },
        "badge": {
            "base_url": f"/api/events/<int:event>/badge/<int:badge>/{name}",
            "matches": ['event', 'badge'],
        },
        "department": {
            "base_url": f"/api/events/<int:event/department/<int:department>/{name}",
            "matches": ['event', 'department'],
        },
        "global": {
            "base_url": f"/api/{name}",
            "matches": [],
        },
    }
    scheme = url_schemes[url_scheme]
    collective_methods = [x for x in methods if x in ["GET", "POST"]]
    if collective_methods:
        app.add_url_rule(scheme['base_url'], f"rest_collective_{name}", partial(crud, schema, default_permissions, matches=scheme['matches'], onchange=onchange), methods=collective_methods)

    individual_methods = [x for x in methods if x in ["GET", "PATCH", "DELETE"]]
    if individual_methods:
        app.add_url_rule(scheme['base_url']+"/<int:id>", f"rest_individual_{name}", partial(crud, schema, default_permissions, matches=scheme['matches'], onchange=onchange), methods=individual_methods)

    for method in methods: 
        for permission in default_permissions[method]:
            if not permission in all_permissions:
                all_permissions.append(permission)

from .users import *
from .hotels import *
from .events import *
from .importer import *
from .emails import *
from .badges import *
from .shifts import *

def indent(string, level=4):
    lines = string.split("\n")
    return " "*level + ("\n" + " "*level).join(lines)

def underline(string, char="-"):
    length = len(string)
    return string + "\n" + char*length

for obj in list(locals().values()):
    if inspect.isclass(obj):
        if issubclass(obj, ModelSchema):
            if not hasattr(obj.Meta, "model"):
                continue
            name = obj.Meta.model.__name__
            description = "Schema for a {}".format(obj.Meta.model.__name__)
            if obj.Meta.model.__doc__:
                description = obj.Meta.model.__doc__
            sample_obj = {}
            for col in obj.Meta.model.__table__.columns:
                if isinstance(col.type, sqlalchemy.sql.sqltypes.Integer):
                    sample_obj[col.name] = 1
                elif isinstance(col.type, sqlalchemy.sql.sqltypes.String):
                    sample_obj[col.name] = ""
                elif isinstance(col.type, sqlalchemy.sql.sqltypes.Boolean):
                    sample_obj[col.name] = False
                elif isinstance(col.type, sqlalchemy.sql.sqltypes.DateTime):
                    sample_obj[col.name] = datetime.datetime.now()
                else:
                    sample_obj[col.name] = None
            sample_json = json.dumps(obj().dump(sample_obj), indent=2, sort_keys=True)
            sample_json = indent(sample_json, 8)

            obj.__doc__ = """**{}**:

    {}

    .. sourcecode:: json

{}
    """.format(name, description, sample_json)

def job_wrapper(func):
    def wrapped(*args, **kwargs):
        def yo_dawg(request_context, before_request_funcs):
            with app.test_request_context(**request_context):
                for before_request_func in before_request_funcs:
                    before_request_func()
                return func(*args, **kwargs)
        request_context = {
            "path": request.path,
            "base_url": request.base_url,
            "query_string": request.query_string,
            "method": request.method,
            "headers": dict(request.headers),
            "data": bytes(request.data),
        }
        result = pool.apply_async(yo_dawg, (request_context, app.before_request_funcs[None]))
        return result.get()
    return wrapped

for key, val in app.view_functions.items():
    app.view_functions[key] = job_wrapper(val)