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
    results = [
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": {
                "unknown_ids": [],
                "unknown_emails": [],
                "unknown_names": [],
                "unknown_names_and_emails": [],
                "attendees": [
                {
                    "_model": "Attendee",
                    "id": "234",
                    "first_name": "Test",
                    "last_name": "Johnson",
                    "legal_name": "",
                    "birthdate": "1999-09-09",
                    "email": "test@johnson.com",
                    "zip_code": "11111",
                    "address1": "",
                    "address2": "",
                    "city": "",
                    "region": "",
                    "country": "",
                    "international": False,
                    "ec_name": "Rest Johnson",
                    "ec_phone": "1111111111",
                    "cellphone": "2222222222",
                    "badge_printed_name": "Test",
                    "badge_num": 28,
                    "found_how": "",
                    "comments": "",
                    "admin_notes": "",
                    "all_years": "",
                    "badge_status": 215389669,
                    "badge_status_label": "Complete",
                    "shirt": 5,
                    "assigned_depts": {
                    "165d54e4-f013-4a1c-ba43-04b67842f538": "Staff Suite",
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "78fec181-7e4f-4615-8b67-057718c89af0": "Staff Tea Room",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS",
                    "23be7a68-5d9e-4d59-80e1-f641a6d0b6d4": "Logistics"
                    },
                    "checklist_admin_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "dept_head_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "poc_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "requested_depts": {}
                }
                ]
            }
        },
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": [
                "234",
            ]
        }
    ]
    results.reverse()
    mock_post.return_value.json = results.pop
    rv = client.post('/api/uber/west2024/login', json={"token": "234"})
    assert(rv.status_code == 200)

    badge = Badge(email="test@magfest.com", uber_id="123")
    db.add(badge)
    db.commit()

    results = [
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": {
                "unknown_ids": [],
                "unknown_emails": [],
                "unknown_names": [],
                "unknown_names_and_emails": [],
                "attendees": [
                {
                    "_model": "Attendee",
                    "id": "123",
                    "first_name": "Test",
                    "last_name": "Johnson",
                    "legal_name": "",
                    "birthdate": "1999-09-09",
                    "email": "test@johnson.com",
                    "zip_code": "11111",
                    "address1": "",
                    "address2": "",
                    "city": "",
                    "region": "",
                    "country": "",
                    "international": False,
                    "ec_name": "Rest Johnson",
                    "ec_phone": "1111111111",
                    "cellphone": "2222222222",
                    "badge_printed_name": "Test",
                    "badge_num": 28,
                    "found_how": "",
                    "comments": "",
                    "admin_notes": "",
                    "all_years": "",
                    "badge_status": 215389669,
                    "badge_status_label": "Complete",
                    "shirt": 5,
                    "assigned_depts": {
                    "165d54e4-f013-4a1c-ba43-04b67842f538": "Staff Suite",
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "78fec181-7e4f-4615-8b67-057718c89af0": "Staff Tea Room",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS",
                    "23be7a68-5d9e-4d59-80e1-f641a6d0b6d4": "Logistics"
                    },
                    "checklist_admin_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "dept_head_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "poc_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "requested_depts": {}
                }
                ]
            }
        },
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": [
                "123",
            ]
        }
    ]
    results.reverse()
    mock_post.return_value.json = results.pop
    rv = client.post('/api/uber/west2024/login', json={"token": "123"})
    assert(rv.status_code == 200)

    results = [
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": {
                "unknown_ids": [],
                "unknown_emails": [],
                "unknown_names": [],
                "unknown_names_and_emails": [],
                "attendees": [
                {
                    "_model": "Attendee",
                    "id": "234",
                    "first_name": "Test",
                    "last_name": "Johnson",
                    "legal_name": "",
                    "birthdate": "1999-09-09",
                    "email": "test@johnson.com",
                    "zip_code": "11111",
                    "address1": "",
                    "address2": "",
                    "city": "",
                    "region": "",
                    "country": "",
                    "international": False,
                    "ec_name": "Rest Johnson",
                    "ec_phone": "1111111111",
                    "cellphone": "2222222222",
                    "badge_printed_name": "Test",
                    "badge_num": 28,
                    "found_how": "",
                    "comments": "",
                    "admin_notes": "",
                    "all_years": "",
                    "badge_status": 215389669,
                    "badge_status_label": "Complete",
                    "shirt": 5,
                    "assigned_depts": {
                    "165d54e4-f013-4a1c-ba43-04b67842f538": "Staff Suite",
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "78fec181-7e4f-4615-8b67-057718c89af0": "Staff Tea Room",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS",
                    "23be7a68-5d9e-4d59-80e1-f641a6d0b6d4": "Logistics"
                    },
                    "checklist_admin_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "dept_head_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "poc_depts": {
                    "22df636d-dd03-4b9b-86a8-f2213f116a78": "Reinforcements",
                    "3324860f-159a-43fb-b2ab-d4eea329a592": "STOPS"
                    },
                    "requested_depts": {}
                }
                ]
            }
        },
        {
            "jsonrpc": "2.0",
            "id": None,
            "result": [
                "234",
            ]
        }
    ]
    results.reverse()
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
