#explainatory statement for movies recommended
def build_reasons(movie, prefs, session):
    reasons = []

    if movie.get("original_language") in (prefs.language or "").split(","):
        reasons.append("In your preferred language")

    votes = movie.get("vote_count", 0)
    popularity = movie.get("popularity", 0)

    if votes >= 2000:
        reasons.append("Extremely popular with viewers")
    elif votes >= 500:
        reasons.append("Well-received by audiences")
    elif popularity >= 100:
        reasons.append("Trending right now")
    else:
        reasons.append("A lesser-known pick worth trying")

    date = movie.get("release_date") or movie.get("first_air_date")
    if date and int(date[:4]) >= 2023:
        reasons.append("Recently released")

    if len(reasons) < 3:
        reasons.append(f"Suits your {session.mood} mood")

    return reasons[:3]
