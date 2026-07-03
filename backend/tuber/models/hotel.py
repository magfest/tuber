from tuber.models import Base
from .badge import Badge
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Date, Table, DateTime, event
from sqlalchemy.orm import relationship


class HotelRoommateRequest(Base):
    __tablename__ = "hotel_roommate_request"
    id = Column(Integer, primary_key=True)
    requester = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    requested = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))


class HotelAntiRoommateRequest(Base):
    __tablename__ = "hotel_anti_roommate_request"
    id = Column(Integer, primary_key=True)
    requester = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    requested = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))


class RoomNightRequest(Base):
    __tablename__ = "room_night_request"
    __url__ = "/api/event/<int:event>/room_night_request"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    requested = Column(Boolean)
    room_night = Column(Integer, ForeignKey(
        'hotel_room_night.id', ondelete="CASCADE"))


class RoomNightAssignment(Base):
    __tablename__ = "room_night_assignment"
    __url__ = "/api/event/<int:event>/room_night_assignment"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    room_night = Column(Integer, ForeignKey(
        'hotel_room_night.id', ondelete="CASCADE"))
    hotel_room = Column(Integer, ForeignKey(
        'hotel_room.id', ondelete="CASCADE"))


class RoomNightApproval(Base):
    __tablename__ = "room_night_approval"
    __url__ = "/api/event/<int:event>/department/<int:department>/room_night_approval"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    room_night = Column(Integer, ForeignKey(
        'hotel_room_night.id', ondelete="CASCADE"))
    department = Column(Integer, ForeignKey(
        'department.id', ondelete="CASCADE"))
    approved = Column(Boolean)


class HotelRoomRequest(Base):
    __tablename__ = "hotel_room_request"
    __url__ = "/api/event/<int:event>/hotel_room_request"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    badge_obj = relationship("Badge", viewonly=True)
    uber_id = Column(String(), nullable=True)
    first_name = Column(String(), nullable=True)
    last_name = Column(String(), nullable=True)
    declined = Column(Boolean, nullable=True)
    prefer_department = Column(Boolean, nullable=True)
    preferred_department = Column(
        Integer, ForeignKey('department.id', ondelete="SET NULL"), nullable=True)
    hotel_block = Column(Integer, ForeignKey(
        'hotel_room_block.id', ondelete="SET NULL"), nullable=True)
    notes = Column(String(), nullable=True)
    prefer_single_gender = Column(Boolean, nullable=True)
    preferred_gender = Column(String(), nullable=True)
    noise_level = Column(String(), nullable=True)
    smoke_sensitive = Column(Boolean, nullable=True)
    sleep_time = Column(String(), nullable=True)
    room_night_justification = Column(String(), nullable=True)
    roommate_requests = relationship("Badge", secondary="hotel_roommate_request", foreign_keys=[
                                     HotelRoommateRequest.requested, HotelRoommateRequest.requester], primaryjoin=badge == HotelRoommateRequest.requester, secondaryjoin=Badge.id == HotelRoommateRequest.requested)
    roommate_anti_requests = relationship("Badge", secondary="hotel_anti_roommate_request", foreign_keys=[
                                          HotelAntiRoommateRequest.requested, HotelAntiRoommateRequest.requester], primaryjoin=badge == HotelAntiRoommateRequest.requester, secondaryjoin=Badge.id == HotelAntiRoommateRequest.requested)
    room_night_requests = relationship("RoomNightRequest", foreign_keys=[
                                       RoomNightRequest.badge], primaryjoin=badge == RoomNightRequest.badge, overlaps="room_night_requests")
    room_night_approvals = relationship("RoomNightApproval", foreign_keys=[
                                        RoomNightApproval.badge], primaryjoin=badge == RoomNightApproval.badge, overlaps="room_night_approvals")
    room_night_assignments = relationship("RoomNightAssignment", foreign_keys=[
                                          RoomNightAssignment.badge], primaryjoin=badge == RoomNightAssignment.badge, overlaps="room_night_assignments")


class HotelRoomBlock(Base):
    __tablename__ = "hotel_room_block"
    __url__ = "/api/event/<int:event>/hotel_room_block"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String(), nullable=True)
    description = Column(String(), nullable=True)
    rooms = relationship("HotelRoom")


class HotelRoom(Base):
    __tablename__ = "hotel_room"
    __url__ = "/api/event/<int:event>/hotel_room"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String(), nullable=True)
    notes = Column(String(), nullable=True)
    messages = Column(String(), nullable=True)
    hotel_block = Column(Integer, ForeignKey(
        'hotel_room_block.id', ondelete="CASCADE"))
    hotel_location = Column(Integer, ForeignKey(
        'hotel_location.id', ondelete="CASCADE"))
    completed = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)
    suggested = Column(Boolean, default=False, server_default='false')
    room_night_assignments = relationship(
        'RoomNightAssignment', cascade="all, delete", passive_deletes=True)
    roommates = relationship("Badge", secondary="room_night_assignment",
                             primaryjoin=id == RoomNightAssignment.hotel_room, viewonly=True)


class HotelLocation(Base):
    __tablename__ = "hotel_location"
    __url__ = "/api/event/<int:event>/hotel_location"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    address = Column(String())
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    rooms = relationship("HotelRoom")


class HotelRoomNight(Base):
    __tablename__ = "hotel_room_night"
    __url__ = "/api/event/<int:event>/hotel_room_night"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    date = Column(Date)
    name = Column(String())
    restricted = Column(Boolean, default=False)
    # How eligibility for this night is decided:
    #   none         - available to everyone
    #   shift_window - requires a shift overlapping [shift_starttime, shift_endtime]
    #   shift_hours  - requires >= shift_hours_required total assigned shift hours
    #   manual       - requires a manual approval (department head or admin)
    # A manual approval always satisfies any mode. `restricted` is kept in sync
    # as a legacy mirror (restriction_mode != 'none'); `restriction_type` is a
    # free-text display label only.
    restriction_mode = Column(String(), nullable=False,
                              default='none', server_default='none')
    shift_hours_required = Column(Integer, nullable=True)
    shift_starttime = Column(DateTime(), nullable=True)
    shift_endtime = Column(DateTime(), nullable=True)
    restriction_type = Column(String(), nullable=True)
    hidden = Column(Boolean, default=False)
    requests = relationship(
        "RoomNightRequest", cascade="all, delete", passive_deletes=True)
    assignments = relationship(
        "RoomNightAssignment", cascade="all, delete", passive_deletes=True)
    approvals = relationship(
        "RoomNightApproval", cascade="all, delete", passive_deletes=True)


# Keep restriction_mode (source of truth) and the legacy `restricted` mirror
# consistent no matter which one a writer sets (generic CRUD, importer, tests).
# The "set" events fire before the new value lands on the instance, so the
# listeners read raw __dict__ state and guard against re-entering each other.

@event.listens_for(HotelRoomNight.restriction_mode, "set", retval=True)
def _sync_restricted(target, value, oldvalue, initiator):
    if getattr(target, '_restriction_sync', False):
        return value
    restricted = value is not None and value != 'none'
    if target.__dict__.get('restricted') != restricted:
        target._restriction_sync = True
        try:
            target.restricted = restricted
        finally:
            target._restriction_sync = False
    return value


@event.listens_for(HotelRoomNight.restricted, "set", retval=True)
def _sync_restriction_mode(target, value, oldvalue, initiator):
    # Legacy writers only set `restricted`; give them the equivalent mode.
    if getattr(target, '_restriction_sync', False):
        return value
    mode = target.__dict__.get('restriction_mode')
    target._restriction_sync = True
    try:
        if value and mode in (None, 'none'):
            target.restriction_mode = 'shift_window'
        elif not value and mode not in (None, 'none'):
            target.restriction_mode = 'none'
    finally:
        target._restriction_sync = False
    return value
