from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, cast, and_, Interval, union
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.sql import select, func


class BadgeToDepartment(Base):
    __tablename__ = "badge_to_department"
    id = Column(Integer, primary_key=True)
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    department = Column(Integer, ForeignKey(
        'department.id', ondelete="CASCADE"))


class DepartmentPermission(Base):
    __tablename__ = "department_permission"
    __url__ = "/api/event/<int:event>/department_permission"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    role = Column(Integer, ForeignKey(
        'department_role.id', ondelete="CASCADE"))


class DepartmentGrant(Base):
    __tablename__ = "department_grant"
    __url__ = "/api/event/<int:event>/department_grant"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    role = Column(Integer, ForeignKey(
        'department_role.id', ondelete="CASCADE"))
    department = Column(Integer, ForeignKey(
        'department.id', ondelete="CASCADE"), nullable=True)


class DepartmentRole(Base):
    __tablename__ = "department_role"
    __url__ = "/api/event/<int:event>/department_role"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    description = Column(String)
    permissions = relationship(
        DepartmentPermission, cascade="all, delete", passive_deletes=True)
    grants = relationship(
        DepartmentGrant, cascade="all, delete", passive_deletes=True)

class Badge(Base):
    __tablename__ = "badge"
    __url__ = "/api/event/<int:event>/badge"
    id = Column(Integer, primary_key=True)
    id.allow_r = {"searchname"}
    event = Column('event', Integer, ForeignKey('event.id', ondelete="CASCADE"))
    event_obj = relationship("Event", back_populates="badges")
    badge_type = Column(Integer, ForeignKey(
        'badge_type.id', ondelete="SET NULL"), nullable=True)
    printed_number = Column(String())
    printed_name = Column(String())
    public_name = Column(String())
    public_name.allow_r = {"searchname"}
    search_name = Column(String())
    search_name.allow_r = {"searchname"}
    first_name = Column(String())
    last_name = Column(String())
    legal_name = Column(String())
    legal_name_matches = Column(Boolean)
    emergency_contact_name = Column(String())
    emergency_contact_phone = Column(String())
    phone = Column(String())
    email = Column(String())
    user = Column(Integer, ForeignKey(
        'user.id', ondelete="SET NULL"), nullable=True)
    uber_id = Column(String(), unique=True, nullable=True)
    departments = relationship(
        "Department", secondary="badge_to_department", back_populates="badges")
    ribbons = relationship(
        "RibbonType", secondary="ribbon_to_badge", back_populates="badges")
    room_night_requests = relationship(
        "RoomNightRequest", cascade="all, delete", passive_deletes=True)
    room_night_assignments = relationship(
        "RoomNightAssignment", cascade="all, delete", passive_deletes=True)

    hotel_room_request = relationship(
        "HotelRoomRequest", cascade="all, delete", passive_deletes=True)
    shift_assignments = relationship("ShiftAssignment", viewonly=True)
    shifts = relationship("Shift", secondary="shift_assignment", viewonly=True)
    
    # --- 1. RELATIONSHIP for Shift Overlaps ---
    shift_overlap_nights = relationship(
        "HotelRoomNight",
        secondary="join(ShiftAssignment, Shift, ShiftAssignment.shift == Shift.id)",
        primaryjoin="Badge.id == ShiftAssignment.badge",
        secondaryjoin="""and_(
            Shift.event == HotelRoomNight.event,
            HotelRoomNight.restriction_mode == 'shift_window',
            Shift.starttime < HotelRoomNight.shift_endtime,
            (Shift.starttime + func.make_interval(0, 0, 0, 0, 0, 0, Shift.duration)) > HotelRoomNight.shift_starttime
        )""",
        viewonly=True,
        doc="Shift-window nights where one of this badge's shifts overlaps the window."
    )

    # --- 2. RELATIONSHIP for Manual Approvals ---
    manually_approved_nights = relationship(
        "HotelRoomNight",
        secondary="room_night_approval",
        primaryjoin="Badge.id == RoomNightApproval.badge",
        secondaryjoin="""and_(
            RoomNightApproval.room_night == HotelRoomNight.id,
            RoomNightApproval.approved == True
        )""",
        viewonly=True,
        doc="Hotel nights manually approved for this badge."
    )

    @property
    def shift_hours_nights(self):
        """Shift-hours nights where this badge has enough total shift hours."""
        from sqlalchemy import func as sqlfunc
        from sqlalchemy.orm import object_session
        from tuber.models.shift import Shift, ShiftAssignment
        from tuber.models.hotel import HotelRoomNight
        session = object_session(self)
        nights = session.query(HotelRoomNight).filter(
            HotelRoomNight.event == self.event,
            HotelRoomNight.restriction_mode == 'shift_hours',
            HotelRoomNight.shift_hours_required != None).all()
        if not nights:
            return []
        seconds = session.query(sqlfunc.sum(Shift.duration)).join(
            ShiftAssignment, ShiftAssignment.shift == Shift.id).filter(
            ShiftAssignment.badge == self.id).scalar() or 0
        hours = seconds / 3600
        return [x for x in nights if hours >= x.shift_hours_required]

    @property
    def approved_hotel_nights(self):
        """
        Returns a distinct, sorted list of all approved hotel nights
        by combining results from the underlying relationships.
        For bulk use, prefer tuber.api.night_approval.approved_night_ids.
        """
        all_nights = set()
        all_nights.update(self.shift_overlap_nights)
        all_nights.update(self.shift_hours_nights)
        all_nights.update(self.manually_approved_nights)
        all_nights.update(self.event_obj.unrestricted_nights)

        return list(all_nights)

class Department(Base):
    __tablename__ = "department"
    __url__ = "/api/event/<int:event>/department"
    id = Column(Integer, primary_key=True)
    uber_id = Column(String(), unique=True, nullable=True)
    description = Column(String(), nullable=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String(256))
    badges = relationship(
        "Badge", secondary="badge_to_department", back_populates="departments")


class BadgeType(Base):
    __tablename__ = "badge_type"
    __url__ = "/api/event/<int:event>/badge_type"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String())
    description = Column(String())


class RibbonType(Base):
    __tablename__ = "ribbon_type"
    __url__ = "/api/event/<int:event>/ribbon_type"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String())
    description = Column(String())
    badges = relationship(
        "Badge", secondary="ribbon_to_badge", back_populates="ribbons")


class RibbonToBadge(Base):
    __tablename__ = "ribbon_to_badge"
    id = Column(Integer, primary_key=True)
    ribbon = Column(Integer, ForeignKey('ribbon_type.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
