from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema

class BadgeSchema(ModelSchema):
    class Meta:
        model = Badge
        sqla_session = db.session
        fields = ['id', 'printed_number', 'printed_name', 'search_name', 'first_name', 'last_name', 'legal_name', 'legal_name_matches', 'email', 'user_id', 'uber_id', 'departments', 'room_night_requests', 'room_night_assignments']

register_crud("badges", BadgeSchema())

class DepartmentSchema(ModelSchema):
    class Meta:
        model = Department
        sqla_session = db.session
        fields = ['id', 'uber_id', 'description', 'name']

register_crud("departments", DepartmentSchema())
