from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from services.database import Base
from datetime import datetime

class EventRegistration(Base):
    __tablename__ = "event_registration"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    participant_id = Column(Integer, ForeignKey("participants.id"))
    status = Column(String, default="Pendiente")
    payment_reference = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
