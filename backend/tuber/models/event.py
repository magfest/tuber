from tuber.models import Base
from sqlalchemy import Column, Integer, String, Boolean


class Event(Base):
    __tablename__ = "event"
    __url__ = "/api/event"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    description = Column(String())
    readonly = Column(Boolean, default=False)
    uber_url = Column(String(), nullable=True)
    uber_url.allow_r = {"admin"}
    uber_apikey = Column(String(), nullable=True)
    uber_apikey.allow_r = {"admin"}
    uber_slug = Column(String(), nullable=True)
    uber_slug.allow_r = {"admin"}
