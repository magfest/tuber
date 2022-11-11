from tuber import app
from tuber.database import db, r
from tuber.models import Event
from flask import jsonify
import traceback

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
        traceback.print_exc()

    try:
        if r:
            r.ping()
            status['redis'] = "healthy"
        else:
            status['redis'] = "disabled"
    except:
        status['redis'] = "unhealthy"
        result = 500
        traceback.print_exc()
    return jsonify(status), result