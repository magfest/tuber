from unittest.mock import patch

from tests.test_room_matching import _seed


class _Uber:
    """Stands in for Uber's hotel.update_assignment, recording each call."""

    def __init__(self):
        self.calls = []
        self.rooms = {}
        self.fail_for = None
        self.lose_reply = False

    def __call__(self, url, headers=None, json=None, timeout=None):
        assert json["method"] == "hotel.update_assignment"
        self.calls.append(json["params"])
        params = dict(json["params"])
        create_missing = params.pop("create_missing", False)
        status, body = 200, None
        if self.fail_for and params.get("attendee_id") == self.fail_for:
            status, body = 404, {"error": {"code": -32603, "message": "Could not locate occupants"}}
        elif params["id"] not in self.rooms and not create_missing:
            status, body = 404, {"error": {"code": -32603, "message": "Could not locate room assignment"}}
        else:
            room = self.rooms.setdefault(params["id"], {"status": "Assigned"})
            room.update(params)
            body = {"result": {"id": params["id"], "is_live": room["status"] != "Cancelled"}}
        if self.lose_reply:
            raise ConnectionError("connection reset")

        class Response:
            status_code = status

            def json(self):
                return body
        return Response()


def _rooms(db, models, uber_inventory_id="inv-1"):
    """Alice (Fri+Sat) and Bob (Sat only) share a room at a mapped location."""
    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three"])
    event = db.query(models.Event).filter(models.Event.id == 1).one()
    event.uber_url = "https://uber.test/jsonrpc"
    event.uber_apikey = "123456"
    location = models.HotelLocation(event=1, name="Big Hotel", address="", uber_inventory_id=uber_inventory_id)
    db.add(location)
    db.flush()
    room = models.HotelRoom(event=1, name="Room 1", notes="Near elevator", hotel_block=s["block"].id,
                            hotel_location=location.id)
    db.add(room)
    db.flush()
    friday, saturday = s["nights"]
    for name, nights in [("Alice One", [friday, saturday]), ("Bob Two", [saturday])]:
        s["badges"][name].uber_id = "uber-" + name.split()[0].lower()
        for night in nights:
            db.add(models.RoomNightAssignment(event=1, badge=s["badges"][name].id, room_night=night.id,
                                              hotel_room=room.id))
    db.commit()
    return room.id, location.id


def _room(db, models, room_id):
    db.expire_all()
    return db.query(models.HotelRoom).filter(models.HotelRoom.id == room_id).one()


def test_export_room_as_crash_space_with_occupants(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.status_code == 200
        assert rv.json == {"exported": 1, "unchanged": 0, "cancelled": 0, "skipped": [], "inactive": [], "failed": []}
        uber_id = _room(db, models, room_id).uber_id
        assert uber.calls == [{
            "id": uber_id,
            "create_missing": True,
            "attendee_id": "uber-alice",
            "inventory_id": "inv-1",
            "assignment_reason": "Staff Crash Space",
            "assigned_check_in_date": "2025-08-08",
            "assigned_check_out_date": "2025-08-10",
            "special_requests": "Near elevator",
            "payment_type": "masterbill",
            "occupants": [
                {"attendee_id": "uber-alice", "check_in_date": "2025-08-08", "check_out_date": "2025-08-10"},
                {"attendee_id": "uber-bob", "check_in_date": "2025-08-09", "check_out_date": "2025-08-10"},
            ],
        }]


def test_reexport_sends_only_changed_rooms(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        client.post("/api/event/1/uber/export_rooms")
        uber_id = _room(db, models, room_id).uber_id

        # Nothing changed, so Uber (and any edits made there) is left alone.
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["unchanged"]) == (0, 1)
        assert len(uber.calls) == 1

        _room(db, models, room_id).notes = "Top floor"
        db.commit()
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["unchanged"]) == (1, 0)
        assert uber.calls[1]["id"] == uber_id
        assert uber.calls[1]["special_requests"] == "Top floor"
        # Billing is only set on the first export.
        assert "payment_type" not in uber.calls[1]
        assert list(uber.rooms) == [uber_id]


def test_reexport_after_lost_reply_reuses_the_uber_room(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        # Uber makes the room, but Tuber never hears back.
        uber.lose_reply = True
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 0 and len(rv.json["failed"]) == 1
        uber_id = _room(db, models, room_id).uber_id
        assert list(uber.rooms) == [uber_id]

        uber.lose_reply = False
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 1
        assert list(uber.rooms) == [uber_id]
        assert uber.calls[1]["payment_type"] == "masterbill"


def test_export_reports_room_cancelled_in_uber(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        client.post("/api/event/1/uber/export_rooms")
        uber.rooms[_room(db, models, room_id).uber_id]["status"] = "Cancelled"
        _room(db, models, room_id).notes = "Top floor"
        db.commit()

        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 0
        assert rv.json["inactive"] == ["Room 1: updated, but it is cancelled in Uber"]


def test_export_cancels_emptied_room(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        client.post("/api/event/1/uber/export_rooms")
        uber_id = _room(db, models, room_id).uber_id
        db.query(models.RoomNightAssignment).delete()
        db.commit()

        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["cancelled"] == 1
        assert uber.calls[-1] == {"id": uber_id, "status": "Cancelled"}
        assert _room(db, models, room_id).uber_id is None

        # Nothing more to tell Uber about it.
        client.post("/api/event/1/uber/export_rooms")
        assert len(uber.calls) == 2


def test_export_skips_unmapped_location_and_reports_failures(client):
    import tuber.models as models
    from tuber.database import db

    room_id, location_id = _rooms(db, models, uber_inventory_id=None)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 0
        assert rv.json["skipped"] == ["Room 1: its location has no Uber inventory ID"]
        assert uber.calls == []

        db.query(models.HotelLocation).filter(models.HotelLocation.id == location_id).one().uber_inventory_id = "inv-1"
        db.commit()
        uber.fail_for = "uber-alice"
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["failed"] == ["Room 1: Could not locate occupants"]
        assert uber.rooms == {}

        # The failed room is sent again, in full, next time.
        uber.fail_for = None
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 1
        assert uber.calls[-1]["payment_type"] == "masterbill"
