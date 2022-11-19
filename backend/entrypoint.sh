#!/bin/sh
echo "Starting"
tuber migrate
echo "Running webserver"
export PYTHONUNBUFFERED=TRUE
WORKER_TIMEOUT=${TIMEOUT:-300}

PYTHONUNBUFFERED=TRUE gunicorn --workers $WORKERS --timeout $WORKER_TIMEOUT -b 0.0.0.0:8080 tuber.wsgi:app
echo "Exited webserver"