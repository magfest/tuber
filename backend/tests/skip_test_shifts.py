import datetime
import json

def test_schedule_change(client):
    """Make sure that creating an scheduleevent on a schedule creates a shift on the associated job"""
    schedule = client.post("/api/event/1/schedule", json={
        "name": "Shift Schedule",
        "description": "A schedule for shifts!"
    }).json
    assert(schedule['name'] == "Shift Schedule")

    eventstart = datetime.datetime.utcnow()
    scheduleevent = client.post("/api/event/1/schedule_event", json={
        "name": "The big panel",
        "description": "You know the one",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(scheduleevent['name'] == "The big panel")

    department = client.post("/api/event/1/department", json={
        "name": "Product Testing"
    }).json
    assert(department['name'] == "Product Testing")

    job = client.post("/api/event/1/job", json={
        "name": "Do a thing",
        "description": "Help make the thing happen, at the place",
        "documentation": "Here's how to do the thing",
        "department": department['id'],
        "method": {
            "name": "copy",
            "slots": 4
        },
        "schedules": [
            schedule['id']
        ]
    }).json
    assert(job['name'] == "Do a thing")

    shifts = client.get("/api/event/1/shift").json
    assert(len(shifts) == 1)
    assert(shifts[0]['starttime'] == scheduleevent['starttime'])
    assert(shifts[0]['duration'] == scheduleevent['duration'])
    assert(shifts[0]['slots'] == 4)

    newevent = client.post("/api/event/1/schedule_event", json={
        "name": "Another cool panel",
        "description": "You probably don't know about this one yet",
        "starttime": (eventstart + datetime.timedelta(seconds=3600)).isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(newevent['name'] == "Another cool panel")

    shifts = client.get("/api/event/1/shift").json
    assert(len(shifts) == 2)

    client.delete("/api/event/1/schedule_event/"+str(scheduleevent['id']))

    events = client.get("/api/event/1/schedule_event").json
    assert(len(events) == 1)

    shifts = client.get("/api/event/1/shift").json
    assert(len(shifts) == 1)

def test_signup_persistence(client):
    """Make sure that a signup survives a shift being deleted and coming back"""
    schedule = client.post("/api/event/1/schedule", json={
        "name": "Shift Schedule",
        "description": "A schedule for shifts!"
    }).json
    assert(schedule['name'] == "Shift Schedule")

    eventstart = datetime.datetime.utcnow()
    scheduleevent = client.post("/api/event/1/schedule_event", json={
        "name": "The big panel",
        "description": "You know the one",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(scheduleevent['name'] == "The big panel")

    department = client.post("/api/event/1/department", json={
        "name": "Product Testing"
    }).json
    assert(department['name'] == "Product Testing")

    role = client.post("/api/event/1/department_role", json={
        "name": "Manager",
        "description": "Allowed to sign up for manager shifts"
    }).json
    assert(role['name'] == "Manager")

    user = client.post("/api/user", json={
        "username": "testing",
        "email": "test@test.com",
        "active": True
    }).json
    assert(user['username'] == "testing")

    grant = client.post("/api/event/1/department_grant", json={
        "user": user['id'],
        "role": role['id'],
        "department": department['id']
    }).json
    assert(grant['user'] == user['id'])

    job = client.post("/api/event/1/job", json={
        "name": "Do a thing",
        "description": "Help make the thing happen, at the place",
        "documentation": "Here's how to do the thing",
        "department": department['id'],
        "sticky": False,
        "method": {
            "name": "copy",
            "slots": 4
        },
        "schedules": [
            schedule['id']
        ]
    })
    assert job.status_code == 200
    job = job.json
    assert(job['name'] == "Do a thing")
    assert(job['department'] == department['id'])

    badge = client.post("/api/event/1/badge", json={
        "legal_name": "Test User",
        "user": user['id'],
        "departments": [
            department['id']
        ]
    }).json
    assert(badge['legal_name'] == "Test User")

    jobs = client.get("/api/event/1/job/available", query_string={"badge": badge['id']}).json
    assert(len(jobs) == 1)
    assert(len(jobs[0]['shifts']) == 1)

    signup = client.post("/api/event/1/shift/"+str(jobs[0]['shifts'][0]['id'])+"/signup", json={
        "badge": badge['id']
    }).json
    assert(signup['shift'])

    assignedshifts = client.get("/api/event/1/shift_assignment", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 1)

    client.delete("/api/event/1/schedule_event/"+str(scheduleevent['id']))

    assignedshifts = client.get("/api/event/1/shift_assignment", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 0)

    replacement_scheduleevent = client.post("/api/event/1/schedule_event", json={
        "name": "A similar large panel",
        "description": "It starts the same time as the old one, and is just as long!",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(replacement_scheduleevent['name'] == "A similar large panel")

    assignedshifts = client.get("/api/event/1/shift_assignment", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 1)
