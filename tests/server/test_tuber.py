from flask_sqlalchemy import SQLAlchemy
import tempfile
import pytest
import tuber
import json
import os

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

def test_csrf(client):
    """Ensure that the CSRF cookie is being set and checked"""
    rv = client.get('/api/check_initial_setup')
    assert(csrf(rv))
    rv = client.post('/api/check_initial_setup', data="{}", content_type="application/json")
    assert("You must pass a csrf token" in str(rv.data))
    rv = client.post('/api/check_initial_setup', data=json.dumps({"csrf_token": csrf(rv)}), content_type="application/json")
    assert(not "csrf" in str(rv.data))

def test_initial_setup(client):
    """Ensure that initial setup is available until a user is created"""
    rv = client.get("/api/check_initial_setup")
    data = json.loads(rv.data)
    assert(data['initial_setup'])
    for cookie in rv.headers.getlist('Set-Cookie'):
        if cookie.startswith("csrf_token="):
            value = cookie.split("; ")[0].split("=")[1]
    rv = client.post('/api/initial_setup', data=json.dumps({"csrf_token": value, "username": "admin", "email": "admin@magfest.org", "password": "admin"}), content_type="application/json")
    data = json.loads(rv.data)
    assert(data['success'])
    rv = client.get("/api/check_initial_setup")
    data = json.loads(rv.data)
    assert(not data['initial_setup'])

def test_login(client):
    """Ensure that invalid username/password is rejected and valid ones accepted"""
    rv = client.get('/api/check_login')
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/logout', data=json.dumps({"csrf_token": csrf(rv)}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": csrf(rv), "username": "admin", "password": "WRONG"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": csrf(rv), "username": "bad", "password": "WRONG"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": csrf(rv), "username": "bad", "password": "admin"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": csrf(rv), "username": "admin", "password": "admin"}), content_type="application/json")
    assert(json.loads(rv.data)['success'])
    session = json.loads(rv.data)['session']
    assert(session)

    rv = client.get('/api/check_login')
    assert(json.loads(rv.data)['success'])

    rv = client.post('/api/logout', data=json.dumps({"csrf_token": csrf(rv)}), content_type="application/json")
    assert(json.loads(rv.data)['success'])

    rv = client.get('/api/check_login')
    assert(not json.loads(rv.data)['success'])

