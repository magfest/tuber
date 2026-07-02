import datetime


def _seed(db, models):
    """One restricted night with a UTC window (Aug 7 noon -> Aug 8 6am Pacific),
       a worker with an overlapping shift, and a slacker with none."""
    night = models.HotelRoomNight(
        event=1, name="Wednesday", date=datetime.date(2025, 8, 6),
        restricted=True, restriction_type="Setup",
        shift_starttime=datetime.datetime(2025, 8, 7, 19, 0, 0),
        shift_endtime=datetime.datetime(2025, 8, 8, 13, 0, 0))
    open_night = models.HotelRoomNight(
        event=1, name="Thursday", date=datetime.date(2025, 8, 7),
        restricted=False)
    db.add(night)
    db.add(open_night)
    db.flush()

    worker = models.Badge(event=1, public_name="Setup Worker",
                          first_name="Setup", last_name="Worker",
                          email="worker@example.com")
    slacker = models.Badge(event=1, public_name="No Shifts",
                           first_name="No", last_name="Shifts",
                           email="noshifts@example.com")
    db.add(worker)
    db.add(slacker)
    db.flush()

    department = models.Department(event=1, name="Arcade")
    db.add(department)
    db.flush()
    db.add(models.BadgeToDepartment(badge=slacker.id, department=department.id))

    db.add(models.RoomNightRequest(event=1, badge=worker.id,
                                   room_night=night.id, requested=True))
    db.add(models.RoomNightRequest(event=1, badge=slacker.id,
                                   room_night=night.id, requested=True))
    # Requesting an unrestricted night must not flag anyone.
    db.add(models.RoomNightRequest(event=1, badge=slacker.id,
                                   room_night=open_night.id, requested=True))

    job = models.Job(event=1, name="Setup: Arcade Load-In",
                     description="", department=department.id)
    db.add(job)
    db.flush()
    shift = models.Shift(event=1, job=job.id,
                         starttime=datetime.datetime(2025, 8, 7, 20, 0, 0),
                         duration=3 * 3600, slots=6, filledslots=0, weighting=1.0)
    db.add(shift)
    db.flush()
    db.add(models.ShiftAssignment(event=1, badge=worker.id, shift=shift.id))
    db.add(models.HotelRoomRequest(event=1, badge=slacker.id,
                                   room_night_justification="I help set up the arcade."))
    db.commit()
    return night, slacker


def test_missing_shifts(client):
    """Badges requesting a restricted night appear iff they lack an overlapping shift."""
    import tuber.models as models
    from tuber.database import db

    night, slacker = _seed(db, models)

    rv = client.get("/api/event/1/hotel/missing_shifts")
    assert rv.status_code == 200
    res = rv.json
    names = [x["name"] for x in res]
    assert "No Shifts" in names
    assert "Setup Worker" not in names
    flagged = [x for x in res if x["name"] == "No Shifts"][0]
    assert flagged["email"] == "noshifts@example.com"
    assert flagged["departments"] == ["Arcade"]
    assert [n["name"] for n in flagged["missing_nights"]] == ["Wednesday"]
    missing = flagged["missing_nights"][0]
    assert missing["restriction_type"] == "Setup"
    assert missing["requested"] is True
    assert missing["approved"] is False
    assert missing["assigned"] is False


def test_missing_shifts_toggles(client):
    """Approval and assignment can be toggled per badge+night."""
    import tuber.models as models
    from tuber.database import db

    night, slacker = _seed(db, models)
    night_id, badge_id = night.id, slacker.id

    def flagged_night():
        rv = client.get("/api/event/1/hotel/missing_shifts")
        assert rv.status_code == 200
        return [x for x in rv.json if x["id"] == badge_id][0]["missing_nights"][0]

    rv = client.post("/api/event/1/hotel/missing_shifts/approve",
                     json={"badge": badge_id, "room_night": night_id, "approved": True})
    assert rv.status_code == 200 and rv.json["approved"] is True
    assert flagged_night()["approved"] is True

    rv = client.post("/api/event/1/hotel/missing_shifts/assign",
                     json={"badge": badge_id, "room_night": night_id, "assigned": True})
    assert rv.status_code == 200 and rv.json["assigned"] is True
    assert flagged_night()["assigned"] is True
    assignments = db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.badge == badge_id).all()
    assert len(assignments) == 1 and assignments[0].hotel_room is None

    rv = client.post("/api/event/1/hotel/missing_shifts/approve",
                     json={"badge": badge_id, "room_night": night_id, "approved": False})
    assert rv.status_code == 200 and rv.json["approved"] is False
    rv = client.post("/api/event/1/hotel/missing_shifts/assign",
                     json={"badge": badge_id, "room_night": night_id, "assigned": False})
    assert rv.status_code == 200 and rv.json["assigned"] is False
    updated = flagged_night()
    assert updated["approved"] is False
    assert updated["assigned"] is False
    assert db.query(models.RoomNightApproval).filter(
        models.RoomNightApproval.badge == badge_id).count() == 0
    assert db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.badge == badge_id).count() == 0


def test_missing_shifts_export(client):
    """The CSV export includes emails and the missing days."""
    import tuber.models as models
    from tuber.database import db

    _seed(db, models)

    rv = client.get("/api/event/1/hotel/missing_shifts/export")
    assert rv.status_code == 200
    assert rv.headers["Content-Type"].startswith("text/csv")
    body = rv.data.decode()
    lines = body.strip().splitlines()
    assert lines[0] == "Name,Email,Departments,Nights Missing a Shift"
    assert any("noshifts@example.com" in line and "Wednesday (2025-08-06)" in line
               for line in lines[1:])
    assert "worker@example.com" not in body


def test_missing_shifts_detail(client):
    """The detail endpoint returns the schedule and request summary for the modal."""
    import tuber.models as models
    from tuber.database import db

    night, slacker = _seed(db, models)
    worker = db.query(models.Badge).filter(
        models.Badge.public_name == "Setup Worker").one()

    rv = client.get(f"/api/event/1/hotel/missing_shifts/{slacker.id}")
    assert rv.status_code == 200
    detail = rv.json
    assert detail["email"] == "noshifts@example.com"
    assert detail["shifts"] == []
    assert detail["room_request"]["justification"] == "I help set up the arcade."
    nights = {x["name"]: x for x in detail["nights"]}
    assert nights["Wednesday"]["requested"] is True
    assert nights["Wednesday"]["has_shift"] is False
    assert nights["Wednesday"]["shift_starttime"] == "2025-08-07T19:00:00Z"
    assert nights["Wednesday"]["shift_endtime"] == "2025-08-08T13:00:00Z"
    assert nights["Thursday"]["restricted"] is False

    rv = client.get(f"/api/event/1/hotel/missing_shifts/{worker.id}")
    assert rv.status_code == 200
    detail = rv.json
    assert len(detail["shifts"]) == 1
    assert detail["shifts"][0]["job"] == "Setup: Arcade Load-In"
    assert detail["shifts"][0]["department"] == "Arcade"
    assert detail["shifts"][0]["starttime"] == "2025-08-07T20:00:00Z"
    assert detail["shifts"][0]["duration"] == 3 * 3600
    nights = {x["name"]: x for x in detail["nights"]}
    assert nights["Wednesday"]["has_shift"] is True
