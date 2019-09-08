from tuber import app, config
from flask import send_from_directory, send_file, request, jsonify

@app.route("/api/users")
def api_users():
    return "It works!"