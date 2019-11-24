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
