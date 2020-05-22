from util import *
import json

def test_schedule_change(client):
    """Make sure that creating an scheduleevent on a schedule creates a shift on the associated job"""
    rv = client.post("/api/shifts")
    print(rv.data)
    assert(rv.json['id'] == 1)