from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema

class EventSchema(ModelSchema):
    class Meta:
        model = Event
        sqla_session = db.session
        fields = ['id', 'description', 'name']

register_crud("events", EventSchema(), url_scheme="global")
