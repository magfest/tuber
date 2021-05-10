from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify, Response, escape
from tuber.models import *
from tuber.permissions import *
from sqlalchemy import or_
from rq import Queue
import sqlalchemy
import requests
import datetime
import random
import names
import uuid
import csv
import io

@app.route("/api/importer/csv", methods=["GET", "POST"])
def csv_import():
    if request.method == "GET":
        if not check_permission("export.csv"):
            return "Permission Denied", 403
        export_type = request.args['csv_type']
        model = globals()[export_type]
        data = db.session.query(model).all()
        cols = model.__table__.columns.keys()
        def generate():
            yield ','.join(cols)+"\n"
            for row in data:
                yield ','.join([str(getattr(row, x)) for x in cols])+"\n"
        response = Response(generate(), mimetype="text/csv")
        response.headers.set('Content-Disposition', 'attachment; filename={}.csv'.format(export_type))
        return response
    elif request.method == "POST":
        if not check_permission("import.csv"):
            return "Permission Denied", 403
        import_type = request.form['csv_type']
        model = globals()[import_type]
        raw_import = request.form['raw_import'].lower().strip() == "true"
        full_import = request.form['full_import'].lower().strip() == "true"
        file = request.files['files']
        data = file.read().decode('UTF-8').replace("\r\n", "\n")
        if full_import:
            db.session.query(model).delete()
        rows = data.split("\n")
        cols = rows[0].split(",")
        rows = rows[1:]
        def convert(key, val):
            col = model.__table__.columns[key]
            if col.nullable:
                if val == 'None':
                    return None
            coltype = type(col.type)
            if coltype is sqlalchemy.sql.sqltypes.Integer:
                if val == '':
                    return None
                return int(val)
            if coltype is sqlalchemy.sql.sqltypes.Boolean:
                if val.lower() == "true":
                    return True
                return False
            return val
            
        count = 0
        for row in rows:
            if not row.strip():
                continue
            row = row.split(",")
            new = model(**{key: convert(key, val) for key,val in zip(cols, row)})
            db.session.add(new)
            count += 1
        db.session.commit()
        return str(count), 200

def get_uber_csv(session, model, url):
    data = session.post(url+"/devtools/export_model", data={"selected_model": model}).text
    stream = io.StringIO(data)
    reader = csv.DictReader(stream)
    return list(reader)

def run_staff_import(email, password, url, event):
    session = requests.Session()
    session.post(url+"/accounts/login", data={"email": email, "password": password, "original_location": "homepage"})
    attendees = get_uber_csv(session, "Attendee", url)
    num_staff = 0
    print("Retrieved export")

    role = db.session.query(Role).filter(Role.name == "Default Staff").one_or_none()
    if not role:
        role = Role(name="Default Staff", description="Automatically assigned to staff.", event=event)
        db.session.add(role)
        db.session.flush()
        for perm in ['staff.search_names', 'hotel_request.create', 'event.read']:
            permission = Permission(operation=perm, role=role.id)
            db.session.add(permission)

    dh_role = db.session.query(Role).filter(Role.name == "Department Head").one_or_none()
    if not dh_role:
        dh_role = Role(name="Department Head", description="Automatically assigned to department heads.", event=event)
        db.session.add(dh_role)
        db.session.flush()
        for perm in ['department.write', 'hotel_request.approve']:
            permission = Permission(operation=perm, role=dh_role.id)
            db.session.add(permission)

    print("Adding attendees...")
    for attendee in attendees:
        if attendee['hotel_eligible'].lower() == "true":
            num_staff += 1
            user = db.session.query(User).filter(User.password == attendee['id']).one_or_none()
            if not user:
                user = User(username=attendee['id'], email=attendee['id'], password=attendee['id'], active=False)
                db.session.add(user)
                db.session.flush()
            grant = db.session.query(Grant).filter(Grant.user == user.id, Grant.role == role.id).one_or_none()
            if not grant:
                grant = Grant(user=user.id, role=role.id)
                db.session.add(grant)
            badge = db.session.query(Badge).filter(Badge.event == event, Badge.uber_id == attendee['id']).one_or_none()
            if badge:
                badge.printed_number = attendee['badge_num']
                badge.printed_name = attendee['badge_printed_name']
                badge.search_name = "{} {}".format(attendee['first_name'].lower(), attendee['last_name'].lower())
                badge.first_name = attendee['first_name']
                badge.last_name = attendee['last_name']
                badge.legal_name = attendee['legal_name']
                badge.legal_name_matches = bool(attendee['legal_name'])
                badge.email = attendee['email']
                badge.phone = attendee['cellphone']
                db.session.add(badge)
            if not badge:
                badge = Badge(
                    uber_id = attendee['id'],
                    event = event,
                    printed_number = attendee['badge_num'],
                    printed_name = attendee['badge_printed_name'],
                    search_name = "{} {}".format(attendee['first_name'].lower(), attendee['last_name'].lower()),
                    first_name = attendee['first_name'],
                    last_name = attendee['last_name'],
                    legal_name = attendee['legal_name'],
                    legal_name_matches = bool(attendee['legal_name']),
                    email = attendee['email'],
                    phone = attendee['cellphone'],
                    user_id = user.id
                )
                db.session.add(badge)

    print("Adding departments...")
    departments = get_uber_csv(session, "Department", url)
    for department in departments:
        current = db.session.query(Department).filter(Department.event == event, Department.uber_id == department['id']).one_or_none()
        if not current:
            dept = Department(
                uber_id = department['id'],
                name = department['name'],
                description = department['description'],
                event = event
            )
            db.session.add(dept)
            
    print("Adding staffers to departments...")
    deptmembers = get_uber_csv(session, "DeptMembership", url)
    for dm in deptmembers:
        badge = db.session.query(Badge).filter(Badge.event == event, Badge.uber_id == dm['attendee_id']).one_or_none()
        if not badge:
            print("Could not find badge {} to place in department {}.".format(dm['attendee_id'], dm['department_id']))
            continue
        department = db.session.query(Department).filter(Department.event == event, Department.uber_id == dm['department_id']).one_or_none()
        if not department:
            print("Could not find department {} for attendee {}.".format(dm['department_id'], dm['attendee_id']))
            continue
        existing = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge == badge.id, BadgeToDepartment.department == department.id).one_or_none()
        if not existing:
            department_member = BadgeToDepartment(
                badge = badge.id,
                department = department.id
            )
            db.session.add(department_member)
        grant = db.session.query(Grant).filter(Grant.user == badge.user_id, Grant.role == dh_role.id, Grant.department==department.id).one_or_none()
        if (dm['is_dept_head'].lower() == "true") or (dm['is_checklist_admin'].lower() == "true"):
            if not grant:
                grant = Grant(user=badge.user_id, role=dh_role.id, department=department.id)
                db.session.add(grant)
        elif grant:
            db.session.delete(grant)
    print("Committing changes...")
    db.session.commit()
    print("Done.")

@app.route("/api/importer/uber_staff", methods=["POST"])
def import_uber_staff():
    print("Importing staff...")
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return "", 412
    if not check_permission("import.staff", event=request.json['event']):
        return "", 403

    email = request.json['email']
    password = request.json['password']
    url = request.json['uber_url']

    run_staff_import(email, password, url, event.id)
    return "null", 200

@app.route("/api/importer/mock", methods=["POST"])
def import_mock():
    if not 'event' in request.json:
        return "Event is a required parament.", 406
    event = db.session.query(Event).filter(Event.id == request.json['event']).one_or_none()
    if not event:
        return "Could not locate event {}".format(escape(request.json['event'])), 404
    badges = db.session.query(Badge).filter(Badge.event == event.id).all()
    if badges:
        return "You cannot generate mock data if there are already badges. Please delete the badges first if you really want junk data.", 412
    staff_badge_type = db.session.query(BadgeType).filter(BadgeType.name == "Staff").one_or_none()
    if not staff_badge_type:
        staff_badge_type = BadgeType(name="Staff", description="Helps run the show")
        db.session.add(staff_badge_type)
    attendee_badge_type = db.session.query(BadgeType).filter(BadgeType.name == "Attendee").one_or_none()
    if not attendee_badge_type:
        attendee_badge_type = BadgeType(name="Attendee", description="Come to see the show")
        db.session.add(attendee_badge_type)
    db.session.flush()
    if 'attendees' in request.json:
        print("Generating {} attendees".format(request.json['attendees']))
        for i in range(request.json['attendees']):
            if i % 1000 == 0:
                print("  ...{}/{}".format(i, request.json['attendees']))
            first_name = names.get_first_name()
            last_name = names.get_last_name()
            legal_name = "{} {}".format(first_name, last_name)
            full_name = legal_name
            legal_name_matches = True
            printed_name = legal_name
            if random.random() > 0.95:
                legal_name = names.get_full_name()
                legal_name_matches = False
            if random.random() > 0.75:
                printed_name = names.get_last_name()
            provider = random.choice(["verizon", "gmail", "yahoo", "aol", "magfest"])
            site = random.choice(["net", "com", "org", "co.uk"])
            email="{}.{}@{}.{}".format(first_name, last_name, provider, site)
            badge = Badge(
                event=event.id,
                badge_type=attendee_badge_type.id,
                printed_number=(((i + request.json['staffers']) // 1000 + 1) * 1000) if 'staffers' in request.json else i,
                printed_name=printed_name,
                search_name=printed_name.lower(),
                first_name=first_name,
                last_name=last_name,
                legal_name=legal_name,
                legal_name_matches=legal_name_matches,
                email=email
            )
            db.session.add(badge)

    departments = []
    if 'departments' in request.json:
        print("Generating {} departments...".format(request.json['departments']))
        dept_names = {}
        while len(dept_names.keys()) < request.json['departments']:
            name = random.choice(["Tech", "Staff", "Arcade", "Game", "Medical", "Hotel", "Cat", "Concert", "Music", "Security", "Food", "Rescue", "Warehouse", "Logistics", "Truck", "Management"])
            name += random.choice([" Ops", " Management", " Wranglers", " Herders", "", " Chasers", " Fixers", " Breakers", " Managers", " Destroyers", " Cleaners"])
            name = ''.join([x.upper() if random.random() < 0.05 else x for x in name])
            dept_names[name] = None
        for name in dept_names.keys():
            description = "The {} department.".format(name)
            department = Department(name=name, description=description, event=event.id)
            db.session.add(department)
            departments.append(department)
    
    staffers = []
    if 'staffers' in request.json:
        print("Generating {} staffers...".format(request.json['staffers']))
        for i in range(request.json['staffers']):
            if i % 1000 == 0:
                print("  ...{}/{}".format(i, request.json['staffers']))
            first_name = names.get_first_name()
            last_name = names.get_last_name()
            legal_name = "{} {}".format(first_name, last_name)
            full_name = legal_name
            legal_name_matches = True
            printed_name = legal_name
            if random.random() > 0.95:
                legal_name = names.get_full_name()
                legal_name_matches = False
            if random.random() > 0.75:
                printed_name = names.get_last_name()
            provider = random.choice(["verizon", "gmail", "yahoo", "aol", "magfest"])
            site = random.choice(["net", "com", "org", "co.uk"])
            email="{}.{}@{}.{}".format(first_name, last_name, provider, site)
            badge = Badge(
                event=event.id,
                badge_type=staff_badge_type.id,
                printed_number=i,
                printed_name=printed_name,
                search_name=printed_name.lower(),
                first_name=first_name,
                last_name=last_name,
                legal_name=legal_name,
                legal_name_matches=legal_name_matches,
                email=email
            )
            db.session.add(badge)
            staffers.append(badge)
        print("Flushing database...")
        db.session.flush()

        print("Adding hotel information...")
        room_block = HotelRoomBlock(event=event.id, name="The staff block", description="")
        db.session.add(room_block)
        hotel_location = HotelLocation(name="The Really Big Hotel", address="123 Waterfront", event=event.id)
        db.session.add(hotel_location)
        room_nights = []
        for i in ["Wednesday", "Thursday"]:
            room_night = HotelRoomNight(name=i, event=event.id, restricted=True, restriction_type="Setup", hidden=False)
            db.session.add(room_night)
            room_nights.append(room_night)
        for i in ["Friday", "Saturday", "Sunday"]:
            room_night = HotelRoomNight(name=i, event=event.id, restricted=False, restriction_type="Setup", hidden=False)
            db.session.add(room_night)
            room_nights.append(room_night)
        print("Flushing database...")
        db.session.flush()

        print("Adding staffers to departments...")
        requested_room = []
        for staffer in staffers:
            staffer_depts = list(departments)
            hotel_requested = False
            declined = False
            
            preferred_department=None
            for i in range(int(random.random()/0.3)):
                staffer_dept = random.choice(staffer_depts)
                staffer_depts.remove(staffer_dept)
                assignment = BadgeToDepartment(badge=staffer.id, department=staffer_dept.id)
                db.session.add(assignment)
                preferred_department = staffer_dept.id
        
            if random.random() > 0.3:
                hotel_requested = True
                if random.random() > 0.1:
                    declined = True
                else:
                    requested_room.append(staffer)
                hotel_request = HotelRoomRequest(
                    badge=staffer.id,
                    declined=declined,
                    prefer_department=random.random() > 0.1,
                    preferred_department=preferred_department,
                    notes="Please give room.",
                    prefer_single_gender=random.random() > 0.3,
                    preferred_gender=random.choice(['male', 'female', 'other']),
                    noise_level=random.choice(['Quiet - I am quiet, and prefer quiet.', "Moderate - I don't make a lot of noise.", "Loud - I'm ok if someone snores or I snore.",]),
                    smoke_sensitive=random.choice([True, False]),
                    sleep_time=random.choice(['2am-4am', '4am-6am', '6am-8am', '8am-10am']),
                )
                db.session.add(hotel_request)

        print("Requesting Roommates...")
        requested_roommates = []
        for staffer in requested_room:
            for i in room_nights:
                if random.random() > 0.2:
                    req = RoomNightRequest(badge=staffer.id, requested=True, room_night=i.id)
                    db.session.add(req)
            for i in range(random.randrange(0, 3)):
                other = random.choice(requested_room)
                if other == staffer:
                    continue
                if random.random() > 0.2:
                    if not (staffer.id, other.id) in requested_roommates:
                        req = HotelRoommateRequest(requester=staffer.id, requested=other.id)
                        requested_roommates.append((staffer.id, other.id))
                        db.session.add(req)
                    if random.random() > 0.6:
                        if not (other.id, staffer.id) in requested_roommates:
                            req = HotelRoommateRequest(requester=other.id, requested=staffer.id)
                            requested_roommates.append((other.id, staffer.id))
                            db.session.add(req)
                else:
                    if not (staffer.id, other.id) in requested_roommates:
                        req = HotelAntiRoommateRequest(requester=staffer.id, requested=other.id)
                        requested_roommates.append((staffer.id, other.id))
                        db.session.add(req)
                if random.random() > 0.9:
                    if not (other.id, staffer.id) in requested_roommates:
                        req = HotelAntiRoommateRequest(requester=other.id, requested=staffer.id)
                        requested_roommates.append((other.id, staffer.id))
                        db.session.add(req)
        print("Flushing session...")
        db.session.flush()

    print("Committing...")
    db.session.commit()
    print("Done!")
    return "null", 200