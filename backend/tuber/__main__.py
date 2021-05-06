import tuber

def main():
    tuber.migrate()
    tuber.app.run(host='0.0.0.0', port=8080)
