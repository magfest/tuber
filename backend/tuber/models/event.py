from tuber.models import Base, TimeZone
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Boolean, and_
from sqlalchemy.orm import relationship
# HotelRoomNight is defined in a module imported after this one; the lambda
# below resolves it when the mappers are configured.
import tuber.models as models


class Event(Base):
    __tablename__ = "event"
    __url__ = "/api/event"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    description = Column(String())
    readonly = Column(Boolean, default=False)
    uber_url = Column(String(), nullable=True)
    uber_apikey = Column(String(), nullable=True)
    uber_apikey.hidden = True
    uber_slug = Column(String(), nullable=True)
    timezone = Column(TimeZone, nullable=False, default=ZoneInfo("UTC"))
    
    unrestricted_nights = relationship(
        "HotelRoomNight",
        primaryjoin=lambda: and_(Event.id == models.HotelRoomNight.event,
                                 models.HotelRoomNight.restriction_mode == 'none'),
        viewonly=True
    )
    badges = relationship("Badge", back_populates="event_obj")