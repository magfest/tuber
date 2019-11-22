from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify, Response, stream_with_context
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt
from botocore.exceptions import ClientError
import datetime
import jinja2
import boto3
import uuid
import lupa
import csv
import io

@app.route('/api/emails', methods=['GET', 'POST'])
def api_emails():
    fields = ['name', 'description', 'code', 'subject', 'body', 'active', 'source', 'event', 'send_once']
    if request.method == 'GET':
        if not check_permission('emails.read', event=request.values['event']):
            return jsonify(success=False)
        emails = db.session.query(Email).filter(Email.event == request.values['event']).all()
        result = []
        for email in emails:
            result.append({ i:getattr(email, i) for i in ['id', *fields]})
        return jsonify(success=True, emails=result)
    if request.method == 'POST':
        if not check_permission('emails.write', event=request.json['event']):
            return jsonify(success=False)
        for i in fields:
            if not i in request.json:
                return jsonify(success=False, reason="{} is a required parameter".format(i))
        if ('id' in request.json) and request.json['id']:
            email = db.session.query(Email).filter(Email.id == request.json['id']).one_or_none()
            if not email:
                return jsonify(success=False, reason="Could not locate email {}".format(request.json['id']))
        else:
            email = Email()
        for i in fields:
            setattr(email, i, request.json[i])
        db.session.add(email)
        db.session.commit()
        res = {i:getattr(email, i) for i in ['id', *fields]}
        return jsonify(success=True, email=res)

@app.route('/api/emails/delete', methods=['POST'])
def api_emails_delete():
    if not check_permission('emails.write', event=request.json['event']):
        return jsonify(success=False, reason="Permission Denied")
    if not 'id' in request.json:
        return jsonify(success=False, reason="id is a required parameter")
    email = db.session.query(Email).filter(Email.id == request.json['id']).one_or_none()
    if not email:
        return jsonify(success=False, reason="Could not find email {}".format(request.json['id']))
    db.session.delete(email)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/emails/sources', methods=['GET', 'POST'])
def api_email_sources():
    fields = ['name', 'description', 'event', 'address', 'ses_access_key', 'ses_secret_key', 'region']
    if request.method == 'GET':
        if not check_permission('emailsource.read', event=request.values['event']):
            return jsonify(success=False)
        sources = db.session.query(EmailSource).filter(EmailSource.event == request.values['event']).all()
        result = []
        for source in sources:
            result.append({ i:getattr(source, i) for i in ['id', *fields]})
        return jsonify(success=True, sources=result)
    if request.method == 'POST':
        if not check_permission('emailsource.write', event=request.json['event']):
            return jsonify(success=False)
        for i in fields:
            if not i in request.json:
                return jsonify(success=False, reason="{} is a required parameter".format(i))
        if 'id' in request.json:
            source = db.session.query(EmailSource).filter(EmailSource.id == request.json['id']).one_or_none()
            if not source:
                return jsonify(success=False, reason="Could not locate email source {}".format(request.json['id']))
        else:
            source = EmailSource()
        for i in fields:
            setattr(source, i, request.json[i])
        db.session.add(source)
        db.session.commit()
        res = {i:getattr(source, i) for i in ['id', *fields]}
        return jsonify(success=True, email_source=res)

@app.route('/api/emails/sources/delete', methods=['POST'])
def api_emails_sources_delete():
    if not check_permission('emailsource.write', event=request.json['event']):
        return jsonify(success=False, reason="Permission Denied")
    if not 'id' in request.json:
        return jsonify(success=False, reason="id is a required parameter")
    emails = db.session.query(Email).filter(Email.source == request.json['id']).all()
    if email:
        return jsonify(success=False, reason="Email source {} is still in use.".format(request.json['id']))
    emailsource = db.session.query(EmailSource).filter(EmailSource.id == request.json['id']).one_or_none()
    if not emailsource:
        return jsonify(success=False, reason="Could not locate email source {}".format(request.json['id']))
    db.session.delete(emailsource)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/emails/receipts', methods=['GET'])
def api_email_receipts():
    if not check_permission('emailreceipt.read', event=request.values['event']):
        return jsonify(success=False, reason="Permission Denied")
    if not 'email' in request.values:
        return jsonify(success=False, reason="email is a required parameter")
    receipts = db.session.query(EmailReceipt).filter(EmailReceipt.email == request.values['email']).all()
    res = []
    for i in receipts:
        res.append({x: getattr(i, x) for x in ['id', 'email', 'badge', 'source', 'to_address', 'from_address', 'subject', 'body', 'timestamp']})
    return jsonify(success=True, receipts=res)
            
def get_email_context(badge, tables):
    event = db.session.query(Event).filter(Event.id == badge.event_id).one()
    requested_nights = [x.room_night for x in badge.room_night_requests if x.requested]
    assigned_nights = [x.room_night for x in badge.room_night_assignments]
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
        "hotel_room_nights": {x.id:x for x in hotel_room_nights},
        "has_edge_night": has_edge_night,
        "hotel_request": hotel_request,
    }

def generate_emails(email):
    source = db.session.query(EmailSource).filter(EmailSource.id == email.source).one()
    badges = db.session.query(Badge).filter(Badge.event_id == email.event).all()

    L = lupa.LuaRuntime(register_eval=False)
    filter = L.execute(email.code)
    subject_template = jinja2.Template(email.subject)
    body_template = jinja2.Template(email.body)

    tables = {
        "HotelRoomNight": db.session.query(HotelRoomNight).filter(HotelRoomNight.event == email.event).all(),
        "HotelRoomRequest": db.session.query(HotelRoomRequest).join(Badge, Badge.id == HotelRoomRequest.badge).filter(Badge.event_id == email.event).all(),
        "RoomNightApproval": db.session.query(RoomNightApproval).join(RoomNightRequest, RoomNightRequest.id == RoomNightApproval.room_night).filter(RoomNightApproval.approved == True).all(),
        "Department": {x.id: x for x in db.session.query(Department).filter(Department.event_id == email.event).all()},
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
        return jsonify(success=False, reason="Permission Denied")
    event = db.session.query(Event).filter(Event.id == request.args['event']).one()
    if not 'email' in request.args:
        return jsonify(success=False, reason="email is a required parameter")
    email = db.session.query(Email).filter(Email.id == request.args['email']).one_or_none()
    if not email:
        return jsonify(success=False, reason="Could not find requested email {}".format(request.args['email']))

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
        return jsonify(success=False, reason="Permission Denied")
    event = db.session.query(Event).filter(Event.id == request.json['event']).one()
    if not 'email' in request.json:
        return jsonify(success=False, reason="email is a required parameter")
    email = db.session.query(Email).filter(Email.id == request.json['email']).one_or_none()
    if not email:
        return jsonify(success=False, reason="Could not find requested email {}".format(request.json['email']))
    if not email.active:
        return jsonify(success=False, reason="Email must be activated before triggering.")
    source = db.session.query(EmailSource).filter(EmailSource.id == email.source).one_or_none()
    if not source:
        return jsonify(success=False, reason="Could not find EmailSource to send email from")

    client = boto3.client('ses', region_name=source.region, aws_access_key_id=source.ses_access_key, aws_secret_access_key=source.ses_secret_key)

    for compiled in generate_emails(email):
        if email.send_once:
            receipts = db.session.query(EmailReceipt).filter(EmailReceipt.email == email.id, EmailReceipt.badge == compiled[0]).all()
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
            db.session.add(receipt)
    db.session.commit()
    return jsonify(success=True)