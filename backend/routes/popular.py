from fastapi import APIRouter,Request
import httpx
import asyncio
import os
from backend.rate_limiter import limiter

router = APIRouter(prefix="/popular", tags=["Popular"])

BASE_URL = os.getenv("BASE_URL")
TMDB_KEY = os.getenv("TMDB_KEY")

HEADERS = {
    "Authorization": f"Bearer {TMDB_KEY}",
    "Content-Type": "application/json"
}

GENRES = {
    "Action": 28,
    "Thriller": 53,
    "Comedy": 35
}

async def fetch_genre_movies(client, genre_name, genre_id, lang):

    movies = []
    tasks = []

    for page in [1, 2, 3]:
        params = {
            "with_genres": genre_id,
            "with_original_language": lang,
            "sort_by": "popularity.desc",
            "page": page
        }

        tasks.append(
            client.get(f"{BASE_URL}/discover/movie", params=params)
        )

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for res in responses:
        if isinstance(res, Exception):
            continue

        if res.status_code == 200:
            movies.extend(res.json().get("results", []))

    unique = {}
    for m in movies:
        unique[m["id"]] = m
    movies = list(unique.values())
    movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)

    formatted = []
    for m in movies[:8]:
        formatted.append({
            "id": m["id"],
            "title": m.get("title"),
            "poster": m.get("poster_path"),
            "language": m.get("original_language"),
            "tmdb_link": f"https://www.themoviedb.org/movie/{m['id']}"
        })

    return {
        "name": genre_name,
        "movies": formatted
    }
#api
@router.get("/")
@limiter.limit("7/minute")
async def popular(request:Request,lang: str = "en"):
    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=10
    ) as client:

        tasks = []

        for genre_name, genre_id in GENRES.items():
            tasks.append(
                fetch_genre_movies(client, genre_name, genre_id, lang)
            )

        results = await asyncio.gather(*tasks)

    return {
        "language": lang,
        "genres": results
    }