from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema

class EventSchema(ModelSchema):
    class Meta:
        model = Event
        fields = ['id', 'description', 'name']

register_crud("event", EventSchema(), url_scheme="global")
