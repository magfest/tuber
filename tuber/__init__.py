from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_talisman import Talisman
import json
import sys
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


config = {
    "development": False,
    "static_folder": "../dist",
    "migrations_folder": "migrations",
    "sql_connection": "sqlite:///database.db",
    "session_duration": 7200,
    "uber_api_token": "",
    "uber_api_url": ""
}

config_file = "/etc/tuber/tuber.json"

if '--config' in sys.argv:
    config_file = sys.argv[sys.argv.index('--config') + 1]
if os.path.isfile(config_file):
    try:
        with open(config_file, "r") as FILE:
            config.update(json.loads(FILE.read()))
    except:
        sys.exit("Failed to parse configuration file: {}".format(config_file))

if 'DATABASE_URL' in os.environ:
    config['sql_connection'] = os.environ['DATABASE_URL']

if 'UBER_API_URL' in os.environ:
    config['uber_api_url'] = os.environ['UBER_API_URL']

if 'UBER_API_TOKEN' in os.environ:
    config['uber_api_token'] = os.environ['UBER_API_TOKEN']

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[FlaskIntegration(), SqlalchemyIntegration()]
    )

app = Flask(__name__)
if not config['development']:
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
    
    talisman = Talisman(app, content_security_policy=os.environ.get("CSP_DIRECTIVES", csp))
app.static_folder = config['static_folder']

if config['sql_connection'].startswith("sqlite://"):
    path = config['sql_connection'].split("sqlite://")[1]
    if not os.path.isabs(path):
        config['sql_connection'] = "sqlite://" + os.path.join(os.path.dirname(__file__), "../../", path)

app.config['SQLALCHEMY_DATABASE_URI'] = config['sql_connection']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def init_db():
    global db
    db = SQLAlchemy(app)

    import tuber.csrf
    import tuber.models
    import tuber.static
    import tuber.api
    
    db.create_all()
    db.session.commit()
    Migrate(app, db)