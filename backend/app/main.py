from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import engine, Base, SessionLocal
from app.config import CORS_ORIGINS

# Import ALL models before create_all
from app.models.models import ScrapeJob, ScrapedData
from app.models.auth_models import User

# Auto-create all tables on startup
Base.metadata.create_all(bind=engine)

from app.routes.scrape import router as scrape_router
from app.routes.auth import router as auth_router
from app.routes.google_auth import router as google_router

app = FastAPI(
    title="DataPulse API",
    description="Smart web scraping + market intelligence platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)
app.include_router(auth_router)
app.include_router(google_router)

# Price Tracker waitlist — simple email capture
class NotifyRequest(BaseModel):
    email: str

notify_router = APIRouter(prefix="/api/notify", tags=["notify"])

@notify_router.post("/tracker")
def notify_tracker(req: NotifyRequest):
    """Collect email for Price Tracker launch notification."""
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Valid email required")
    # In production, save to DB or email service
    print(f"[Notify] Price Tracker interest: {req.email}")
    return {"status": "registered", "email": req.email}

app.include_router(notify_router)

@app.get("/")
def root():
    return {"message": "DataPulse API is running"}

@app.get("/health")
def health():
    from sqlalchemy import text
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "connected" if db_ok else "disconnected"}
