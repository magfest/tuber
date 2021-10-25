from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship

class Email(Base):
    __tablename__ = "email"
    __url__ = "/api/event/<int:event>/email"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    description = Column(String(256))
    event = Column(Integer, ForeignKey('event.id'))
    code = Column(String(4096), nullable=True)
    subject = Column(String(4096))
    body = Column(String(4096))
    active = Column(Boolean)
    send_once = Column(Boolean)
    source = Column(Integer, ForeignKey('email_source.id'), nullable=True)
    receipts = relationship("EmailReceipt")

class EmailTrigger(Base):
    __tablename__ = "email_trigger"
    __url__ = "/api/event/<int:event>/email_trigger"
    id = Column(Integer, primary_key=True)
    trigger = Column(String(128))
    timestamp = Column(DateTime())
    context = Column(JSON())

class EmailSource(Base):
    __tablename__ = "email_source"
    __url__ = "/api/event/<int:event>/email_source"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    description = Column(String(256), nullable=True)
    event = Column(Integer, ForeignKey('event.id'))
    address = Column(String(128))
    region = Column(String(64))
    ses_access_key = Column(String(128))
    ses_secret_key = Column(String(128))
    active = Column(Boolean)
    emails = relationship("Email")
    receipts = relationship("EmailReceipt")

class EmailReceipt(Base):
    __tablename__ = "email_receipt"
    __url__ = "/api/event/<int:event>/email_receipt"
    id = Column(Integer, primary_key=True)
    email = Column(Integer, ForeignKey('email.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    source = Column(Integer, ForeignKey('email_source.id'))
    trigger = Column(Integer, ForeignKey('email_trigger.id'), nullable=True)
    to_address = Column(String(1024))
    from_address = Column(String(1024))
    subject = Column(String(4096))
    body = Column(String(4096))
    timestamp = Column(DateTime())
