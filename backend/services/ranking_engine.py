from backend.services.tmdb_service import GENRE_MAP
from backend.services.mood_genres import MOOD_GENRE_HINTS
import asyncio

def _user_genre_ids(prefs):
    raw = (prefs.genres or "").lower().split(",")
    ids = []
    for name in raw:
        key = name.strip()
        if key in GENRE_MAP:
            ids.append(GENRE_MAP[key])
    return ids


def _mood_alignment_bonus(mood_lower, genre_ids):
    """Reward movies whose genres fit the current session intent (free-text mood)."""
    if not mood_lower:
        return 0
    bonus = 0
    for keywords, gids in MOOD_GENRE_HINTS:
        if any(k in mood_lower for k in keywords) and any(g in genre_ids for g in gids):
            bonus += 3.6
    return min(bonus, 8)

#ranking "n" movies fetched form TMDb
async def score_movie(movie, session, preferred_languages, prefs):
    score = 0

    mood = (session.get("mood") or "").lower()
    primary_genre = (prefs.primary_genre or "").lower()
    tone_profile = (prefs.tone_profile or "").lower()
    genre_ids = movie.get("genre_ids", [])
    language = movie.get("original_language")

    if language and language in preferred_languages:
        score += 8

    score += min(movie.get("popularity", 0) / 100, 1.0)

    score += _mood_alignment_bonus(mood, genre_ids)

    for gid in _user_genre_ids(prefs):
        if gid in genre_ids:
            score += 3

    if primary_genre in GENRE_MAP:
        if GENRE_MAP[primary_genre] in genre_ids:
            score += 4

    if "dark" in tone_profile:
        if any(g in genre_ids for g in (27, 53, 80, 9648)):
            score += 2
    if any(x in tone_profile for x in ("light", "warm", "fun")):
        if any(g in genre_ids for g in (35, 10751, 10402)):
            score += 1

    return score

async def rank_movies(movies, session, preferred_languages, prefs, limit=8):
    if not movies:
        return []

    scored = []
    
    score_tasks = [score_movie(m, session, preferred_languages, prefs) for m in movies]

    scores = await asyncio.gather(*score_tasks, return_exceptions=True)
    
    for score, m in zip(scores, movies):
        try:
            if isinstance(score, Exception):
                print("RANK ERROR:", score)
                continue
            scored.append((score, m))
        except Exception as e:
            print("RANK ERROR:", e)

    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored[:limit]]
