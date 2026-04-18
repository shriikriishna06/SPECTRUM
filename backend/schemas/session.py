from pydantic import BaseModel

class SessionIntent(BaseModel):
    mood: str
    language_mode: str