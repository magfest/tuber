import datetime


def _seed(db, models, names, roommate_pairs=(), anti_pairs=()):
    """A block, two unrestricted nights, and a staffer + request per name."""
    nights = []
    for offset, night_name in enumerate(["Friday", "Saturday"]):
        night = models.HotelRoomNight(
            event=1, name=night_name, date=datetime.date(2025, 8, 8 + offset),
            restriction_mode="none")
        db.add(night)
        nights.append(night)
    block = models.HotelRoomBlock(event=1, name="Staff", description="")
    db.add(block)
    db.flush()

    badges = {}
    requests = {}
    for name in names:
        badge = models.Badge(
            event=1, public_name=name, first_name=name.split()[0],
            last_name=name.split()[-1], search_name=name.lower(),
            email=name.replace(" ", ".").lower() + "@example.com")
        db.add(badge)
        db.flush()
        request = models.HotelRoomRequest(
            event=1, badge=badge.id, first_name=name.split()[0],
            last_name=name.split()[-1], hotel_block=block.id)
        db.add(request)
        db.flush()
        for night in nights:
            db.add(models.RoomNightRequest(
                event=1, badge=badge.id, room_night=night.id, requested=True))
        badges[name] = badge
        requests[name] = request

    for requester, requested in roommate_pairs:
        db.add(models.HotelRoommateRequest(
            requester=badges[requester].id, requested=badges[requested].id))
    for requester, requested in anti_pairs:
        db.add(models.HotelAntiRoommateRequest(
            requester=badges[requester].id, requested=badges[requested].id))
    db.commit()
    return {"nights": nights, "block": block, "badges": badges,
            "requests": requests}


def test_suggest_accept_reject_cycle(client):
    """Suggested rooms persist; accept keeps assignments, reject frees people."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three", "Dave Four"],
              roommate_pairs=[("Alice One", "Bob Two"), ("Bob Two", "Alice One"),
                              ("Carol Three", "Dave Four"), ("Dave Four", "Carol Three")])
    block = s["block"].id

    rv = client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    assert rv.status_code == 200
    created = rv.json["created"]
    assert len(created) == 1  # two mutual pairs combine into one 4-person room

    rooms = db.query(models.HotelRoom).filter(
        models.HotelRoom.hotel_block == block).all()
    assert all(x.suggested and not x.completed for x in rooms)
    assert db.query(models.RoomNightAssignment).count() == 8  # 4 people x 2 nights

    # Re-running creates nothing new — everyone is already assigned.
    rv = client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    assert rv.json["created"] == []

    # Accept: mark completed via generic CRUD; assignments survive.
    room_id = created[0]
    rv = client.patch(f"/api/event/1/hotel_room/{room_id}",
                      json={"id": room_id, "completed": True, "suggested": False})
    assert rv.status_code == 200
    db.expire_all()
    assert db.query(models.RoomNightAssignment).count() == 8

    # Reject a fresh suggestion: occupants return to the pool.
    extra = _seed  # noqa: F841 (documentation only)
    rv = client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    assert rv.json["created"] == []  # nobody unhoused yet
    # Un-house nobody; instead build a new person and suggest again.
    badge = models.Badge(event=1, public_name="Eve Five", first_name="Eve",
                         last_name="Five", search_name="eve five",
                         email="eve@example.com")
    db.add(badge)
    db.flush()
    request = models.HotelRoomRequest(event=1, badge=badge.id,
                                      first_name="Eve", last_name="Five",
                                      hotel_block=block)
    db.add(request)
    for night in s["nights"]:
        db.add(models.RoomNightRequest(
            event=1, badge=badge.id, room_night=night.id, requested=True))
    db.commit()
    rv = client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    new_room = rv.json["created"][0]
    rv = client.delete(f"/api/event/1/hotel_room/{new_room}")
    assert rv.status_code == 200
    db.expire_all()
    assert db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.badge == badge.id).count() == 0


def test_clear_matches_spares_handmade_rooms(client):
    """clear_matches deletes only unaccepted suggestions."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two"])
    block = s["block"].id

    handmade = models.HotelRoom(event=1, name="Hand Built", hotel_block=block,
                                completed=False, locked=False, suggested=False)
    db.add(handmade)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=s["badges"]["Alice One"].id,
        room_night=s["nights"][0].id, hotel_room=handmade.id))
    db.commit()
    handmade_id = handmade.id

    rv = client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    assert len(rv.json["created"]) == 1  # a room for Bob

    rv = client.post(f"/api/event/1/hotel/{block}/clear_matches", json={})
    assert rv.status_code == 200
    db.expire_all()
    remaining = db.query(models.HotelRoom).filter(
        models.HotelRoom.hotel_block == block).all()
    assert [x.id for x in remaining] == [handmade_id]


def test_suggest_roommates(client):
    """Candidates are scored by fit and filtered by anti-requests and
       completed-room membership."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models,
              ["Alice One", "Bob Two", "Carol Three", "Dave Four", "Eve Five"],
              roommate_pairs=[("Alice One", "Bob Two"), ("Bob Two", "Alice One")],
              anti_pairs=[("Alice One", "Dave Four")])
    block = s["block"].id

    # Alice occupies a hand-built incomplete room.
    room = models.HotelRoom(event=1, name="Alice's Room", hotel_block=block,
                            completed=False, suggested=False)
    # Eve sits in a completed room -> excluded from suggestions.
    done_room = models.HotelRoom(event=1, name="Done", hotel_block=block,
                                 completed=True)
    # Carol sits in another incomplete room -> included, flagged as a move.
    other_room = models.HotelRoom(event=1, name="Other", hotel_block=block,
                                  completed=False, suggested=True)
    db.add(room)
    db.add(done_room)
    db.add(other_room)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=s["badges"]["Alice One"].id,
        room_night=s["nights"][0].id, hotel_room=room.id))
    db.add(models.RoomNightAssignment(
        event=1, badge=s["badges"]["Eve Five"].id,
        room_night=s["nights"][0].id, hotel_room=done_room.id))
    db.add(models.RoomNightAssignment(
        event=1, badge=s["badges"]["Carol Three"].id,
        room_night=s["nights"][0].id, hotel_room=other_room.id))
    db.commit()

    rv = client.get(f"/api/event/1/hotel/room/{room.id}/suggest_roommates")
    assert rv.status_code == 200
    results = rv.json
    names = [x["name"] for x in results]
    # Bob (mutual request with Alice) ranks first; Dave (anti-requested) and
    # Eve (completed room) are excluded; Carol appears with her current room.
    assert names[0] == "Bob Two"
    assert "Dave Four" not in names
    assert "Eve Five" not in names
    carol = [x for x in results if x["name"] == "Carol Three"][0]
    assert carol["current_room"] == other_room.id
    bob = results[0]
    assert bob["score"] > 0
    assert set(bob["score_parts"]) == {"room_night", "roommate", "department", "other"}
    assert bob["missing_in_room"] == []
    assert bob["nights"] == [x.id for x in s["nights"]]

    rv = client.get("/api/event/1/hotel/room/99999/suggest_roommates")
    assert rv.status_code == 404
