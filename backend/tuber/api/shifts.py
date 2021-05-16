from tuber.api import *
from tuber.models import *
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
        schedule_events = db.query(ScheduleEvent).filter(or_(ScheduleEvent.schedule.in_([x.id for x in job.schedules]), ScheduleEvent.id.in_([x.id for x in job.schedule_events]))).all()

    if not schedule_event:
        # Completely regenerate this schedule. Drop and recreate everything.
        existing = db.query(Shift).filter(Shift.job == job.id).all()
        new = create_shift_schedule(job, schedule_events)
        for shift in existing:
            remove_shift(db, shift)
        db.flush()
        for shift in new:
            add_shift(db, shift)
    if schedule_event:
        # Find adjacent schedule events
        adjacent = []
        starttime = schedule_event.starttime - datetime.timedelta(seconds=10) # Treat times within 10 seconds as being adjacent
        endtime = schedule_event.starttime + datetime.timedelta(seconds=schedule_event.duration+10) # Calculate the endtime, and add 10 seconds of margin
        for event in schedule_events:
            if not event in adjacent:
                eventstart = event.starttime
                eventend = event.starttime + datetime.timedelta(seconds=event.duration)
                if eventstart <= starttime and eventend >= starttime:
                    adjacent.append(event)
                elif eventstart >= starttime and eventstart <= endtime:
                    adjacent.append(event)
        # Delete all adjacent schedule events
        for event in adjacent:
            shifts = db.query(Shift).filter(Shift.schedule_event == event.id).all()
            for shift in shifts:
                remove_shift(db, shift)
        db.flush()
        # Create new shifts for adjacent schedule events
        if request.method == "DELETE":
            adjacent.remove(schedule_event)
        new = create_shift_schedule(job, adjacent)
        for shift in new:
            add_shift(db, shift)
    shifts = db.query(Shift).filter(Shift.job == job.id).all()
    assignments = db.query(ShiftAssignment).all()
    return shifts

def schedulechange(db, schedule):
    if request.method == "DELETE":
        shifts = db.query(Shift).filter(Shift.schedule == schedule.id).all()
        list(map(db.delete, shifts))
        jobs = db.query(Job).filter(Job.schedules.any(Schedule.id == schedule.id)).all()
        for job in jobs:
            job.schedules.remove(schedule.id)
            db.add(job)
        shiftassignments = db.query(ShiftAssignment).filter(ShiftAssignment.shift.in_([x.id for x in shifts])).all()
        list(map(db.delete, shiftassignments))
        shiftsignups = db.query(ShiftSignup).filter(ShiftSignup.schedule == schedule.id).all()
        for signup in shiftsignups:
            signup.schedule = None
            db.add(signup)

def scheduleeventchange(db, schedule_event):
    jobs = db.query(Job).filter(Job.schedules.any(Schedule.id == schedule_event.schedule)).all()
    for job in jobs:
        reschedule_job(job, schedule_event=schedule_event)

def remove_shift(db, shift):
    signups = db.query(ShiftSignup).filter(ShiftSignup.shift == shift.id).order_by(ShiftSignup.signuptime.desc()).all()
    for signup in signups:
        signup.shift = None
        db.add(signup)
    db.query(ShiftAssignment).filter(ShiftAssignment.shift == shift.id).delete()
    db.delete(shift)    

def clear_broken_signups(db, shift):
    signups = db.query(ShiftSignup).filter(ShiftSignup.shift == shift.id).order_by(ShiftSignup.signuptime.desc()).all()
    for signup in signups:
        if signup.starttime != shift.starttime or signup.duration != shift.duration or signup.job != shift.job or shift.filledslots > shift.slots:
            signup.shift = None
            db.query(ShiftAssignment).filter(ShiftAssignment.shift == shift.id).delete()
            db.add(signup)
            shift.filledslots = max(0, shift.filledslots-1)
    db.add(shift)

def add_shift(db, shift):
    signups = db.query(ShiftSignup).filter(ShiftSignup.job == shift.job, ShiftSignup.starttime == shift.starttime, ShiftSignup.duration == shift.duration, ShiftSignup.shift == None).order_by(ShiftSignup.signuptime).all()
    for signup in signups:
        if shift.slots > shift.filledslots:
            db.add(shift)
            db.flush()
            signup.shift = shift.id
            db.add(signup)
            assignment = ShiftAssignment(badge=signup.badge, shift=shift.id)
            db.add(assignment)
            shift.filledslots += 1
    db.add(shift)

def shiftchange(db, shift):
    if request.method == "POST":
        add_shift(db, shift)
    elif request.method == "PATCH":
        clear_broken_signups(db, shift)
        add_shift(db, shift)
    elif request.method == "DELETE":
        clear_broken_signups(db, shift)

def shiftassignmentchange(db, shiftassignment):
    if request.method == "POST":
        shift = db.query(Shift).filter(Shift.id == shiftassignment.shift).one()
        shift.filledslots += 1
        if shift.filledslots > shift.slots:
            return "Too many badges assigned to shift.", 412
        db.add(shift)
    elif request.method == "DELETE":
        shift = db.query(Shift).filter(Shift.id == shiftassignmentchange.shift).one()
        shift.filledslots = max(0, shift.filledslots - 1)
        db.add(shift)

@app.route("/api/events/<int:event>/jobs/available", methods=["GET"])
def available_jobs(event):
    if "badge" in request.args:
        badge = db.query(Badge).filter(Badge.id == request.args['badge']).one_or_none()
    elif g.badge:
        badge = g.badge
    if not badge:
        return "Your current user does not have a badge and no badge was passed as a parameter.", 412
    all_roles = db.query(Role, Grant).join(Grant, Grant.role == Role.id).filter(Grant.user == badge.user).all()

    roles = {}
    for dept in badge.departments:
        roles[dept.id] = []
        for role, grant in all_roles:
            if grant.department == dept.id or grant.department is None:
                roles[dept.id].append(role.id)

    res = db.query(Department, Job).join(Job, Job.department == Department.id).filter(Department.id.in_([x.id for x in badge.departments])).all()
    jobs = []
    for department, job in res:
        for role in job.roles:
            if not role.id in roles[department.id]:
                break
        else:
            # All required roles are present, this user may sign up for this job.
            jobject = {
                "job": Job.serialize(job),
                "shifts": []
            }
            shifts = db.query(Shift).filter(Shift.job == job.id).all()
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
    if 'badge' in request.json:
        badge = db.query(Badge).filter(Badge.id == request.json['badge']).one()
    elif g.badge:
        badge = g.badge
    else:
        return "The current user does not have a badge, and thus cannot sign up for shifts.", 412
    shift = db.query(Shift).filter(Shift.id == shift).one()
    if shift.filledslots >= shift.slots:
        return "The shift is full.", 412
    shift.filledslots += 1
    assignment = ShiftAssignment(shift=shift.id, badge=badge.id)
    signup = ShiftSignup(badge=badge.id, shift=shift.id, job=shift.job, schedule=shift.schedule, schedule_event=shift.schedule_event, starttime=shift.starttime, duration=shift.duration)
    db.add(shift)
    db.add(assignment)
    db.add(signup)
    db.commit()
    return jsonify(shift=Shift.serialize(shift), shift_assignment=ShiftAssignment.serialize(assignment), shift_signup=ShiftSignup.serialize(signup))

@app.route("/api/events/<int:event>/jobs/<int:job>/dryrun", methods=["POST"])
def job_dryrun(event, job):
    jobobj = db.query(Job).filter(Job.id == job).one()
    for i in request.json:
        if hasattr(jobobj, i):
            setattr(jobobj, i, request.json[i])
    return jsonify(reschedule_job(jobobj))