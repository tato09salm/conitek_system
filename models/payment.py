from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from services.database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    amount = Column(Float)
    method = Column(String) # Yape, Plin, Transferencia
    reference = Column(String)
    status = Column(String, default="Pendiente") # Pendiente, Aprobado
    created_at = Column(DateTime, default=datetime.utcnow)
    
    participant = relationship("Participant", back_populates="payments")