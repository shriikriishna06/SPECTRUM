import os
import json
from dotenv import load_dotenv
from google import genai
from fastapi import HTTPException
import asyncio

from backend.services.tmdb_service import GENRE_MAP

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

_GENRE_ID_TO_NAME = {v: k for k, v in GENRE_MAP.items()}

def _genre_labels(genre_ids):
    if not genre_ids:
        return []
    return [_GENRE_ID_TO_NAME.get(gid, str(gid)) for gid in genre_ids]

def _parse_json_response(text: str):
    text = (text or "").strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

#gemini user long term taste analysis
async def analyze_taste(preferences: dict):
    """
    Long-term taste only: genres, language, runtime_pref, risk.
    Session mood is applied separately at recommendation time.
    """

    PROMPT = f"""
    You are an expert movie taste analyzer.
    You will receive coded preference values.
    Interpret them as follows:
    Language codes:
    en = English
    ta = Tamil
    hi = Hindi
    te = Telugu
    kn = Kannada
    ml = Malayalam  
    es = Spanish
    ja = Japanese
    ko = Korean
    Runtime preferences:
    short = movies under 90 minutes
    long = feature-length movies (2 hours or more)
    any = no runtime preference

    Risk appetite:
    high = enjoys experimenting with new or unfamiliar content
    low = prefers familiar and safe choices

    Always convert codes into their natural language meaning before analyzing taste.

    Based on this user's long-term preferences:
    Genres: {preferences.get('genres')}
    Language: {preferences.get('language')}
    Runtime Preference: {preferences.get('runtime_pref')}
    Risk Tolerance: {preferences.get('risk')}

    Return ONLY STRICT JSON with exactly these keys:
    persona
    primary_genre
    tone_profile

    Example:(treat this as an example only)
    {{
    "persona": "Loves dark intense thrillers with strong story depth",
    "primary_genre": "Thriller",
    "tone_profile": "Dark, emotional, story-driven"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT
        )

        text = response.text.strip()

        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text)

        return {
            "persona": data.get("persona"),
            "primary_genre": data.get("primary_genre"),
            "tone_profile": data.get("tone_profile"),
        }

    except Exception as e:
        raise ValueError(f"Failed to generate AI taste profile: {str(e)}")

#gemini ranking the 28 fetched pre-ranked movies
async def rank_movie_candidates(candidates: list, prefs, session: dict, language_mode: str, limit: int = 8):
    """
    Ask Gemini to order candidates for this user and session.
    Returns (ordered_movies, reasons_by_id) or (None, {}) on failure / bad output.
    `candidates` should already be a small shortlist (e.g. ≤28).
    """
    if not candidates:
        return None, {}

    payload_movies = []

    for m in candidates:
        mid = m.get("id")
        if mid is None:
            continue
        overview = (m.get("overview") or "").replace("\n", " ").strip()
        if len(overview) > 200:
            overview = overview[:197] + "..."
        payload_movies.append({
            "id": mid,
            "title": m.get("title") or m.get("name") or "",
            "language": m.get("original_language") or "",
            "genres": _genre_labels(m.get("genre_ids") or []),
            "overview": overview,
            "year": (m.get("release_date") or "")[:4] or None,
        })

    if not payload_movies:
        return None, {}

    taste_block = f"""
    Long-term taste (from onboarding + prior analysis):
    - Stated genres: {prefs.genres or "unknown"}
    - Preferred language codes: {prefs.language or "unknown"}
    - Runtime preference: {prefs.runtime_pref or "any"}
    - Risk tolerance: {prefs.risk or "unknown"}
    - AI persona summary: {prefs.ai_persona or "not available"}
    - Primary genre lean: {prefs.primary_genre or "unknown"}
    - Tone profile: {prefs.tone_profile or "unknown"}
    """

    session_block = f"""
    This session only:
    - Mood / vibe: {session.get("mood") or "unspecified"}
    - Language mode: {language_mode} (how wide to go on original language)
    The candidate movies were fetched for this user using long-term genres plus this mood (and language), then scored; your job is to finalize the best order for right now.
    """

    movie_json = json.dumps(payload_movies, ensure_ascii=False)

    prompt = f"""
    You are a thoughtful movie recommender.
    {taste_block}
    {session_block}

    Here is a JSON array of candidate movies (each has id, title, language, genres, overview, year):
    {movie_json}

    Task:
    1) Pick the best {limit} movies for this user RIGHT NOW, ordered from best to next-best.
    2) Use persona, tone, genres, risk, runtime preference, and especially the session mood.
    3) Prefer variety (do not pick {limit} nearly identical films unless the user is extremely narrow).
    4) Only use ids that appear in the array above. Do not invent ids.

    Return ONLY strict JSON with exactly these keys:
    - "ranked_ids": array of integers, length at most {limit}, best first
    - "pick_reasons": object mapping string id (e.g. "123") to one short reason (max 120 chars), only for ids you return

    Example shape:
    {{"ranked_ids": [101, 202], "pick_reasons": {{"101": "Matches your intense mood with a tight thriller.", "202": "Lighter counterpoint; still fits your taste."}}}}
    """

    try:
        def _call_gemini():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call_gemini)
        data = _parse_json_response(response.text)
        ranked_ids = data.get("ranked_ids") or []
        pick_reasons = data.get("pick_reasons") or {}

        if not isinstance(ranked_ids, list):
            return None, {}

        by_id = {m["id"]: m for m in candidates if m.get("id") is not None}
        ordered = []
        for raw_id in ranked_ids:
            try:
                iid = int(raw_id)
            except (TypeError, ValueError):
                continue
            if iid in by_id and iid not in {x["id"] for x in ordered}:
                ordered.append(by_id[iid])

        reasons_by_id = {}
        if isinstance(pick_reasons, dict):
            for k, v in pick_reasons.items():
                if v and isinstance(v, str):
                    try:
                        reasons_by_id[int(k)] = v.strip()[:200]
                    except (TypeError, ValueError):
                        pass

        if not ordered:
            return None, {}

        seen = {m["id"] for m in ordered}
        rest = [m for m in candidates if m.get("id") not in seen]
        rest.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        for m in rest:
            if len(ordered) >= limit:
                break
            ordered.append(m)

        return ordered[:limit], reasons_by_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
