import tempfile
import sqlite3
import pytest
import tuber.config

fd, filename = tempfile.mkstemp()
tuber.config.database_url = "sqlite:///" + filename
import tuber

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