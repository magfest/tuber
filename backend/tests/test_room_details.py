from tests.test_room_matching import _seed


def _room(db, models, block, name="Room 1"):
    room = models.HotelRoom(event=1, name=name, hotel_block=block)
    db.add(room)
    db.commit()
    return room.id


def _details(client, room):
    return client.get("/api/event/1/hotel/room_details", query_string={"rooms": str(room)}).json[str(room)]


def test_extra_night_warning_survives_an_approved_roommate(client):
    """A night someone is not approved for stays flagged on them, whoever else is in the room."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two"])
    block = s["block"].id
    friday = s["nights"][0]
    friday.restriction_mode = "manual"
    db.add(models.RoomNightApproval(event=1, badge=s["badges"]["Bob Two"].id, room_night=friday.id, approved=True))
    db.commit()
    alice, bob = s["badges"]["Alice One"].id, s["badges"]["Bob Two"].id
    room = _room(db, models, block)

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates",
                json={"roommates": [alice], "nights": "requested"})
    assert _details(client, room)["roommates"][str(alice)]["errors"] == ["Extra Room Night (Fr)"]

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates", json={"roommates": [bob]})
    mates = _details(client, room)["roommates"]
    assert mates[str(alice)]["errors"] == ["Extra Room Night (Fr)"]
    assert mates[str(bob)]["errors"] == []
    assert len(mates[str(alice)]["room_night_assignments"]) == 2

    # Removing the extra night clears the warning and leaves her other night.
    assert mates[str(alice)]["extra_nights"] == [friday.id]
    rv = client.post(f"/api/event/1/hotel/{block}/room/{room}/remove_nights",
                     json={"badge": alice, "nights": mates[str(alice)]["extra_nights"]})
    assert rv.status_code == 200
    mates = _details(client, room)["roommates"]
    assert mates[str(alice)]["errors"] == [] and len(mates[str(alice)]["room_night_assignments"]) == 1
    assert len(mates[str(bob)]["room_night_assignments"]) == 2


def test_requested_roommates_say_whether_they_can_be_added(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three", "Dave Four", "Erin Five"],
              roommate_pairs=[("Alice One", x) for x in ("Bob Two", "Carol Three", "Dave Four", "Erin Five")])
    block = s["block"].id
    ids = {name: badge.id for name, badge in s["badges"].items()}
    # Carol is housed elsewhere, Dave is in another block, Erin declined.
    other_block = models.HotelRoomBlock(event=1, name="Other", description="")
    db.add(other_block)
    db.flush()
    s["requests"]["Dave Four"].hotel_block = other_block.id
    s["requests"]["Erin Five"].declined = True
    db.commit()
    room, elsewhere = _room(db, models, block), _room(db, models, block, "Room 2")
    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates", json={"roommates": [ids["Alice One"]]})
    client.post(f"/api/event/1/hotel/{block}/room/{elsewhere}/add_roommates", json={"roommates": [ids["Carol Three"]]})

    missing = _details(client, room)["roommates"][str(ids["Alice One"])]["requested_missing"]
    assert {x["name"]: x["addable"] for x in missing} == {
        "Bob Two": True, "Carol Three": False, "Dave Four": False, "Erin Five": False}

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates", json={"roommates": [ids["Bob Two"]]})
    missing = _details(client, room)["roommates"][str(ids["Alice One"])]["requested_missing"]
    assert "Bob Two" not in [x["name"] for x in missing]


def _restricted_friday(db, models, names):
    """Friday needs manual approval, which only the last name has."""
    s = _seed(db, models, names)
    friday = s["nights"][0]
    friday.restriction_mode = "manual"
    db.add(models.RoomNightApproval(event=1, badge=s["badges"][names[-1]].id, room_night=friday.id, approved=True))
    db.commit()
    return s, {name: badge.id for name, badge in s["badges"].items()}


def _nights(db, models, badge):
    return {x.room_night for x in db.query(models.RoomNightAssignment).filter(models.RoomNightAssignment.badge == badge)}


def test_adding_roommates_uses_approved_nights_unless_asked(client):
    import tuber.models as models
    from tuber.database import db

    s, ids = _restricted_friday(db, models, ["Alice One", "Bob Two"])
    block, (friday, saturday) = s["block"].id, [x.id for x in s["nights"]]
    room = _room(db, models, block)

    rv = client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates", json={"roommates": list(ids.values())})
    assert rv.json == {"skipped": []}
    assert _nights(db, models, ids["Alice One"]) == {saturday}
    assert _nights(db, models, ids["Bob Two"]) == {friday, saturday}
    # Alice has nothing approved left to place, so she leaves the pool.
    pool = client.get(f"/api/event/1/hotel/{block}/request_search").json
    assert pool["count"] == 0
    pool = client.get(f"/api/event/1/hotel/{block}/request_search", query_string={"nights": "requested"}).json
    assert pool["count"] == 1

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates",
                json={"roommates": [ids["Alice One"]], "nights": "requested"})
    assert _nights(db, models, ids["Alice One"]) == {friday, saturday}


def test_suggested_rooms_use_approved_nights_unless_asked(client):
    import tuber.models as models
    from tuber.database import db

    s, ids = _restricted_friday(db, models, ["Alice One", "Bob Two"])
    block, (friday, saturday) = s["block"].id, [x.id for x in s["nights"]]

    client.post(f"/api/event/1/hotel/{block}/suggest_rooms", json={})
    assert _nights(db, models, ids["Alice One"]) == {saturday}
    assert _nights(db, models, ids["Bob Two"]) == {friday, saturday}

    client.post(f"/api/event/1/hotel/{block}/rematch_all", json={"nights": "requested"})
    assert _nights(db, models, ids["Alice One"]) == {friday, saturday}


def test_all_departments_approvals(client):
    import tuber.models as models
    from tuber.database import db

    s, ids = _restricted_friday(db, models, ["Alice One", "Bob Two"])
    friday = s["nights"][0].id

    rows = {x["name"]: x for x in client.get("/api/event/1/hotel/requests").json}
    assert set(rows) == {"Alice One", "Bob Two"}
    assert rows["Alice One"]["room_nights"][str(friday)]["approved_by_anyone"] is False

    rv = client.post("/api/event/1/hotel/approve", json={"badge": ids["Alice One"], "room_night": friday, "approved": True})
    assert rv.status_code == 200
    rows = {x["name"]: x for x in client.get("/api/event/1/hotel/requests").json}
    assert rows["Alice One"]["room_nights"][str(friday)]["approved"] is True
    assert rows["Alice One"]["room_nights"][str(friday)]["approved_by_anyone"] is True
