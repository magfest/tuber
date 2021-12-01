from tuber import app
from flask import request, Response, stream_with_context, escape
from tuber.models import *
from tuber.database import db
from tuber.permissions import *
from botocore.exceptions import ClientError
from sqlalchemy.orm import joinedload
import datetime
import jinja2
import boto3
import lupa
from tuber.api import *
from tuber.models import *

def get_email_context(badge, tables):
    event = tables['Event']
    request = tables['HotelRoomRequest'].get(badge.id, HotelRoomRequest(declined=True))
    requested_nights = [x.room_night for x in request.room_night_requests if x.requested]
    assigned_nights = [x.room_night for x in request.room_night_assignments]
    hotel_room_ids = list(set([x.hotel_room for x in request.room_night_assignments]))
    hotel_rooms = []
    for room_id in hotel_room_ids:
        room = tables['HotelRoom'][room_id]
        assignments = list(room.room_night_assignments)
        assignments.sort(key=lambda x: tables['HotelRoomNight'][x.room_night].date)
        start_night = assignments[0].room_night
        end_night = assignments[-1].room_night
        roommates = {x.id: {"badge": tables['Badge'][x.id], "nights": []} for x in room.roommates}
        for i in assignments:
            roommates[i.badge]['nights'].append(i.room_night)
        for roommate in roommates:
            roommates[roommate]['nights'].sort()
        hotel_rooms.append({
            "roommates": roommates, 
            "messages": room.messages,
            "completed": room.completed,
            "start_night": start_night,
            "end_night": end_night,
        })

    approved_nights = []
    approving_depts = []
    approving_dept_ids = []
    hotel_room_nights = tables['HotelRoomNight']
    has_edge_night = any([tables['HotelRoomNight'][x.room_night].restricted for x in request.room_night_requests if x.requested])
    approvals = [x.room_night for x in request.room_night_approvals if x.approved]
    approving_dept_ids = [x.department for x in request.room_night_approvals if x.approved]
    approving_depts = [tables['Department'][x].name for x in set(approving_dept_ids)]
    approved_nights = [x.room_night for x in request.room_night_requests if x.requested and ((not tables['HotelRoomNight'][x.room_night].restricted) or (x.room_night in approvals))]
    
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
        "hotel_room_nights": hotel_room_nights,
        "has_edge_night": has_edge_night,
        "hotel_request": request,
    }

def generate_emails(email):
    source = db.query(EmailSource).filter(EmailSource.id == email.source).one()
    badges = db.query(Badge).filter(Badge.event == email.event).all()
    event = db.query(Event).filter(Event.id == email.event).one()

    L = lupa.LuaRuntime(register_eval=False)
    filter = L.execute(email.code)
    subject_template = jinja2.Template(email.subject)
    body_template = jinja2.Template(email.body)

    tables = {
        "Badge": {x.id: x for x in badges},
        "HotelRoomNight": {x.id: x for x in db.query(HotelRoomNight).filter(HotelRoomNight.event == email.event).all()},
        "HotelRoomRequest": { x.badge : x for x in db.query(HotelRoomRequest).filter(HotelRoomRequest.event == email.event)
            .options(joinedload(HotelRoomRequest.room_night_assignments))
            .options(joinedload(HotelRoomRequest.room_night_approvals))
            .options(joinedload(HotelRoomRequest.room_night_requests)).all()},
        "Department": {x.id: x for x in db.query(Department).filter(Department.event == email.event).all()},
        "HotelRoom": {x.id: x for x in db.query(HotelRoom).filter(HotelRoom.event == email.event)
            .options(joinedload(HotelRoom.room_night_assignments))
            .options(joinedload(HotelRoom.roommates)).all()},
        "Event": event,
    }
    
    for badge in badges:
        context = get_email_context(badge, tables)
        if filter(context):
            subject = subject_template.render(**context)
            body = body_template.render(**context)
            yield [badge.id, badge.email, source.address, subject, body]

@app.route('/api/event/<int:event>/email/<int:email>/csv')
def email_csv(event, email):
    if not check_permission('email.*.read', event=event):
        return "Permission Denied", 403
    email = db.query(Email).filter(Event.id == event, Email.id == email).one_or_none()
    if not email:
        return "Could not find requested email {}".format(email), 404

    def stream_emails():
        yield "Badge ID,To,From,Subject,Body\n"
        for i in generate_emails(email):
            yield '"{}","{}","{}","{}","{}"\n'.format(*i)

    headers = {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=emails.csv",
    }
    return Response(stream_with_context(stream_emails()), headers=headers)

@app.route('/api/event/<int:event>/email/<int:email>/trigger', methods=['POST'])
def api_email_trigger(event, email):
    if not check_permission('email.*.send', event=request.json['event']):
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

    return "", 200
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