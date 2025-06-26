from tuber import app, config
from flask import request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from passlib.hash import sha256_crypt
from sqlalchemy.orm import joinedload
import datetime
import uuid
from tuber.api import *
import requests


@app.route("/api/event/<int:event>/uber/import_shifts", methods=["POST"])
def import_shifts(event):
    event_obj = db.query(Event).filter(Event.id == event).one()
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }
    depts = db.query(Department).filter(Department.event == event).all()
    for idx, dept in enumerate(depts):
        g.progress(idx / len(depts), status=f"Importing shifts from {dept.name}")
        req = {
            "method": "shifts.lookup",
            "params": {
                "department_id": dept.uber_id
            }
        }
        jobs = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
        db.query(Job).filter(Job.department == dept.id, Job.event == event).delete()
        for job in jobs:
            job_obj = Job(
                name=job["name"],
                description=job["description"],
                department=dept.id,
                event=event
            )
            db.add(job_obj)
            db.flush()
            start_time = datetime.datetime.strptime(job["start_time"], "%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.datetime.strptime(job["end_time"], "%Y-%m-%d %H:%M:%S.%f")
            shift_obj = Shift(
                event=event,
                job=job_obj.id,
                starttime=start_time,
                duration=(end_time-start_time).seconds,
                slots=job["slots"],
                filledslots=job["slots_taken"],
                weighting=1.0
            )
            db.add(shift_obj)
            db.flush()
            for shift in job["shifts"]:
                try:
                    badge = db.query(Badge).filter(Badge.event==event, Badge.uber_id==shift["attendee"]["id"]).one()
                    assignment = ShiftAssignment(
                        event=event,
                        badge=badge.id,
                        shift=shift_obj.id
                    )
                    db.add(assignment)
                except sqlalchemy.exc.NoResultFound:
                    print(f"Failed to find attendee for {shift['attendee']['id']} (Not hotel elligible?)")
    db.commit()
    return "null", 200

def get_nights(url, headers):
    req = {
        "method": "hotel.nights"
    }
    result = requests.post(url, headers=headers,
                           json=req).json()['result']
    dates = {key.lower(): value for key, value in result['dates'].items()}
    lookup = {}
    for idx, name in enumerate(result['names']):
        if not name in dates:
            continue
        newdate = datetime.datetime.strptime(
            dates[name], "%Y-%m-%d") + datetime.timedelta(days=1)
        newdate = newdate.strftime("%Y-%m-%d")
        lookup[newdate] = str(result['order'][idx])
    return lookup

def create_room(url, headers, notes="", message="", locked_in="", nights=None):
    req = {
        "method": "hotel.update_room",
        "params": {
            "notes": notes,
            "message": message,
            "locked_in": locked_in
        }
    }
    if nights != None:
        req['params']['nights'] = ",".join(nights)
    res = requests.post(url, headers=headers, json=req).json()
    return res['result']

def create_request(url, headers, id=None, attendee_id="", nights=None, wanted_roommates="", unwanted_roommates="", special_needs="", approved=True):
    req = {
        "method": "hotel.update_request",
        "params": {
            "attendee_id": attendee_id,
            "wanted_roommates": wanted_roommates,
            "unwanted_roommates": unwanted_roommates,
            "special_needs": special_needs,
            "approved": approved
        }
    }
    if id != None:
        req['params']['id'] = id
    if nights != None:
        req['params']['nights'] = ",".join(nights)
        print(nights, req['params']['nights'])
    res = requests.post(url, headers=headers, json=req).json()['result']
    print(res)
    return res


def assign_roommate(url, headers, room_id="", attendee_id=""):
    req = {
        "method": "hotel.update_assignment",
        "params": {
            "attendee_id": attendee_id,
            "room_id": room_id
        }
    }
    return requests.post(url, headers=headers, json=req).json()['result']

@app.route("/api/event/<int:event>/uber/export_rooms", methods=["POST"])
def export_rooms(event):
    event_obj = db.query(Event).filter(Event.id == event).one()
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }

    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    uber_room_nights = get_nights(event_obj.uber_url, headers)
    room_nights_lookup = {}
    for room_night in room_nights:
        if str(room_night.date) in uber_room_nights.keys():
            room_nights_lookup[room_night.id
                            ] = uber_room_nights[str(room_night.date)]
        else:
            print(f"Could not find uber entry for {room_night.name}")

    rooms = db.query(HotelRoom).filter(HotelRoom.event == event).all()
    assignments = db.query(RoomNightAssignment).filter(RoomNightAssignment.event == event).all()
    badges = db.query(Badge).filter(Badge.event == event).all()

    badges = {x.id: x for x in badges}

    hrr = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event).all()
    hrr = {x.badge: x for x in hrr}
    reqs = {}

    for idx, room in enumerate(rooms):
        g.progress(idx / len(rooms), status=f"Exporting Room {room.name}")
        nights = []
        assign = []
        assigned = []
        for ass in assignments:
            if ass.hotel_room == room.id:
                assign.append(ass)
        for ass in assign:
            if not ass.room_night in nights:
                nights.append(ass.room_night)
        ubernights = [room_nights_lookup[x]
                    for x in nights if x in room_nights_lookup]
        uber_room = create_room(
            event_obj.uber_url,
            headers,
            notes=room.notes,
            message=room.messages,
            locked_in=room.completed,
            nights=ubernights
        )
        for ass in assign:
            badge = ass.badge
            if not badge in reqs.keys():
                req = hrr[badge]
                reqs[badge] = req
                requested_nights = [x.room_night
                                    for x in req.room_night_requests if x.requested]
                req_nights = [room_nights_lookup[x]
                            for x in nights if x in room_nights_lookup and x in requested_nights]
                request = create_request(
                    event_obj.uber_url,
                    headers,
                    hrr[badge].uber_id,
                    attendee_id=badges[badge].uber_id,
                    special_needs=hrr[badge].notes,
                    approved=True,
                    nights=req_nights
                )
                hrr[badge].uber_id = request['id']
                db.add(hrr[badge])
            if not badge in assigned:
                assigned.append(badge)
                try:
                    assignment = assign_roommate(
                        event_obj.uber_url,
                        headers,
                        room_id=uber_room['id'],
                        attendee_id=badges[badge].uber_id
                    )
                except:
                    print(
                        f"Failed to assign roommate {badges[badge].uber_id} ({badges[badge].search_name})")
    db.commit()
    return "null", 200

def export_requests(event, hotel_room_requests):
    event_obj = db.query(Event).filter(Event.id == event).one()
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }

    room_nights = db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()
    uber_room_nights = get_nights(event_obj.uber_url, headers)
    room_nights_lookup = {}
    for room_night in room_nights:
        if room_night.date.strftime("%Y-%m-%d") in uber_room_nights.keys():
            room_nights_lookup[room_night.id
                            ] = uber_room_nights[room_night.date.strftime("%Y-%m-%d")]
        else:
            print(f"Could not find uber entry for {room_night.name}")

    badges = db.query(Badge).filter(Badge.event == event).all()

    badges = {x.id: x for x in badges}

    hrr = {x.badge: x for x in hotel_room_requests}

    for idx, badge in enumerate(hrr.keys()):
        g.progress(idx / len(hrr), status=f"Exporting Request {badges[badge].public_name}")
        req = hrr[badge]
        if req.declined:
            continue
        requested_nights = [x.room_night
                            for x in req.room_night_requests if x.requested]
        if not requested_nights:
            continue
        req_nights = [room_nights_lookup[x]
                    for x in requested_nights if x in room_nights_lookup]
        request = create_request(
            event_obj.uber_url,
            headers,
            hrr[badge].uber_id,
            attendee_id=badges[badge].uber_id,
            special_needs=hrr[badge].notes,
            approved=True,
            nights=req_nights
        )
        req.uber_id = request['id']
        db.add(req)

    db.commit()
    return "null", 200

@app.route("/api/event/<int:event>/uber/export_requests", methods=["POST"])
def export_requests_api(event):
    hrr = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event).all()
    export_requests(event, hrr)
    return "null", 200

def create_attendee(uber_model, event, hotel_eligible=True):
    staff_badge_type = db.query(BadgeType).filter(BadgeType.name == "Staff", BadgeType.event == event).one_or_none()
    if not staff_badge_type:
        staff_badge_type = BadgeType(name="Staff", description="Experienced Volunteers")
        db.flush()
    badge = Badge(
        event=event,
        badge_type=staff_badge_type.id,
        printed_number=uber_model['badge_num'],
        printed_name=uber_model['badge_printed_name'],
        public_name=uber_model['full_name'],
        search_name=uber_model['full_name'].lower(),
        first_name=uber_model['first_name'],
        last_name=uber_model['last_name'],
        legal_name_matches=(not uber_model['legal_name']),
        emergency_contact_name=uber_model['ec_name'],
        emergency_contact_phone=uber_model['ec_phone'],
        phone=uber_model['cellphone'],
        email=uber_model['email'],
        uber_id=uber_model['id']
    )
    db.add(badge)
    db.flush()
    if hotel_eligible:
        hotel_request = HotelRoomRequest(event=event, badge=badge.id)
        db.add(hotel_request)
        db.flush()
    return badge

@app.route("/api/event/<int:event>/uber/sync_attendees", methods=["POST"])
def sync_attendees(event):
    event_obj = db.query(Event).filter(Event.id == event).one()
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }
    if not check_permission("attendee.*.sync"):
        return "", 403
    req = {"method": "hotel.eligible_attendees"}
    eligible = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
    req = {"method": "dept.list"}
    uber_depts = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
    uber_depts_names = {}
    for dept_id in uber_depts:
        uber_depts_names[uber_depts[dept_id]] = dept_id

    changed = False
    for dept in uber_depts.keys():
        department = db.query(Department).filter(Department.uber_id == dept).one_or_none()
        if department:
            if department.name != uber_depts[dept]:
                department.name = uber_depts[dept]
                db.add(department)
                changed = True
    if changed:
        db.commit()

    departments = db.query(Department).filter(Department.event == event).all()
    dept_names = {}
    for dept in departments:
        dept_names[dept.name] = dept

    badges = db.query(Badge).filter(Badge.event == event).options(joinedload(Badge.departments)).all()
    badgelookup = {badge.uber_id: badge for badge in badges}

    counter = 0
    for idx, attendee in enumerate(eligible):
        print(f"Importing {attendee}")
        req = {
            "method": "attendee.search",
            "params": [
                attendee,
                "full"
            ]
        }
        uber_model = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
        if uber_model:
            uber_model = uber_model[0]
        else:
            print(f"Skipping attendee {attendee} since I couldn't find it in Uber")
            continue
        if counter % 10 == 0:
            g.progress(idx / len(eligible), status=f"Checking attendee {uber_model['full_name']}")
        counter += 1
        if attendee in badgelookup:
            badge = badgelookup[attendee]
            if uber_model['full_name'] != badge.public_name or uber_model['legal_name'] != badge.legal_name or uber_model['first_name'] != badge.first_name or uber_model['last_name'] != badge.last_name or badge.search_name != f"{uber_model['first_name']} {uber_model['last_name']}".lower():
                print(f"Updating public name from {badge.public_name} to {uber_model['full_name']}")
                badge.first_name = uber_model['first_name']
                badge.last_name = uber_model['last_name']
                badge.public_name = uber_model['full_name']
                badge.legal_name = uber_model['legal_name']
                badge.search_name = f"{uber_model['first_name']} {uber_model['last_name']}".lower()
                db.add(badge)
        if uber_model['badge_status_label'] == "Deferred":
            if attendee in badgelookup:
                print(f"Deleting deferred attendee {attendee} ({badgelookup[attendee].public_name})")
                rnrs = badgelookup[attendee].room_night_requests
                if any([x.requested for x in rnrs]):
                    print("WARNING: ATTENDEE REQUESTED ROOM NIGHTS")
                #db.delete(badgelookup[attendee])
        else:
            print("  not deferred")
            if not attendee in badgelookup:
                print(f"Missing attendee: {attendee}")
                new_badge = create_attendee(uber_model, event)
                badgelookup[attendee] = new_badge

            badge = badgelookup[attendee]
            for dept_name in uber_model['assigned_depts_labels']:
                print(f"  {dept_name}")
                if not dept_name in dept_names and dept_name in uber_depts_names:
                    new_dept = Department(uber_id=uber_depts_names[dept_name], event=event, name=dept_name)
                    dept_names[dept_name] = new_dept
                    print(f"Creating department {dept_name}")
                    db.add(new_dept)
                if not dept_names[dept_name] in badge.departments:
                    badge.departments.append(dept_names[dept_name])
                    print(f"Adding {badge.public_name} to {dept_name}")

            print("  Removing depts")
            to_remove = []
            for dept in badge.departments:
                if not dept.name in uber_model['assigned_depts_labels']:
                    to_remove.append(dept)
            for dept in to_remove:
                print(f"Removing {badge.public_name} from {dept.name}")
                badge.departments.remove(dept)
            db.add(badge)
        db.commit()
    print("done")
    return "{}", 200

@app.route("/api/uber/<string:slug>/login", methods=["POST"])
def staffer_auth(slug):
    event_obj = db.query(Event).filter(Event.uber_slug == slug).one()
    if not User.query.first():
        return "You must set up this server before using this method to log in.", 403
    req = {
        "method": "attendee.export",
        "params": [
            request.json['token'],
            "full"
        ]
    }
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }
    results = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
    result = results['attendees']
    if len(result) == 0:
        return "no attendee found", 403
    if len(result) > 1:
        return "too many attendees found", 403
    result = result[0]
    if not 'id' in result:
        return "no id", 403
    uber_id = result['id']
    if uber_id != request.json['token']:
        return "wrong token", 403
    if result['badge_status_label'] == "Deferred":
        return "Badge is deferred", 403

    badge = db.query(Badge).filter(Badge.uber_id == uber_id).one_or_none()
    hotel_request = None
    if badge:
        hotel_request = db.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if not hotel_request or not badge:
        req = {"method": "hotel.eligible_attendees"}
        eligible = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
        if len(eligible) == 0:
            return "Failed to load eligible attendees", 403
        if not uber_id in eligible:
            return "You are not eligible", 403
    if not badge:
        staff_badge_type = db.query(BadgeType).filter(BadgeType.event == event_obj.id, BadgeType.name == "Staff").one_or_none()
        if not staff_badge_type:
            staff_badge_type = BadgeType(name="Staff", description="Experienced Volunteers", event=event_obj.id)
            db.flush()
        badge = Badge(
            event=event_obj.id,
            badge_type=staff_badge_type.id,
            printed_number=result['badge_num'],
            printed_name=result['badge_printed_name'],
            public_name=f"{result['first_name']} {result['last_name']}",
            search_name=f"{result['first_name']} {result['last_name']}".lower(),
            first_name=result['first_name'],
            last_name=result['last_name'],
            legal_name=result['legal_name'],
            legal_name_matches=(not result['legal_name']),
            emergency_contact_name=result['ec_name'],
            emergency_contact_phone=result['ec_phone'],
            phone=result['cellphone'],
            email=result['email'],
            uber_id=result['id']
        )

    departments = db.query(Department).filter(Department.event == event_obj.id).all()
    dept_by_uber_id = {x.uber_id: x for x in departments}

    for dept_uber_id, dept_name in result['assigned_depts'].items():
        if not dept_uber_id in dept_by_uber_id:
            new_dept = Department(uber_id=dept_uber_id, event=event_obj.id, name=dept_name)
            db.add(new_dept)
            badge.departments.append(new_dept)
            dept_by_uber_id[dept_uber_id] = new_dept
        else:
            dept = dept_by_uber_id[dept_uber_id]
            if dept.name != dept_name:
                dept.name = dept_name
                db.add(dept)
            badge.departments.append(dept_by_uber_id[dept_uber_id])
    db.add(badge)
    db.flush()

    if not hotel_request:
        hotel_request = HotelRoomRequest(event=event_obj.id, badge=badge.id)
        db.add(hotel_request)
        db.flush()

    permissions = {
        "event": {
            str(event_obj.id): [
                "rooming.*.request",
                "badge.*.searchname",
                f"hotel_room_request.{hotel_request.id}.write",
                "hotel_room_block.*.read",
                "hotel_location.*.read",
                "hotel_room_night.*.read",
            ],
            "*": [
                "event.*.read",
                f"badge.{badge.id}.read",
                "department.*.read"
            ]
        },
        "department": {
            str(event_obj.id): {}
        }
    }

    for dept_uber_id in result['checklist_admin_depts'].keys():
        permissions["department"][str(event_obj.id)][str(dept_by_uber_id[dept_uber_id].id)] = [
            "department.*.checklist_admin",
            "hotel_request.*.approve"
        ]

    session = Session(badge=badge.id, secret=str(uuid.uuid4()), permissions=json.dumps(permissions), last_active=datetime.datetime.now())
    db.add(session)
    db.commit()
    response = jsonify(session.secret)
    response.set_cookie('session', session.secret)
    return response