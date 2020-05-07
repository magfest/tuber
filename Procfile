web: cd backend && gunicorn tuber.wsgi:app -b 0.0.0.0:$PORT --timeout 120 --log-file -
worker: cd backend && python tuber/worker.py