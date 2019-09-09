from tuber import app
from flask import send_from_directory, send_file, request, Response
import uuid

@app.before_request
def validate_csrf():
    if 'csrf_token' in request.cookies:
        if request.method == "POST":
            if not request.json is None:
                if not 'csrf_token' in request.json:
                    return "You must pass a csrf token in the body with all POST requests that include a csrf cookie."
                if request.json['csrf_token'] != request.cookies.get('csrf_token'):
                    return "Invalid csrf token."
                return
            return "POST Method requires json."

@app.after_request
def insert_csrf(response):
    response.set_cookie('csrf_token', str(uuid.uuid4()))
    return response