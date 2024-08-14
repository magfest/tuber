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
    for dept in depts:
        req = {
            "method": "shifts.lookup",
            "params": {
                "department_id": dept.uber_id
            }
        }
        shifts = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
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
        if room_night.date in uber_room_nights.keys():
            room_nights_lookup[room_night['id']
                            ] = uber_room_nights[room_night['date']]
        else:
            print(f"Could not find uber entry for {room_night['name']}")
    print(room_nights_lookup)

    rooms = db.query(HotelRoom).filter(HotelRoom.event == event).all()
    assignments = db.query(RoomNightAssignment).filter(RoomNightAssignment.event == event).all()
    badges = db.query(Badge).filter(Badge.event == event).all()

    badges = {x.id: x for x in badges}

    hrr = db.query(HotelRoomRequest).filter(HotelRoomRequest.event == event).all()
    #hrr = get(f"{BASE_URL}/hotel_room_request?full=true&deep=true")
    hrr = {x.badge: x for x in hrr}
    reqs = {}

    for room in rooms:
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
                hrr.uber_id = request['id']
                db.add(hrr)
                print(request)
            if not badge in assigned:
                assigned.append(badge)
                try:
                    assignment = assign_roommate(
                        event_obj.uber_url,
                        headers,
                        room_id=uber_room['id'],
                        attendee_id=badges[badge].uber_id
                    )
                    print(assignment)
                except:
                    print(
                        f"Failed to assign roommate {badges[badge].uber_id} ({badges[badge].search_name})")
    db.commit()
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

    departments = db.query(Department).filter(Department.event == event).all()
    dept_names = {}
    for dept in departments:
        dept_names[dept.name] = dept

    badges = db.query(Badge).filter(Badge.event == event).options(joinedload(Badge.departments)).all()
    badgelookup = {badge.uber_id: badge for badge in badges}

    for attendee in eligible:
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
        if attendee in badgelookup:
            badge = badgelookup[attendee]
            if uber_model['full_name'] != badge.public_name:
                print(f"Updating public name from {badge.public_name} to {uber_model['full_name']}")
                badge.first_name = uber_model['first_name']
                badge.last_name = uber_model['last_name']
                badge.public_name = uber_model['full_name']
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
        print("End loop")
        db.commit()
    print("done")
    return "", 200

@app.route("/api/uber/<string:slug>/login", methods=["POST"])
def staffer_auth(slug):
    event_obj = db.query(Event).filter(Event.uber_slug == slug).one()
    if not User.query.first():
        return "You must set up this server before using this method to log in.", 403
    req = {
        "method": "attendee.search",
        "params": [
            request.json['token'],
            "full"
        ]
    }
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }
    results = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
    if len(results) == 0:
        return "no result", 403
    result = results[0]
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
            public_name=result['full_name'],
            search_name=result['full_name'].lower(),
            first_name=result['first_name'],
            last_name=result['last_name'],
            legal_name_matches=(not result['legal_name']),
            emergency_contact_name=result['ec_name'],
            emergency_contact_phone=result['ec_phone'],
            phone=result['cellphone'],
            email=result['email'],
            uber_id=result['id']
        )

        req = {
            "method": "dept.list",
            "params": []
        }
        uber_depts = requests.post(event_obj.uber_url, headers=headers, json=req).json()['result']
        uber_depts_names = {}
        for dept_id in uber_depts:
            uber_depts_names[uber_depts[dept_id]] = dept_id

        departments = db.query(Department).filter(Department.event == event_obj.id).all()
        dept_names = {}
        for dept in departments:
            dept_names[dept.name] = dept

        for dept_name in result['assigned_depts_labels']:
            if not dept_name in dept_names and dept_name in uber_depts_names:
                new_dept = Department(uber_id=uber_depts_names[dept_name], event=event_obj.id, name=dept_name)
                db.add(new_dept)
                badge.departments.append(new_dept)
            elif dept_name in dept_names:
                badge.departments.append(dept_names[dept_name])
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
        "department": {}
    }

    for department in badge.departments:
        req = {
            "method": "dept.members",
            "params": {
                "department_id": department.uber_id
            }
        }
        result = requests.post(event_obj.uber_url, headers=headers, json=req).json()
        if 'error' in result:
            print(f"Could not locate {department.name} ({department.uber_id})")
            continue
        uber_dept_members = result['result']
        for attendee in uber_dept_members['checklist_admins']:
            if attendee['id'] == badge.uber_id:
                if not str(event_obj.id) in permissions["department"]:
                    permissions["department"][str(event_obj.id)] = {}
                permissions["department"][str(event_obj.id)][str(department.id)] = [
                    f"department.*.checklist_admin",
                    "hotel_request.*.approve"
                ]

    session = Session(badge=badge.id, secret=str(uuid.uuid4()), permissions=json.dumps(permissions), last_active=datetime.datetime.now())
    db.add(session)
    db.commit()
    response = jsonify(session.secret)
    response.set_cookie('session', session.secret)
    return response