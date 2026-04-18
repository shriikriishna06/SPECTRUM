from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.schemas.preferences import PreferenceInput
from backend.models.preferences import Preferences
from backend.models.users import User
from backend.utils.uuid_helper import generate_uuid
from backend.services.gemini_service import analyze_taste
from backend.rate_limiter import limiter


router = APIRouter(prefix="/questionnaire", tags=["Questionnaire"])

#long term taste 
@router.post("/submit")
@limiter.limit("5/minute")
async def submit_preferences(request:Request,data: PreferenceInput, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.user_id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.age_group:
        user.age_group = data.age_group

    existing = db.query(Preferences).filter(
        Preferences.user_id == data.user_id
    ).first()

    if existing:
        pref = existing
        pref.genres = ",".join(data.genres)
        pref.language = data.language
        pref.runtime_pref = data.runtime_pref
        pref.risk = data.risk
    else:
        pref = Preferences(
            pref_id=generate_uuid(),
            user_id=data.user_id,
            genres=",".join(data.genres),
            language=data.language,
            runtime_pref=data.runtime_pref,
            risk=data.risk
        )
        db.add(pref)

    db.flush()

    needs_taste = not (pref.ai_persona or "").strip()
    taste = None

    if needs_taste:
        try:
            taste = await analyze_taste({
                "genres": data.genres,
                "language": data.language,
                "runtime_pref": data.runtime_pref,
                "risk": data.risk,
            })
            pref.ai_persona = taste["persona"]
            pref.primary_genre = taste["primary_genre"]
            pref.tone_profile = taste["tone_profile"]
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail=f"AI profile generation failed: {str(e)}. Please try again later."
            )

    db.commit()

    profile = taste or {
        "persona": pref.ai_persona,
        "primary_genre": pref.primary_genre,
        "tone_profile": pref.tone_profile,
    }
    return {
        "message": "Preferences saved" + ("; AI taste profile created" if needs_taste else ""),
        "ai_profile": profile,
    }