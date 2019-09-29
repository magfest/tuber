from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt

@app.route("/api/users")
def api_users():
    return "It works!"

@app.route("/api/check_initial_setup")
def check_initial_setup():
    if not User.query.first():
        # No users have been created yet, so permissions are disabled for now
        return jsonify({"initial_setup": True})
    return jsonify({"initial_setup": False})

@app.route("/api/initial_setup", methods=["POST"])
def initial_setup():
    if User.query.first():
        raise PermissionDenied("Initial setup has already completed.")
    print(request.json)
    if request.json['username'] and request.json['email'] and request.json['password']:
        user = User(username=request.json['username'], email=request.json['email'], password=sha256_crypt.encrypt(request.json['password']))
        db.session.add(user)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False})