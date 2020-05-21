from tuber import db

class Schedule(db.Model):
    """A Schedule is used to store ScheduleEvents that are used for shift 
    creation and the public event schedule.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    event = db.Column(db.Integer)
    tags = db.Column(db.JSON)

class ScheduleEvent(db.Model):
    """A ScheduleEvent is used to store when something will happen during an Event.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    starttime = db.Column(db.TIMESTAMP(timezone=True))
    duration = db.Column(db.Float),
    schedule = db.Column(db.Integer)

class JobScheduleAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    schedule = db.Column(db.Integer, db.ForeignKey('schedule.id'))

class JobScheduleEventAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.Integer, db.ForeignKey('job.id'))
    scheduleevent = db.Column(db.Integer, db.ForeignKey('scheduleevent.id'))

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
    event = db.Column(db.Integer)
    documentation = db.Column(db.String)
    department = db.Column(db.Integer)
    method = db.Column(db.JSON)
    signuprules = db.Column(db.JSON)
    sticky = db.Column(db.Boolean)
    schedules = db.relationship("schedule", secondary=JobScheduleAssociation)
    scheduleevents = db.relationship("scheduleevent", secondary=JobScheduleEventAssociation)
    roles = db.relationship("role", secondary=JobRoleAssociation)
    shifts = db.relationship("shift")

