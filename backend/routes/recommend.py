from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio
from backend.rate_limiter import limiter
from backend.db import get_db
from backend.schemas.recommend import RecommendRequest
from backend.models.users import User
from backend.models.preferences import Preferences
from backend.services.tmdb_service import fetch_movies, fetch_watch_providers
from backend.services.ranking_engine import rank_movies
from backend.services.gemini_service import rank_movie_candidates
from backend.services.explain import build_reasons

_INDIAN_ORIGINAL_LANG_CODES = ["hi", "ta", "te", "ml", "kn", "mr", "bn"]
_RECOMMEND_COUNT = 8

router = APIRouter(prefix="/recommend", tags=["Recommend"])

#recommendation api
@router.post("/")
@limiter.limit("15/minute")
async def recommend(request: Request, req: RecommendRequest, db: Session = Depends(get_db)):

    try:
        user = db.query(User).filter(User.user_id == req.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        prefs = db.query(Preferences).filter(
            Preferences.user_id == req.user_id
        ).first()

        if not prefs:
            raise HTTPException(
                status_code=400,
                detail="Preferences not found"
            )

        preferred_languages = []
        if prefs.language:
            preferred_languages = [l.strip().lower() for l in prefs.language.split(",")]

        if req.session.language_mode == "primary_only":
            languages = preferred_languages

        elif req.session.language_mode == "mixed_indian":
            languages = list(
                set(preferred_languages + _INDIAN_ORIGINAL_LANG_CODES)
            )

        else:
            languages = list(
                set(preferred_languages + _INDIAN_ORIGINAL_LANG_CODES + ["en"])
            )

        candidates = await fetch_movies(
            genres=prefs.genres or "",
            language_codes=languages,
            session_mood=req.session.mood,
        )

        if not candidates:
            return {
                "status": "ok",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": 0,
                "recommendations": []
            }

        unique = {m["id"]: m for m in candidates if "id" in m}
        candidates = list(unique.values())

        session_dict = req.session.model_dump()

        shortlist = await rank_movies(
            movies=candidates,
            session=session_dict,
            preferred_languages=languages,
            prefs=prefs,
            limit=28,
        )
        ranked, ai_reasons = await rank_movie_candidates(
            shortlist,
            prefs,
            session_dict,
            req.session.language_mode,
            limit=_RECOMMEND_COUNT,
        )
        if not ranked:
            ranked = await rank_movies(
                movies=candidates,
                session=session_dict,
                preferred_languages=languages,
                prefs=prefs,
                limit=_RECOMMEND_COUNT,
            )
            ai_reasons = {}

        final = []

        watch_tasks = [fetch_watch_providers(m["id"]) for m in ranked]
        watch_results = await asyncio.gather(*watch_tasks)

        for idx, m in enumerate(ranked):
            try:
                watch_on = watch_results[idx]

                why = build_reasons(m, prefs, req.session)
                ai_line = ai_reasons.get(m["id"])
                if ai_line:
                    why = ([ai_line] + why)[:3]

                final.append({
                    "id": m["id"],
                    "title": m.get("title") or m.get("name"),
                    "poster": m.get("poster_path"),
                    "type": "movie",
                    "language": m.get("original_language"),
                    "why_recommended": why,
                    "watch_on": watch_on,
                    "tmdb_link": f"https://www.themoviedb.org/movie/{m['id']}",
                })
            except Exception as e:
                raise HTTPException(detail={"error":f'{e}'})

        return {
            "status": "ok",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(final),
            "recommendations": final
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")