from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from services.database import Base

class ParticipantType(str, enum.Enum):
    ESTUDIANTE = "Estudiante"
    PROFESIONAL = "Profesional"
    PONENTE = "Ponente"

class Modality(str, enum.Enum):
    PRESENCIAL = "Presencial"
    VIRTUAL = "Virtual"

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    university = Column(String)
    p_type = Column(String) # Enum como string para simplificar
    modality = Column(String) # Enum como string
    phone = Column(String)
    
    payments = relationship("Payment", back_populates="participant")
    certificates = relationship("Certificate", back_populates="participant")