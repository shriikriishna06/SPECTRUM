import httpx
import os
import random
from dotenv import load_dotenv
import asyncio
from backend.services.mood_genres import genre_ids_for_mood

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
TMDB_KEY = os.getenv("TMDB_KEY")

GENRE_MAP = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37
}
PLATFORM_ORDER = [
    "Netflix",
    "Amazon Prime Video",
    "Apple TV",
    "Disney+ Hotstar",
    "JioHotstar",
    "Sony LIV",
    "ZEE5",
    "JioCinema",
    "MX Player"
]


if not BASE_URL or not TMDB_KEY:
    raise ValueError("BASE_URL and TMDB_KEY must be set in .env file")

HEADERS = {
    "Authorization": f"Bearer {TMDB_KEY}",
    "Content-Type": "application/json"
}

def genres_to_ids(genres_str: str):
    names = genres_str.split(",")
    ids = []

    for name in names:
        key = name.strip().lower()
        if key in GENRE_MAP:
            ids.append(str(GENRE_MAP[key]))

    return ",".join(ids)

def _user_taste_genre_int_set(genres_str: str) -> set[int]:
    s = genres_to_ids(genres_str)
    if not s:
        return set()
    return {int(x) for x in s.split(",")}


def _movie_matches_long_term_genres(movie: dict, taste: set[int]) -> bool:
    if not taste:
        return True
    mg = set(movie.get("genre_ids") or [])
    return taste <= mg


async def _discover_page(lang: str, with_genres: str, page: int, sort_by: str) -> list:
    params = {
        "with_original_language": lang,
        "sort_by": sort_by,
        "page": page,
    }
    if with_genres:
        params["with_genres"] = with_genres
    if sort_by == "vote_average.desc":
        params["vote_count.gte"] = 200
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{BASE_URL}/discover/movie",
                headers=HEADERS,
                params=params,
            )
            res.raise_for_status()
            return res.json().get("results", []) or []
    except httpx.HTTPStatusError as e:
        print(f"TMDB Error fetching movies for language {lang}: {e.response.status_code} - {e.response.text[:100]}")
        return []
    except httpx.RequestError as e:
        print(f"Network error fetching movies for language {lang}: {type(e).__name__} - {str(e)[:100]}")
        return []

#fetch movies from TMDb
async def fetch_movies(genres, language_codes, session_mood: str | None = None):
    """
    Candidates from TMDB: long-term genres (AND) + session mood (OR genres),
    varied pages so repeats across sessions are less likely. Mood OR results
    are kept only if they still satisfy the same long-term genre AND as discover.
    """

    taste = _user_taste_genre_int_set(genres or "")
    mood_ids = genre_ids_for_mood(session_mood or "")
    mood_or = "|".join(str(g) for g in mood_ids) if mood_ids else ""
    base_with_genres = genres_to_ids(genres or "")

    results = []
    tasks = []
    
    for lang in language_codes:
        page_taste = random.randint(1, 5)
        sort_taste = random.choice(
            ("popularity.desc", "vote_average.desc", "primary_release_date.desc")
        )

        tasks.append(_discover_page(lang, base_with_genres, page_taste, sort_taste))
        
        if mood_or and taste:
            page_mood = random.randint(1, 4)
            tasks.append(_discover_page(lang, mood_or, page_mood, "popularity.desc"))

    if tasks:
        batch_results = await asyncio.gather(*tasks)
        for batch in batch_results:
            results.extend(batch)

    if mood_or and taste:
        filtered_results = []
        for result in results:
            if _movie_matches_long_term_genres(result, taste):
                filtered_results.append(result)
        return filtered_results

    return results

#fetch watch providers (logo)
async def fetch_watch_providers(tmdb_id: int):
    url = f"{BASE_URL}/movie/{tmdb_id}/watch/providers"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=HEADERS)
            res.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"TMDB Error fetching watch providers for {tmdb_id}: {e.response.status_code} - {e.response.text[:100]}")
        return []
    except httpx.RequestError as e:
        print(f"Network error fetching watch providers for {tmdb_id}: {type(e).__name__} - {str(e)[:100]}")
        return []

    data = res.json()
    results = data.get("results", {})
    if not isinstance(results, dict):
        return []

    providers = []

    for region_data in results.values():
        for key in ("flatrate", "rent", "buy"):
            for p in region_data.get(key, []):
                name = p.get("provider_name")
                if name in PLATFORM_ORDER:
                    providers.append({
                        "platform": name,
                        "logo": p.get("logo_path")
                    })

    unique = {p["platform"]: p for p in providers}
    return order_platforms(list(unique.values()))


def order_platforms(providers):
    order_index = {name: i for i, name in enumerate(PLATFORM_ORDER)}
    return sorted(
        providers,
        key=lambda p: order_index.get(p["platform"], 999)
    )

