from tuber.models import Base
from sqlalchemy import Column, Integer, String

class Event(Base):
    __tablename__ = "event"
    __url__ = "/api/event"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    description = Column(String(256))
