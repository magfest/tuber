from tuber import app
from flask import jsonify

class MalformedRequest(Exception):
    status_code = 406

    def __init__(self, message="Received a malformed request.", status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(MalformedRequest)
def handle_malformed_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

class MethodNotAllowed(Exception):
    status_code = 405

    def __init__(self, message=f"Request method is not allowed.", status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(MethodNotAllowed)
def handle_method_not_allowed(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

class PermissionDenied(Exception):
    status_code = 403

    def __init__(self, message="Permission Denied.", status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(PermissionDenied)
def handle_permission_denied(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response