#!/bin/sh
source venv/bin/activate

exec gunicorn tuber.wsgi:app -b 0.0.0.0:8080 --timeout 120 --log-file -