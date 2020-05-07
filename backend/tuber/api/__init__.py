from functools import partial
from flask import send_from_directory, send_file, request, jsonify, g
from tuber.models import *
from tuber.permissions import *
from tuber import app, db
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import ModelSchema
import inspect
import json
import sqlalchemy

all_permissions = []

def check_matches(matches, row, env):
    for match in matches:
        if getattr(row, match) != env[match]:
            return False
    return True

def crud(schema, permissions, matches=[], event=0, badge=0, department=0, id=None):
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
            if 'full' in g.data and g.data['full'].lower() == "true":
                rows = db.session.query(model).filter(*get_filters).all()
                return jsonify(schema.dump(rows, many=True))
            rows = db.session.query(model.id).filter(*get_filters).all()
            return jsonify([x.id for x in rows])
        if request.method == "POST":
            row = model(**{key:val for key, val in g.data.items() if key in schema.Meta.fields})
            for match in matches:
                setattr(row, match, locals()[match])
            db.session.add(row)
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
                db.session.commit()
                return jsonify(schema.dump(row))
            return "",  403
        if request.method == "DELETE":
            row = schema.get_instance({"id": id})
            if not check_matches(matches, row, locals()):
                return "", 403
            db.session.delete(row)
            db.session.commit()
            return jsonify(schema.dump(row))

def register_crud(name, schema, methods=["GET", "POST", "PATCH", "DELETE"], permissions={}, url_scheme="event"):
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
        app.add_url_rule(scheme['base_url'], f"rest_collective_{name}", partial(crud, schema, default_permissions, matches=scheme['matches']), methods=collective_methods)

    individual_methods = [x for x in methods if x in ["GET", "PATCH", "DELETE"]]
    if individual_methods:
        app.add_url_rule(scheme['base_url']+"/<int:id>", f"rest_individual_{name}", partial(crud, schema, default_permissions, matches=scheme['matches']), methods=individual_methods)

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
