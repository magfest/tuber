from tuber import app
from flask import send_from_directory, send_file, request, Response, g
import uuid

@app.before_request
def validate_csrf():
    if 'csrf_token' in request.cookies:
        if request.method == "GET":
            if request.path.startswith("/api"):
                if not 'csrf_token' in request.args:
                    return "You must pass a csrf token when making an API request with the csrf_token cookie set."
                if request.args['csrf_token'] != request.cookies.get('csrf_token'):
                    return "Invalid csrf token."
                g.data = dict(request.args)
                del g.data['csrf_token']
            return
        if not request.json is None:
            if not 'csrf_token' in request.json:
                return f"You must pass a csrf token in the body with all {request.method} requests that include a csrf cookie."
            if request.json['csrf_token'] != request.cookies.get('csrf_token'):
                return "Invalid csrf token."
            g.data = dict(request.json)
            del g.data['csrf_token']
            return
        return f"{request.method} Method requires json."

@app.after_request
def insert_csrf(response):
    if not 'csrf_token' in request.cookies:
        response.set_cookie('csrf_token', str(uuid.uuid4()))
    return response