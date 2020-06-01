from unittest.mock import patch
import json

@patch('tuber.api.users.requests.post')
def test_staffer_auth(mock_post, client):
    """Make sure the staffer login system is able to authenticate against uber"""
    mock_post.return_value.json = lambda: {"result": [{"id": "123", "email": "test@test.com", "staffing": True}]}
    rv = client.post('/api/uber_login', json={"token": "123"})
    assert(rv.status_code != 200)

    user = client.post("/api/users", json={
        "email": "test@magfest.com",
        "password": "123",
        "username": "testuser"
    }).json
    assert(user)

    rv = client.post('/api/uber_login', json={"token": "123"})
    assert(rv.status_code == 200)

    rv = client.post('/api/uber_login', json={"token": "abc"})
    assert(rv.status_code != 200)
