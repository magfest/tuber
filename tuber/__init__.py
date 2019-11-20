from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import upgrade, Migrate
from flask_talisman import Talisman
import tuber.config
import json
import sys
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

db = None
app = None
initialized = False

def init():
    global initialized
    if initialized:
        return
    initialized = True
    global db
    global app
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
                ]
            }
        
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
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(os.path.join(config.migrations_path, "alembic.ini"))
        command.stamp(alembic_cfg, "head")

def migrate():
    Migrate(app, db)
    with app.app_context():
        upgrade()