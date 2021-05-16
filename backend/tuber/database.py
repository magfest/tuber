import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import alembic
from alembic.config import Config as AlembicConfig
import redis
from tuber import config, app
from tuber.errors import *
from flask import _app_ctx_stack
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

engine = sqlalchemy.create_engine(config.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)
            
def create_tables():
    from tuber.models import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    from tuber.models import Base
    Base.metadata.drop_all(bind=engine)

def migrate():
    alembic_config = AlembicConfig(config.alembic_ini)
    if oneshot_db_create:
        # To avoid running migrations on sqlite dev databases just create the current
        # tables and stamp them as being up to date so that migrations won't run.
        # This should only run if there is not an existing db.
        create_tables()
        alembic.command.stamp(alembic_config, "head")
    alembic.command.upgrade(alembic_config, "head")

r = None
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
