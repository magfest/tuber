import datetime


def _seed(db, models):
    """A small but complete rooming world: two nights (one restricted), three
       people at different stages, one room."""
    window_night = models.HotelRoomNight(
        event=1, name="Setup", date=datetime.date(2025, 8, 6),
        restriction_mode="shift_window", restriction_type="Setup",
        shift_starttime=datetime.datetime(2025, 8, 6, 19, 0, 0),
        shift_endtime=datetime.datetime(2025, 8, 7, 13, 0, 0))
    open_night = models.HotelRoomNight(
        event=1, name="Friday", date=datetime.date(2025, 8, 7),
        restriction_mode="none")
    db.add(window_night)
    db.add(open_night)
    db.flush()

    block = models.HotelRoomBlock(event=1, name="Staff", description="")
    db.add(block)
    db.flush()

    department = models.Department(event=1, name="Arcade")
    db.add(department)
    db.flush()

    # Alice: complete request, approved via shift, assigned to a room.
    alice = models.Badge(event=1, public_name="Alice Aardvark",
                         first_name="Alice", last_name="Aardvark",
                         search_name="alice aardvark",
                         email="alice@example.com")
    # Bob: requested the restricted night, no shift -> missing.
    bob = models.Badge(event=1, public_name="Bob Badger",
                       first_name="Bob", last_name="Badger",
                       search_name="bob badger",
                       email="bob@example.com")
    # Carol: declined.
    carol = models.Badge(event=1, public_name="Carol Cat",
                         first_name="Carol", last_name="Cat",
                         search_name="carol cat",
                         email="carol@example.com")
    for badge in (alice, bob, carol):
        db.add(badge)
    db.flush()

    db.add(models.HotelRoomRequest(
        event=1, badge=alice.id, first_name="Alice", last_name="Aardvark",
        hotel_block=block.id))
    db.add(models.HotelRoomRequest(
        event=1, badge=bob.id, first_name="Bob", last_name="Badger",
        hotel_block=block.id, notes="ground floor please"))
    db.add(models.HotelRoomRequest(event=1, badge=carol.id, declined=True))

    for badge in (alice, bob):
        db.add(models.RoomNightRequest(
            event=1, badge=badge.id, room_night=window_night.id, requested=True))
        db.add(models.RoomNightRequest(
            event=1, badge=badge.id, room_night=open_night.id, requested=True))

    job = models.Job(event=1, name="Load-In", description="",
                     department=department.id)
    db.add(job)
    db.flush()
    shift = models.Shift(
        event=1, job=job.id, starttime=datetime.datetime(2025, 8, 6, 20, 0, 0),
        duration=3 * 3600, slots=6, filledslots=0, weighting=1.0)
    db.add(shift)
    db.flush()
    db.add(models.ShiftAssignment(event=1, badge=alice.id, shift=shift.id))

    room = models.HotelRoom(event=1, name="Room 101", hotel_block=block.id,
                            completed=True)
    db.add(room)
    db.flush()
    for night in (window_night, open_night):
        db.add(models.RoomNightAssignment(
            event=1, badge=alice.id, room_night=night.id, hotel_room=room.id))
    db.commit()
    return {"window": window_night, "open": open_night, "block": block,
            "alice": alice, "bob": bob, "carol": carol, "room": room}


def test_attendees_filters(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)

    def names(mode, **params):
        rv = client.get("/api/event/1/hotel/attendees",
                        query_string={"filter": mode, **params})
        assert rv.status_code == 200
        return {x["name"] for x in rv.json["results"]}, rv.json["count"]

    all_names, count = names("all")
    assert {"Alice Aardvark", "Bob Badger", "Carol Cat"} <= all_names

    complete, _ = names("complete")
    assert "Alice Aardvark" in complete and "Bob Badger" in complete
    assert "Carol Cat" not in complete

    declined, _ = names("declined")
    assert declined == {"Carol Cat"}

    missing, _ = names("missing_shifts")
    assert missing == {"Bob Badger"}

    unassigned, _ = names("unassigned_approved")
    # Bob has an approved (unrestricted) night and no assignment.
    assert "Bob Badger" in unassigned and "Alice Aardvark" not in unassigned

    # The old "roomless" state is folded into unassigned: a night granted
    # without a room counts even when it isn't approved. Alice gets a
    # room-less grant for the restricted night she isn't approved for...
    # actually Alice is approved for everything, so grant Carol's slot to
    # Alice on a brand-new unapproved manual night.
    import datetime as _dt
    manual_night = models.HotelRoomNight(
        event=1, name="Manual", date=_dt.date(2025, 8, 9),
        restriction_mode="manual")
    db.add(manual_night)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=s["alice"].id, room_night=manual_night.id,
        hotel_room=None))
    db.commit()
    unassigned, _ = names("unassigned_approved")
    assert "Alice Aardvark" in unassigned

    # The removed filter name is rejected.
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "roomless"})
    assert rv.status_code == 400

    # Search and pagination.
    searched, count = names("all", search="badger")
    assert searched == {"Bob Badger"} and count == 1
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "all", "limit": 1, "offset": 0})
    assert len(rv.json["results"]) == 1 and rv.json["count"] >= 3

    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "bogus"})
    assert rv.status_code == 400

    # Row shape used by the Requests page.
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "missing_shifts"})
    bob = rv.json["results"][0]
    assert bob["email"] == "bob@example.com"
    assert bob["hotel_block"] == s["block"].id
    assert bob["requested_nights"] == 2
    assert bob["approved_nights"] == 1
    assert bob["missing_nights"][0]["mode"] == "shift_window"


def test_attendees_export(client):
    import tuber.models as models
    from tuber.database import db

    _seed(db, models)
    rv = client.get("/api/event/1/hotel/attendees/export",
                    query_string={"filter": "missing_shifts"})
    assert rv.status_code == 200
    assert rv.headers["Content-Type"].startswith("text/csv")
    body = rv.data.decode()
    assert "bob@example.com" in body
    assert "alice@example.com" not in body


def test_room_grid(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    rv = client.get(f"/api/event/1/hotel/room/{s['room'].id}/details")
    assert rv.status_code == 200
    grid = rv.json
    assert grid["name"] == "Room 101"
    assert grid["completed"] is True
    assert grid["hotel_block"]["name"] == "Staff"
    assert [x["name"] for x in grid["occupants"]] == ["Alice Aardvark"]
    alice_nights = grid["occupants"][0]["nights"]
    window = alice_nights[str(s["window"].id)]
    assert window["requested"] is True
    assert window["approved"] is True
    assert window["assigned"] is True
    assert window["assigned_room"] == s["room"].id

    rv = client.get("/api/event/1/hotel/room/99999/details")
    assert rv.status_code == 404


def test_room_grid_roomless_never_masks_assignment(client):
    """A room-less grant (hotel_room=NULL) for the same night must not hide a
       real room assignment in the grid, and is reported separately."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    alice, room = s["alice"], s["room"]
    window, friday = s["window"], s["open"]

    # Alice ends up with BOTH a room-less grant and a real assignment for the
    # window night (the attendee view granted it, then she was placed).
    db.add(models.RoomNightAssignment(
        event=1, badge=alice.id, room_night=window.id, hotel_room=None))
    # And a room-less-only grant for a third night nobody placed yet.
    saturday = models.HotelRoomNight(
        event=1, name="Saturday", date=datetime.date(2025, 8, 8),
        restriction_mode="none")
    db.add(saturday)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=alice.id, room_night=saturday.id, hotel_room=None))
    db.commit()

    rv = client.get(f"/api/event/1/hotel/room/{room.id}/details")
    assert rv.status_code == 200
    nights = rv.json["occupants"][0]["nights"]

    # The real assignment wins regardless of row order.
    window_status = nights[str(window.id)]
    assert window_status["assigned"] is True
    assert window_status["assigned_room"] == room.id
    assert window_status["roomless"] is True

    # A purely room-less night reads as unassigned but flagged.
    saturday_status = nights[str(saturday.id)]
    assert saturday_status["assigned"] is False
    assert saturday_status["assigned_room"] is None
    assert saturday_status["roomless"] is True

    # An untouched assigned night is unaffected.
    friday_status = nights[str(friday.id)]
    assert friday_status["assigned"] is True
    assert friday_status["roomless"] is False


def test_attendee_detail_rooms(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    rv = client.get(f"/api/event/1/hotel/attendee/{s['alice'].id}")
    assert rv.status_code == 200
    detail = rv.json
    assert len(detail["rooms"]) == 1
    room = detail["rooms"][0]
    assert room["name"] == "Room 101"
    assert room["block_name"] == "Staff"
    assert len(room["nights"]) == 2
    assert room["roommates"] == []
    nights = {x["name"]: x for x in detail["nights"]}
    assert nights["Setup"]["assigned_room"] == s["room"].id
    assert detail["room_request"]["hotel_block"] == s["block"].id


def test_dashboard(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    rv = client.get("/api/event/1/hotel/dashboard")
    assert rv.status_code == 200
    data = rv.json

    assert data["requests"]["eligible"] == 3
    assert data["requests"]["completed"] == 2
    assert data["requests"]["declined"] == 1
    assert data["requests"]["pending"] == 0
    assert data["requests"]["percent_resolved"] == 100.0

    assert data["room_nights"]["requested"] == 4
    assert data["room_nights"]["assigned"] == 2
    assert data["room_nights"]["roomless_assignments"] == 0

    assert data["rooms"]["total"] == 1
    assert data["rooms"]["completed"] == 1
    assert data["rooms"]["by_block"][0]["name"] == "Staff"

    issues = {x["kind"]: x for x in data["issues"]}
    assert issues["missing_shifts"]["count"] == 1
    assert issues["missing_shifts"]["link"]["filter"] == "missing_shifts"
    # Bob has an approved night without an assignment.
    assert issues["unassigned_approved"]["count"] == 1
    # Roomless is folded into unassigned — no separate issue kind.
    assert "roomless_assignments" not in issues
    # Alice's completed room has no roommate errors (mutual single occupant).
    assert "rooms_with_errors" not in issues or issues["rooms_with_errors"]["count"] == 0
