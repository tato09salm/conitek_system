from sqlalchemy import Column, Integer, String, Boolean
from services.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # Admin, Tesorero, Evaluador, Participante
    is_active = Column(Boolean, default=True)
