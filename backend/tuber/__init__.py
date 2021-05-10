"""The base module for Tuber"""

from flask import Flask, g, _app_ctx_stack
from flask_talisman import Talisman
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from types import SimpleNamespace
import redis
import tuber.config as config
import json
import sys
import os
import re
import alembic
from alembic.config import Config as AlembicConfig

db = None
r = None
app = Flask(__name__)
initialized = False
alembic_config = None

if not initialized:
    initialized = True

    if config.flask_env == "production":
        csp = config.csp_directives
        if not csp:
            csp = {
                'default-src': '\'self\'',
                'style-src': [
                    '\'unsafe-inline\' \'self\'',
                    'fonts.googleapis.com',
                    'use.fontawesome.com',
                ],
                'font-src': [
                    'fonts.gstatic.com',
                    'use.fontawesome.com',
                ],
                'worker-src': [
                    'blob:',
                ],
                'img-src': [
                    'https:',
                ],
            }
            
        if config.force_https:
            talisman = Talisman(app, content_security_policy=csp)

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

    if config.redis_url:
        m = re.search("redis://([a-z0-9\.]+)(:(\d+))?(/(\d+))?", config.redis_url)
        redis_host = m.group(1)
        redis_port = 6379
        if m.group(3):
            redis_port = int(m.group(3))
        redis_db = 0
        if m.group(5):
            redis_db = int(m.group(5))
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    #db = SQLAlchemy(app)
    db = sqlalchemy
    db.Model = declarative_base()
    db.relationship = relationship
    engine = sqlalchemy.create_engine(config.database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db.session = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)
    db.Model.query = db.session.query_property()
    import tuber.csrf
    import tuber.models
    import tuber.api

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
