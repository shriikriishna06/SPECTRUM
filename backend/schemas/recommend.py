from pydantic import BaseModel
from backend.schemas.session import SessionIntent

class RecommendRequest(BaseModel):
    user_id: str
    session: SessionIntent
