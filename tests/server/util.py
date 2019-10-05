import tempfile
import sqlite3
import pytest
import tuber

fd, filename = tempfile.mkstemp()
tuber.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + filename
tuber.init_db()

@pytest.fixture
def client():
    tuber.app.config['TESTING'] = True
    with tuber.app.test_client() as client:
        yield client

def csrf(rv):
    for cookie in rv.headers.getlist('Set-Cookie'):
        if cookie.startswith('csrf_token='):
            return cookie.split("; ")[0].split("=")[1]
    
db = sqlite3.connect(filename)

def clear_table(table):
    c = db.cursor()
    c.execute("DELETE FROM {}".format(table))
    db.commit()