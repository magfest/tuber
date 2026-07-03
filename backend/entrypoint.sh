#!/bin/sh
# Fail hard if migrations fail — serving with a stale schema breaks every
# endpoint that touches new columns, which is worse than a failed deploy
# (ECS keeps the previous task running when the new one won't start).
set -e
echo "Starting"
# python -m resolves the package from the working directory (/app) as well as
# site-packages, so migrations run even if the installed package is broken.
python -m tuber migrate
echo "Running webserver"
export PYTHONUNBUFFERED=TRUE
WORKER_TIMEOUT=${TIMEOUT:-300}

PYTHONUNBUFFERED=TRUE gunicorn --workers $WORKERS --timeout $WORKER_TIMEOUT -b 0.0.0.0:8080 tuber.wsgi:app
echo "Exited webserver"