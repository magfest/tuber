from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema
from flask import g, request, jsonify
from sqlalchemy import or_
import datetime

def create_shift_schedule(job, schedule_events=[]):
    res = []
    if job.method['name'] == "copy":
        for event in schedule_events:
            res.append(Shift(job=job.id, schedule=event.schedule, schedule_event=event.id, starttime=event.starttime, duration=event.duration, slots=job.method['slots'], filledslots=0))
    return res

def reschedule_job(job, schedule_event=None):
    """Regenerates the shifts associated with this job. If a schedule_event is passed then it will
    only regenerate overlapping shifts.
    """
    if schedule_event:
        schedule_events = [schedule_event]
    else:
        schedule_events = db.session.query(ScheduleEvent).filter(or_(ScheduleEvent.schedule._in(job.schedules), ScheduleEvent.id._in(job.schedule_events))).all()

    if not schedule_event:
        # Completely regenerate this schedule. Drop and recreate everything.
        existing = db.session.query(Shift).filter(Shift.job == job.id).all()
        new = create_shift_schedule(job, schedule_events)
        for shift in existing:
            clear_broken_signups(db, shift)
        for shift in new:
            add_fixed_signups(db, shift)
    if schedule_event:
        # Find adjacent schedule events
        adjacent = [schedule_event]
        starttime = schedule_event.starttime - datetime.timedelta(seconds=10) # Treat times within 10 seconds as being adjacent
        endtime = schedule_event.starttime + datetime.timedelta(seconds=schedule_event.duration+10) # Calculate the endtime, and add 10 seconds of margin
        for event in schedule_events:
            eventstart = event.starttime
            eventend = event.starttime + datetime.timedelta(seconds=event.duration)
            if eventstart <= starttime and eventend >= starttime:
                adjacent.append(event)
            elif eventstart >= starttime and eventstart <= endtime:
                adjacent.append(event)
        # Delete all adjacent schedule events
        for event in adjacent:
            shifts = db.session.query(Shift).filter(Shift.schedule_event == event.id).all()
            for shift in shifts:
                clear_broken_signups(db, shift)
        # Create new shifts for adjacent schedule events
        new = create_shift_schedule(job, adjacent)
        for shift in new:
            add_fixed_signups(db, shift)
    shifts = db.session.query(Shift).filter(Shift.job == job.id).all()
    return shifts

class ScheduleSchema(ModelSchema):
    class Meta:
        model = Schedule
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'tags']

def schedulechange(db, schedule):
    if request.method == "DELETE":
        shifts = db.session.query(Shift).filter(Shift.schedule == schedule.id).all()
        list(map(db.session.delete, shifts))
        jobs = db.session.query(Job).filter(Job.schedules.any(Schedule.id == schedule.id)).all()
        for job in jobs:
            job.schedules.remove(schedule.id)
            db.session.add(job)
        shiftassignments = db.session.query(ShiftAssignment).filter(ShiftAssignment.shift._in([x.id for x in shifts])).all()
        list(map(db.session.delete, shiftassignments))
        shiftsignups = db.session.query(ShiftSignup).filter(ShiftSignup.schedule == schedule.id).all()
        for signup in shiftsignups:
            signup.schedule = None
            db.session.add(signup)

register_crud("schedules", ScheduleSchema(), onchange=schedulechange)

class ScheduleEventSchema(ModelSchema):
    class Meta:
        model = ScheduleEvent
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'starttime', 'duration', 'schedule']

def scheduleeventchange(db, schedule_event):
    jobs = db.session.query(Job).filter(Job.schedule == schedule_event.schedule).all()
    for job in jobs:
        reschedule_job(job, schedule_event=schedule_event)

register_crud("scheduleevents", ScheduleEventSchema(), onchange=scheduleeventchange, url_scheme="global")

class JobSchema(ModelSchema):
    class Meta:
        model = Job
        sqla_session = db.session
        fields = ['id', 'name', 'description', 'documentation', 'method', 'signuprules', 'sticky', 'schedules', 'scheduleevents', 'roles', 'shifts']

def jobchange(db, job):
    reschedule_job(job)

register_crud("jobs", JobSchema(), onchange=jobchange)

class ShiftSchema(ModelSchema):
    class Meta:
        model = Shift
        sqla_session = db.session
        fields = ['id', 'job', 'schedule', 'scheduleevent', 'starttime', 'duration', 'slots', 'filledslots', 'weighting']

def clear_broken_signups(db, shift):
    signups = db.session.query(ShiftSignup).filter(ShiftSignup.shift == shift.id).order_by(ShiftSignup.signuptime.desc()).all()
    for signup in signups:
        if signup.starttime != shift.starttime or signup.duration != shift.duration or signup.job != shift.job or shift.filledslots > shift.slots:
            signup.shift = None
            db.session.add(signup)
            shift.filledslots = max(0, shift.filledslots-1)
    
    db.session.add(shift)

def add_fixed_signups(db, shift):
    signups = db.session.query(ShiftSignup).filter(ShiftSignup.job == shift.job, ShiftSignup.starttime == shift.starttime, ShiftSignup.duration == shift.duration, ShiftSignup.shift == None).order_by(ShiftSignup.signuptime).all()
    for signup in signups:
        if shift.slots > shift.filledslots:
            signup.shift = shift.id
            db.session.add(signup)
            assignment = ShiftAssignment(badge=signup.badge, shift=shift.id)
            db.session.add(assignment)
            shift.filledslots += 1
    db.session.add(shift)

def shiftchange(db, shift):
    if request.method == "POST":
        add_fixed_signups(db, shift)
    elif request.method == "PATCH":
        clear_broken_signups(db, shift)
        add_fixed_signups(db, shift)
    elif request.method == "DELETE":
        clear_broken_signups(db, shift)

register_crud("shifts", ShiftSchema(), onchange=shiftchange, url_scheme="global")

class ShiftAssignmentSchema(ModelSchema):
    class Meta:
        model = ShiftAssignment
        sqla_session = db.session
        fields = ['id', 'badge', 'shift', 'signuptime']

def shiftassignmentchange(db, shiftassignment):
    if request.method == "POST":
        shift = db.session.query(Shift).filter(Shift.id == shiftassignment.shift).one()
        shift.filledslots += 1
        if shift.filledslots > shift.slots:
            return "Too many badges assigned to shift.", 412
        db.session.add(shift)
    elif request.method == "DELETE":
        shift = db.session.query(Shift).filter(Shift.id == shiftassignmentchange.shift).one()
        shift.filledslots = max(0, shift.filledslots - 1)
        db.session.add(shift)

register_crud("shiftassignments", ShiftAssignmentSchema(), methods=["GET", "POST", "DELETE"], onchange=shiftassignmentchange, url_scheme="global")

class ShiftSignupSchema(ModelSchema):
    class Meta:
        model = ShiftSignup
        sqla_session = db.session
        fields = ['id', 'badge', 'job', 'shift', 'schedule', 'scheduleevent', 'starttime', 'duration']

register_crud("shiftsignups", ShiftSignupSchema(), url_scheme="global")

@app.route("/api/events/<int:event>/jobs/available", methods=["GET"])
def available_jobs(event):
    if "badge" in request.args:
        badge = db.session.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
    elif g.badge:
        badge = g.badge
    if not badge:
        return "Your current user does not have a badge and no badge was passed as a parameter.", 412
    all_roles = db.session.query(Role, Grant).join(Grant, Grant.role == Role.id).filter(Grant.user == badge.user).all()
    roles = {}
    for dept in badge.departments:
        roles[dept.id] = []
        for role, grant in all_roles:
            if grant.department == dept:
                roles[dept.id].append(role.id)

    res = db.session.query(Department, Job).join(Job, Job.department == Department.id).filter(Department.id._in(badge.departments)).all()
    jobs = []
    for department, job in res:
        for role in job.roles:
            if not role in roles[department.id]:
                break
        else:
            # All required roles are present, this user may sign up for this job.
            jobject = {
                "job": job,
                "shifts": []
            }
            shifts = db.session.query(Shift).filter(Shift, Shift.job == job.id).all()
            for shift in shifts:
                jobject['shifts'].append({
                    'id': shift.id,
                    'job': shift.job,
                    'schedule': shift.schedule, 
                    'schedule_event': shift.schedule_event, 
                    'starttime': shift.starttime,
                    'duration': shift.duration,
                    'slots': shift.slots,
                    'filledslots': shift.filledslots,
                    'weighting': shift.weighting,
                    'blocks': []
                })
                if shift.filledslots >= shift.slots:
                    jobject['shifts'][-1]['blocks'].append("Shift is full.")
            jobs.append(jobject)
    return jsonify(jobs)

@app.route("/api/events/<int:event>/shifts/<int:shift>/signup", methods=["POST"])
def shift_signup(event, shift):
    if not g.badge:
        return "The current user does not have a badge, and thus cannot sign up for shifts.", 412
    shift = db.session.query(Shift).filter(Shift.id == shift).one()
    if shift.filledslots >= shift.slots:
        return "The shift is full.", 412
    shift.filledslots += 1
    assignment = ShiftAssignment(shift=shift.id, badge=badge.id)
    signup = ShiftSignup(shift=shift.id, job=shift.job, schedule=shift.schedule, schedule_event=shift.schedule_event, starttime=shift.starttime, duration=shift.duration)
    db.session.add(shift)
    db.session.add(assignment)
    db.session.add(signup)
    db.session.commit()
    return jsonify(shift=shift, shift_assignment=assignment, shift_signup=signup)

@app.route("/api/events/<int:event>/jobs/<int:job>/dryrun", methods=["POST"])
def job_dryrun(event, job):
    return jsonify(reschedule_job(job))