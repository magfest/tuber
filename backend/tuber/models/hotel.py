from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Date
from sqlalchemy.orm import relationship

class HotelRoomRequest(Base):
    __tablename__ = "hotel_room_request"
    __url__ = "/api/event/<int:event>/hotel_room_request"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    first_name = Column(String(), nullable=True)
    last_name = Column(String(), nullable=True)
    declined = Column(Boolean, nullable=True)
    prefer_department = Column(Boolean, nullable=True)
    preferred_department = Column(Integer, ForeignKey('department.id'), nullable=True)
    notes = Column(String(), nullable=True)
    prefer_single_gender = Column(Boolean, nullable=True)
    preferred_gender = Column(String(), nullable=True)
    noise_level = Column(String(), nullable=True)
    smoke_sensitive = Column(Boolean, nullable=True)
    sleep_time = Column(String(), nullable=True)
    room_night_justification = Column(String(), nullable=True)

class HotelRoomBlock(Base):
    __tablename__ = "hotel_room_block"
    __url__ = "/api/event/<int:event>/hotel_room_block"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    name = Column(String(), nullable=True)
    description = Column(String(), nullable=True)
    rooms = relationship("HotelRoom")

class HotelRoom(Base):
    __tablename__ = "hotel_room"
    __url__ = "/api/event/<int:event>/hotel_room"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    name = Column(String(), nullable=True)
    notes = Column(String(), nullable=True)
    messages = Column(String(), nullable=True)
    hotel_block = Column(Integer, ForeignKey('hotel_room_block.id'))
    hotel_location = Column(Integer, ForeignKey('hotel_location.id'))
    completed = Column(Boolean)
    room_night_assignments = relationship('RoomNightAssignment')

class HotelRoommateRequest(Base):
    __tablename__ = "hotel_roommate_request"
    id = Column(Integer, primary_key=True)
    requester = Column(Integer, ForeignKey('badge.id'))
    requested = Column(Integer, ForeignKey('badge.id'))

class HotelAntiRoommateRequest(Base):
    __tablename__ = "hotel_anti_roommate_request"
    id = Column(Integer, primary_key=True)
    requester = Column(Integer, ForeignKey('badge.id'))
    requested = Column(Integer, ForeignKey('badge.id'))

class HotelLocation(Base):
    __tablename__ = "hotel_location"
    __url__ = "/api/event/<int:event>/hotel_location"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    address = Column(String())
    event = Column(Integer, ForeignKey('event.id'))
    rooms = relationship("HotelRoom")

class HotelRoomNight(Base):
    __tablename__ = "hotel_room_night"
    __url__ = "/api/event/<int:event>/hotel_room_night"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    date = Column(Date)
    name = Column(String())
    restricted = Column(Boolean, default=False)
    restriction_type = Column(String(), nullable=True)
    hidden = Column(Boolean, default=False)
    requests = relationship("RoomNightRequest")
    assignments = relationship("RoomNightAssignment")
    approvals = relationship("RoomNightApproval")

class RoomNightRequest(Base):
    __tablename__ = "room_night_request"
    __url__ = "/api/event/<int:event>/room_night_request"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    requested = Column(Boolean)
    room_night = Column(Integer, ForeignKey('hotel_room_night.id'))

class RoomNightAssignment(Base):
    __tablename__ = "room_night_assignment"
    __url__ = "/api/event/<int:event>/room_night_assignment"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    room_night = Column(Integer, ForeignKey('hotel_room_night.id'))
    hotel_room = Column(Integer, ForeignKey('hotel_room.id'))

class RoomNightApproval(Base):
    __tablename__ = "room_night_approval"
    __url__ = "/api/event/<int:event>/department/<int:department>/room_night_approval"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    room_night = Column(Integer, ForeignKey('hotel_room_night.id'))
    department = Column(Integer, ForeignKey('department.id'))
    approved = Column(Boolean)
