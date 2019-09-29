from tuber import app, config
import tuber
import sys

def main():
    tuber.init_db()
    app.run(host='0.0.0.0', port=8080)
