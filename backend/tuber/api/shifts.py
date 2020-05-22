from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema
from flask import g

class ScheduleSchema(ModelSchema):
    class Meta:
        model = Schedule
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'tags']

def schedulechange(db, schedule):
    pass

register_crud("schedules", ScheduleSchema(), onchange=schedulechange)

class ScheduleEventSchema(ModelSchema):
    class Meta:
        model = ScheduleEvent
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'starttime', 'duration', 'schedule']

def scheduleeventchange(db, scheduleevent):
    pass

register_crud("scheduleevents", ScheduleEventSchema(), onchange=scheduleeventchange, url_scheme="global")

class JobSchema(ModelSchema):
    class Meta:
        model = Job
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'documentation', 'method', 'signuprules', 'sticky', 'schedules', 'scheduleevents', 'roles', 'shifts']

def jobchange(db, job):
    pass

register_crud("jobs", JobSchema(), onchange=jobchange)

class ShiftSchema(ModelSchema):
    class Meta:
        model = Shift
        sqla_session = db.session
        fields = ['id', 'job', 'schedule', 'scheduleevent', 'starttime', 'duration', 'slots', 'filledslots', 'weighting']

def shiftchange(db, shift):
    pass

register_crud("shifts", ShiftSchema(), onchange=shiftchange, url_scheme="global")

class ShiftAssignmentSchema(ModelSchema):
    class Meta:
        model = ShiftAssignment
        sqla_session = db.session
        fields = ['id', 'badge', 'shift', 'signuptime']

def shiftassignmentchange(db, shiftassignment):
    pass

register_crud("shiftassignments", ShiftAssignmentSchema(), onchange=shiftassignmentchange, url_scheme="global")

class ShiftSignupSchema(ModelSchema):
    class Meta:
        model = ShiftSignup
        sqla_session = db.session
        fields = ['id', 'badge', 'job', 'shift', 'schedule', 'scheduleevent', 'starttime', 'duration']

register_crud("shiftsignups", ShiftSignupSchema(), url_scheme="global")

@app.route("/api/events/<int:event>/jobs/available", methods=["GET"])
def available_jobs(event):
    return ""

@app.route("/api/events/<int:event>/shifts/<int:shift>/signup", methods=["POST"])
def shift_signup(event, shift):
    return ""

@app.route("/api/events/<int:event>/jobs/<int:job>/dryrun", methods=["POST"])
def job_dryrun(event, job):
    return ""