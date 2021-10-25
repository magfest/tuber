from werkzeug.serving import run_simple
import tuber
import sys
from .backgroundjobs import AsyncMiddleware

tuber.database.migrate()
app = AsyncMiddleware(tuber.app)
