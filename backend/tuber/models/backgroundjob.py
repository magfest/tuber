from tuber.models import Base
from sqlalchemy import Column, Integer, ForeignKey, String, JSON, LargeBinary

class BackgroundJob(Base):
    __tablename__ = "background_job"
    __url__ = "/api/job"
    id = Column(Integer, primary_key=True)
    session = Column(Integer, ForeignKey('session.id', ondelete="CASCADE"), nullable=True)
    uuid = Column(String)
    progress = Column(JSON)
    result = Column(LargeBinary)
    context = Column(JSON)