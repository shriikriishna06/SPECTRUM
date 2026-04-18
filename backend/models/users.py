from sqlalchemy import Column, String, DateTime
from datetime import datetime
from backend.db import Base

#users table model
class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    age_group = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
