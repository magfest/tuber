import importlib
import fakeredis
import tempfile
import sqlite3
import pytest
import json
import sys
import os

def csrf(client):
    for cookie in client.cookie_jar:
        if cookie.name == "csrf_token":
            return cookie.value
    return ""

#@pytest.fixture(params=[True, False])
@pytest.fixture
def tuber(redis=False):
    os.environ['FORCE_HTTPS'] = "false"
    os.environ['FLASK_ENV'] = "development"
    os.environ['REDIS_URL'] = ""
    os.environ['DATABASE_URL'] = "sqlite:///test.db"
    os.environ['CIRCUITBREAKER_TIMEOUT'] = "5"
    os.environ['ENABLE_CIRCUITBREAKER'] = "true"
    mod = importlib.import_module('tuber')
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': "sqlite:///test.db"
    }
    mod.app.config.update(settings_override)
    if redis:
        redis = fakeredis.FakeStrictRedis()
        mod.r = redis
    yield mod
    for key in list(sys.modules.keys()):
        if key.startswith("tuber"):
            del sys.modules[key]

@pytest.fixture
def client_fresh(tuber):
    """Creates a client with a fresh database and no active sessions. Initial setup will not yet be completed.
    """
    tuber.create_tables()
    with tuber.app.test_client() as client:
        yield client
    tuber.drop_tables()
    del sys.modules['tuber']

@pytest.fixture
def client(tuber):
    """Creates a test client with initial setup complete and the admin user logged in already.
    Also patches the get/post/patch/delete functions to handle CSRF tokens for you.
    """
    tuber.create_tables()
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
            if 'data' in kwargs:
                kwargs['data']['csrf_token'] = csrf(client)
            else:
                if not 'json' in kwargs:
                    kwargs['json'] = {}
                kwargs['json']['csrf_token'] = csrf(client)
            rv = _post(*args, **kwargs)
            return rv
        _patch = client.patch
        def patch(*args, **kwargs):
            if 'data' in kwargs:
                kwargs['data']['csrf_token'] = csrf(client)
            else:
                if not 'json' in kwargs:
                    kwargs['json'] = {}
                kwargs['json']['csrf_token'] = csrf(client)
            rv = _patch(*args, **kwargs)
            return rv
        _delete = client.delete
        def delete(*args, **kwargs):
            if 'data' in kwargs:
                kwargs['data']['csrf_token'] = csrf(client)
            else:
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
    tuber.drop_tables()

@pytest.fixture
def prod_client():
    os.environ['REDIS_URL'] = ""
    os.environ['DATABASE_URL'] = "sqlite:///test.db"
    os.environ['CIRCUITBREAKER_TIMEOUT'] = "5"
    os.environ['FORCE_HTTPS'] = "true"
    os.environ['FLASK_ENV'] = "production"
    tuber = importlib.import_module('tuber')
    tuber.create_tables()
    with tuber.app.test_client() as client:
        yield client
    tuber.drop_tables()
    for key in list(sys.modules.keys()):
        if key.startswith("tuber"):
            del sys.modules[key]