import tuber
import sys

def main():
    tuber.migrate()
    if "migrate" in sys.argv:
        sys.exit(0)
    tuber.app.run(host='0.0.0.0', port=8080)
