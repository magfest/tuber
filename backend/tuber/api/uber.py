from tuber import app, config
from flask import request, jsonify
from tuber.models import *
from tuber.permissions import *
from tuber.database import db
from passlib.hash import sha256_crypt
from sqlalchemy.orm import joinedload
import datetime
import hashlib
import json
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
            start_time = datetime.datetime.strptime(job["start_time"], "%Y-%m-%dT%H:%M:%S%z")
            end_time = datetime.datetime.strptime(job["end_time"], "%Y-%m-%dT%H:%M:%S%z")
            shift_obj = Shift(
                event=event,
                job=job_obj.id,
                starttime=start_time,
                duration=int((end_time-start_time).total_seconds()),
                slots=job["slots"],
                filledslots=job["slots_taken"],
                weighting=1.0
            )
            db.add(shift_obj)
            db.flush()
            for shift in job.get("shifts", []):
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


class UberError(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def update_assignment(url, headers, **params):
    req = {
        "method": "hotel.update_assignment",
        "params": params
    }
    response = requests.post(url, headers=headers, json=req, timeout=60)
    res = response.json()
    if res.get('error'):
        raise UberError(response.status_code, res['error'].get('message', 'Unknown error'))
    return res['result']

@app.route("/api/event/<int:event>/uber/export_rooms", methods=["POST"])
def export_rooms(event):
    """Export each room to Uber as one "Staff Crash Space" room assignment.

    The room's roommates go along as its occupants, each with their own
    dates. Running it again is safe: each room keeps one Uber assignment
    (HotelRoom.uber_id, chosen here and saved before Uber is called), a room
    that has not changed since it was last sent is left alone, and a room
    that has been emptied gets cancelled in Uber.
    """
    event_obj = db.query(Event).filter(Event.id == event).one()
    url = event_obj.uber_url
    headers = {
        'X-Auth-Token': event_obj.uber_apikey
    }

    # Plain values, since the commit after each room expires loaded objects.
    night_dates = {x.id: x.date for x in db.query(HotelRoomNight).filter(HotelRoomNight.event == event).all()}
    inventory_ids = {x.id: x.uber_inventory_id for x in db.query(HotelLocation).filter(HotelLocation.event == event).all()}
    badge_uber_ids = {x.id: x.uber_id for x in db.query(Badge).filter(Badge.event == event).all()}
    rooms = [(x.id, x.name, x.notes, x.hotel_location, x.uber_id, x.uber_export_hash)
             for x in db.query(HotelRoom).filter(HotelRoom.event == event).order_by(HotelRoom.id).all()]

    room_stays = {}
    for ass in db.query(RoomNightAssignment).filter(RoomNightAssignment.event == event).all():
        if badge_uber_ids.get(ass.badge) and night_dates.get(ass.room_night):
            room_stays.setdefault(ass.hotel_room, {}).setdefault(ass.badge, []).append(night_dates[ass.room_night])

    def save(room_id, **values):
        db.query(HotelRoom).filter(HotelRoom.id == room_id).update(values)
        db.commit()

    summary = {"exported": 0, "unchanged": 0, "cancelled": 0, "skipped": [], "inactive": [], "failed": []}
    one_day = datetime.timedelta(days=1)

    for idx, (room_id, name, notes, location, uber_id, exported_hash) in enumerate(rooms):
        g.progress(idx / len(rooms), status=f"Exporting Room {name}")
        stays = room_stays.get(room_id)
        try:
            if not stays:
                if uber_id:
                    try:
                        update_assignment(url, headers, id=uber_id, status="Cancelled")
                    except UberError as e:
                        # A 404 means the room never reached Uber, so there is nothing to cancel.
                        if e.status != 404:
                            raise
                    save(room_id, uber_id=None, uber_export_hash=None)
                    summary["cancelled"] += 1
                continue

            if not inventory_ids.get(location):
                summary["skipped"].append(f"{name}: its location has no Uber inventory ID")
                continue

            # The night of date X is slept X to X+1, so check-out is the day after the last night.
            occupants = [{
                "attendee_id": badge_uber_ids[badge],
                "check_in_date": str(min(dates)),
                "check_out_date": str(max(dates) + one_day)
            } for badge, dates in sorted(stays.items())]
            all_dates = [x for dates in stays.values() for x in dates]
            params = {
                # Uber needs one name on the reservation; any roommate will do.
                "attendee_id": occupants[0]["attendee_id"],
                "inventory_id": inventory_ids[location],
                "assignment_reason": "Staff Crash Space",
                "assigned_check_in_date": str(min(all_dates)),
                "assigned_check_out_date": str(max(all_dates) + one_day),
                "special_requests": notes or "",
                "occupants": occupants
            }
            fingerprint = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
            if uber_id and fingerprint == exported_hash:
                # Leaving it alone also keeps any edits made to it in Uber.
                summary["unchanged"] += 1
                continue

            if not uber_id:
                # Saved before Uber is called, so a retry after a lost reply reuses the same Uber room.
                db.query(HotelRoom).filter(HotelRoom.id == room_id, HotelRoom.uber_id == None).update(
                    {"uber_id": str(uuid.uuid4())})
                db.commit()
                uber_id = db.query(HotelRoom.uber_id).filter(HotelRoom.id == room_id).scalar()
            if not exported_hash:
                # Only until the first export lands, so a billing change made in Uber survives a re-export.
                params["payment_type"] = "masterbill"
            result = update_assignment(url, headers, id=uber_id, create_missing=True, **params)
            save(room_id, uber_export_hash=fingerprint)
            if result.get("is_live") is False:
                summary["inactive"].append(f"{name}: updated, but it is cancelled in Uber")
            else:
                summary["exported"] += 1
        except Exception as e:
            db.rollback()
            print(f"Failed to export room {name}: {e}")
            summary["failed"].append(f"{name}: {e}")
    return jsonify(summary), 200

def export_requests(event, hotel_room_requests):
    event_obj = db.query(Event).filter(Event.id == event).one()
    if not event_obj.uber_url:
        # Not every event syncs to Uber; saving a request locally is fine.
        return
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
        #request = create_request(
        #    event_obj.uber_url,
        #    headers,
        #    hrr[badge].uber_id,
        #    attendee_id=badges[badge].uber_id,
        #    special_needs=hrr[badge].notes,
        #    approved=True,
        #    nights=req_nights
        #)
        #req.uber_id = request['id']
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
                db.delete(badgelookup[attendee])
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
