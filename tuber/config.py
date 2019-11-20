import json
import os

conf = {
    "verbose": False,
    "flask_env": "development",
    "static_path": os.path.abspath("../dist"),
    "migrations_path": "migrations",
    "database_url": "sqlite:////tmp/database.db",
    #"database_url": "postgres://tuber:tuber@127.0.0.1:5432/tuber",
    "session_duration": 7200,
    "uber_api_token": "",
    "uber_api_url": "",
    "config": "/etc/tuber/tuber.json",
    "background_tasks": False,
    "sentry_dsn": "",
    "csp_directives": "",
}

environment = {}
for i in conf.keys():
    if i.upper() in os.environ:
        environment[i] = os.environ[i.upper()]

if os.path.isfile(conf['config']):
    with open(conf['config'], "r") as FILE:
        configfile = json.loads(FILE.read())
    configfile.update(environment)
    conf.update(configfile)

for i in conf:
    vars()[i] = conf[i]