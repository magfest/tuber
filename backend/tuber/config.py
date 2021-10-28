import pathlib
import json
import tuber
import os

conf = {
    "verbose": False,
    "flask_env": "development",
    "database_url": "sqlite:///database.db",
    "session_duration": 7200,
    "uber_api_token": "",
    "uber_api_url": "",
    "uber_event": 1,
    "csp_directives": "",
    "force_https": False,
    "enable_circuitbreaker": False,
    "circuitbreaker_timeout": 1,
    "circuitbreaker_threads": 10,
    "redis_url": "",
    "static_path": os.path.join(tuber.__path__[0], "static")
}

environment = {}
for i in conf.keys():
    if i.upper() in os.environ:
        environment[i] = os.environ[i.upper()]

conf.update(environment)
pathlib.Path("/tmp/app-initialized").touch()
conf['database_url'] = conf['database_url'].replace("postgres:", "postgresql:")

for i in ["verbose", "force_https", "enable_circuitbreaker"]:
    if isinstance(conf[i], str):
        conf[i] = conf[i].lower() == "true"

for i in ["session_duration", "circuitbreaker_threads", "uber_event"]:
    if isinstance(conf[i], str):
        conf[i] = int(conf[i])

for i in ["circuitbreaker_timeout"]:
    if isinstance(conf[i], str):
        conf[i] = float(conf[i])

for i in conf:
    vars()[i] = conf[i]
    print("{}: {}".format(i, conf[i]))
