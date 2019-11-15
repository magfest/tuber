from tuber import app, config, db
from flask import send_from_directory, send_file, request, jsonify
from tuber.models import *
from tuber.permissions import *
from passlib.hash import sha256_crypt
from botocore.exceptions import ClientError
import datetime
import jinja2
import boto3
import uuid
import lupa

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
            
@app.route('/api/emails/trigger', methods=['POST'])
def api_email_trigger():
    if not check_permission('email.send', event=request.json['event']):
        return jsonify(success=False, reason="Permission Denied")
    if not 'email' in request.json:
        return jsonify(success=False, reason="email is a required parameter")
    email = db.session.query(Email).filter(Email.id == request.json['email']).one_or_none()
    if not email:
        return jsonify(success=False, reason="Could not find requested email {}".format(request.json['email']))
    source = db.session.query(EmailSource).filter(EmailSource.id == email.source).one_or_none()
    if not source:
        return jsonify(success=False, reason="Could not find EmailSource to send email from")
    if 'badge' in request.json:
        badges = db.session.query(Badge).filter(Badge.id == request.json['event']).all()
    else:
        badges = db.session.query(Badge).filter(Badge.event_id == request.json['event']).all()

    L = lupa.LuaRuntime(register_eval=False)
    filter = L.execute(email.code)
    subject_template = jinja2.Template(email.subject)
    body_template = jinja2.Template(email.body)
    client = boto3.client('ses', region_name=source.region)
    for badge in badges:
        if email.send_once:
            receipts = db.session.query(EmailReceipt).filter(EmailReceipt.email == email.id, EmailReceipt.badge == badge.id).all()
            if receipts:
                continue
        context = {
            "badge": badge
        }
        if filter(context):
            subject = subject_template.render(**context)
            body = body_template.render(**context)

            try:
                client.send_email(
                    Destination={
                        'ToAddresses': [
                            badge.email,
                        ],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Charset': 'UTF-8',
                                'Data': body,
                            },
                        },
                        'Subject': {
                            'Charset': 'UTF-8',
                            'Data': subject,
                        },
                    },
                    Source=source.address,
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                receipt = EmailReceipt(email=email.id, badge=badge.id, source=source.id, to_address=badge.email, from_address=source.address, subject=subject, body=body, timestamp=datetime.datetime.now())
                db.session.add(receipt)
    db.session.commit()
    return jsonify(success=True)