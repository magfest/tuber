from werkzeug.serving import run_simple
import tuber
import sys
from .backgroundjobs import AsyncMiddleware

def main():
    tuber.database.migrate()
    if "migrate" in sys.argv:
        sys.exit(0)
    if tuber.config.enable_circuitbreaker:
        app = AsyncMiddleware(tuber.app)
    else:
        app = tuber.app
    run_simple('0.0.0.0', 8080, app, use_reloader=True, use_debugger=True, use_evalex=True, threaded=True)
