from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.models.users import User
from backend.models.preferences import Preferences
from backend.utils.uuid_helper import generate_uuid

router = APIRouter(prefix="/init", tags=["User Init"])

#init user on land page
@router.post("/")
async def init_user(db: Session = Depends(get_db)):
    user_id = generate_uuid()

    user = User(user_id=user_id)
    db.add(user)
    db.commit()

    return {"user_id": user_id}

#checking user exists in db else fallback
@router.get("/exists/{user_id}")
async def user_exists(user_id: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.user_id == user_id).first()
    return { "exists": bool(exists) }

#checks whether or not user has onboarded else fallback
@router.get("/onboarded/{user_id}")
async def is_onboarded(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(Preferences).filter(Preferences.user_id == user_id).first()
    is_onboarded = preferences is not None and preferences.ai_persona is not None
    
    return { 
        "onboarded": is_onboarded,
        "user_id": user_id 
    }

#reset user preferences
@router.delete("/preferences/{user_id}")
async def reset_preferences(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(Preferences).filter(Preferences.user_id == user_id).first()
    if preferences:
        db.delete(preferences)
        db.commit()
    
    return {"message": "Preferences reset"}
