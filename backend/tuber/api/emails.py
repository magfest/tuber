from tuber import app
from flask import request, Response, stream_with_context, escape
from tuber.models import *
from tuber.database import db
from tuber.permissions import *
from botocore.exceptions import ClientError
import datetime
import jinja2
import boto3
import lupa
from tuber.api import *
from tuber.models import *

def get_email_context(badge, tables):
    event = db.query(Event).filter(Event.id == badge.event).one()
    requested_nights = [x.room_night for x in badge.room_night_requests if x.requested]
    assigned_nights = [x.room_night for x in badge.room_night_assignments]
    hotel_room_ids = list(set([x.hotel_room for x in badge.room_night_assignments]))
    hotel_rooms = []
    for room in hotel_room_ids:
        assignments = [x for x in tables['RoomNightAssignment'] if x.hotel_room == room]
        start_night = assignments[0].room_night
        end_night = assignments[0].room_night
        for i in assignments:
            if i.room_night < start_night:
                start_night = i.room_night
            if i.room_night > end_night:
                end_night = i.room_night
        roommates = {}
        for i in assignments:
            if not i.badge in roommates:
                roommates[i.badge] = {
                    "badge": tables['Badge'][i.badge],
                    "nights": [i.room_night,],
                }
            else:
                if not i.room_night in roommates[i.badge]['nights']:
                    roommates[i.badge]['nights'].append(i.room_night)
        for roommate in roommates.keys():
            roommates[roommate]['nights'].sort()
        hotel_rooms.append({
            "roommates": roommates, 
            "messages": tables['HotelRoom'][room].messages,
            "completed": tables['HotelRoom'][room].completed,
            "start_night": start_night,
            "end_night": end_night,
        })
    approved_nights = []
    approving_depts = []
    approving_dept_ids = []
    hotel_room_nights = tables['HotelRoomNight']
    has_edge_night = False
    for night in hotel_room_nights:
        if night.id in requested_nights and not night.restricted:
            approved_nights.append(night.id)
        if night.id in requested_nights and night.restricted:
            has_edge_night = True
    for approval in tables['RoomNightApproval']:
        for rnr in badge.room_night_requests:
            if rnr.id == approval.room_night:
                if not rnr.room_night in approved_nights:
                    approved_nights.append(rnr.room_night)
                if not approval.department in approving_dept_ids:
                    approving_dept_ids.append(approval.department)
                    approving_depts.append(tables['Department'][approval.department].name)            
    hotel_request = [x for x in tables['HotelRoomRequest'] if x.badge == badge.id]
    if hotel_request:
        hotel_request = hotel_request[0]
    else:
        hotel_request = HotelRoomRequest(declined=True)
    requested_nights.sort()
    assigned_nights.sort()
    approved_nights.sort()
    return {
        "badge": badge,
        "event": event,
        "requested_nights": requested_nights,
        "assigned_nights": assigned_nights,
        "approved_nights": approved_nights,
        "approving_depts": ", ".join(approving_depts),
        "hotel_rooms": hotel_rooms,
        "hotel_room_nights": {x.id:x for x in hotel_room_nights},
        "has_edge_night": has_edge_night,
        "hotel_request": hotel_request,
    }

def generate_emails(email):
    source = db.query(EmailSource).filter(EmailSource.id == email.source).one()
    badges = db.query(Badge).filter(Badge.event == email.event).all()

    L = lupa.LuaRuntime(register_eval=False)
    filter = L.execute(email.code)
    subject_template = jinja2.Template(email.subject)
    body_template = jinja2.Template(email.body)

    tables = {
        "HotelRoomNight": db.query(HotelRoomNight).filter(HotelRoomNight.event == email.event).all(),
        "HotelRoomRequest": db.query(HotelRoomRequest).join(Badge, Badge.id == HotelRoomRequest.badge).filter(Badge.event == email.event).all(),
        "RoomNightApproval": db.query(RoomNightApproval).join(RoomNightRequest, RoomNightRequest.id == RoomNightApproval.room_night).filter(RoomNightApproval.approved == True).all(),
        "Department": {x.id: x for x in db.query(Department).filter(Department.event == email.event).all()},
        "HotelRoom": {x.id: x for x in db.query(HotelRoom).all()},
        "Badge": {x.id: x for x in db.query(Badge).filter(Badge.event_id == email.event).all()},
        "RoomNightAssignment": db.query(RoomNightAssignment).all(),
    }
    
    for badge in badges:
        context = get_email_context(badge, tables)
        if filter(context):
            subject = subject_template.render(**context)
            body = body_template.render(**context)
            yield [badge.id, badge.email, source.address, subject, body]

@app.route('/api/emails/csv')
def email_csv():
    if not check_permission('email.read', event=request.args['event']):
        return "Permission Denied", 403
    event = db.query(Event).filter(Event.id == request.args['event']).one()
    if not 'email' in request.args:
        return "email is a required parameter", 406
    email = db.query(Email).filter(Email.id == request.args['email']).one_or_none()
    if not email:
        return "Could not find requested email {}".format(escape(request.args['email'])), 404

    def stream_emails():
        yield "Badge ID,To,From,Subject,Body\n"
        for i in generate_emails(email):
            yield '"{}","{}","{}","{}","{}"\n'.format(*i)

    headers = {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=emails.csv",
    }
    return Response(stream_with_context(stream_emails()), headers=headers)

@app.route('/api/emails/trigger', methods=['POST'])
def api_email_trigger():
    if not check_permission('email.send', event=request.json['event']):
        return "Permission Denied", 403
    event = db.query(Event).filter(Event.id == request.json['event']).one()
    if not 'email' in request.json:
        return "email is a required parameter", 400
    email = db.query(Email).filter(Email.id == request.json['email']).one_or_none()
    if not email:
        return "Could not find requested email {}".format(escape(request.json['email'])), 404
    if not email.active:
        return "Email must be activated before triggering.", 400
    source = db.query(EmailSource).filter(EmailSource.id == email.source).one_or_none()
    if not source:
        return "Could not find EmailSource to send email from", 400
    if not source.active:
        return "The email source for this email is inactive.", 400

    def stream_emails():
        client = boto3.client('ses', region_name=source.region, aws_access_key_id=source.ses_access_key, aws_secret_access_key=source.ses_secret_key)
        yield '{'
        for compiled in generate_emails(email):
            if email.send_once:
                receipts = db.query(EmailReceipt).filter(EmailReceipt.email == email.id, EmailReceipt.badge == compiled[0]).all()
                if receipts:
                    continue
            try:
                client.send_email(
                    Destination={
                        'ToAddresses': [
                            compiled[1],
                        ],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Charset': 'UTF-8',
                                'Data': compiled[4],
                            },
                        },
                        'Subject': {
                            'Charset': 'UTF-8',
                            'Data': compiled[3],
                        },
                    },
                    Source=source.address,
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                receipt = EmailReceipt(email=email.id, badge=compiled[0], source=source.id, to_address=compiled[1], from_address=source.address, subject=compiled[3], body=compiled[4], timestamp=datetime.datetime.now())
                db.add(receipt)
                db.commit()
            yield '"{}": true,'.format(compiled[0])
        yield '}'
    headers = {
        "Content-Type": "application/json",
        "Content-Disposition": "attachment; filename=emails.json",
    }
    return Response(stream_with_context(stream_emails()), headers=headers)