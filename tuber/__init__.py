from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_talisman import Talisman
import argparse
import json
import sys
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Increase Verbosity", action="store_true")
parser.add_argument("-e", "--flask_env", help="Set the flask environment")
parser.add_argument("-s", "--static_path", help="Set the folder to serve static files from")
parser.add_argument("-m", "--migrations_path", help="Set the folder that contains the sql database migrations to run")
parser.add_argument("-d", "--database_url", help="Set the connection string for the sql server")
parser.add_argument("-S", "--session_duration", help="Sets the duration of a user session", type=int)
parser.add_argument("-u", "--uber_api_token", help="The API key to use when importing data from uber")
parser.add_argument("-U", "--uber_api_url", help="The URL of the uber server to import data from")
parser.add_argument("-c", "--config", help="Path to the tuber config file")
args = parser.parse_args()

config = {
    "verbose": False,
    "flask_env": "production",
    "static_path": "../dist",
    "migrations_path": "migrations",
    "database_url": "sqlite:///database.db",
    "session_duration": 7200,
    "uber_api_token": "",
    "uber_api_url": "",
    "config": "/etc/tuber/tuber.json"
}

for i in config.keys():
    if i.upper() in os.environ:
        config[i] = os.environ[i.upper()]

for i in vars(args).keys():
    if getattr(args, i):
        config[i] = getattr(args, i)

if os.path.isfile(config['config']):
    with open(config['config'], "r") as FILE:
        configfile = json.loads(FILE.read())
    configfile.update(config)
    config = configfile

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[FlaskIntegration(), SqlalchemyIntegration(), RedisIntegration()]
    )

app = Flask(__name__)
if config['flask_env'] == "production":
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
app.static_folder = config['static_path']

if config['database_url'].startswith("sqlite://"):
    path = config['database_url'].split("sqlite://")[1]
    if not os.path.isabs(path):
        config['database_url'] = "sqlite://" + os.path.join(os.path.dirname(__file__), "../../", path)

app.config['SQLALCHEMY_DATABASE_URI'] = config['database_url']
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