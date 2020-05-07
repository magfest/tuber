from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from sqlalchemy import and_
import requests
import datetime
import uuid
import os
from tuber.api import *
from marshmallow_sqlalchemy import ModelSchema

class HotelRoomRequestSchema(ModelSchema):
    class Meta:
        model = HotelRoomRequest
        sqla_session = db.session
        fields = [
            'id',
            'badge',
            'declined',
            'prefer_department',
            'notes',
            'prefer_single_gender',
            'noise_level',
            'smoke_sensitive',
            'sleep_time',
            'room_night_justification',
        ]

register_crud("hotel_room_requests", HotelRoomRequestSchema())

class HotelRoomBlockSchema(ModelSchema):
    class Meta:
        model = HotelRoomBlock
        sqla_session = db.session
        fields = [
            'id',
            'event',
            'name',
            'description',
            'rooms',
        ]

register_crud("hotel_room_blocks", HotelRoomBlockSchema())

class HotelRoomSchema(ModelSchema):
    class Meta:
        model = HotelRoom
        sqla_session = db.session
        fields = [
            'id',
            'name',
            'notes',
            'messages',
            'hotel_block',
            'hotel_location',
            'completed',
        ]

register_crud("hotel_rooms", HotelRoomSchema())

class HotelLocationSchema(ModelSchema):
    """Schema for the physical location of the hotel"""
    class Meta:
        model = HotelLocation
        sqla_session = db.session
        fields = [
            'id',
            'name',
            'address',
            'event',
            'rooms',
        ]

register_crud("hotel_locations", HotelLocationSchema())

class HotelRoomNightSchema(ModelSchema):
    class Meta:
        model = HotelRoomNight
        sqla_session = db.session
        fields = [
            'id',
            'name',
            'event',
            'restricted',
            'restriction_type',
            'hidden',
            'requests',
            'assignments',
            'approvals',
        ]

register_crud("hotel_room_nights", HotelRoomNightSchema())

@app.route("/api/hotels/statistics", methods=["GET"])
def hotel_statistics():
    if check_permission("hotel_statistics.read", event=request.args['event']):
        num_badges = db.session.query(Badge).filter(Badge.event == request.args['event']).count()
        num_requests = db.session.query(Badge, HotelRoomRequest).filter(Badge.id == HotelRoomRequest.badge, Badge.event == request.args['event']).count()
        return jsonify(success=True, num_badges=num_badges, num_requests=num_requests)
    return jsonify(success=False)

@app.route("/api/hotels/all_requests", methods=["GET"])
def hotel_all_requests():
    if request.method == "GET":
        if not check_permission("hotel_request.assign", event=request.args['event']):
            return jsonify(success=False)
        room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        room_night_ids = [x.id for x in room_nights]
        requests = db.session.query(Badge, HotelRoomRequest).join(HotelRoomRequest, Badge.id == HotelRoomRequest.badge).filter(HotelRoomRequest.declined != True).all()
        badges = [x[0].id for x in requests]
        default_room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event'], HotelRoomNight.restricted != True).all()
        default_room_nights = [x.id for x in default_room_nights]
        approvals = db.session.query(RoomNightRequest).join(RoomNightApproval, RoomNightApproval.room_night == RoomNightRequest.id).filter(RoomNightRequest.badge.in_(badges), RoomNightApproval.approved == True).all()
        requested_roommates = db.session.query(HotelRoommateRequest).filter(HotelRoommateRequest.requester.in_(badges)).all()
        antirequested_roommates = db.session.query(HotelAntiRoommateRequest).filter(HotelAntiRoommateRequest.requester.in_(badges)).all()
        department_membership = db.session.query(BadgeToDepartment).filter(BadgeToDepartment.badge.in_(badges)).all()
        results = {}
        genders = {
            "male": 0,
            "guy": 0,
            "bro": 0,
            "boys": 0,
            "males": 0,
            "female": 1,
            "females": 1,
            "woman": 1,
            "women": 1,
            "he/him": 0,
            "she/her": 1,
            "m": 0,
            "f": 1,
        }
        noise_levels = {
            'Quiet - I am quiet, and prefer quiet.': 0,
            "Moderate - I don't make a lot of noise.": 1,
            "Loud - I'm ok if someone snores or I snore.": 2,
        }
        sleep_times = {
            '8pm-10pm': 0,
            '10pm-12am': 1,
            '12am-2am': 2,
            '2am-4am': 3,
            '4am-6am': 4,
            '6am-8am': 5,
            '8am-10am': 6,
            '10am-12pm': 7,
            '12pm-2pm': 8,
            '2pm-4pm': 9,
            '4pm-6pm': 10,
            '6pm-8pm': 11,
        }
        for badge, req in requests:
            notes = req.notes
            preferred_gender = None
            if req.preferred_gender:
                if req.preferred_gender.lower().strip() in genders.keys():
                    preferred_gender = genders[req.preferred_gender.lower().strip()]
                elif "trans" in req.preferred_gender.lower():
                    preferred_gender = 2
                else:
                    print("Unhandled gender preference: {}".format(req.preferred_gender))
                    notes += "\nRequested to be roomed with ({}) gender.".format(req.preferred_gender)
            noise_level = None
            if req.noise_level in noise_levels:
                noise_level = noise_levels[req.noise_level]
            sleep_time = None
            if req.sleep_time in sleep_times:
                sleep_time = sleep_times[req.sleep_time]
            results[badge.id] = {
                "id": badge.id,
                "name": "{} {}".format(badge.first_name, badge.last_name),
                "first_name": badge.first_name,
                "last_name": badge.last_name,
                "legal_name": badge.legal_name if badge.legal_name else "",
                "justification": req.room_night_justification,
                "room_nights": [x for x in default_room_nights if x in [y.room_night for y in badge.room_night_requests if y.requested]],
                "prefer_department": req.prefer_department,
                "preferred_department": req.preferred_department,
                "notes": notes,
                "prefer_single_gender": req.prefer_single_gender,
                "preferred_gender": preferred_gender,
                "noise_level": noise_level,
                "smoke_sensitive": req.smoke_sensitive,
                "sleep_time": sleep_time,
                "requested_roommates": [],
                "antirequested_roommates": [],
                "departments": []
            }
        for rnr in approvals:
            if not rnr.room_night in results[rnr.badge]["room_nights"]:
                results[rnr.badge]["room_nights"].append(rnr.room_night)
        for req in requested_roommates:
            results[req.requester]['requested_roommates'].append(req.requested)
        for req in antirequested_roommates:
            results[req.requester]['antirequested_roommates'].append(req.requested)
        for membership in department_membership:
            results[membership.badge]['departments'].append(membership.department)
        to_del = []
        for res in results.keys():
            if not results[res]["room_nights"]:
                to_del.append(res)
        for i in to_del:
            del results[i]
        return jsonify(success=True, requests=results)

@app.route("/api/hotels/requests", methods=["GET", "POST"])
def hotel_requests():
    if request.method == "GET":
        if check_permission("hotel_request.approve", event=request.args['event']):
            requests = db.session.query(Department, Badge, HotelRoomRequest).join(BadgeToDepartment, BadgeToDepartment.department == Department.id).join(HotelRoomRequest, HotelRoomRequest.badge == BadgeToDepartment.badge).join(Badge, Badge.id == BadgeToDepartment.badge).all()
            departments = {}
            for req in requests:
                dept, badge, roomrequest = req
                if not check_permission("hotel_request.approve", event=request.args['event'], department=dept.id):
                    continue
                if not dept.id in departments:
                    departments[dept.id] = {
                        "id": dept.id,
                        "name": dept.name,
                        "requests": []
                    }
                room_nights = db.session.query(RoomNightRequest, RoomNightApproval).join(RoomNightApproval, and_(RoomNightApproval.room_night == RoomNightRequest.id, RoomNightApproval.department == dept.id), isouter=True).filter(RoomNightRequest.badge == badge.id).all()
                departments[dept.id]['requests'].append({
                    "id": badge.id,
                    "name": badge.first_name + " " + badge.last_name,
                    "justification": roomrequest.room_night_justification,
                    "room_nights": {
                        btr.room_night: {
                        "id": btr.id,
                        "requested": btr.requested,
                        "room_night": btr.room_night,
                        "approved": rna.approved if rna else None
                    } for btr, rna in room_nights}
                })
            res = []
            for i in departments:
                res.append(departments[i])
            return jsonify(success=True, departments=res)
        return jsonify(success=False, reason="Permission Denied.")
    return jsonify(success=False)
            
@app.route("/api/hotels/approve", methods=["POST"])
def hotel_approve():
    if request.method == "POST":
        if check_permission("hotel_request.approve", event=request.json['event'], department=request.json['department']):
            room_night = db.session.query(RoomNightRequest).filter(RoomNightRequest.id == request.json['room_night_request']).one_or_none()
            if not room_night:
                return jsonify(success=False, reason="Could not find corresponding request.")
            approval = db.session.query(RoomNightApproval).filter(RoomNightApproval.room_night == room_night.id, RoomNightApproval.department == request.json['department']).one_or_none()
            if request.json['approved'] is None:
                if approval:
                    db.session.delete(approval)
            else:
                if not approval:
                    approval = RoomNightApproval()
                approval.approved = request.json['approved']
                approval.department = request.json['department']
                approval.room_night = room_night.id
                db.session.add(approval)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False, reason="Permission denied.")

@app.route("/api/hotels/room_nights", methods=["GET"])
def hotel_room_nights():
    if request.method == "GET":
        if check_permission("hotel_request.approve", event=request.args['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            res = []
            for rn in room_nights:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "restricted": rn.restricted,
                    "restriction_type": rn.restriction_type,
                    "hidden": rn.hidden
                })
            return jsonify(success=True, room_nights=res)
    return jsonify(success=False)

@app.route("/api/hotels/hotel_room", methods=["GET", "POST", "DELETE"])
def hotel_room():
    if request.method == "GET":
        if not check_permission("hotel_settings.*", event=request.args['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.args['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        hotel_rooms = db.session.query(HotelRoom).filter(HotelRoom.hotel_block.in_(room_block_ids)).all()
        res = []
        for rn in hotel_rooms:
            res.append({
                "id": rn.id,
                "name": rn.name,
                "notes": rn.notes,
                "messages": rn.messages,
                "hotel_block": rn.hotel_block,
                "hotel_location": rn.hotel_location,
                "completed": rn.completed,
            })
        return jsonify(success=True, hotel_rooms=res)
    if request.method == "POST":
        if not check_permission("hotel_settings.write", event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.json['event']).all()
        room_block_ids = [x.id for x in room_blocks]
        room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.json['event']).all()
        room_location_ids = [x.id for x in room_locations]
        if 'rooms' in request.json:
            for room in request.json['rooms']:
                rn = db.session.query(HotelRoom).filter(HotelRoom.id == room['id']).one_or_none()
                if not rn:
                    return jsonify(success=False, reason="Could not find hotel room {}".format(room['id']))
                if 'hotel_block' in room:
                    if not room['hotel_block'] in room_block_ids:
                        return jsonify(success=False, reason="Could not find hotel block {}".format(room['hotel_block']))
                if 'hotel_location' in room:
                    if not room['hotel_location'] in room_location_ids:
                        return jsonify(success=False, reason="Could not find hotel location {}".format(room['hotel_location']))
                for attr in ['name', 'notes', 'messages', 'hotel_block', 'hotel_location', 'completed']:
                    if attr in room:
                        setattr(rn, attr, room[attr])
                db.session.add(rn)
            db.session.commit()
            return jsonify(success=True)
        if not room_blocks:
            return jsonify(success=False, reason="No room blocks defined.")
        if not room_locations:
            return jsonify(success=False, reason="No hotel locations defined.")
        rn = HotelRoom(hotel_block=room_block_ids[0], hotel_location=room_location_ids[0])
        db.session.add(rn)
        db.session.flush()
        db.session.commit()
        return jsonify(success=True, room={'id': rn.id, 'name': rn.name, 'notes': rn.notes, 'messages': rn.messages, 'hotel_block': rn.hotel_block, 'hotel_location': rn.hotel_location})
    if request.method == "DELETE": 
        if not check_permission("hotel_settings.write", event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        for room in request.json['rooms']:
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.hotel_room == room).all()
            for rna in rnas:
                db.session.delete(rna)
            rn = db.session.query(HotelRoom).filter(HotelRoom.id == room).one_or_none()
            if not rn:
                return jsonify(success=False, reason="Could not find hotel room {}".format(room))
            db.session.delete(rn)
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False, reason="Unsupported request method")

@app.route("/api/hotels/settings/room_night", methods=["GET", "POST"])
def hotel_room_night_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
            res = []
            for rn in room_nights:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "restricted": rn.restricted,
                    "restriction_type": rn.restriction_type,
                    "hidden": rn.hidden
                })
            return jsonify(success=True, room_nights=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.json['event']).all()
            for i in room_nights:
                if [x for x in request.json['room_nights'] if 'id' in x and x['id'] == i.id]:
                    continue
                for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_nights']:
                room_night = None
                if 'id' in i:
                    room_night = db.session.query(HotelRoomNight).filter(HotelRoomNight.id == i['id']).one_or_none()
                if not room_night:
                    room_night = HotelRoomNight()
                room_night.name = i['name']
                room_night.event = request.json['event']
                room_night.restricted = i['restricted']
                if room_night.restricted:
                    room_night.restriction_type = i['restriction_type']
                else:
                    room_night.restriction_type = ""
                room_night.hidden = i['hidden']
                db.session.add(room_night)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route("/api/hotels/settings/room_block", methods=["GET", "POST"])
def hotel_room_block_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.args['event']).all()
            res = []
            for rn in room_blocks:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "description": rn.description
                })
            return jsonify(success=True, room_blocks=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_blocks = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.event == request.json['event']).all()
            for i in room_blocks:
                if [x for x in request.json['room_blocks'] if 'id' in x and x['id'] == i.id]:
                    continue
                #Need to add later
                #for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                #    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_blocks']:
                room_block = None
                if 'id' in i:
                    room_block = db.session.query(HotelRoomBlock).filter(HotelRoomBlock.id == i['id']).one_or_none()
                if not room_block:
                    room_block = HotelRoomBlock()
                room_block.name = i['name']
                room_block.description = i['description']
                room_block.event = request.json['event']
                db.session.add(room_block)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route("/api/hotels/settings/room_location", methods=["GET", "POST"])
def hotel_room_location_settings():
    if request.method == "GET":
        if check_permission("hotel_settings.*", event=request.args['event']):
            room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.args['event']).all()
            res = []
            for rn in room_locations:
                res.append({
                    "id": rn.id,
                    "name": rn.name,
                    "address": rn.address
                })
            return jsonify(success=True, room_locations=res)
    if request.method == "POST":
        if check_permission("hotel_settings.write", event=request.json['event']):
            room_locations = db.session.query(HotelLocation).filter(HotelLocation.event == request.json['event']).all()
            for i in room_locations:
                if [x for x in request.json['room_locations'] if 'id' in x and x['id'] == i.id]:
                    continue
                #Need to add later
                #for j in db.session.query(RoomNightRequest).filter(RoomNightRequest.room_night == i.id).all():
                #    db.session.delete(i)
                db.session.delete(i)
                        
            for i in request.json['room_locations']:
                room_location = None
                if 'id' in i:
                    room_location = db.session.query(HotelLocation).filter(HotelLocation.id == i['id']).one_or_none()
                if not room_location:
                    room_location = HotelLocation()
                room_location.name = i['name']
                room_location.address = i['address']
                room_location.event = request.json['event']
                db.session.add(room_location)
            db.session.commit()
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/hotels/request_complete.png')
def request_complete():
    if not 'id' in request.args:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    id = request.args['id']
    badge = db.session.query(Badge).filter(Badge.uber_id == id).one_or_none()
    if not badge:
        resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
        resp.cache_control.max_age = 10
        return resp
    req = db.session.query(HotelRoomRequest).filter(HotelRoomRequest.badge == badge.id).one_or_none()
    if req:
        return send_file(os.path.join(config.static_path, "checkbox_checked.png"))
    resp = send_file(os.path.join(config.static_path, "checkbox_unchecked.png"))
    resp.cache_control.max_age = 10
    return resp

@app.route('/api/hotels/room_assignments', methods=['GET', 'POST'])
def hotel_room_assignments():
    if request.method == "GET":
        if not check_permission('room_assignment.read', event=request.args['event']):
            return jsonify(success=False, reason="Permission Denied")
        room_nights = db.session.query(HotelRoomNight).filter(HotelRoomNight.event == request.args['event']).all()
        if 'badge' in request.args:
            badge = db.session.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
            if not badge:
                return jsonify(success=False, reason="Could not locate badge {}".format(request.args['badge']))
            if badge.event != request.args['event']:
                return jsonify(success=False, reason="Permission Denied")
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge == badge.id).all()
            res = {x.id: [y.hotel_room for y in rnas if y.room_night == x.id] for x in room_nights}
            return jsonify(success=True, room_assignments=res)
        badges = db.session.query(Badge).filter(Badge.event == request.args['event']).all()
        badge_ids = [x.id for x in badges]
        rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge.in_(badge_ids)).all()
        res = {}
        for badge in badge_ids:
            res[badge] = {}
            for room_night in room_nights:
                res[badge][room_night.id] = []
            for rna in rnas:
                if rna.badge == badge:
                    res[rna.badge][rna.room_night].append(rna.hotel_room)
        return jsonify(success=True, room_assignments=res)
    if request.method == "POST":
        if not check_permission('room_assignment.write', event=request.json['event']):
            return jsonify(success=False, reason="Permission Denied")
        if 'badge' in request.json:
            badges = [request.json['badge']]
        if 'badges' in request.json:
            badges = request.json['badges']
        if not badges:
            return jsonify(success=False, reason="Either badge or badges must be provided")
        for badge in badges:
            rnas = db.session.query(RoomNightAssignment).filter(RoomNightAssignment.badge==badge, RoomNightAssignment.hotel_room==int(request.json['hotel_room'])).all()
            for rna in rnas:
                db.session.delete(rna)
            if type(request.json['room_nights']) is list:
                for room_night in request.json['room_nights']:
                    rna = RoomNightAssignment(badge=badge, room_night=room_night, hotel_room=request.json['hotel_room'])
                    db.session.add(rna)
            else:
                requested = db.session.query(RoomNightRequest, HotelRoomNight).join(HotelRoomNight, RoomNightRequest.room_night == HotelRoomNight.id).filter(RoomNightRequest.badge == badge, RoomNightRequest.requested == True).all()
                approvals = db.session.query(RoomNightApproval, RoomNightRequest).join(RoomNightRequest, RoomNightRequest.id == RoomNightApproval.room_night).filter(RoomNightRequest.badge == badge).all()
                approved = [x[1].room_night for x in approvals if x[0].approved]
                for req, night in requested:
                    if (night.id in approved) or (not night.restricted):
                        rna = RoomNightAssignment(badge=badge, room_night=req.room_night, hotel_room=request.json['hotel_room'])
                        db.session.add(rna)
        db.session.commit()
        return jsonify(success=True)
            
    return jsonify(success=False, reason="Unsupported method type {}".format(request.method))

@app.route("/api/hotels/badges")
def hotel_badges():
    if not check_permission('badges.read', event=request.args['event']):
        return jsonify(success=False, reason="Permission Denied.")
    badges = db.session.query(Badge).filter(Badge.event == request.args['event']).all()
    ret = []
    for badge in badges:
        ret.append({
            "id": badge.id,
            "first_name": badge.first_name,
            "last_name": badge.last_name,
        })
    return jsonify(success=True, badges=ret)
