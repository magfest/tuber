import datetime


def _seed(db, models):
    """One night per restriction mode plus badges exercising each criterion."""
    window_night = models.HotelRoomNight(
        event=1, name="Window", date=datetime.date(2025, 8, 6),
        restriction_mode="shift_window", restriction_type="Setup",
        shift_starttime=datetime.datetime(2025, 8, 7, 19, 0, 0),
        shift_endtime=datetime.datetime(2025, 8, 8, 13, 0, 0))
    hours_night = models.HotelRoomNight(
        event=1, name="Hours", date=datetime.date(2025, 8, 7),
        restriction_mode="shift_hours", shift_hours_required=6,
        restriction_type="Volunteer")
    manual_night = models.HotelRoomNight(
        event=1, name="Manual", date=datetime.date(2025, 8, 8),
        restriction_mode="manual", restriction_type="Special")
    open_night = models.HotelRoomNight(
        event=1, name="Open", date=datetime.date(2025, 8, 9),
        restriction_mode="none")
    for night in (window_night, hours_night, manual_night, open_night):
        db.add(night)
    db.flush()

    worker = models.Badge(event=1, public_name="Window Worker",
                          first_name="Window", last_name="Worker",
                          email="window@example.com")
    grinder = models.Badge(event=1, public_name="Hour Grinder",
                           first_name="Hour", last_name="Grinder",
                           email="hours@example.com")
    slacker = models.Badge(event=1, public_name="No Shifts",
                           first_name="No", last_name="Shifts",
                           email="none@example.com")
    for badge in (worker, grinder, slacker):
        db.add(badge)
    db.flush()

    department = models.Department(event=1, name="Arcade")
    db.add(department)
    db.flush()

    job = models.Job(event=1, name="Load-In", description="",
                     department=department.id)
    db.add(job)
    db.flush()
    # 3h shift inside the window: satisfies the window night; not enough
    # for the 6h hours night.
    short_shift = models.Shift(
        event=1, job=job.id, starttime=datetime.datetime(2025, 8, 7, 20, 0, 0),
        duration=3 * 3600, slots=6, filledslots=0, weighting=1.0)
    # 8h shift outside the window: satisfies the hours night only.
    long_shift = models.Shift(
        event=1, job=job.id, starttime=datetime.datetime(2025, 8, 9, 0, 0, 0),
        duration=8 * 3600, slots=6, filledslots=0, weighting=1.0)
    db.add(short_shift)
    db.add(long_shift)
    db.flush()
    db.add(models.ShiftAssignment(event=1, badge=worker.id, shift=short_shift.id))
    db.add(models.ShiftAssignment(event=1, badge=grinder.id, shift=long_shift.id))
    db.commit()

    return {
        "window": window_night, "hours": hours_night,
        "manual": manual_night, "open": open_night,
        "worker": worker, "grinder": grinder, "slacker": slacker,
        "department": department,
    }


def test_approved_night_ids_per_mode(client):
    """Each restriction mode approves exactly the badges meeting its criterion."""
    import tuber.models as models
    from tuber.database import db
    from tuber.api.night_approval import approved_night_ids, shift_hours_totals

    s = _seed(db, models)
    badge_ids = [s["worker"].id, s["grinder"].id, s["slacker"].id]
    approved = approved_night_ids(db, 1, badge_ids)

    # Everyone gets the unrestricted night.
    for badge in badge_ids:
        assert s["open"].id in approved[badge]

    # Window night: only the worker's shift overlaps.
    assert s["window"].id in approved[s["worker"].id]
    assert s["window"].id not in approved[s["grinder"].id]
    assert s["window"].id not in approved[s["slacker"].id]

    # Hours night: only the grinder has >= 6 hours.
    assert s["hours"].id in approved[s["grinder"].id]
    assert s["hours"].id not in approved[s["worker"].id]
    assert s["hours"].id not in approved[s["slacker"].id]

    # Manual night: nobody yet.
    for badge in badge_ids:
        assert s["manual"].id not in approved[badge]

    totals = shift_hours_totals(db, 1, badge_ids)
    assert totals[s["worker"].id] == 3
    assert totals[s["grinder"].id] == 8
    assert s["slacker"].id not in totals


def test_manual_approval_satisfies_any_mode(client):
    """A manual approval approves the badge for any restricted night."""
    import tuber.models as models
    from tuber.database import db
    from tuber.api.night_approval import approved_night_ids

    s = _seed(db, models)
    for night in (s["window"], s["hours"], s["manual"]):
        db.add(models.RoomNightApproval(
            event=1, badge=s["slacker"].id, room_night=night.id,
            department=s["department"].id, approved=True))
    db.commit()

    approved = approved_night_ids(db, 1, [s["slacker"].id])
    assert {s["window"].id, s["hours"].id, s["manual"].id,
            s["open"].id} <= approved[s["slacker"].id]


def test_legacy_restricted_flag_maps_to_shift_window(client):
    """Writers that only set restricted=True get shift_window behavior."""
    import tuber.models as models
    from tuber.database import db

    night = models.HotelRoomNight(
        event=1, name="Legacy", date=datetime.date(2025, 8, 10),
        restricted=True,
        shift_starttime=datetime.datetime(2025, 8, 10, 0, 0, 0),
        shift_endtime=datetime.datetime(2025, 8, 11, 0, 0, 0))
    db.add(night)
    db.commit()
    assert night.restriction_mode == "shift_window"
    assert night.restricted is True

    # And the mirror tracks mode changes both ways.
    night.restriction_mode = "none"
    assert night.restricted is False
    night.restriction_mode = "manual"
    assert night.restricted is True


def test_missing_shifts_reports_modes(client):
    """The missing-shifts attendee filter understands all three restricted modes."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    # Eligibility requires a hotel room request record.
    db.add(models.HotelRoomRequest(event=1, badge=s["slacker"].id))
    db.add(models.HotelRoomRequest(event=1, badge=s["grinder"].id))
    # Slacker requests all four nights.
    for night in ("window", "hours", "manual", "open"):
        db.add(models.RoomNightRequest(
            event=1, badge=s["slacker"].id, room_night=s[night].id, requested=True))
    # Grinder requests the hours night (satisfied) and manual night (not).
    db.add(models.RoomNightRequest(
        event=1, badge=s["grinder"].id, room_night=s["hours"].id, requested=True))
    db.add(models.RoomNightRequest(
        event=1, badge=s["grinder"].id, room_night=s["manual"].id, requested=True))
    db.commit()

    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "missing_shifts"})
    assert rv.status_code == 200
    by_name = {x["name"]: x for x in rv.json["results"]}

    slacker_nights = {x["name"]: x for x in by_name["No Shifts"]["missing_nights"]}
    assert set(slacker_nights) == {"Window", "Hours", "Manual"}
    assert slacker_nights["Window"]["mode"] == "shift_window"
    assert slacker_nights["Hours"]["mode"] == "shift_hours"
    assert slacker_nights["Hours"]["hours_required"] == 6
    assert slacker_nights["Hours"]["hours_assigned"] == 0
    assert slacker_nights["Manual"]["mode"] == "manual"

    grinder_nights = {x["name"] for x in by_name["Hour Grinder"]["missing_nights"]}
    assert grinder_nights == {"Manual"}

    # Manually approving the manual night resolves it for the grinder.
    db.add(models.RoomNightApproval(
        event=1, badge=s["grinder"].id, room_night=s["manual"].id,
        department=None, approved=True))
    db.commit()
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "missing_shifts"})
    assert "Hour Grinder" not in {x["name"] for x in rv.json["results"]}


def test_department_approvals_payload_modes(client):
    """The department approvals endpoint reports per-mode coverage."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    db.add(models.BadgeToDepartment(badge=s["grinder"].id,
                                    department=s["department"].id))
    db.add(models.HotelRoomRequest(event=1, badge=s["grinder"].id))
    for night in ("window", "hours", "manual"):
        db.add(models.RoomNightRequest(
            event=1, badge=s["grinder"].id, room_night=s[night].id, requested=True))
    db.commit()

    rv = client.get(f"/api/event/1/hotel/requests/{s['department'].id}")
    assert rv.status_code == 200
    grinder = [x for x in rv.json if x["name"] == "Hour Grinder"][0]
    nights = {x["mode"]: x for x in grinder["room_nights"].values()}
    assert nights["shift_window"]["approved_by_shifts"] is False
    assert nights["shift_hours"]["hours_met"] is True
    assert nights["shift_hours"]["hours_assigned"] == 8
    assert nights["shift_hours"]["hours_required"] == 6
    assert nights["manual"]["approved"] is None
