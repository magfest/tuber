def _seed_preview(db, models):
    """Two badges with distinct names for filter/render checks."""
    alice = models.Badge(event=1, public_name="Alice Aardvark",
                         first_name="Alice", last_name="Aardvark",
                         search_name="alice aardvark",
                         email="alice@example.com")
    bob = models.Badge(event=1, public_name="Bob Badger",
                       first_name="Bob", last_name="Badger",
                       search_name="bob badger",
                       email="bob@example.com")
    db.add(alice)
    db.add(bob)
    db.commit()
    return alice, bob


def test_email_preview(client):
    """The preview reports filter matches and renders for one attendee."""
    import tuber.models as models
    from tuber.database import db

    alice, bob = _seed_preview(db, models)

    rv = client.post("/api/event/1/email/preview", json={
        "code": 'return function(c) return c.badge.first_name == "Alice" end',
        "subject": "Hi {{ badge.first_name }}",
        "body": "You requested {{ requested_nights | length }} night(s).",
    })
    assert rv.status_code == 200
    data = rv.json
    assert data["total"] == 2
    assert data["matched_count"] == 1
    assert data["showing"] == "matched"
    assert data["attendees"][0]["name"] == "Alice Aardvark"
    assert data["filter_errors"] == []
    assert data["preview"]["subject"] == "Hi Alice"
    assert data["preview"]["body"] == "You requested 0 night(s)."
    assert data["render_error"] is None
    # The variables card covers the full context for the previewed attendee.
    assert data["variables"]["badge"] == "Alice Aardvark"
    assert data["variables"]["requested_nights"] == []

    # Non-matches view lists everyone the filter excludes.
    rv = client.post("/api/event/1/email/preview", json={
        "code": 'return function(c) return c.badge.first_name == "Alice" end',
        "subject": "", "body": "", "show": "unmatched",
    })
    data = rv.json
    assert data["showing"] == "unmatched"
    assert [x["name"] for x in data["attendees"]] == ["Bob Badger"]
    assert data["matched_count"] == 1

    # Referenced symbols become debugging columns with per-attendee values.
    rv = client.post("/api/event/1/email/preview", json={
        "code": 'return function(c) return c.requested_nights == nil end',
        "subject": "", "body": "", "show": "unmatched",
    })
    data = rv.json
    assert data["filter_errors"] == []
    assert data["symbols"] == ["requested_nights"]
    assert data["matched_count"] == 0
    assert len(data["attendees"]) == 2
    assert data["attendees"][0]["pertinent"] == {"requested_nights": []}

    # Previewing against a specific (even unmatched) attendee.
    rv = client.post("/api/event/1/email/preview", json={
        "code": 'return function(c) return c.badge.first_name == "Alice" end',
        "subject": "Hi {{ badge.first_name }}",
        "body": "",
        "badge": bob.id,
    })
    assert rv.json["preview"]["subject"] == "Hi Bob"

    # Broken Lua reports instead of failing.
    rv = client.post("/api/event/1/email/preview", json={
        "code": "return function(c", "subject": "", "body": ""})
    assert rv.status_code == 200
    assert rv.json["filter_errors"]

    # Broken Jinja reports a render error but still identifies matches.
    rv = client.post("/api/event/1/email/preview", json={
        "code": "return function(c) return true end",
        "subject": "{{ badge.first_name", "body": ""})
    assert rv.json["matched_count"] == 2
    assert rv.json["render_error"]


def test_email_preview_event_level_approval(client):
    """Badges with department-less (event-level) approvals must not break
       email context building — previously a KeyError: None."""
    import tuber.models as models
    from tuber.database import db

    import datetime
    alice, bob = _seed_preview(db, models)
    night = models.HotelRoomNight(event=1, name="Setup",
                                  date=datetime.date(2025, 8, 6),
                                  restriction_mode="manual")
    block = models.HotelRoomBlock(event=1, name="General", description="")
    db.add(night)
    db.add(block)
    db.flush()
    room = models.HotelRoom(event=1, name="Room 1", hotel_block=block.id,
                            completed=True)
    db.add(room)
    db.add(models.HotelRoomRequest(event=1, badge=alice.id))
    db.flush()
    db.add(models.RoomNightRequest(event=1, badge=alice.id,
                                   room_night=night.id, requested=True))
    # The admin approve toggle creates approvals with department=None.
    db.add(models.RoomNightApproval(event=1, badge=alice.id,
                                    room_night=night.id, department=None,
                                    approved=True))
    db.add(models.RoomNightAssignment(event=1, badge=alice.id,
                                      room_night=night.id, hotel_room=room.id))
    db.commit()

    rv = client.post("/api/event/1/email/preview", json={
        "code": """return function(context)
  send = false
  if (context.hotel_rooms) then
      for room in python.iter(context.hotel_rooms) do
          if (room.completed ~= true) then
              return false
          else
              if (room.hotel_block_name == "General") then
                  send = true
              end
          end
      end
      return send
  end
  return false
end""",
        "subject": "Your room in {{ hotel_rooms[0].hotel_block_name }}",
        "body": "Approved by: {{ approving_depts }}",
    })
    assert rv.status_code == 200
    data = rv.json
    assert data["filter_errors"] == []
    assert data["matched_count"] == 1
    assert data["attendees"][0]["name"] == "Alice Aardvark"
    assert data["preview"]["subject"] == "Your room in General"
    # Event-level approvals have no department to name.
    assert data["preview"]["body"] == "Approved by: "
    # The filter only references hotel_rooms — that's the debug column.
    assert data["symbols"] == ["hotel_rooms"]
    assert data["attendees"][0]["pertinent"]["hotel_rooms"][0]["hotel_block_name"] == "General"


def test_email_preview_render_only(client):
    """Template-only refreshes render against one attendee without running
       the filter over everyone."""
    import tuber.models as models
    from tuber.database import db

    alice, bob = _seed_preview(db, models)

    rv = client.post("/api/event/1/email/preview", json={
        "code": "this is not even lua",
        "subject": "Hi {{ badge.first_name }}",
        "body": "Bye {{ badge.last_name }}",
        "badge": bob.id,
        "evaluate_filter": False,
    })
    assert rv.status_code == 200
    data = rv.json
    # The broken filter code is never evaluated in render-only mode.
    assert data["render_only"] is True
    assert "matched_count" not in data
    assert data["preview"]["subject"] == "Hi Bob"
    assert data["preview"]["body"] == "Bye Badger"
    assert data["variables"]["badge"] == "Bob Badger"

    # Unknown badge is a 404, and a render error reports cleanly.
    rv = client.post("/api/event/1/email/preview", json={
        "subject": "", "body": "", "badge": 99999, "evaluate_filter": False})
    assert rv.status_code == 404
    rv = client.post("/api/event/1/email/preview", json={
        "subject": "{{ nope(", "body": "", "badge": alice.id,
        "evaluate_filter": False})
    assert rv.status_code == 200
    assert rv.json["render_error"]


def test_email_import(client):
    """Templates and sources copy from another event, inactive, with source
       references remapped and existing names skipped."""
    import tuber.models as models
    from tuber.database import db

    other = models.Event(name="Last Year", description="")
    db.add(other)
    db.flush()
    source = models.EmailSource(
        event=other.id, name="Main Sender", address="noreply@example.com",
        region="us-east-1", ses_access_key="key", ses_secret_key="secret",
        active=True)
    db.add(source)
    db.flush()
    db.add(models.Email(
        event=other.id, name="Welcome", description="Welcome email",
        code="return function(c) return true end", subject="Welcome!",
        body="Hello {{ badge.first_name }}", active=True, send_once=True,
        source=source.id))
    db.add(models.Email(
        event=other.id, name="Reminder", description="", code="",
        subject="Reminder", body="", active=False, send_once=False,
        source=None))
    db.commit()

    rv = client.post("/api/event/1/email/import", json={
        "from_event": other.id, "emails": True, "sources": True})
    assert rv.status_code == 200
    assert rv.json["sources"] == 1
    assert rv.json["emails"] == 2
    assert rv.json["skipped"] == []

    copied_source = db.query(models.EmailSource).filter(
        models.EmailSource.event == 1,
        models.EmailSource.name == "Main Sender").one()
    # Copies arrive inactive so nothing sends until reviewed.
    assert copied_source.active is False
    assert copied_source.ses_access_key == "key"
    welcome = db.query(models.Email).filter(
        models.Email.event == 1, models.Email.name == "Welcome").one()
    assert welcome.active is False
    assert welcome.send_once is True
    assert welcome.source == copied_source.id
    assert welcome.body == "Hello {{ badge.first_name }}"

    # Importing again skips everything by name.
    rv = client.post("/api/event/1/email/import", json={
        "from_event": other.id, "emails": True, "sources": True})
    assert rv.json["sources"] == 0
    assert rv.json["emails"] == 0
    assert len(rv.json["skipped"]) == 3

    # Importing from the same event is rejected.
    rv = client.post("/api/event/1/email/import", json={"from_event": 1})
    assert rv.status_code == 400
