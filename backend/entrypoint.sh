#!/bin/sh
echo "Starting"
tuber migrate
echo "Running webserver"
gunicorn --workers $WORKERS -b 0.0.0.0:8080 tuber.wsgi:app
echo "Exited webserver"