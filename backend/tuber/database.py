
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
import alembic
from alembic.config import Config as AlembicConfig
import redis
from tuber import config, app
from flask import g, _app_ctx_stack
import json
import sys
import os
import re

oneshot_db_create = False
if config.database_url.startswith("sqlite://"):
    db_path = config.database_url.split("sqlite://")[1]
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(__file__), "../../", db_path)
        config.database_url = "sqlite://" + db_path
    if not os.path.exists(db_path):
        oneshot_db_create = True

app.config['SQLALCHEMY_DATABASE_URI'] = config.database_url
print("Connecting to database {}".format(config.database_url))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

alembic_config = AlembicConfig(config.alembic_ini)

db = sqlalchemy

class Model_Base(object):
    modelclasses = {}

    @classmethod
    def get_modelclasses(cls):
        if cls.modelclasses:
            return
        for mapper in db.Model.registry.mappers:
            cls = mapper.class_
            if hasattr(cls, "__tablename__"):
                cls.modelclasses[cls.__tablename__] = cls

    def __perms__(self, g):
        return []

    @classmethod
    def get_fields(cls):
        columns = cls.__table__.columns
        relationships = inspect(cls).relationships
        return columns, relationships

    @classmethod
    def get_perms(cls, g, instances):
        name = cls.__tablename__
        actions = set()
        action_ids = {}
        for perm in g.perms:
            table, id, action = perm.split(".")
            if table != name:
                continue
            if id == "*":
                actions.add(action)
                continue
            else:
                if not action in action_ids:
                    action_ids[action] = set()
                action_ids[action].add(id)
            if type(instances) is cls:
                if id == str(instances.id):
                    actions.add(action)
        
        if type(instances) is cls:
            actions.update(instances.__perms__(g))
            return actions

        for instance in instances:
            instance_actions = instance.__perms__(g)
            for action in instance_actions:
                if not action in action_ids:
                    action_ids = set()
                action_ids[action].add(id)
        if action_ids:
            instance_ids = {str(x.id) for x in instances}
            for action, ids in action_ids.items():
                if instance_ids.issubset(ids):
                    actions.add(action)
        return actions

    @classmethod
    def serialize_column(cls, data, instances, column):
        """If instances is a list then data must be a list of the same length.
           Data gets updated in place.
        """
        transform = lambda inst, column: getattr(inst, column.name)
        if type(column.type) is db.JSON:
            transform = lambda inst, column: json.loads(getattr(inst, column.name))
        if type(instances) is cls:
            data[column.name] = transform(instances, column)
        else:
            for i in range(len(instances)):
                data[i][column.name] = transform(instances[i], column)

    @classmethod
    def serialize(cls, instances, g, parents=None):
        cls.get_modelclasses()
        perms = cls.get_perms(g, instances)
        if not parents:
            parents = []
        # If we are recursing then just truncate to the ID
        if cls in parents:
            if type(instances) is list:
                return [instance.id for instance in instances]
            return instance.id
        columns, relationships = cls.get_fields()
        def filter(field):
            if hasattr(field, "hidden") and field.hidden:
                return False
            if perms.intersection({"read", "write", "*"}.union(field.allow_r, field.allow_rw)):
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

        if type(instances) is cls:
            data = {}
            for relation in visible_relationships:
                new_parents = parents + [cls,]
                data[relation.key] = cls.modelclasses[relation.target.name].serialize(getattr(instances, relation.key), g, parents=new_parents)
        else:
            data = []
            for instance in instances:
                inst_ser = {}
                for relation in visible_relationships:
                    new_parents = parents + [cls,]
                    inst_ser[relation.key] = cls.modelclasses[relation.target.name].serialize(getattr(instance, relation.key), g, parents=new_parents)
                data.append(inst_ser)
            
        for column in visible_columns:
            cls.serialize_column(data, instances, column)
        return data

    @classmethod
    def deserialize(cls, data, g, perms=[]):
        print(data)

db.Model = declarative_base(cls=Model_Base)
db.relationship = relationship
engine = sqlalchemy.create_engine(config.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db.session = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)
db.Model.query = db.session.query_property()

def create_tables():
    db.Model.metadata.create_all(bind=engine)

def drop_tables():
    db.Model.metadata.drop_all(bind=engine)

def migrate():
    if oneshot_db_create:
        # To avoid running migrations on sqlite dev databases just create the current
        # tables and stamp them as being up to date so that migrations won't run.
        # This should only run if there is not an existing db.
        create_tables()
        alembic.command.stamp(alembic_config, "head")
    alembic.command.upgrade(alembic_config, "head")

db.r = None
if config.redis_url:
    m = re.search("redis://([a-z0-9\.]+)(:(\d+))?(/(\d+))?", config.redis_url)
    redis_host = m.group(1)
    redis_port = 6379
    if m.group(3):
        redis_port = int(m.group(3))
    redis_db = 0
    if m.group(5):
        redis_db = int(m.group(5))
    db.r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
