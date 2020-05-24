from unittest.mock import patch
from util import *
import json

@patch('tuber.api.hotels.requests.post')
def test_staffer_auth(mock_post, client):
    """Make sure the staffer login system is able to authenticate against uber"""
    mock_post.return_value.json = lambda: {"result": [{"id": "123", "email": "test@test.com", "staffing": True}]}
    rv = client.post('/api/uber_login', json={"token": "123"})
    print(rv.data)
    assert(rv.is_json)
    assert(not rv.json['success'])

    rv = client.post('/api/uber_login', json={"token": "123"})
    assert(not rv.json['success'])

    rv = client.post('/api/uber_login', json={"token": "abc"})
    assert(not rv.json['success'])
