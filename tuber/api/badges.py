from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema
from flask import g

def allow_self_edits(event=0, department=0):
    if set(g.data.keys()) & set(['id', 'event', 'badge_type', 'printed_number', 'search_name', 'user', 'uber_id', 'departments', 'room_night_assignments', 'room_night_approvals']):
        return False
    return g.url_params['id'] in [x.id for x in g.user.badges]

def allow_self_reads(event=0, department=0):
    return g.url_params['id'] in [x.id for x in g.user.badges]

class BadgeSchema(ModelSchema):
    class Meta:
        model = Badge
        sqla_session = db.session
        fields = [
            'id',
            'event',
            'badge_type',
            'printed_number',
            'printed_name',
            'search_name',
            'first_name',
            'last_name',
            'legal_name',
            'legal_name_matches',
            'email',
            'user',
            'uber_id',
            'departments',
            'room_night_requests',
            'room_night_assignments',
            'room_night_approvals',
            'hotel_room_request'
        ]

register_crud("badges", BadgeSchema(), permissions={"GET": [[allow_self_reads, "badges.read"]], "PATCH": [[allow_self_edits, "badges.update"]]})

class DepartmentSchema(ModelSchema):
    class Meta:
        model = Department
        sqla_session = db.session
        fields = ['id', 'uber_id', 'description', 'name', 'badges']

register_crud("departments", DepartmentSchema())

class BadgeTypeSchema(ModelSchema):
    class Meta:
        model = BadgeType
        sqla_session = db.session
        fields = ['id', 'name', 'description']

register_crud("badge_types", BadgeTypeSchema())

class RibbonTypeSchema(ModelSchema):
    class Meta:
        model = RibbonType
        sqla_session = db.session
        fields = ['id', 'name', 'description']

register_crud("ribbon_types", RibbonType())