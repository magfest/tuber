from tuber import db

class Email(db.Model):
    __tablename__ = "email"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    code = db.Column(db.String(4096), nullable=True)
    subject = db.Column(db.String(4096), nullable=False)
    body = db.Column(db.String(4096), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    send_once = db.Column(db.Boolean, nullable=False)
    source = db.Column(db.Integer, db.ForeignKey('email_source.id'), nullable=True)
    receipts = db.relationship("EmailReceipt")

class EmailTrigger(db.Model):
    __tablename__ = "email_trigger"
    id = db.Column(db.Integer, primary_key=True)
    trigger = db.Column(db.String(128), nullable=False)
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=True)
    context = db.Column(db.JSON())

class EmailSource(db.Model):
    __tablename__ = "email_source"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=True)
    event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    address = db.Column(db.String(128), nullable=False)
    region = db.Column(db.String(64), nullable=False)
    ses_access_key = db.Column(db.String(128), nullable=False)
    ses_secret_key = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean)
    emails = db.relationship("Email")
    receipts = db.relationship("EmailReceipt")

class EmailReceipt(db.Model):
    __tablename__ = "email_receipt"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Integer, db.ForeignKey('email.id'))
    badge = db.Column(db.Integer, db.ForeignKey('badge.id'))
    source = db.Column(db.Integer, db.ForeignKey('email_source.id'))
    trigger = db.Column(db.Integer, db.ForeignKey('email_trigger.id'), nullable=True)
    to_address = db.Column(db.String(1024), nullable=False)
    from_address = db.Column(db.String(1024), nullable=False)
    subject = db.Column(db.String(4096), nullable=False)
    body = db.Column(db.String(4096), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
