from tuber import db
import datetime

class Schedule(db.Model):
    """A Schedule is used to store ScheduleEvents that are used for shift 
    creation and the public event schedule.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    event = db.Column(db.Integer, db.ForeignKey('event.id'))
    tags = db.Column(db.JSON)

class ScheduleEvent(db.Model):
    """A ScheduleEvent is used to store when something will happen during an Event.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    starttime = db.Column(db.TIMESTAMP(timezone=True))
    duration = db.Column(db.Float)
    schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))

class JobScheduleAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))

class JobScheduleEventAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    schedule_event = db.Column(db.Integer, db.ForeignKey('schedule_event.id'))

class JobRoleAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    role = db.Column(db.Integer, db.ForeignKey('role.id'))

class Job(db.Model):
    """A Job describes something we might ask a volunteer to do. It holds the actual
    job description for the human as well as scheduling rules for the system to
    create Shifts. All Shifts are linked to a Job.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    event = db.Column(db.Integer, db.ForeignKey('event.id'))
    documentation = db.Column(db.String)
    department = db.Column(db.Integer, db.ForeignKey('department.id'))
    method = db.Column(db.JSON)
    signuprules = db.Column(db.JSON)
    sticky = db.Column(db.Boolean)
    schedules = db.relationship("Schedule", secondary="job_schedule_association")
    scheduleevents = db.relationship("ScheduleEvent", secondary="job_schedule_event_association")
    roles = db.relationship("Role", secondary="job_role_association")
    shifts = db.relationship("Shift")

class Shift(db.Model):
    """A Shift is a block of time that a staffer can sign up to work. All Shifts are linked to a Job.
    """
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    schedule_event = db.Column(db.Integer, db.ForeignKey('schedule_event.id'))
    starttime = db.Column(db.TIMESTAMP(timezone=True))
    duration = db.Column(db.Float)
    slots = db.Column(db.Integer)
    filledslots = db.Column(db.Integer)
    weighting = db.Column(db.Float)

class ShiftAssignment(db.Model):
    """A ShiftAssignment connect badges to shifts that they will work. They store the current state,
    and may be blown away when jobs or schedules are changed without direct user intervention.
    """
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))
    shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    signuptime = db.Column(db.TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)

class ShiftSignup(db.Model):
    """A ShiftSignup tracks the intent of a user to signup for a shift. This is different than a
    ShiftAssignment. A ShiftSignup persists even if the underlying shift is removed, so that the
    user's desires are still known if a new, similar shift is created. Thus it must hold a copy
    of the associated shift so that it can be compared to potential replacement shifts.
    """
    id = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    shift = db.Column(db.Integer, db.ForeignKey('shift.id'))
    schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    schedule_event = db.Column(db.Integer, db.ForeignKey('schedule_event.id'))
    starttime = db.Column(db.TIMESTAMP(timezone=True))
    duration = db.Float()