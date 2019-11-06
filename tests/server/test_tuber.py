from util import *
import json

def test_csrf(client):
    """Ensure that the CSRF cookie is being set and checked"""
    rv = client.get('/api/check_initial_setup')
    token = csrf(rv)
    assert(token)
    rv = client.post('/api/check_initial_setup', data="{}", content_type="application/json")
    assert("You must pass a csrf token" in str(rv.data))
    rv = client.post('/api/check_initial_setup', data=json.dumps({"csrf_token": token}), content_type="application/json")
    assert(not "csrf" in str(rv.data))

def test_initial_setup(client):
    """Ensure that initial setup is available until a user is created"""
    rv = client.get("/api/check_initial_setup")
    data = json.loads(rv.data)
    assert(data['initial_setup'])
    token = csrf(rv)
    rv = client.post('/api/initial_setup', data=json.dumps({"csrf_token": token, "username": "admin", "email": "admin@magfest.org", "password": "admin"}), content_type="application/json")
    data = json.loads(rv.data)
    assert(data['success'])
    rv = client.get("/api/check_initial_setup", query_string={"csrf_token": token})
    data = json.loads(rv.data)
    assert(not data['initial_setup'])

def test_login(client):
    """Ensure that invalid username/password is rejected and valid ones accepted"""
    rv = client.get('/api/check_login')
    token = csrf(rv)
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/logout', data=json.dumps({"csrf_token": token}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": token, "username": "admin", "password": "WRONG"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": token, "username": "bad", "password": "WRONG"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": token, "username": "bad", "password": "admin"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    rv = client.post('/api/login', data=json.dumps({"csrf_token": token, "username": "admin", "password": "admin"}), content_type="application/json")
    assert(json.loads(rv.data)['success'])
    session = json.loads(rv.data)['session']
    assert(session)

    rv = client.get('/api/check_login', query_string={"csrf_token": token})
    assert(json.loads(rv.data)['success'])

    rv = client.post('/api/logout', data=json.dumps({"csrf_token": token}), content_type="application/json")
    assert(json.loads(rv.data)['success'])

    rv = client.get('/api/check_login', query_string={"csrf_token": token})
    assert(not json.loads(rv.data)['success'])

