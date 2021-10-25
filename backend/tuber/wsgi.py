from werkzeug.serving import run_simple
import tuber
import sys
from .backgroundjobs import AsyncMiddleware
import pathlib

tuber.database.migrate()
app = AsyncMiddleware(tuber.app)

pathlib.Path("/tmp/app-initialized").touch()