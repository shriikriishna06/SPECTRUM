# 🎬 SPECTRUM – AI Powered Movie Recommendation System
SPECTRUM is an AI-powered movie recommendation web app that helps users decide what to watch using:
- Long-term taste preferences  
- Current mood  
- Preferred languages  
- TMDB movie data  
- Streaming availability  
- AI-based ranking<br>
Live on: https://spectrumx.netlify.app<br>
⚠️IMP NOTE: Used GEMINI API(free tier), CORE tool may not be accessible.

---
## 🚀 Features

### Landing Page
- Start onboarding or browse **Popular Now**
- Language-based filtering
- Animated genre rows

### Onboarding (AI Taste Profiling)
- Collects:
  - Genres
  - Language
  - Runtime preference
  - Risk level
- Generates an **AI taste persona** using Gemini

### Session Recommendations
- Input current mood + language mode
- Returns personalized recommendations with:
  - AI explanation
  - Streaming platforms
  - TMDB links

---

## 🧠 Tech Stack
### Frontend
- HTML
- Tailwind CSS (CDN)
- JavaScript

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL (supabase)
- HTTPX (async req. handling)
- SlowAPI (rate limiting)
- AWS (EC2) for hosting

### APIs
- TMDB API
- Gemini API

---

# 🗂️PROJECT STRUCTURE
```
SPECTRUM/
│
├── backend/                   # FastAPI backend (core logic + APIs)
│ │
│ ├── main.py                  # Entry point
│ ├── db.py                    # Database connection + SQLAlchemy setup
│ ├── rate_limiter.py          # API rate limiting config (SlowAPI)
│ ├── dockerFile               # Docker config
│ ├── requirements.txt         # Backend dependencies
│
│ ├── models/                  # Database models (tables)
│ │ ├── users.py               # User table
│ │ ├── preferences.py         # User preferences + AI profile
│ │ └── init.py
│
│ ├── routes/                  # API endpoints (FastAPI routers)
│ │ ├── init_user.py           # User creation + validation endpoints
│ │ ├── questionnaire.py       # Onboarding (save preferences + AI profiling)
│ │ ├── recommend.py           # Main recommendation API
│ │ ├── popular.py             # Popular movies endpoint
│ │ └── init.py
│
│ ├── schemas/                 # Pydantic schemas 
│ │ ├── preferences.py         # Preference input schema
│ │ ├── recommend.py           # Recommendation response schema
│ │ ├── session.py             # Session input schema
│ │ └── init.py
│
│ ├── services/                # Logic layer (core intelligence)
│ │ ├── tmdb_service.py        # Fetch movies + providers from TMDB
│ │ ├── ranking_engine.py      # Local scoring + ranking logic
│ │ ├── gemini_service.py      # Gemini API integration (AI reasoning)
│ │ ├── mood_genres.py         # Maps mood → genre IDs
│ │ ├── explain.py             # Generates explanation text
│ │ └── init.py
│
│ └── utils/                   # Helper utilities
│ ├── uuid_helper.py           # UUID generation helpers
│ └── init.py
│
├── frontend/                                                            
│ │
│ └── public/
│ │
│ ├── index.html                # Landing page + Popular section
│ ├── app.html                 # Onboarding 
│ ├── session.html             # Recommendation page
│
│ ├── js/
│ │ └── script.js              # All frontend logic + API calls
│
│ └── assets/
│ ├── icons/                   # UI icons
│ └── favicon.ico
│
├── .env                       # Environment variables
├── .dockerignore              # Docker ignore rules
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
```
---

## 🖥️ Run Locally
1. Clone repo
```bash
git clone https://github.com/shriikriishna06/SPECTRUM.git
```
2. Install backend deps
```bash
pip install -r requirements.txt
```
3. Creation of .env
```
Fill .env.example and rename it to .env
```
4. Start backend service
```bash
python -m uvicorn backend.main:app --reload
```
5. Go live
```
use python http server or any live servers
```

---

## 🐳 Docker 
Note: Docker setup required<br>
For remote setup:<br>
Build:
```bash
docker build -f backend/dockerFile -t spectrum .
```
Run:
```bash
docker run -p 8000:8000 --env-file .env spectrum
```

Using docker hub:<br>
Pull image:
```bash
docker pull shrikrishnarprabhu/spectrum
```
Run:
```bash 
docker run -p 8000:8000 --env-file .env shrikrishnarprabhu/spectrum
```
---

## ⚡ Recommendation Pipeline
- User submits mood + language mode
- Backend loads preferences
- Fetches candidates(movies) from TMDB
- Filters + ranks locally
- Gemini refines ranking + explanations
- Returns final results

---

## 📌 Future Improvements
- Authentication system
- TV show support
- Caching

---

