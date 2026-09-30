from tests.test_restriction_modes import _seed


def test_rewritten_relationships_load(client):
    """The relationships ported from string expressions to lambdas for
       SQLAlchemy 2.1, plus the distinct roommates link, still resolve and
       return the right rows."""
    import tuber.models as models
    from tuber.database import db

    s = _seed(db, models)
    event = db.get(models.Event, 1)
    worker, grinder, slacker = s["worker"], s["grinder"], s["slacker"]
    window, hours, manual, open_night = s["window"], s["hours"], s["manual"], s["open"]

    # Event.unrestricted_nights: only the night with no restriction.
    assert [n.id for n in event.unrestricted_nights] == [open_night.id]

    # Badge.shift_overlap_nights: the worker's shift sits inside the window
    # night; the grinder's shift is outside it; the slacker has none.
    assert {n.id for n in worker.shift_overlap_nights} == {window.id}
    assert list(grinder.shift_overlap_nights) == []
    assert list(slacker.shift_overlap_nights) == []

    # Badge.manually_approved_nights: only rows with approved=True count.
    db.add(models.RoomNightApproval(
        event=1, badge=slacker.id, room_night=manual.id,
        department=s["department"].id, approved=True))
    db.add(models.RoomNightApproval(
        event=1, badge=slacker.id, room_night=hours.id,
        department=s["department"].id, approved=False))
    db.commit()
    assert {n.id for n in slacker.manually_approved_nights} == {manual.id}

    # HotelRoom.roommates: one entry per person however many nights they
    # hold, and room-less grants never appear.
    room = models.HotelRoom(event=1, name="201")
    db.add(room)
    db.flush()
    for night in (window, hours):
        db.add(models.RoomNightAssignment(
            event=1, badge=worker.id, room_night=night.id, hotel_room=room.id))
    db.add(models.RoomNightAssignment(
        event=1, badge=grinder.id, room_night=open_night.id, hotel_room=None))
    db.commit()
    assert [b.id for b in room.roommates] == [worker.id]
