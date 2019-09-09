from tuber import app as application

if __name__ == "__main__":
    tuber.init_db()
    application.run()