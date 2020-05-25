import datetime
import json

def test_schedule_change(client):
    """Make sure that creating an scheduleevent on a schedule creates a shift on the associated job"""
    schedule = client.post("/api/events/1/schedules", json={
        "name": "Shift Schedule",
        "description": "A schedule for shifts!"
    }).json
    assert(schedule['name'] == "Shift Schedule")

    eventstart = datetime.datetime.utcnow()
    scheduleevent = client.post("/api/scheduleevents", json={
        "name": "The big panel",
        "description": "You know the one",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(scheduleevent['name'] == "The big panel")

    job = client.post("/api/events/1/jobs", json={
        "name": "Do a thing",
        "description": "Help make the thing happen, at the place",
        "documentation": "Here's how to do the thing",
        "method": {
            "name": "copy",
            "slots": 4
        },
        "schedules": [
            schedule['id']
        ]
    }).json
    assert(job['name'] == "Do a thing")

    shifts = client.get("/api/shifts", query_string={"full": True}).json
    assert(len(shifts) == 1)
    assert(shifts[0]['starttime'] == scheduleevent['starttime'])
    assert(shifts[0]['duration'] == scheduleevent['duration'])
    assert(shifts[0]['slots'] == 4)

    newevent = client.post("/api/scheduleevents", json={
        "name": "Another cool panel",
        "description": "You probably don't know about this one yet",
        "starttime": (eventstart + datetime.timedelta(seconds=3600)).isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(newevent['name'] == "Another cool panel")

    shifts = client.get("/api/shifts", query_string={"full": True}).json
    assert(len(shifts) == 2)

    client.delete("/api/scheduleevents/"+str(scheduleevent['id']))

    events = client.get("/api/scheduleevents", query_string={"full": True}).json
    assert(len(events) == 1)

    shifts = client.get("/api/shifts", query_string={"full": True}).json
    assert(len(shifts) == 1)

def test_signup_persistence(client):
    """Make sure that a signup survives a shift being deleted and coming back"""
    schedule = client.post("/api/events/1/schedules", json={
        "name": "Shift Schedule",
        "description": "A schedule for shifts!"
    }).json
    assert(schedule['name'] == "Shift Schedule")

    eventstart = datetime.datetime.utcnow()
    scheduleevent = client.post("/api/scheduleevents", json={
        "name": "The big panel",
        "description": "You know the one",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(scheduleevent['name'] == "The big panel")

    department = client.post("/api/events/1/departments", json={
        "name": "Product Testing"
    }).json
    assert(department['name'] == "Product Testing")

    role = client.post("/api/roles", json={
        "name": "Manager",
        "description": "Allowed to sign up for manager shifts",
        "event": 1
    }).json
    assert(role['name'] == "Manager")

    user = client.post("/api/users", json={
        "username": "testing",
        "email": "test@test.com",
        "active": True
    }).json
    assert(user['username'] == "testing")

    grant = client.post("/api/grants", json={
        "user": user['id'],
        "role": role['id'],
        "department": department['id']
    }).json
    assert(grant['user'] == user['id'])

    job = client.post("/api/events/1/jobs", json={
        "name": "Do a thing",
        "description": "Help make the thing happen, at the place",
        "documentation": "Here's how to do the thing",
        "method": {
            "name": "copy",
            "slots": 4
        },
        "schedules": [
            schedule['id']
        ],
        "roles": [
            role['id']
        ],
        "department": department['id']
    }).json
    assert(job['name'] == "Do a thing")
    assert(job['department'] == department['id'])

    badge = client.post("/api/events/1/badges", json={
        "legal_name": "Test User",
        "user": user['id'],
        "departments": [
            department['id']
        ]
    }).json
    assert(badge['legal_name'] == "Test User")

    jobs = client.get("/api/events/1/jobs/available", query_string={"badge": badge['id']}).json
    assert(len(jobs) == 1)
    assert(len(jobs[0]['shifts']) == 1)

    signup = client.post("/api/events/1/shifts/"+str(jobs[0]['shifts'][0]['id'])+"/signup", json={
        "badge": badge['id']
    }).json
    assert(signup['shift'])

    assignedshifts = client.get("/api/shiftassignments", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 1)

    client.delete("/api/scheduleevents/"+str(scheduleevent['id']))

    assignedshifts = client.get("/api/shiftassignments", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 0)

    replacement_scheduleevent = client.post("/api/scheduleevents", json={
        "name": "A similar large panel",
        "description": "It starts the same time as the old one, and is just as long!",
        "starttime": eventstart.isoformat(),
        "duration": 3600,
        "schedule": schedule['id']
    }).json
    assert(replacement_scheduleevent['name'] == "A similar large panel")

    assignedshifts = client.get("/api/shiftassignments", query_string={"badge": badge['id']}).json
    assert(len(assignedshifts) == 1)
