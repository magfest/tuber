from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, migrate
import json
import sys
import os

config = {
    "development": True,
    "static_folder": "web",
    "migrations_folder": "migrations",
    "sql_connection": "sqlite:///database.db"
}

config_file = "/etc/tuber/tuber.conf"

if '--config' in sys.argv:
    config_file = sys.argv[sys.argv.index('--config') + 1]
if os.path.isfile(config_file):
    try:
        with open(config_file, "r") as FILE:
            config.update(json.loads(FILE.read()))
    except:
        sys.exit("Failed to parse configuration file: {}".format(config_file))

app = Flask(__name__)
app.static_folder = config['static_folder']

app.config['SQLALCHEMY_DATABASE_URI'] = config['sql_connection']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import tuber.models
import tuber.static
import tuber.api

Migrate(app, db)
with app.app_context():
    if os.path.isdir(config['migrations_folder']):
        if config['development']:
            migrate()
        upgrade()
