from tuber import app, config
from flask import send_from_directory, send_file, request
import requests
import os

@app.route('/')
def home():
    if config['development']:
        return requests.get(f'http://localhost:8081/').content
    return send_file(os.path.join(config['static_folder'], "index.html"))

@app.route('/<path:path>')
def files(path):
    if config['development']:
        headers = {}
        for header in ["Accept"]:
            if header in request.headers:
                headers[header] = request.headers[header]
        return requests.get(f'http://localhost:8081/{path}', headers=headers).content
    return send_from_directory(config['static_folder'], path)

@app.errorhandler(404)
def default(e):
    return send_file(os.path.join(config['static_folder'], "index.html"))
