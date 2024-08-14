from unittest.mock import patch
import json
import time

from sqlalchemy.orm.exc import ObjectDeletedError
import pytest


def test_clear_matches(client):
    """Tests that the clear_matches endpoint clears existing Hotel Room matches"""
    from tuber.database import db
    from tuber.models import (Badge, HotelRoom, HotelRoomRequest,
                              RoomNightAssignment)

    _ = client.post(
        "/api/importer/mock",
        json={
            "event": 1,
            "attendees": 100,
            "departments": 10,
            "staffers": 100,
        },
    )

    hotel_room = HotelRoom(event=1, hotel_block=1, hotel_location=1)
    for i in range(1, 5):
        b = db.query(Badge).filter(Badge.id == i).one()
        rna = RoomNightAssignment(
            event=1, badge=b.id, room_night=1, hotel_room=hotel_room.id
        )
        hotel_room.room_night_assignments.append(rna)
        hotel_room.roommates.append(b)
        db.add(rna)

        hrr = HotelRoomRequest(event=1, badge=b.id)
        db.add(hrr)

    db.add(hotel_room)
    db.flush()
    db.commit()

    rv = client.post("/api/event/1/hotel/1/clear_matches", json={})
    assert rv.status_code == 200

    with pytest.raises(ObjectDeletedError):
        _ = db.query(HotelRoom).filter(HotelRoom.id == hotel_room.id).one_or_none()

@patch('tuber.api.uber.requests.post')
def test_staffer_auth(mock_post, client):
    """Make sure the staffer login system is able to authenticate against uber"""
    from tuber.database import db
    from tuber.models import Event, Badge
    event = Event(name="MAGWest 2024", description="West Event", uber_url="https://west2024.test.com", uber_apikey="123456", uber_slug="west2024")
    db.add(event)
    db.commit()
    results = [{"result": []}, {"result": ["234"]},{"result": [{"id": "234", "email": "test1@test.com", "assigned_depts_labels": [], "badge_status_label": "", "staffing": True, "badge_num": "", "badge_printed_name": "", "full_name": "", "first_name": "", "last_name": "", "legal_name": "", "ec_name": "", "ec_phone": "", "cellphone": ""}]}]
    mock_post.return_value.json = results.pop
    rv = client.post('/api/uber/west2024/login', json={"token": "234"})
    assert(rv.status_code == 200)

    badge = Badge(email="test@magfest.com", uber_id="123")
    db.add(badge)
    db.commit()

    results = [{"result": []}, {"result": ["123"]},{"result": [{"id": "123", "email": "test2@test.com", "assigned_depts_labels": [], "badge_status_label": "", "staffing": True, "badge_num": "", "badge_printed_name": "", "full_name": "", "first_name": "", "last_name": "", "legal_name": "", "ec_name": "", "ec_phone": "", "cellphone": ""}]}]
    mock_post.return_value.json = results.pop
    rv = client.post('/api/uber/west2024/login', json={"token": "123"})
    assert(rv.status_code == 200)

    results = [{"result": []}, {"result": ["234"]},{"result": [{"id": "456", "email": "test3@test.com", "assigned_depts_labels": [], "badge_status_label": "", "staffing": True, "badge_num": "", "badge_printed_name": "", "full_name": "", "first_name": "", "last_name": "", "legal_name": "", "ec_name": "", "ec_phone": "", "cellphone": ""}]}]
    mock_post.return_value.json = results.pop
    rv = client.post('/api/uber/west2024/login', json={"token": "456"})
    assert(rv.status_code != 200)

def test_requests(client):
    rv = client.get("/api/event/1/hotel_room_request")
    assert not rv.json
    rv = client.post("/api/importer/mock", json={
        "event": 1,
        "attendees": 100,
        "departments": 10,
        "staffers": 100,
    })
    assert rv.status_code == 200
    rv = client.get("/api/event")
    assert rv.status_code == 200
    assert rv.json
    event = rv.json[0]
    rv = client.get(f"/api/event/{event['id']}/hotel_room_request")
    assert rv.status_code == 200
    assert rv.json
    for req in rv.json:
        assert 'id' in req
        assert 'badge' in req
        assert 'first_name' in req

#def test_approve(client):
#    pass
#def test_room_nights(client):
#    pass
#def test_hotel_room(client):
#    pass
#def test_room_night(client):
#    pass
#def test_room_block(client):
#    pass
#def test_request_complete(client):
#    pass
#def test_room_assignments(client):
#    pass
