from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship

class Email(Base):
    __tablename__ = "email"
    __url__ = "/api/event/<int:event>/email"
    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    description = Column(String())
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    code = Column(String(), nullable=True)
    subject = Column(String())
    body = Column(String())
    active = Column(Boolean)
    send_once = Column(Boolean)
    source = Column(Integer, ForeignKey('email_source.id'), nullable=True)
    receipts = relationship("EmailReceipt")

class EmailTrigger(Base):
    __tablename__ = "email_trigger"
    __url__ = "/api/event/<int:event>/email_trigger"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    trigger = Column(String())
    timestamp = Column(DateTime())
    context = Column(JSON())

class EmailSource(Base):
    __tablename__ = "email_source"
    __url__ = "/api/event/<int:event>/email_source"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    name = Column(String(), unique=True)
    description = Column(String(), nullable=True)
    address = Column(String())
    region = Column(String())
    ses_access_key = Column(String())
    ses_secret_key = Column(String())
    active = Column(Boolean)
    emails = relationship("Email")
    receipts = relationship("EmailReceipt")

class EmailReceipt(Base):
    __tablename__ = "email_receipt"
    __url__ = "/api/event/<int:event>/email_receipt"
    id = Column(Integer, primary_key=True)
    event = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"))
    email = Column(Integer, ForeignKey('email.id'))
    badge = Column(Integer, ForeignKey('badge.id'))
    source = Column(Integer, ForeignKey('email_source.id'))
    trigger = Column(Integer, ForeignKey('email_trigger.id'), nullable=True)
    to_address = Column(String())
    from_address = Column(String())
    subject = Column(String())
    body = Column(String())
    timestamp = Column(DateTime())
