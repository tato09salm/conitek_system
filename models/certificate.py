from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from services.database import Base
from datetime import datetime

class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    issue_date = Column(DateTime, default=datetime.utcnow)
    code = Column(String, unique=True)
    type = Column(String) # Asistencia, Ponencia
    
    participant = relationship("Participant", back_populates="certificates")