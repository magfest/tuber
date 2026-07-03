import datetime


def _seed(db, models):
    """One restricted night with a UTC window, a worker with an overlapping
       shift, and a slacker with none."""
    night = models.HotelRoomNight(
        event=1, name="Wednesday", date=datetime.date(2025, 8, 6),
        restriction_mode="shift_window", restriction_type="Setup",
        shift_starttime=datetime.datetime(2025, 8, 7, 19, 0, 0),
        shift_endtime=datetime.datetime(2025, 8, 8, 13, 0, 0))
    open_night = models.HotelRoomNight(
        event=1, name="Thursday", date=datetime.date(2025, 8, 7),
        restriction_mode="none")
    db.add(night)
    db.add(open_night)
    db.flush()

    worker = models.Badge(event=1, public_name="Setup Worker",
                          first_name="Setup", last_name="Worker",
                          search_name="setup worker",
                          email="worker@example.com")
    slacker = models.Badge(event=1, public_name="No Shifts",
                           first_name="No", last_name="Shifts",
                           search_name="no shifts",
                           email="noshifts@example.com")
    db.add(worker)
    db.add(slacker)
    db.flush()

    department = models.Department(event=1, name="Arcade")
    db.add(department)
    db.flush()
    db.add(models.BadgeToDepartment(badge=slacker.id, department=department.id))

    db.add(models.HotelRoomRequest(event=1, badge=worker.id,
                                   first_name="Setup", last_name="Worker"))
    db.add(models.HotelRoomRequest(
        event=1, badge=slacker.id, first_name="No", last_name="Shifts",
        room_night_justification="I help set up the arcade."))
    db.add(models.RoomNightRequest(event=1, badge=worker.id,
                                   room_night=night.id, requested=True))
    db.add(models.RoomNightRequest(event=1, badge=slacker.id,
                                   room_night=night.id, requested=True))
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
    db.commit()
    return night, worker, slacker


def test_attendee_toggles(client):
    """Approval, assignment, and requested toggles round-trip per badge+night."""
    import tuber.models as models
    from tuber.database import db

    night, worker, slacker = _seed(db, models)
    night_id, badge_id = night.id, slacker.id

    def attendee_night():
        rv = client.get(f"/api/event/1/hotel/attendee/{badge_id}")
        assert rv.status_code == 200
        return [x for x in rv.json["nights"] if x["id"] == night_id][0]

    rv = client.post("/api/event/1/hotel/attendee/approve",
                     json={"badge": badge_id, "room_night": night_id, "approved": True})
    assert rv.status_code == 200 and rv.json["approved"] is True
    assert attendee_night()["approved"] is True

    rv = client.post("/api/event/1/hotel/attendee/assign",
                     json={"badge": badge_id, "room_night": night_id, "assigned": True})
    assert rv.status_code == 200 and rv.json["assigned"] is True
    assert attendee_night()["assigned"] is True
    assignments = db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.badge == badge_id).all()
    assert len(assignments) == 1 and assignments[0].hotel_room is None

    rv = client.post("/api/event/1/hotel/attendee/approve",
                     json={"badge": badge_id, "room_night": night_id, "approved": False})
    assert rv.status_code == 200 and rv.json["approved"] is False
    rv = client.post("/api/event/1/hotel/attendee/assign",
                     json={"badge": badge_id, "room_night": night_id, "assigned": False})
    assert rv.status_code == 200 and rv.json["assigned"] is False
    updated = attendee_night()
    assert updated["approved"] is False
    assert updated["assigned"] is False
    assert db.query(models.RoomNightApproval).filter(
        models.RoomNightApproval.badge == badge_id).count() == 0
    assert db.query(models.RoomNightAssignment).filter(
        models.RoomNightAssignment.badge == badge_id).count() == 0

    # Requested toggle: un-requesting removes the person from the missing list.
    rv = client.post("/api/event/1/hotel/attendee/request",
                     json={"badge": badge_id, "room_night": night_id, "requested": False})
    assert rv.status_code == 200 and rv.json["requested"] is False
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "missing_shifts"})
    assert badge_id not in [x["id"] for x in rv.json["results"]]
    rv = client.post("/api/event/1/hotel/attendee/request",
                     json={"badge": badge_id, "room_night": night_id, "requested": True})
    assert rv.status_code == 200
    rv = client.get("/api/event/1/hotel/attendees",
                    query_string={"filter": "missing_shifts"})
    assert badge_id in [x["id"] for x in rv.json["results"]]


def test_attendee_detail(client):
    """The attendee endpoint returns the schedule, windows, and request summary."""
    import tuber.models as models
    from tuber.database import db

    night, worker, slacker = _seed(db, models)

    rv = client.get(f"/api/event/1/hotel/attendee/{slacker.id}")
    assert rv.status_code == 200
    detail = rv.json
    assert detail["email"] == "noshifts@example.com"
    assert detail["shifts"] == []
    assert detail["rooms"] == []
    assert detail["room_request"]["justification"] == "I help set up the arcade."
    nights = {x["name"]: x for x in detail["nights"]}
    assert nights["Wednesday"]["requested"] is True
    assert nights["Wednesday"]["has_shift"] is False
    assert nights["Wednesday"]["mode"] == "shift_window"
    assert nights["Wednesday"]["shift_starttime"] == "2025-08-07T19:00:00Z"
    assert nights["Wednesday"]["shift_endtime"] == "2025-08-08T13:00:00Z"
    assert nights["Thursday"]["restricted"] is False

    rv = client.get(f"/api/event/1/hotel/attendee/{worker.id}")
    assert rv.status_code == 200
    detail = rv.json
    assert len(detail["shifts"]) == 1
    assert detail["shifts"][0]["job"] == "Setup: Arcade Load-In"
    assert detail["shifts"][0]["department"] == "Arcade"
    assert detail["shifts"][0]["starttime"] == "2025-08-07T20:00:00Z"
    assert detail["shifts"][0]["duration"] == 3 * 3600
    nights = {x["name"]: x for x in detail["nights"]}
    assert nights["Wednesday"]["has_shift"] is True

    rv = client.get("/api/event/1/hotel/attendee/99999")
    assert rv.status_code == 404
