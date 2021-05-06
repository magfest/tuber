import json
import os

conf = {
    "verbose": False,
    "flask_env": "development",
    "migrations_path": "migrations",
    "alembic_ini": "alembic.ini",
    "database_url": "sqlite:///database.db",
    "session_duration": 7200,
    "uber_api_token": "",
    "uber_api_url": "",
    "background_tasks": False,
    "csp_directives": "",
    "force_https": False,
    "server_name": "localhost:8080"
}

environment = {}
for i in conf.keys():
    if i.upper() in os.environ:
        environment[i] = os.environ[i.upper()]

conf.update(environment)

for i in ["verbose", "background_tasks", "force_https"]:
    if isinstance(conf[i], str):
        conf[i] = conf[i].lower() == "true"

for i in ["session_duration"]:
    if isinstance(conf[i], str):
        conf[i] = int(conf[i])

for i in conf:
    vars()[i] = conf[i]
    print("{}: {}".format(i, conf[i]))