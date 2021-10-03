from tuber import app
from flask import send_from_directory, send_file, request, Response, g
import uuid

@app.before_request
def validate_csrf():
    if 'csrf_token' in request.cookies:
        if request.path.startswith("/api"):
            if not 'CSRF_Token' in request.headers:
                return "You must pass a csrf token when making an API request with a session cookie."
            if request.cookies['csrf_token'] != request.headers['CSRF_Token']:
                return "Invalid csrf token."
        if request.method == "GET":
            g.data = dict(request.args)
            return
        if not request.json is None:
            g.data = dict(request.json)
            return
        if not request.form is None:
            g.data = dict(request.form)
            return
        return f"{request.method} Method requires json or form data."

@app.after_request
def insert_csrf(response):
    if not 'csrf_token' in request.cookies:
        response.set_cookie('csrf_token', str(uuid.uuid4()))
    return response