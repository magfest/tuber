import datetime

from tests.test_room_matching import _seed


def _search(client, block, **params):
    rv = client.get(f"/api/event/1/hotel/{block}/request_search",
                    query_string=params)
    assert rv.status_code == 200
    return rv.json


def test_request_search_filters(client):
    """Night, approval, and roommate filters plus the nights sort."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One", "Bob Two", "Carol Three"],
              roommate_pairs=[("Carol Three", "Alice One")])
    block = s["block"].id
    friday, saturday = s["nights"]

    # Bob only wants Friday.
    db.query(models.RoomNightRequest).filter(
        models.RoomNightRequest.badge == s["badges"]["Bob Two"].id,
        models.RoomNightRequest.room_night == saturday.id).update(
        {"requested": False})
    # A manual-restriction night that only Alice requests and nobody approved.
    sunday = models.HotelRoomNight(
        event=1, name="Sunday", date=datetime.date(2025, 8, 10),
        restriction_mode="manual", restriction_type="Special")
    db.add(sunday)
    db.flush()
    db.add(models.RoomNightRequest(
        event=1, badge=s["badges"]["Alice One"].id, room_night=sunday.id,
        requested=True))
    db.commit()

    def names(res):
        return [x["public_name"] for x in res["results"]]

    # Baseline: everyone with an unassigned requested night.
    assert names(_search(client, block)) == [
        "Alice One", "Bob Two", "Carol Three"]

    # Only people who requested Saturday.
    res = _search(client, block, night=saturday.id)
    assert names(res) == ["Alice One", "Carol Three"]
    assert res["count"] == 2

    # Only people with outgoing roommate requests.
    assert names(_search(client, block, has_roommates="true")) == ["Carol Three"]

    # Approval coverage: Alice has the unapproved Sunday night.
    assert names(_search(client, block, approval="partial")) == ["Alice One"]
    assert names(_search(client, block, approval="full")) == [
        "Bob Two", "Carol Three"]

    # Sorting by number of requested nights (Alice 3, Carol 2, Bob 1).
    assert names(_search(client, block, sort="nights", order="desc")) == [
        "Alice One", "Carol Three", "Bob Two"]
    assert names(_search(client, block, sort="nights", order="asc")) == [
        "Bob Two", "Carol Three", "Alice One"]

    # Pagination applies after filtering.
    res = _search(client, block, sort="nights", order="desc", offset=1, limit=1)
    assert names(res) == ["Carol Three"]
    assert res["count"] == 3


def test_room_search_filters(client):
    """Status, location, search, and sort on the unified room listing."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One"])
    block = s["block"].id
    location = models.HotelLocation(event=1, name="Marriott", address="123 St")
    db.add(location)
    db.flush()

    red = models.HotelRoom(event=1, name="Red Room", hotel_block=block,
                           completed=True)
    blue = models.HotelRoom(event=1, name="Blue Room", hotel_block=block,
                            locked=True)
    green = models.HotelRoom(event=1, name="Green Room", hotel_block=block,
                             hotel_location=location.id)
    suggested = models.HotelRoom(event=1, name="Suggested Room",
                                 hotel_block=block, suggested=True)
    for room in (red, blue, green, suggested):
        db.add(room)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=s["badges"]["Alice One"].id,
        room_night=s["nights"][0].id, hotel_room=green.id))
    db.commit()

    def rooms(**params):
        rv = client.get("/api/event/1/hotel/room_search", query_string=params)
        assert rv.status_code == 200
        return [x["name"] for x in rv.json["hotel_rooms"]], rv.json["count"]

    names, count = rooms(hotel_block=block, sort="name", order="asc")
    assert names == ["Blue Room", "Green Room", "Red Room", "Suggested Room"]
    assert count == 4

    # The workspace's main list excludes pending suggestions.
    names, _ = rooms(hotel_block=block, suggested="false", sort="name")
    assert names == ["Blue Room", "Green Room", "Red Room"]

    names, _ = rooms(hotel_block=block, status="completed")
    assert names == ["Red Room"]
    names, _ = rooms(hotel_block=block, status="incomplete", suggested="false")
    assert names == ["Blue Room", "Green Room"]
    names, _ = rooms(hotel_block=block, status="locked")
    assert names == ["Blue Room"]
    names, count = rooms(hotel_block=block, status="unlocked", suggested="false")
    assert names == ["Green Room", "Red Room"]
    assert count == 2

    names, _ = rooms(hotel_block=block, hotel_location=location.id)
    assert names == ["Green Room"]

    # Search matches the room name or a roommate's name, composed with filters.
    names, _ = rooms(hotel_block=block, search="blue")
    assert names == ["Blue Room"]
    names, _ = rooms(hotel_block=block, search="alice")
    assert names == ["Green Room"]
    names, _ = rooms(hotel_block=block, search="alice", status="completed")
    assert names == []

    # Sort by name descending and paginate.
    names, count = rooms(hotel_block=block, suggested="false", sort="name",
                         order="desc", limit=1, offset=1)
    assert names == ["Green Room"]
    assert count == 3
