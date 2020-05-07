import tempfile
import sqlite3
import pytest
import os

fd, filename = tempfile.mkstemp()
os.environ['DATABASE_URL'] = "sqlite:///" + filename
import tuber
tuber.migrate()

@pytest.fixture
def client():
    tuber.app.config['TESTING'] = True
    with tuber.app.test_client() as client:
        yield client

def csrf(rv):
    for cookie in rv.headers.getlist('Set-Cookie'):
        if cookie.startswith('csrf_token='):
            print(cookie)
            token = cookie.split("; ")[0].split("=")[1]
            print(token)
            return token

db = sqlite3.connect(filename)

def clear_table(table):
    c = db.cursor()
    c.execute("DELETE FROM {}".format(table))
    db.commit()