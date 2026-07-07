import datetime


def _seed(db, models):
    """A badge for the logged-in admin user with an empty request, plus one
       open and one restricted night."""
    open_night = models.HotelRoomNight(
        event=1, name="Friday", date=datetime.date(2025, 8, 8),
        restriction_mode="none")
    setup_night = models.HotelRoomNight(
        event=1, name="Setup", date=datetime.date(2025, 8, 6),
        restriction_mode="manual", restriction_type="Setup")
    db.add(open_night)
    db.add(setup_night)
    db.flush()

    user = db.query(models.User).filter(
        models.User.username == "admin").one()
    badge = models.Badge(event=1, public_name="Admin Staffer",
                         first_name="Admin", last_name="Staffer",
                         search_name="admin staffer",
                         email="admin@example.com", user=user.id)
    db.add(badge)
    db.flush()
    db.add(models.HotelRoomRequest(event=1, badge=badge.id))
    db.commit()
    return open_night, setup_night, badge


def test_request_form_required_fields(client):
    """The staffer form endpoint enforces name, nights, and justification."""
    import tuber.models as models
    from tuber.database import db

    open_night, setup_night, badge = _seed(db, models)

    rv = client.get("/api/event/1/hotel/request")
    assert rv.status_code == 200
    form = rv.json
    nights = {x["name"]: x for x in form["room_nights"]}

    # Empty form: every requirement is reported at once.
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 400
    errors = " ".join(rv.json["errors"])
    assert "First name" in errors
    assert "Last name" in errors
    assert "at least one night" in errors

    # Whitespace names don't count.
    form["first_name"] = "   "
    form["last_name"] = "Staffer"
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 400
    assert any("First name" in x for x in rv.json["errors"])

    # Names plus an unrestricted night saves.
    form["first_name"] = "Admin"
    nights["Friday"]["requested"] = True
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 200

    # Adding a restricted night requires a justification.
    nights["Setup"]["requested"] = True
    form["room_night_justification"] = "  "
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 400
    assert any("justification" in x.lower() for x in rv.json["errors"])

    form["room_night_justification"] = "Helping the arcade load in."
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 200

    # The saved state round-trips.
    rv = client.get("/api/event/1/hotel/request")
    saved = {x["name"]: x for x in rv.json["room_nights"]}
    assert saved["Friday"]["requested"] is True
    assert saved["Setup"]["requested"] is True
    assert rv.json["room_night_justification"] == "Helping the arcade load in."


def test_request_form_decline_skips_validation(client):
    """Declining a room is a complete answer — no other fields required."""
    import tuber.models as models
    from tuber.database import db

    _seed(db, models)

    rv = client.get("/api/event/1/hotel/request")
    form = rv.json
    form["declined"] = True
    form["first_name"] = ""
    form["last_name"] = ""
    rv = client.patch("/api/event/1/hotel/request", json=form)
    assert rv.status_code == 200
    rv = client.get("/api/event/1/hotel/request")
    assert rv.json["declined"] is True
