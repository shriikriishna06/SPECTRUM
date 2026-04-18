from pydantic import BaseModel
from typing import List, Optional

class PreferenceInput(BaseModel):
    user_id: str
    age_group: Optional[str] = None
    genres: List[str]
    language: str
    runtime_pref: str
    risk: str
