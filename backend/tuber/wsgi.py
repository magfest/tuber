from werkzeug.serving import run_simple
import tuber
import sys
from .backgroundjobs import AsyncMiddleware
import logging
logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

if tuber.config.enable_circuitbreaker:
    print("Using circuitbreaker")
    app = AsyncMiddleware(tuber.app)
else:
    print("Not using circuitbreaker")
    app = tuber.app
