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
    """Alice (Fri+Sat) and Bob (Sat only) share a room with an Uber inventory."""
    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three"])
    event = db.query(models.Event).filter(models.Event.id == 1).one()
    event.uber_url = "https://uber.test/jsonrpc"
    event.uber_apikey = "123456"
    # The location's own inventory is a leftover the export must ignore.
    location = models.HotelLocation(event=1, name="Big Hotel", address="", uber_inventory_id="inv-location")
    db.add(location)
    db.flush()
    room = models.HotelRoom(event=1, name="Room 1", notes="Near elevator", hotel_block=s["block"].id,
                            hotel_location=location.id, completed=True, uber_inventory_id=uber_inventory_id)
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
        assert rv.json == {"exported": 1, "unchanged": 0, "cancelled": 0, "incomplete": 0, "skipped": [], "inactive": [], "failed": []}
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
            "occupant_message": "",
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


def test_room_messages_go_to_uber_and_admin_notes_do_not(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    room = _room(db, models, room_id)
    room.admin_notes = "Do not share"
    db.commit()
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        client.post("/api/event/1/uber/export_rooms")
        # A room with no message keeps its fingerprint, so it is not re-sent.
        assert client.post("/api/event/1/uber/export_rooms").json["unchanged"] == 1

        _room(db, models, room_id).messages = "Keys are at the staff suite"
        db.commit()
        client.post("/api/event/1/uber/export_rooms")
        assert uber.calls[-1]["occupant_message"] == "Keys are at the staff suite"

        _room(db, models, room_id).messages = None
        db.commit()
        client.post("/api/event/1/uber/export_rooms")
        assert len(uber.calls) == 3 and uber.calls[-1]["occupant_message"] == ""
    assert all("Do not share" not in str(call) for call in uber.calls)


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


def test_export_skips_room_without_inventory_and_reports_failures(client):
    import tuber.models as models
    from tuber.database import db

    room_id, location_id = _rooms(db, models, uber_inventory_id=None)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["exported"] == 0
        # Its location has one, but only the room's own counts.
        assert rv.json["skipped"] == ["Room 1: it has no Uber inventory assigned"]
        assert uber.calls == []

        _room(db, models, room_id).uber_inventory_id = "inv-1"
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


class _UberLists:
    """Stands in for Uber's hotel.inventory and hotel.partitions."""

    def __init__(self):
        self.inventory = [
            {"id": "inv-king", "name": "King", "hotel_name": "Big Hotel", "active": True},
            {"id": "inv-double", "name": "Double", "hotel_name": "Big Hotel", "active": False},
        ]
        self.partitions = [
            {"id": "part-staff", "name": "Staff", "active": True,
             "blocks": [{"inventory_id": "inv-king", "quantity": 5}]},
        ]
        self.error = None

    def __call__(self, url, headers=None, json=None, timeout=None):
        assert headers == {"X-Auth-Token": "123456"}
        lists, error = self, self.error

        class Response:
            status_code = 500 if error else 200

            def json(self):
                if error:
                    return {"error": {"code": -32601, "message": error}}
                return {"result": {"hotel.inventory": lists.inventory,
                                   "hotel.partitions": lists.partitions}[json["method"]]}
        return Response()


def test_import_inventory_and_partitions(client):
    import tuber.models as models
    from tuber.database import db

    _rooms(db, models)
    assert client.get("/api/event/1/uber/inventory_options").json == {
        "inventory": [], "partitions": [], "imported": None}

    uber = _UberLists()
    with patch('tuber.api.uber.requests.post', uber):
        rv = client.post("/api/event/1/uber/import_inventory")
        assert rv.status_code == 200
        options = client.get("/api/event/1/uber/inventory_options").json
        assert rv.json == options
        assert options["inventory"] == [
            {"uber_id": "inv-double", "name": "Double", "hotel_name": "Big Hotel", "active": False},
            {"uber_id": "inv-king", "name": "King", "hotel_name": "Big Hotel", "active": True},
        ]
        assert options["partitions"] == [
            {"uber_id": "part-staff", "name": "Staff", "active": True, "inventory_ids": ["inv-king"]}]
        assert options["imported"]

        # A re-import replaces the lists rather than adding to them.
        uber.inventory = uber.inventory[:1]
        uber.partitions = []
        rv = client.post("/api/event/1/uber/import_inventory")
        assert [x["uber_id"] for x in rv.json["inventory"]] == ["inv-king"]
        assert rv.json["partitions"] == []

        # A failed call leaves what was imported before in place.
        uber.error = "Method not found"
        rv = client.post("/api/event/1/uber/import_inventory")
        assert rv.status_code == 502
        assert "Method not found" in rv.get_data(as_text=True)
        options = client.get("/api/event/1/uber/inventory_options").json
        assert [x["uber_id"] for x in options["inventory"]] == ["inv-king"]


def test_room_inventory_and_partition_are_exported(client):
    import tuber.models as models
    from tuber.database import db

    room_id, location_id = _rooms(db, models)
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        client.post("/api/event/1/uber/export_rooms")
        # No partition of its own, so none is sent and Uber's is left alone.
        assert uber.calls[0]["inventory_id"] == "inv-1"
        assert "partition_id" not in uber.calls[0]

        # Assigned through the ordinary room API, as the page does.
        rv = client.patch(f"/api/event/1/hotel_room/{room_id}", json={
            "id": room_id, "uber_inventory_id": "inv-king", "uber_partition_id": "part-staff"})
        assert rv.status_code == 200
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["unchanged"]) == (1, 0)
        assert uber.calls[1]["inventory_id"] == "inv-king"
        assert uber.calls[1]["partition_id"] == "part-staff"

        # Clearing it stops the export; the location's is not a fallback.
        rv = client.patch(f"/api/event/1/hotel_room/{room_id}", json={
            "id": room_id, "uber_inventory_id": None})
        assert rv.status_code == 200
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["skipped"] == ["Room 1: it has no Uber inventory assigned"]
        assert len(uber.calls) == 2


def test_room_search_uber_filters(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models, uber_inventory_id=None)
    other = models.HotelRoom(event=1, name="Room 2", uber_inventory_id="inv-king",
                             uber_partition_id="part-staff")
    db.add(other)
    db.commit()

    def names(**params):
        rv = client.get("/api/event/1/hotel/room_search", query_string=dict(params, sort="name"))
        assert rv.status_code == 200
        return [x["name"] for x in rv.json["hotel_rooms"]]

    assert names(uber_inventory="missing") == ["Room 1"]
    assert names(uber_inventory="inv-king") == ["Room 2"]
    assert names(uber_partition="missing") == ["Room 1"]
    assert names(uber_partition="part-staff") == ["Room 2"]
    room = client.get("/api/event/1/hotel/room_search", query_string={"uber_inventory": "inv-king"}).json["hotel_rooms"][0]
    assert (room["uber_inventory_id"], room["uber_partition_id"]) == ("inv-king", "part-staff")


def test_only_completed_rooms_are_exported(client):
    import tuber.models as models
    from tuber.database import db

    room_id, _ = _rooms(db, models)
    _room(db, models, room_id).completed = False
    db.commit()
    uber = _Uber()
    with patch('tuber.api.uber.requests.post', uber):
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["incomplete"]) == (0, 1)
        assert uber.calls == []
        assert _room(db, models, room_id).uber_id is None

        _room(db, models, room_id).completed = True
        db.commit()
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["incomplete"]) == (1, 0)

        # Reopened and changed, even emptied: Uber keeps what it has until
        # the room is completed again.
        room = _room(db, models, room_id)
        room.completed = False
        room.notes = "Top floor"
        db.query(models.RoomNightAssignment).filter(
            models.RoomNightAssignment.hotel_room == room_id).delete()
        db.commit()
        rv = client.post("/api/event/1/uber/export_rooms")
        assert (rv.json["exported"], rv.json["cancelled"], rv.json["incomplete"]) == (0, 0, 1)
        assert len(uber.calls) == 1

        # Completed while empty: now the cancellation goes through.
        _room(db, models, room_id).completed = True
        db.commit()
        rv = client.post("/api/event/1/uber/export_rooms")
        assert rv.json["cancelled"] == 1
