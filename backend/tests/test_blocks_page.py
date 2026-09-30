from tests.test_room_matching import _seed


def _names(rv):
    assert rv.status_code == 200
    return [x["name"] for x in rv.json["results"]]


def test_active_filter_and_no_block_filter(client):
    """The Blocks page lists placeable people (not declined, wants a night)
       and can narrow to those who have no block yet."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three"])
    staff = s["block"].id
    # Bob has no block yet; Carol declined; Dave never asked for a night.
    s["requests"]["Bob Two"].hotel_block = None
    s["requests"]["Carol Three"].declined = True
    dave = models.Badge(event=1, public_name="Dave Four", first_name="Dave",
                        last_name="Four", search_name="dave four",
                        email="dave@example.com")
    db.add(dave)
    db.flush()
    db.add(models.HotelRoomRequest(event=1, badge=dave.id))
    db.commit()

    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "active"})
    assert _names(rv) == ["Alice One", "Bob Two"]
    assert rv.json["count"] == 2

    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "active", "block": -1})
    assert _names(rv) == ["Bob Two"]
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "active", "block": staff})
    assert _names(rv) == ["Alice One"]
    # "Everyone" still includes the declined and the empty request.
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "all", "block": -1})
    assert _names(rv) == ["Bob Two", "Dave Four"]


def test_bulk_block_moves(client):
    """One POST moves several requests between blocks; -1 clears a block."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two"])
    staff = s["block"].id
    volunteers = models.HotelRoomBlock(event=1, name="Volunteers", description="")
    db.add(volunteers)
    s["requests"]["Bob Two"].hotel_block = None
    db.commit()
    volunteers_id = volunteers.id
    alice_req = s["requests"]["Alice One"].id
    bob_req = s["requests"]["Bob Two"].id

    def in_block(block):
        rv = client.get("/api/event/1/hotel/attendees",
                        query_string={"filter": "active", "block": block})
        return _names(rv)

    assert in_block(staff) == ["Alice One"]
    assert in_block(-1) == ["Bob Two"]

    rv = client.post("/api/event/1/hotel/block_assignments", json={"updates": [
        {"id": bob_req, "hotel_block": volunteers_id},
        {"id": alice_req, "hotel_block": volunteers_id},
    ]})
    assert rv.status_code == 200
    assert in_block(volunteers_id) == ["Alice One", "Bob Two"]
    assert in_block(staff) == []
    assert in_block(-1) == []

    rv = client.post("/api/event/1/hotel/block_assignments", json={"updates": [
        {"id": alice_req, "hotel_block": -1}]})
    assert rv.status_code == 200
    assert in_block(-1) == ["Alice One"]
    assert in_block(volunteers_id) == ["Bob Two"]
