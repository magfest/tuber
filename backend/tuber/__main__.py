from werkzeug.serving import run_simple
import tuber
import sys
from .backgroundjobs import AsyncMiddleware

def main():
    if "migrate" in sys.argv:
        tuber.database.migrate()
        sys.exit(0)


if __name__ == "__main__":
    main()
