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
    from tuber.api.emails import build_email_tables, get_email_context, summarize_value, \
        render_template, load_filter

    s = _seed(db, models, ["Alice One"])
    s["requests"]["Alice One"].notes = "Allergic to feathers"
    s["requests"]["Alice One"].admin_notes = "Complained last year"
    db.commit()

    badges, tables = build_email_tables(1)
    alice = [x for x in badges if x.public_name == "Alice One"][0]
    context = get_email_context(alice, tables)
    rendered = render_template(
        "{{ hotel_request.notes }}|{{ hotel_request.admin_notes }}|{{ hotel_request.hotel_block }}",
        context)
    assert rendered == f"Allergic to feathers||{s['block'].id}"
    assert "Complained" not in str(summarize_value(context["hotel_request"]))

    # However the request is reached, and whatever helper is tried, the
    # admin note and event secrets stay out of the rendered email.
    event = context["event"]
    event.uber_apikey = "sk-very-secret"
    db.commit()
    context = get_email_context(alice, tables)
    for template in [
        "{{ badge.hotel_room_request[0].admin_notes }}",
        "{{ badge.hotel_room_request[0]['admin_notes'] }}",
        "{{ badge.hotel_room_request[0] | attr('admin_notes') }}",
        "{{ badge.hotel_room_request[0].serialize(badge.hotel_room_request) }}",
        "{{ hotel_request.serialize([hotel_request]) }}",
        "{{ hotel_request.__dict__ }}",
        "{{ badge.hotel_room_request }}",
        "{{ event.uber_apikey }}{{ badge.event_obj.uber_apikey }}",
        "{% for k, v in hotel_request.__dict__.items() %}{{ v }}{% endfor %}",
    ]:
        try:
            rendered = render_template(template, context)
        except Exception:
            continue  # refusing to render is fine too
        assert "Complained" not in rendered, template
        assert "sk-very-secret" not in rendered, template

    # The same policy holds in Lua filters, and they cannot write.
    for code in [
        "return function(c) return c.hotel_request.admin_notes end",
        "return function(c) return c.badge.hotel_room_request[0].admin_notes end",
        "return function(c) return c.badge.event_obj.uber_apikey end",
        "return function(c) return c.event.uber_apikey end",
        "return function(c) return python.builtins.getattr(c.hotel_request, 'admin_notes') end",
        "return function(c) return python.eval('1') end",
        "return function(c) return os.execute('true') end",
        "return function(c) return io.open('/etc/hosts') end",
        "return function(c) return require('os') end",
        "return function(c) return loadstring('return 1')() end",
        "return function(c) return debug.getregistry() end",
        "return function(c) return getmetatable(c.badge) or nil end",
        "return function(c) return setfenv end",
        "return function(c) return rawget end",
        "return function(c) return python.builtins end",
        "return function(c) return ('x').dump end",
        "\27Lua",
    ]:
        try:
            result = load_filter(code)(context)
        except Exception:
            continue
        assert result is None, code
    try:
        load_filter("return function(c) c.badge.email = 'x' end")(context)
    except Exception:
        pass
    assert alice.email != "x"
    assert load_filter(
        "return function(c) return c.hotel_request.notes end")(context) == "Allergic to feathers"
    # The allowlisted standard library is all there.
    assert load_filter("""return function(c)
        local n = 0
        for _ in python.iter(c.requested_nights) do n = n + 1 end
        return string.format("%s:%d:%d:%s", string.upper(c.badge.first_name),
            math.max(n, #c.requested_nights), #c.hotel_room_nights, type(os.time()))
    end""")(context) == "ALICE:2:2:number"

    # Ordinary template features still work under the allowlist.
    assert render_template(
        "{% for n in ['a', 'b'] %}{{ loop.index }}{{ n.upper() }}{% endfor %}"
        "|{{ badge.first_name }}|{{ event.name }}|{{ badge.departments | length }}",
        context) == f"1A2B|Alice|{event.name}|0"
