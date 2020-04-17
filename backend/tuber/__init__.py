from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
import tuber.config as config
import json
import sys
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import alembic
from alembic.config import Config as AlembicConfig

db = None
app = None
initialized = False
alembic_config = None

def init():
    global initialized
    if initialized:
        return
    initialized = True
    global db
    global app
    global alembic_config
    if config.sentry_dsn:
        sentry_sdk.init(
            dsn=config.sentry_dsn,
            integrations=[FlaskIntegration(), SqlalchemyIntegration(), RedisIntegration()]
        )

    app = Flask(__name__)
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
    app.static_folder = config.static_path

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

    db = SQLAlchemy(app)
    import tuber.csrf
    import tuber.models
    import tuber.static
    import tuber.api

    if oneshot_db_create:
        # To avoid running migrations on sqlite dev databases just create the current
        # tables and stamp them as being up to date so that migrations won't run.
        # This should only run if there is not an existing db.
        db.create_all()
        alembic.command.stamp(alembic_config, "head")

def migrate():
    alembic.command.upgrade(alembic_config, "head")
