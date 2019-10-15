from unittest.mock import patch
from util import *
import json

@patch('tuber.api.hotels.requests.post')
def test_staffer_auth(mock_post, client):
    """Make sure the staffer login system is able to authenticate against uber"""
    mock_post.return_value.json = lambda: {"result": [{"id": "123", "email": "test@test.com", "staffing": True}]}
    rv = client.post('/api/hotels/staffer_auth', data=json.dumps({"token": "123"}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])

    rv = client.post('/api/hotels/staffer_auth', data=json.dumps({"token": "123", "csrf_token": csrf(rv)}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])

    rv = client.post('/api/hotels/staffer_auth', data=json.dumps({"token": "abc", "csrf_token": csrf(rv)}), content_type="application/json")
    assert(not json.loads(rv.data)['success'])
    clear_table("user")