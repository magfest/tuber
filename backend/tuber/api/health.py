from tuber import app
from tuber.database import db, r
from tuber.models import Event
from flask import jsonify
@app.route("/api/_health")
def health():
    status = {
        "backend": "healthy"
    }
    result = 200
    try:
        event = db.query(Event).all()
        status['database'] = "healthy"
    except:
        status['database'] = "unhealthy"
        result = 500

    try:
        if r:
            r.ping()
        else:
            status['redis'] = "disabled"
    except:
        status['redis'] = "unhealthy"
        result = 500
    return jsonify(status), result