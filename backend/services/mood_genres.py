# Session mood keywords mapped to TMDB genre ids 

MOOD_GENRE_HINTS = (
    (("intense", "thrill", "suspense", "dark", "grit"), (53, 80, 28)),
    (("light", "feel-good", "uplift", "easy", "comfort"), (35, 10751)),
    (("fun", "laugh", "comedy"), (35,)),
    (("romance", "love", "romantic"), (10749,)),
    (("scary", "horror", "spook"), (27,)),
    (("emotional", "cry", "melanchol", "heart"), (18,)),
    (("action", "adrenaline", "epic"), (28, 12)),
    (("mind", "mystery", "twist", "clever"), (9648, 878)),
)


def genre_ids_for_mood(mood: str) -> list[int]:
    """Collect TMDB genre ids for all hint rows that match the mood text."""
    m = (mood or "").lower()
    if not m:
        return []
    out = []
    for keywords, gids in MOOD_GENRE_HINTS:
        if any(k in m for k in keywords):
            for g in gids:
                if g not in out:
                    out.append(g)
    return out
