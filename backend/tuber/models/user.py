from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    __url__ = "/api/user"
    id = Column(Integer, primary_key=True)
    id.allow_r = {"self"}
    username = Column(String(80), unique=True)
    username.allow_rw = {"self"}
    email = Column(String(120), unique=True)
    email.allow_rw = {"self"}
    password = Column(String(128), default="")
    password.hidden = True
    active = Column(Boolean)
    active.allow_r = {"self"}
    badges = relationship("Badge")
    badges.allow_r = {"self"}
    sessions = relationship("Session")
    sessions.allow_r = {"self"}
    grants = relationship("Grant")
    grants.allow_r = {"self"}

class Session(Base):
    __tablename__ = "session"
    __url__ = "/api/session"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    secret = Column(String(64))
    secret.hidden = True
    permissions = Column(JSON)
    last_active = Column(DateTime)

class Permission(Base):
    __tablename__ = "permission"
    __url__ = "/api/permission"
    id = Column(Integer, primary_key=True)
    operation = Column(String(64))
    role = Column(Integer, ForeignKey('role.id'))

class Role(Base):
    __tablename__ = "role"
    __url__ = "/api/role"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    description = Column(String(128))
    permissons = relationship("Permission")

class Grant(Base):
    __tablename__ = "grant"
    __url__ = "/api/grant"
    # Null values become wildcards, i.e. if event is NULL, then the grant applies to all events
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey('user.id'), nullable=False)
    role = Column(Integer, ForeignKey('role.id'), nullable=False)
    event = Column(Integer, ForeignKey('event.id'), nullable=True)