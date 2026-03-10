from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from services.database import Base
from datetime import datetime

class PaymentFile(Base):
    __tablename__ = "payment_files"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), index=True, nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
