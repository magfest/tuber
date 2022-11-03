from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, JSON, DateTime, Float
from sqlalchemy.orm import relationship
import datetime

class Schedule(Base):
    """A Schedule is used to store ScheduleEvents that are used for shift 
    creation and the public event schedule.
    """
    __tablename__ = "schedule"
    __url__ = "/api/event/<int:event>/schedule"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    schedule_events = relationship("ScheduleEvent", cascade="all, delete", passive_deletes=True)
    tags = Column(JSON)

class ScheduleEvent(Base):
    """A ScheduleEvent is used to store when something will happen during an Event.
    """
    __tablename__ = "schedule_event"
    __url__ = "/api/event/<int:event>/schedule_event"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String)
    description = Column(String)
    starttime = Column(DateTime())
    duration = Column(Integer)
    schedule = Column(Integer, ForeignKey('schedule.id', ondelete="CASCADE"))

class JobScheduleAssociation(Base):
    __tablename__ = "job_schedule_association"
    __url__ = "/api/event/<int:event>/job_schedule_association"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    job = Column(Integer, ForeignKey('job.id', ondelete="CASCADE"))
    schedule = Column(Integer, ForeignKey('schedule.id', ondelete="CASCADE"))

class JobScheduleEventAssociation(Base):
    __tablename__ = "job_schedule_event_association"
    __url__ = "/api/event/<int:event>/job_schedule_event_association"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    job = Column(Integer, ForeignKey('job.id', ondelete="CASCADE"))
    schedule_event = Column(Integer, ForeignKey('schedule_event.id', ondelete="CASCADE"))

class JobRoleAssociation(Base):
    __tablename__ = "job_role_association"
    __url__ = "/api/event/<int:event>/job_role_association"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    job = Column(Integer, ForeignKey('job.id', ondelete="CASCADE"))
    role = Column(Integer, ForeignKey('department_role.id', ondelete="CASCADE"))

class Job(Base):
    """A Job describes something we might ask a volunteer to do. It holds the actual
    job description for the human as well as scheduling rules for the system to
    create Shifts. All Shifts are linked to a Job.
    """
    __tablename__ = "job"
    __url__ = "/api/event/<int:event>/job"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    documentation = Column(String)
    department = Column(Integer, ForeignKey('department.id', ondelete="CASCADE"))
    method = Column(JSON)
    signuprules = Column(JSON)
    sticky = Column(Boolean)
    schedules = relationship("Schedule", secondary="job_schedule_association")
    schedule_events = relationship("ScheduleEvent", secondary="job_schedule_event_association")
    roles = relationship("DepartmentRole", secondary="job_role_association")
    shifts = relationship("Shift")

class Shift(Base):
    """A Shift is a block of time that a staffer can sign up to work. All Shifts are linked to a Job.
    """
    __tablename__ = "shift"
    __url__ = '/api/event/<int:event>/shift'
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    job = Column(Integer, ForeignKey('job.id', ondelete="CASCADE"))
    schedule = Column(Integer, ForeignKey('schedule.id'))
    schedule_event = Column(Integer, ForeignKey('schedule_event.id'))
    starttime = Column(DateTime())
    duration = Column(Integer)
    slots = Column(Integer)
    filledslots = Column(Integer)
    weighting = Column(Float)

class ShiftAssignment(Base):
    """A ShiftAssignment connect badges to shifts that they will work. They store the current state,
    and may be blown away when jobs or schedules are changed without direct user intervention.
    """
    __tablename__ = "shift_assignment"
    __url__ = "/api/event/<int:event>/shift_assignment"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    shift = Column(Integer, ForeignKey('shift.id', ondelete="CASCADE"))

class ShiftSignup(Base):
    """A ShiftSignup tracks the intent of a user to signup for a shift. This is different than a
    ShiftAssignment. A ShiftSignup persists even if the underlying shift is removed, so that the
    user's desires are still known if a new, similar shift is created. Thus it must hold a copy
    of the associated shift so that it can be compared to potential replacement shifts.
    """
    __tablename__ = "shift_signup"
    __url__ = "/api/event/<int:event>/shift_signup"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    badge = Column(Integer, ForeignKey('badge.id', ondelete="CASCADE"))
    job = Column(Integer, ForeignKey('job.id'))
    shift = Column(Integer, ForeignKey('shift.id'))
    schedule = Column(Integer, ForeignKey('schedule.id'))
    schedule_event = Column(Integer, ForeignKey('schedule_event.id'))
    starttime = Column(DateTime())
    duration = Column(Integer())
    signuptime = Column(DateTime(), default=datetime.datetime.utcnow)