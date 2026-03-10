from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from services.database import Base
from datetime import datetime

class PaperFile(Base):
    __tablename__ = "paper_files"
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    filename = Column(String)
    path = Column(String)
    mime_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
