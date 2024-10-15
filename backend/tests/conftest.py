from werkzeug.test import Client
import importlib
import fakeredis
import tempfile
import pytest
import time
import sys
import os

def csrf(client):
    return client.get_cookie("csrf_token").value or ""

@pytest.fixture(params=[False, True])
def tuber(postgresql, redis=False):
    os.environ['FLASK_DEBUG'] = "true"
    os.environ['REDIS_URL'] = ""
    os.environ['DATABASE_URL'] = f"postgresql+psycopg://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    os.environ['CIRCUITBREAKER_TIMEOUT'] = "5"
    os.environ['ENABLE_CIRCUITBREAKER'] = "true"
    mod = importlib.import_module('tuber')
    tuber.backgroundjobs = importlib.import_module('tuber.backgroundjobs')
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"postgresql+psycopg://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    }
    mod.app.config.update(settings_override)
    if redis:
        redis = fakeredis.FakeStrictRedis()
        mod.db.r = redis
    yield mod
    for key in list(sys.modules.keys()):
        if key.startswith("tuber"):
            del sys.modules[key]

@pytest.fixture
def client_fresh(tuber):
    """Creates a client with a fresh database and no active sessions. Initial setup will not yet be completed.
    """
    tuber.database.create_tables()
    if os.environ['ENABLE_CIRCUITBREAKER'].lower() == "true":
        yield Client(tuber.backgroundjobs.AsyncMiddleware(tuber.app))
    else:
        with tuber.app.test_client() as client:
            yield client
    tuber.database.drop_tables()
    del sys.modules['tuber']

def wait_for(rv, _get):
    if rv.status_code == 202:
        print("Waiting for 202 to resolve")
        assert "Location" in rv.headers
        url = rv.headers['Location']
        start_time = time.time()
        while time.time() - start_time < 15:
            rv = _get(url)
            time.sleep(0.2)
            if rv.status_code == 202:
                assert "complete" in rv.json
                assert not rv.json['complete']
            if rv.status_code == 200:
                assert rv.json
                return rv
        raise TimeoutError(f"Timed out waiting for {url} -- Try again without circuitbreaker for exception.")
    return rv

@pytest.fixture
def client(tuber):
    """Creates a test client with initial setup complete and the admin user logged in already.
    Also patches the get/post/patch/delete functions to handle CSRF tokens for you.
    """
    tuber.database.create_tables()
    if os.environ['ENABLE_CIRCUITBREAKER'].lower() == "true":
        client = Client(tuber.backgroundjobs.AsyncMiddleware(tuber.app))
    else:
        client = tuber.app.test_client()
    #with tuber.app.test_client() as client:
    #client = Client(tuber.backgroundjobs.AsyncMiddleware(tuber.app))
    client.post('/api/initial_setup', json={"username": "admin", "email": "admin@magfest.org", "password": "admin"})
    client.post("/api/login", json={"username": "admin", "password": "admin"}, headers={"CSRF-Token": csrf(client)})
    client.post("/api/event", json={"name": "Tuber Event", "description": "It's a potato"}, headers={"CSRF-Token": csrf(client)})
    _get = client.get
    def get(*args, handle_async=True, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['CSRF-Token'] = csrf(client)
        rv = _get(*args, **kwargs)
        if handle_async:
            return wait_for(rv, _get)
        return rv
    _post = client.post
    def post(*args, handle_async=True, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['CSRF-Token'] = csrf(client)
        rv = _post(*args, **kwargs)
        if handle_async:
            return wait_for(rv, _get)
        return rv
    _patch = client.patch
    def patch(*args, handle_async=True, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['CSRF-Token'] = csrf(client)
        rv = _patch(*args, **kwargs)
        if handle_async:
            return wait_for(rv, _get)
        return rv
    _delete = client.delete
    def delete(*args, handle_async=True, **kwargs):
        if not 'headers' in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['CSRF-Token'] = csrf(client)
        rv = _delete(*args, **kwargs)
        if handle_async:
            return wait_for(rv, _get)
        return rv
    client.get = get
    client.post = post
    client.patch = patch
    client.delete = delete
    yield client

@pytest.fixture
def prod_client(postgresql):
    os.environ['REDIS_URL'] = ""
    os.environ['DATABASE_URL'] = f"postgresql+psycopg://{postgresql.info.user}:@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    os.environ['CIRCUITBREAKER_TIMEOUT'] = "5"
    os.environ['FLASK_DEBUG'] = "false"
    tuber = importlib.import_module('tuber')
    tuber.backgroundjobs = importlib.import_module('tuber.backgroundjobs')
    tuber.database.create_tables()
    if os.environ['ENABLE_CIRCUITBREAKER'].lower() == "true":
        yield Client(tuber.backgroundjobs.AsyncMiddleware(tuber.app))
    else:
        with tuber.app.test_client() as client:
            yield client
    tuber.database.drop_tables()
    for key in list(sys.modules.keys()):
        if key.startswith("tuber"):
            del sys.modules[key]