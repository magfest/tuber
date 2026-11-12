from tests.test_room_matching import _seed


def _room(db, models, block, name="Room 1"):
    room = models.HotelRoom(event=1, name=name, hotel_block=block)
    db.add(room)
    db.commit()
    return room.id


def _details(client, room):
    return client.get("/api/event/1/hotel/room_details", query_string={"rooms": str(room)}).json[str(room)]


def test_extra_night_warning_survives_an_approved_roommate(client):
    """A night the room runs that someone is not approved for is flagged on
       them, whoever else is in the room."""
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

    # Removing the extra night leaves her other night. The room still runs
    # Friday for Bob, which she isn't approved for, so the warning stays but
    # there is nothing left of hers to remove.
    assert mates[str(alice)]["extra_nights"] == [friday.id]
    rv = client.post(f"/api/event/1/hotel/{block}/room/{room}/remove_nights",
                     json={"badge": alice, "nights": mates[str(alice)]["extra_nights"]})
    assert rv.status_code == 200
    mates = _details(client, room)["roommates"]
    assert mates[str(alice)]["errors"] == ["Extra Room Night (Fr)"]
    assert mates[str(alice)]["extra_nights"] == []
    assert len(mates[str(alice)]["room_night_assignments"]) == 1
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


def test_missing_night_compares_eligible_nights_to_this_room(client):
    """A night held without a room, or in another room, still counts as
       missing from this room."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One"])
    block = s["block"].id
    alice = s["badges"]["Alice One"].id
    friday, saturday = [x.id for x in s["nights"]]
    room = _room(db, models, block)
    db.add(models.RoomNightAssignment(event=1, badge=alice, room_night=saturday, hotel_room=room))
    db.add(models.RoomNightAssignment(event=1, badge=alice, room_night=friday, hotel_room=None))
    db.commit()
    assert _details(client, room)["roommates"][str(alice)]["errors"] == ["Missing Room Night (Fr)"]

    db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.room_night == friday).update({"hotel_room": room})
    db.commit()
    assert _details(client, room)["roommates"][str(alice)]["errors"] == []


def test_extra_night_when_room_runs_longer(client):
    """Someone eligible for one night in a two-night room is flagged even
       though they only hold their own night."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two"])
    block = s["block"].id
    alice, bob = s["badges"]["Alice One"].id, s["badges"]["Bob Two"].id
    friday, saturday = [x.id for x in s["nights"]]
    db.query(models.RoomNightRequest).filter(models.RoomNightRequest.badge == alice,
                                             models.RoomNightRequest.room_night == saturday).delete()
    room = _room(db, models, block)
    for badge, night in [(alice, friday), (bob, friday), (bob, saturday)]:
        db.add(models.RoomNightAssignment(event=1, badge=badge, room_night=night, hotel_room=room))
    db.commit()
    mates = _details(client, room)["roommates"]
    assert mates[str(alice)]["errors"] == ["Extra Room Night (Sa)"]
    assert mates[str(alice)]["extra_nights"] == []
    assert mates[str(bob)]["errors"] == []


def test_gender_mismatch_skips_requested_roommates(client):
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three"],
              roommate_pairs=[("Alice One", "Bob Two")])
    block = s["block"].id
    ids = {name: badge.id for name, badge in s["badges"].items()}
    s["requests"]["Alice One"].prefer_single_gender = True
    s["requests"]["Alice One"].preferred_gender = "woman"
    s["requests"]["Bob Two"].preferred_gender = "man"
    s["requests"]["Carol Three"].preferred_gender = "nonbinary"
    db.commit()
    room = _room(db, models, block)

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates",
                json={"roommates": [ids["Alice One"], ids["Bob Two"]]})
    assert _details(client, room)["roommates"][str(ids["Alice One"])]["errors"] == []

    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates",
                json={"roommates": [ids["Carol Three"]]})
    errors = _details(client, room)["roommates"][str(ids["Alice One"])]["errors"]
    assert errors == ["Gender Mismatch (woman) (nonbinary, woman)"]


def test_null_gender_answers_are_not_matched_but_shown(client):
    """An answer mapped to null drops the single-gender preference for
       matching and the mismatch warning, but the room still shows it."""
    import tuber.config
    import tuber.models as models
    from tuber.database import db
    tuber.config.gender_map = {"woman": "female", "man": "male", "who's asking?": None}

    s = _seed(db, models, ["Alice One", "Bob Two"])
    block = s["block"].id
    ids = {name: badge.id for name, badge in s["badges"].items()}
    s["requests"]["Alice One"].prefer_single_gender = True
    s["requests"]["Alice One"].preferred_gender = "Who's asking?"
    s["requests"]["Bob Two"].preferred_gender = "man"
    db.commit()
    room = _room(db, models, block)
    client.post(f"/api/event/1/hotel/{block}/room/{room}/add_roommates", json={"roommates": list(ids.values())})

    alice = _details(client, room)["roommates"][str(ids["Alice One"])]
    assert alice["errors"] == []
    assert alice["single_gender"] == {"answer": "Who's asking?", "group": None, "ignored": True}
    assert _details(client, room)["roommates"][str(ids["Bob Two"])]["single_gender"] is None
    grid = client.get(f"/api/event/1/hotel/room/{room}/details").json
    assert {x["name"]: x["single_gender"] for x in grid["occupants"]}["Alice One"]["ignored"] is True

    from tuber.api.room_matcher import load_staffer_pool, single_gender_violated
    pool = load_staffer_pool(db, 1, block, exclude_assigned=False)
    assert not any(x.prefer_single_gender for x in pool)
    assert not single_gender_violated(set(pool))


def test_room_search_single_gender_filter(client):
    import tuber.config
    import tuber.models as models
    from tuber.database import db
    tuber.config.gender_map = {"woman": "female", "trans woman": "female", "man": "male",
                               "who could say": None}

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three", "Dave Four"])
    block = s["block"].id
    ids = {name: badge.id for name, badge in s["badges"].items()}
    answers = {"Alice One": ("Trans Woman", True), "Bob Two": ("man", True),
               "Carol Three": ("woman", False), "Dave Four": ("who could say", True)}
    for name, (answer, prefer) in answers.items():
        s["requests"][name].preferred_gender = answer
        s["requests"][name].prefer_single_gender = prefer
    db.commit()
    rooms = {}
    for name in answers:
        rooms[name] = _room(db, models, block, name)
        client.post(f"/api/event/1/hotel/{block}/room/{rooms[name]}/add_roommates",
                    json={"roommates": [ids[name]]})

    assert client.get("/api/event/1/hotel/gender_groups").json == ["female", "male"]

    def names(group):
        rv = client.get("/api/event/1/hotel/room_search", query_string={"single_gender": group, "limit": 50})
        return sorted(x["name"] for x in rv.json["hotel_rooms"])
    # Carol is female but didn't ask; Dave's answer is ignored.
    assert names("female") == ["Alice One"]
    assert names("male") == ["Bob Two"]
