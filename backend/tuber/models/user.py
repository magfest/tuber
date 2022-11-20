from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"
    __url__ = "/api/user"
    id = Column(Integer, primary_key=True)
    id.allow_r = {"self"}
    username = Column(String(), unique=True)
    username.allow_rw = {"self"}
    email = Column(String(), unique=True)
    email.allow_rw = {"self"}
    password = Column(String(), default="")
    password.hidden = True
    active = Column(Boolean)
    active.allow_r = {"self"}
    badges = relationship("Badge")
    badges.allow_r = {"self"}
    sessions = relationship(
        "Session", cascade="all, delete", passive_deletes=True)
    sessions.allow_r = {"self"}
    grants = relationship("Grant", cascade="all, delete", passive_deletes=True)
    grants.allow_r = {"self"}
    default_event = Column(Integer, ForeignKey('event.id'))


class APIKey(Base):
    __tablename__ = "api_key"
    __url__ = "/api/api_key"
    id = Column(Integer, primary_key=True)
    key = Column(String)
    key.hidden = True
    user = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))
    allow = Column(String)
    enabled = Column(Boolean)


class Session(Base):
    __tablename__ = "session"
    __url__ = "/api/session"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    secret = Column(String())
    secret.hidden = True
    permissions = Column(JSON)
    last_active = Column(DateTime)


class Permission(Base):
    __tablename__ = "permission"
    __url__ = "/api/permission"
    id = Column(Integer, primary_key=True)
    operation = Column(String())
    role = Column(Integer, ForeignKey('role.id', ondelete="CASCADE"))


class Role(Base):
    __tablename__ = "role"
    __url__ = "/api/role"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    description = Column(String())
    permissons = relationship(
        "Permission", cascade="all, delete", passive_deletes=True)


class Grant(Base):
    __tablename__ = "grant"
    __url__ = "/api/grant"
    # Null values become wildcards, i.e. if event is NULL, then the grant applies to all events
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey(
        'user.id', ondelete="CASCADE"), nullable=False)
    role = Column(Integer, ForeignKey(
        'role.id', ondelete="CASCADE"), nullable=False)
    event = Column(Integer, ForeignKey(
        'event.id', ondelete="CASCADE"), nullable=True)
