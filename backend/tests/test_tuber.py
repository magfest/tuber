from conftest import csrf
import json

def test_csrf(client_fresh):
    """Ensure that the CSRF cookie is being set and checked"""
    rv = client_fresh.get('/api/check_initial_setup')
    token = csrf(client_fresh)
    assert(token)
    rv = client_fresh.post('/api/initial_setup', data="{}", content_type="application/json")
    assert("You must pass a csrf token" in str(rv.data))
    rv = client_fresh.post('/api/initial_setup', json={
        "username": "admin", 
        "email": "admin@magfest.org", 
        "password": "admin"
    }, headers={"CSRF-Token": token})
    assert(not "csrf" in str(rv.data))

def test_initial_setup(client_fresh):
    """Ensure that initial setup is available until a user is created"""
    initial_setup = client_fresh.get("/api/check_initial_setup").json
    assert(initial_setup)

    token = csrf(client_fresh)
    rv = client_fresh.post('/api/initial_setup', json={
        "username": "admin", 
        "email": "admin@magfest.org", 
        "password": "admin"
    }, headers={"CSRF-Token": token})
    assert(rv.status_code == 200)

    initial_setup = client_fresh.get("/api/check_initial_setup", query_string={"csrf_token": token}).json
    assert(not initial_setup)

def test_login(client_fresh):
    """Ensure that invalid username/password is rejected and valid ones accepted"""
    test_initial_setup(client_fresh)
    token = csrf(client_fresh)
    rv = client_fresh.get('/api/check_login', headers={"CSRF-Token": token})
    assert(rv.status_code != 200)

    rv = client_fresh.post('/api/logout', headers={"CSRF-Token": token}, content_type="application/json", data=json.dumps({}))
    assert(rv.status_code == 200)

    rv = client_fresh.post('/api/login', data=json.dumps({"username": "admin", "password": "WRONG"}), content_type="application/json", headers={"CSRF-Token": token})
    assert(rv.status_code != 200)

    rv = client_fresh.post('/api/login', data=json.dumps({"username": "bad", "password": "WRONG"}), content_type="application/json", headers={"CSRF-Token": token})
    assert(rv.status_code != 200)

    rv = client_fresh.post('/api/login', data=json.dumps({"username": "bad", "password": "admin"}), content_type="application/json", headers={"CSRF-Token": token})
    assert(rv.status_code != 200)

    rv = client_fresh.post('/api/login', data=json.dumps({"username": "admin", "password": "admin"}), content_type="application/json", headers={"CSRF-Token": token})
    assert(rv.status_code == 200)
    assert(rv.data)

    rv = client_fresh.get('/api/check_login', headers={"CSRF-Token": token})
    assert(rv.status_code == 200)

    rv = client_fresh.post('/api/logout', headers={"CSRF-Token": token}, content_type="application/json", data=json.dumps({}))
    assert(rv.status_code == 200)

    rv = client_fresh.get('/api/check_login', headers={"CSRF-Token": token})
    assert(rv.status_code != 200)