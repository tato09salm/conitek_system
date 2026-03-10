from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from services.database import Base

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"))
    title = Column(String)
    abstract = Column(Text)
    status = Column(String, default="Enviado") # Enviado, Evaluado, Aceptado, Rechazado
    
    evaluations = relationship("Evaluation", back_populates="paper")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    evaluator_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    comments = Column(Text)
    
    paper = relationship("Paper", back_populates="evaluations")