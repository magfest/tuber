import tempfile
import sqlite3
import pytest
import json
import os

database = "sqlite:///"+os.path.join(tempfile.mkdtemp(), "database.db")
os.environ['DATABASE_URL'] = database
import tuber
tuber.migrate()
tuber.app.config['TESTING'] = True

def csrf(client):
    for cookie in client.cookie_jar:
        if cookie.name == "csrf_token":
            return cookie.value
    return ""

@pytest.fixture
def client_fresh():
    """Creates a client with a fresh database and no active sessions. Initial setup will not yet be completed.
    """
    tuber.db.create_all()
    with tuber.app.test_client() as client:
        yield client
    tuber.db.drop_all()

@pytest.fixture
def client():
    """Creates a test client with initial setup complete and the admin user logged in already.
    Also patches the get/post/patch/delete functions to handle CSRF tokens for you.
    """
    tuber.db.create_all()
    with tuber.app.test_client() as client:
        client.post('/api/initial_setup', json={"username": "admin", "email": "admin@magfest.org", "password": "admin"})
        client.post("/api/login", json={"csrf_token": csrf(client), "username": "admin", "password": "admin"})
        client.post("/api/events", json={"csrf_token": csrf(client), "name": "Tuber Event", "description": "It's a potato"})
        _get = client.get
        def get(*args, **kwargs):
            if not 'query_string' in kwargs:
                kwargs['query_string'] = {}
            kwargs['query_string']['csrf_token'] = csrf(client)
            rv = _get(*args, **kwargs)
            return rv
        _post = client.post
        def post(*args, **kwargs):
            if not 'json' in kwargs:
                kwargs['json'] = {}
            kwargs['json']['csrf_token'] = csrf(client)
            rv = _post(*args, **kwargs)
            return rv
        _patch = client.patch
        def patch(*args, **kwargs):
            if not 'json' in kwargs:
                kwargs['json'] = {}
            kwargs['json']['csrf_token'] = csrf(client)
            rv = _patch(*args, **kwargs)
            return rv
        _delete = client.delete
        def delete(*args, **kwargs):
            if not 'json' in kwargs:
                kwargs['json'] = {}
            kwargs['json']['csrf_token'] = csrf(client)
            rv = _delete(*args, **kwargs)
            return rv
        client.get = get
        client.post = post
        client.patch = patch
        client.delete = delete
        yield client
    tuber.db.drop_all()