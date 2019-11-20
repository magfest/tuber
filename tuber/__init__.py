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

    if config.database_url.startswith("sqlite://"):
        path = config.database_url.split("sqlite://")[1]
        if not os.path.isabs(path):
            config.database_url = "sqlite://" + os.path.join(os.path.dirname(__file__), "../../", path)

    app.config['SQLALCHEMY_DATABASE_URI'] = config.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)
    import tuber.csrf
    import tuber.models
    import tuber.static
    import tuber.api

def migrate():
    Migrate(app, db)
    with app.app_context():
        upgrade()