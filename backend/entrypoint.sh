#!/bin/sh
tuber migrate
gunicorn --workers $WORKERS -b 0.0.0.0:8080 tuber.wsgi:app