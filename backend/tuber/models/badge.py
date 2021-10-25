from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

class BadgeToDepartment(Base):
    __tablename__ = "badge_to_department"
    id = Column(Integer, primary_key=True)
    badge = Column(Integer, ForeignKey('badge.id'))
    department = Column(Integer, ForeignKey('department.id'))

class DepartmentPermission(Base):
    __tablename__ = "department_permission"
    __url__ = "/api/event/<int:event>/department_permission"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    event = Column(Integer, ForeignKey('event.id'))
    role = Column(Integer, ForeignKey('department_role.id'))

class DepartmentRole(Base):
    __tablename__ = "department_role"
    __url__ = "/api/event/<int:event>/department_role"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    event = Column(Integer, ForeignKey('event.id'))
    description = Column(String)
    permissions = relationship(DepartmentPermission)

class DepartmentGrant(Base):
    __tablename__ = "department_grant"
    __url__ = "/api/event/<int:event>/department_grant"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id'))
    event = Column(Integer, ForeignKey('event.id'))
    role = Column(Integer, ForeignKey('department_role.id'))
    department = Column(Integer, ForeignKey('department.id'), nullable=True)

class Badge(Base):
    __tablename__ = "badge"
    __url__ = "/api/event/<int:event>/badge"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id'))
    badge_type = Column(Integer, ForeignKey('badge_type.id'))
    printed_number = Column(String(32))
    printed_name = Column(String(256))
    search_name = Column(String(256))
    first_name = Column(String(128))
    last_name = Column(String(128))
    legal_name = Column(String(256))
    legal_name_matches = Column(Boolean)
    phone = Column(String(64))
    email = Column(String(128))
    user = Column(Integer, ForeignKey('user.id'), nullable=True)
    uber_id = Column(String(128), unique=True, nullable=True)
    departments = relationship("Department", secondary="badge_to_department", back_populates="badges")
    room_night_requests = relationship("RoomNightRequest")
    room_night_assignments = relationship("RoomNightAssignment")
    room_night_approvals = relationship("RoomNightApproval")
    hotel_room_request = relationship("HotelRoomRequest")

class Department(Base):
    __tablename__ = "department"
    __url__ = "/api/event/<int:event>/department"
    id = Column(Integer, primary_key=True)
    uber_id = Column(String(128), unique=True, nullable=True)
    description = Column(String(256), nullable=True)
    event = Column(Integer, ForeignKey('event.id'))
    name = Column(String(256))
    badges = relationship("Badge", secondary="badge_to_department", back_populates="departments")

class BadgeType(Base):
    __tablename__ = "badge_type"
    __url__ = "/api/event/<int:event>/badge_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    description = Column(String(256))

class RibbonType(Base):
    __tablename__ = "ribbon_type"
    __url__ = "/api/event/<int:event>/ribbon_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    description = Column(String(256))

class RibbonToBadge(Base):
    __tablename__ = "ribbon_to_badge"
    id = Column(Integer, primary_key=True)
    ribbon = Column(Integer, ForeignKey('ribbon_type.id'))
    badge = Column(Integer, ForeignKey('badge.id'))