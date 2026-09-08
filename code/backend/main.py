"""
Event Collision Detector — FastAPI backend
Run: uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import date as DateType
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, get_db
from models import Base, ExternalEvent, SubmittedEvent, CollisionReport
from scoring import compute_score, risk_level, recommend_dates
from seed import seed
from ingestion import ingest


# ── Lifespan: runs once at startup ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)
    # 2. Seed static events (idempotent — skips if already seeded)
    seed()
    # 3. Fetch live public holidays from Nager.Date API
    db = next(get_db())
    try:
        result = ingest(db)
        print(f"[startup] Live holidays ingested: {result}")
    except Exception as e:
        print(f"[startup] Ingestion failed (continuing with seed data): {e}")
    finally:
        db.close()
    yield   # app runs here


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Event Collision Detector API",
    description="Predictive launch-window intelligence for teams.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    name: str = Field(..., example="My Product Launch")
    proposed_date: str = Field(..., example="2026-06-09")
    industry: str = Field(..., example="tech")
    audience_tags: list[str] = Field(default=[], example=["developers", "enterprise"])


class EventOut(BaseModel):
    id: int
    name: str
    date: str
    industry: str
    audience_tags: list
    magnitude: int
    source: str

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: int
    submitted_event_id: int
    risk_level: str
    score: float
    conflicting_events: list
    recommendations: list

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health(db: Session = Depends(get_db)):
    total = db.query(ExternalEvent).count()
    live  = db.query(ExternalEvent).filter(ExternalEvent.source == "nager-date-api").count()
    seed_count = db.query(ExternalEvent).filter(ExternalEvent.source == "seed").count()
    return {
        "status": "ok",
        "service": "event-collision-detector",
        "events": {"total": total, "live_holidays": live, "seeded": seed_count},
    }


@app.post("/api/ingest")
def trigger_ingest(db: Session = Depends(get_db)):
    """Manually re-fetch live holidays from Nager.Date API."""
    try:
        result = ingest(db)
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {e}")


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    # Validate date
    try:
        proposed = DateType.fromisoformat(req.proposed_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")

    # Persist submitted event
    submitted = SubmittedEvent(
        name=req.name,
        proposed_date=req.proposed_date,
        industry=req.industry,
        audience_tags=req.audience_tags,
    )
    db.add(submitted)
    db.flush()

    # Fetch all external events (seeded + live)
    events = db.query(ExternalEvent).all()

    # Score
    score, conflicts = compute_score(
        proposed, req.industry, req.audience_tags, events, window_days=14
    )
    level = risk_level(score)
    recs = recommend_dates(proposed, req.industry, req.audience_tags, events)

    # Persist report
    report = CollisionReport(
        submitted_event_id=submitted.id,
        risk_level=level,
        score=score,
        conflicting_events=conflicts,
        recommendations=recs,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "proposed_date": req.proposed_date,
        "event_name": req.name,
        "industry": req.industry,
        "risk_level": level,
        "score": score,
        "conflicting_events": conflicts,
        "recommendations": recs,
    }


@app.get("/api/events", response_model=list[EventOut])
def list_events(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ExternalEvent)
    if industry:
        query = query.filter(ExternalEvent.industry == industry)
    events = query.order_by(ExternalEvent.date).all()
    if from_date:
        events = [e for e in events if e.date >= from_date]
    if to_date:
        events = [e for e in events if e.date <= to_date]
    return events


@app.get("/api/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(CollisionReport).filter(CollisionReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
