from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime,UTC
from backend.db import Base

#pref table model
class Preferences(Base):
    __tablename__ = "preferences"

    pref_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))

    genres = Column(String)
    language = Column(String)
    runtime_pref = Column(String)
    risk = Column(String)

    ai_persona = Column(String, nullable=True)
    primary_genre = Column(String, nullable=True)
    tone_profile = Column(String, nullable=True)

    last_updated = Column(
        DateTime, 
        default=datetime.now(UTC), 
        onupdate=datetime.now(UTC)
    )
