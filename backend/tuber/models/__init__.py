
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.inspection
from sqlalchemy.types import JSON
from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime
from tuber.errors import *
from tuber.database import db
from flask import g
import datetime
import json


def model_permissions(name):
    """
    Retrieves the permissions of the current user on the given model class.
    Returns permissions as a dictionary of sets, with instance IDs as keys
    and sets of permitted actions as values.
    """
    permissions = set(g.perms['event'].get('*', []))
    if g.event in g.perms['event']:
        permissions = permissions.union(g.perms['event'][g.event])
    if g.event in g.perms['department'] and g.department in g.perms['department'][g.event]:
        permissions = permissions.union(
            set(g.perms['department'][g.event][g.department]))
    model_perms = {"*": set()}
    for perm in permissions:
        table, instance, action = perm.split(".")
        instance = instance if instance == '*' else int(instance)
        if table == name or table == "*":
            if not instance in model_perms:
                model_perms[instance] = set()
            model_perms[instance].add(action)
    return model_perms


class Model_Base(object):
    modelclasses = {}

    @classmethod
    def onchange(cls, callback):
        if not hasattr(cls, 'onchange_cb'):
            setattr(cls, 'onchange_cb', [])
        cls.onchange_cb.append(callback)
        return callback

    @classmethod
    def get_modelclasses(cls):
        if cls.modelclasses:
            return
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if hasattr(cls, "__tablename__"):
                cls.modelclasses[cls.__tablename__] = cls

    @classmethod
    def get_fields(cls):
        columns = cls.__table__.columns
        relationships = sqlalchemy.inspection.inspect(cls).relationships
        return columns, relationships

    @classmethod
    def serialize_column(cls, data, instances, column):
        """If instances is a list then data must be a list of the same length.
           Data gets updated in place.
        """
        def transform(inst, column): return getattr(inst, column.name)
        if type(column.type) is JSON:
            def transform(inst, column): return json.loads(
                getattr(inst, column.name) or "{}")
        elif type(column.type) is Date:
            def transform(inst, calumn): return getattr(
                inst, column.name).strftime("%Y-%m-%d")
        for i in range(len(instances)):
            data[i][column.name] = transform(instances[i], column)

    @classmethod
    def serialize(cls, instances, parents=None, serialize_relationships=False, deep=False):
        cls.get_modelclasses()
        if type(instances) is cls:
            single_item = True
            instances = [instances]
        else:
            single_item = False
        instance_ids = [instance.id for instance in instances]
        model_perms = model_permissions(cls.__tablename__)
        instance_perms = [model_perms[x]
                          for x in instance_ids if x in model_perms]
        if any(instance_perms):
            instance_perms = set.intersection(*instance_perms)
        else:
            instance_perms = set()
        instances_with_perms = set(model_perms.keys())

        if set(instance_ids).difference(instances_with_perms):
            instance_perms = set()
        perms = set.union(instance_perms, model_perms['*'])
        if not parents:
            parents = []
        # If we are recursing then just truncate to the ID
        if cls in parents:
            if single_item:
                return instance_ids[0]
            return instance_ids
        columns, relationships = cls.get_fields()

        def filter(field):
            if hasattr(field, "hidden") and field.hidden:
                return False
            allow_r = set()
            allow_rw = set()
            if hasattr(field, "allow_r"):
                allow_r = field.allow_r
            if hasattr(field, "allow_rw"):
                allow_rw = field.allow_rw
            if perms.intersection({"read", "write", "*"}.union(allow_r, allow_rw)):
                return True
            return False

        visible_columns = set()
        for column in columns:
            if filter(column):
                visible_columns.add(column)
        visible_relationships = set()
        for relation in relationships:
            if filter(relation):
                visible_relationships.add(relation)

        data = []
        for instance in instances:
            inst_ser = {}
            if serialize_relationships and deep:
                for relation in visible_relationships:
                    new_parents = parents + [cls, ]
                    inst_ser[relation.key] = cls.modelclasses[relation.target.name].serialize(
                        getattr(instance, relation.key), parents=new_parents)
            elif serialize_relationships:
                for relation in visible_relationships:
                    inst_ser[relation.key] = [
                        getattr(x, 'id') for x in getattr(instance, relation.key)]
            data.append(inst_ser)

        for column in visible_columns:
            cls.serialize_column(data, instances, column)
        if single_item:
            return data[0]
        return [x for x in data if x]

    @classmethod
    def filter_columns(cls, instance, perms, existing=None):
        name = cls.__tablename__
        instance_perms = perms['*']
        if "id" in instance:
            if instance['id'] in perms:
                instance_perms.update(perms[instance['id']])
        for key in instance.keys():
            if not hasattr(cls, key):
                raise MalformedRequest(f"Table {name} has no field {key}")
            field = getattr(cls, key)
            if hasattr(field, "hidden") and field.hidden:
                raise PermissionDenied(
                    f"User is not permitted to write {name}.{key}")
            if hasattr(field, "allow_rw"):
                if not instance_perms.intersection(field.allow_rw.union({"write", "*"})):
                    if existing and getattr(existing, key) == instance[key]:
                        continue
                    raise PermissionDenied(
                        f"User is not permitted to write {name}.{key}")
        columns, relations = cls.get_fields()
        for column in columns:
            if column.name in instance:
                key = column.name
                val = instance[key]
                if type(column.type) is DateTime:
                    instance[key] = datetime.datetime.strptime(
                        val, '%Y-%m-%dT%H:%M:%S.%f')
                elif type(column.type) is JSON:
                    instance[key] = json.dumps(val)
        for relation in relations:
            #     new = []
            if relation.key in instance:
                del instance[relation.key]
        #         for model in instance[relation.key]:
        #             new.append(cls.modelclasses[relation.target.name].deserialize(model))
        #         instance[relation.key] = new
        if "created" in instance:
            del instance['created']
        if "modified" in instance:
            del instance['modified']
        return instance

    @classmethod
    def deserialize(cls, data):
        name = cls.__tablename__
        if type(data) is list:
            single_item = False
        else:
            data = [data, ]
            single_item = True
        to_fetch = {}
        models = []
        perms = model_permissions(name)
        for instance in data:
            if type(instance) is int:
                to_fetch[instance] = {}
            elif "id" in instance:
                to_fetch[instance['id']] = instance
            else:
                if not {"create", "*"}.intersection(perms['*']):
                    raise PermissionDenied(
                        f"User is not permitted to create {name}")
                models.append(cls(**cls.filter_columns(instance, perms)))
        existing = db.query(cls).filter(cls.id.in_(to_fetch.keys())).all()
        for model in existing:
            fields = cls.filter_columns(
                to_fetch[model.id], perms, existing=model)
            for key, val in fields.items():
                setattr(model, key, val)
            models.append(model)
        if single_item:
            return models[0]
        return models


_Base = declarative_base(cls=Model_Base)
_Base.query = db.query_property()


class Base(_Base):
    __abstract__ = True
    created = Column(DateTime(), server_default=func.now())
    modified = Column(DateTime(), onupdate=func.now(),
                      server_default=func.now())

# autopep8: off
from tuber.models.user import *
from tuber.models.badge import *
from tuber.models.event import *
from tuber.models.hotel import *
from tuber.models.email import *
from tuber.models.shift import *
from tuber.models.backgroundjob import *