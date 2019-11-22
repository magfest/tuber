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
from tuber.api import *
from tuber.models import *
from marshmallow_sqlalchemy import ModelSchema

class EmailSchemaRead(ModelSchema):
    class Meta:
        model = Email
        fields = ['id', 'name', 'description', 'code', 'subject', 'body', 'active', 'send_once', 'source', 'receipts']

class EmailSchemaWrite(ModelSchema):
    class Meta:
        model = Email
        fields = ['id', 'name', 'description', 'code', 'subject', 'body', 'active', 'send_once']

register_crud("email", {EmailSchemaRead():["GET"], EmailSchemaWrite(): ["POST", "PATCH", "DELETE"]})

class EmailSourceSchemaRead(ModelSchema):
    class Meta:
        model = EmailSource
        fields = ['id', 'name', 'description', 'address', 'region', 'ses_access_key', 'ses_secret_key', 'emails', 'receipts']

class EmailSourceSchemaWrite(ModelSchema):
    class Meta:
        model = EmailSource
        fields = ['id', 'name', 'description', 'address', 'region', 'ses_access_key', 'ses_secret_key']

register_crud("email_source", {EmailSourceSchemaRead(): ["GET"], EmailSourceSchemaWrite(): ["POST", "PATCH", "DELETE"]})

class EmailReceiptSchemaRead(ModelSchema):
    class Meta:
        model = EmailReceipt
        fields = ['id', 'email', 'source', 'to_address', 'from_address', 'subject', 'body', 'timestamp']

register_crud("email_receipt", EmailReceiptSchemaRead(), methods=["GET"], url_scheme="badge")
            
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