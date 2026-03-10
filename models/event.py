from sqlalchemy import Column, Integer, String, Date, Boolean
from services.database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    event_date = Column(Date)
    location = Column(String)
    capacity = Column(Integer, default=500)
    current_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
