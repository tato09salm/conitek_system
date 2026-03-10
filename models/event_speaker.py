from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from services.database import Base

class EventSpeaker(Base):
    __tablename__ = "event_speaker"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    participant_id = Column(Integer, ForeignKey("participants.id"))
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)
    __table_args__ = (UniqueConstraint('event_id', 'participant_id', 'paper_id', name='uq_event_speaker_triplet'),)
