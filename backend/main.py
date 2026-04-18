from fastapi import FastAPI
from backend.db import engine
from backend.models import Base
from backend.routes import init_user,questionnaire,recommend,popular
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from backend.rate_limiter import limiter

app = FastAPI(title="Movie Recommendation SaaS")

#CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#apis
app.include_router(init_user.router)
app.include_router(questionnaire.router)
app.include_router(recommend.router)
app.include_router(popular.router)

@app.get("/")
def root():
    return {"status": "OK"}
