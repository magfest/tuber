import jinja2

from tests.test_room_matching import _seed


def test_request_admin_notes_are_admin_only(client):
    """Admins read and write the note through the rooming endpoints; the
       staffer's form endpoint and the generic API never show or accept it."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One"])
    alice = s["badges"]["Alice One"]
    admin = db.query(models.User).filter(models.User.username == "admin").one()
    alice.user = admin.id  # the logged-in admin doubles as the staffer
    db.commit()
    alice_id = alice.id
    req_id = s["requests"]["Alice One"].id
    block = s["block"].id

    rv = client.patch(f"/api/event/1/hotel/request/{req_id}/admin_notes",
                      json={"admin_notes": "  Keep near the elevator  "})
    assert rv.status_code == 200
    assert rv.json == {"id": req_id, "admin_notes": "Keep near the elevator"}

    # Every admin placement view carries it, and two of them search it.
    rv = client.get("/api/event/1/hotel/attendees", query_string={"filter": "active"})
    assert rv.json["results"][0]["admin_notes"] == "Keep near the elevator"
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"search": "elevator", "search_field": "admin_notes"})
    assert [x["name"] for x in rv.json["results"]] == ["Alice One"]
    rv = client.get(f"/api/event/1/hotel/{block}/request_search")
    assert rv.json["results"][0]["admin_notes"] == "Keep near the elevator"
    rv = client.get(f"/api/event/1/hotel/{block}/request_search",
                    query_string={"search_term": "elevator"})
    assert rv.json["count"] == 1
    rv = client.get(f"/api/event/1/hotel/attendee/{alice_id}")
    assert rv.json["room_request"]["admin_notes"] == "Keep near the elevator"

    # The staffer's own form never sees it, and sending it back changes nothing.
    rv = client.get("/api/event/1/hotel/request")
    assert rv.status_code == 200
    assert "admin_notes" not in rv.json
    form = rv.json
    form["admin_notes"] = "I can see this?"
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 200
    rv = client.get(f"/api/event/1/hotel/attendee/{alice_id}")
    assert rv.json["room_request"]["admin_notes"] == "Keep near the elevator"

    # The generic API hides it and refuses to write it, even for an admin.
    rv = client.get(f"/api/event/1/hotel_room_request/{req_id}")
    assert rv.status_code == 200
    assert "admin_notes" not in rv.json
    rv = client.patch(f"/api/event/1/hotel_room_request/{req_id}",
                      json={"id": req_id, "admin_notes": "through the back door"})
    assert rv.status_code == 403
    rv = client.get(f"/api/event/1/hotel/attendee/{alice_id}")
    assert rv.json["room_request"]["admin_notes"] == "Keep near the elevator"

    # Blank clears it.
    rv = client.patch(f"/api/event/1/hotel/request/{req_id}/admin_notes",
                      json={"admin_notes": "   "})
    assert rv.json["admin_notes"] is None


def test_room_admin_notes_stay_out_of_exports(client):
    """The room note shows in every room view but never in the hotel export
       or the generic API."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models, ["Alice One"])
    block = s["block"].id
    alice_id = s["badges"]["Alice One"].id
    req_id = s["requests"]["Alice One"].id
    room = models.HotelRoom(event=1, name="101", hotel_block=block,
                            completed=True, notes="Late checkout please")
    db.add(room)
    db.flush()
    db.add(models.RoomNightAssignment(
        event=1, badge=alice_id, room_night=s["nights"][0].id, hotel_room=room.id))
    db.commit()
    room_id = room.id

    rv = client.patch(f"/api/event/1/hotel/room/{room_id}/admin_notes",
                      json={"admin_notes": "Comp room, do not bill"})
    assert rv.status_code == 200
    assert rv.json == {"id": room_id, "admin_notes": "Comp room, do not bill"}

    rv = client.get("/api/event/1/hotel/room_search", query_string={"hotel_block": block})
    assert rv.json["hotel_rooms"][0]["admin_notes"] == "Comp room, do not bill"
    rv = client.get(f"/api/event/1/hotel/room/{room_id}/details")
    assert rv.json["admin_notes"] == "Comp room, do not bill"
    assert rv.json["notes"] == "Late checkout please"
    occupant = rv.json["occupants"][0]
    assert occupant["request_id"] == req_id
    assert occupant["admin_notes"] is None
    rv = client.get("/api/event/1/hotel/room_details", query_string={"rooms": room_id})
    mate = rv.json[str(room_id)]["roommates"][str(alice_id)]
    assert mate["request_id"] == req_id

    rv = client.get(f"/api/event/1/hotel_room/{room_id}")
    assert rv.status_code == 200
    assert "admin_notes" not in rv.json
    rv = client.patch(f"/api/event/1/hotel_room/{room_id}",
                      json={"id": room_id, "admin_notes": "nope"})
    assert rv.status_code == 403

    # The Passkey export carries the hotel note and nothing internal.
    rv = client.get("/api/event/1/hotel/export_passkey")
    assert rv.status_code == 200
    body = rv.data.decode()
    assert "Late checkout please" in body
    assert "Comp room" not in body


def test_admin_notes_never_reach_email_templates(client):
    """A template can read the staffer's notes but not the admin note."""
    import tuber.models as models
    from tuber.database import db
    from tuber.api.emails import build_email_tables, get_email_context, summarize_value

    s = _seed(db, models, ["Alice One"])
    s["requests"]["Alice One"].notes = "Allergic to feathers"
    s["requests"]["Alice One"].admin_notes = "Complained last year"
    db.commit()

    badges, tables = build_email_tables(1)
    alice = [x for x in badges if x.public_name == "Alice One"][0]
    context = get_email_context(alice, tables)
    rendered = jinja2.Template(
        "{{ hotel_request.notes }}|{{ hotel_request.admin_notes }}|{{ hotel_request.hotel_block }}"
    ).render(**context)
    assert rendered == f"Allergic to feathers||{s['block'].id}"
    assert "Complained" not in str(summarize_value(context["hotel_request"]))
