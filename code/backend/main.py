"""
Event Collision Detector — FastAPI backend
Run: uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime as DateTimeType, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, inspect
from sqlalchemy.orm import Session
from datetime import date as DateType, time as TimeType
from typing import Literal, Optional
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, get_db
from models import Base, CampusEvent, ExternalEvent, SaturnaliaEvent, SubmittedEvent, CollisionReport
from scoring import compute_score, risk_level, recommend_dates
from seed import seed
from ingestion import ingest
from saturnalia import sync_saturnalia_events


# ── Lifespan: runs once at startup ───────────────────────────────────────────
def _ensure_campus_event_type_column(database_engine=engine):
    with database_engine.begin() as connection:
        columns = {
            column["name"]
            for column in inspect(connection).get_columns(CampusEvent.__tablename__)
        }
        if "event_type" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE campus_events ADD COLUMN event_type VARCHAR(32)"
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)
    _ensure_campus_event_type_column()
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


class CampusEventRequest(BaseModel):
    college: str = Field(..., min_length=1, max_length=160)
    team_name: str = Field(..., min_length=1, max_length=160)
    name: str = Field(..., min_length=1, max_length=200)
    event_type: Literal["Cultural", "Business", "Technical"]
    date: DateType
    start_time: TimeType
    end_time: TimeType
    location: str = Field(..., min_length=1, max_length=200)

    @field_validator("college", "team_name", "name", "location")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "CampusEventRequest":
        if self.end_time <= self.start_time:
            raise ValueError("End time must be later than start time.")
        return self


class CampusRescheduleRequest(BaseModel):
    college: str = Field(..., min_length=1, max_length=160)
    start_time: TimeType
    end_time: TimeType

    @field_validator("college")
    @classmethod
    def trim_college(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("College cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "CampusRescheduleRequest":
        if self.end_time <= self.start_time:
            raise ValueError("End time must be later than start time.")
        return self


class CampusConflictOut(BaseModel):
    id: str
    name: str
    team_name: str
    location: str
    start_at: DateTimeType
    end_at: Optional[DateTimeType]
    overlap_type: str
    overlap_minutes: Optional[int]


class CampusTimeRecommendationOut(BaseModel):
    start_at: DateTimeType
    end_at: DateTimeType
    risk_score: int
    risk_level: str
    risk_weight: float
    overlaps_with: list[CampusConflictOut] = Field(default_factory=list)


class CampusEventOut(BaseModel):
    id: str
    college: str
    team_name: str
    name: str
    category: Optional[str]
    source: str
    start_at: DateTimeType
    end_at: Optional[DateTimeType]
    duration_known: bool
    location: str
    risk_score: int
    risk_level: str
    risk_weight: float
    peak_overlap_minutes: Optional[int]
    reschedulable: bool
    overlaps_with: list[CampusConflictOut] = Field(default_factory=list)
    recommendations: list[CampusTimeRecommendationOut] = Field(default_factory=list)


SATURNALIA_COLLEGE = "Thapar Institute of Engineering and Technology"
CAMPUS_EVENT_TYPE_WEIGHTS = {
    "cultural": 1.0,
    "business": 1.15,
    "technical": 1.3,
}

@dataclass
class _CampusScheduleEntry:
    id: str
    college: str
    team_name: str
    name: str
    category: Optional[str]
    source: str
    start_at: DateTimeType
    end_at: Optional[DateTimeType]
    location: str


def _campus_entry(event: CampusEvent, college: str) -> _CampusScheduleEntry:
    return _CampusScheduleEntry(
        id=str(event.id),
        college=college,
        team_name=event.team_name,
        name=event.name,
        category=event.event_type,
        source="college",
        start_at=DateTimeType.combine(event.date, event.start_time),
        end_at=DateTimeType.combine(event.date, event.end_time),
        location=event.location,
    )


def _saturnalia_entry(event: SaturnaliaEvent) -> _CampusScheduleEntry:
    return _CampusScheduleEntry(
        id=f"saturnalia:{event.source_id}",
        college=SATURNALIA_COLLEGE,
        team_name="Saturnalia",
        name=event.name,
        category=event.category,
        source="Saturnalia",
        start_at=event.start_at,
        end_at=event.end_at,
        location=event.location,
    )


def _campus_overlap_type(
    left: _CampusScheduleEntry,
    right: _CampusScheduleEntry,
) -> Optional[str]:
    if left.college.casefold() != right.college.casefold():
        return None
    if left.end_at is None or right.end_at is None:
        return "same_start_time" if left.start_at == right.start_at else None
    if left.start_at < right.end_at and right.start_at < left.end_at:
        return "time_range"
    return None


def _campus_events_overlap(left: _CampusScheduleEntry, right: _CampusScheduleEntry) -> bool:
    return _campus_overlap_type(left, right) is not None


def _campus_overlap_minutes(
    event: _CampusScheduleEntry,
    conflict: _CampusScheduleEntry,
) -> Optional[int]:
    if _campus_overlap_type(event, conflict) != "time_range":
        return None
    overlap_start = max(event.start_at, conflict.start_at)
    overlap_end = min(event.end_at, conflict.end_at)
    return max(0, round((overlap_end - overlap_start).total_seconds() / 60))


def _campus_conflicts(
    event: _CampusScheduleEntry,
    schedule: list[_CampusScheduleEntry],
) -> list[tuple[_CampusScheduleEntry, str]]:
    return [
        (other, overlap_type)
        for other in schedule
        if other.id != event.id
        and (overlap_type := _campus_overlap_type(event, other)) is not None
    ]


def _campus_risk_score(
    event: _CampusScheduleEntry,
    conflicts: list[tuple[_CampusScheduleEntry, str]],
) -> tuple[int, Optional[int]]:
    weight = CAMPUS_EVENT_TYPE_WEIGHTS.get((event.category or "").casefold(), 1.0)
    if not conflicts:
        return 0, 0

    peak_overlap = max(
        (
            minutes
            for other, _ in conflicts
            if (minutes := _campus_overlap_minutes(event, other)) is not None
        ),
        default=None,
    )
    if event.end_at is None or any(other.end_at is None for other, _ in conflicts):
        base_score = max(75, min(100, 20 * len(conflicts)))
        return min(100, round(base_score * weight)), peak_overlap

    duration_minutes = (event.end_at - event.start_at).total_seconds() / 60
    peak_ratio = (peak_overlap or 0) / duration_minutes if duration_minutes else 0
    score = min(100, round((20 * len(conflicts) + 80 * peak_ratio) * weight))
    return score, peak_overlap


def _campus_event_type_weight(event: _CampusScheduleEntry) -> float:
    return CAMPUS_EVENT_TYPE_WEIGHTS.get((event.category or "").casefold(), 1.0)


def _campus_recommendations(
    event: _CampusScheduleEntry,
    schedule: list[_CampusScheduleEntry],
) -> list[CampusTimeRecommendationOut]:
    if event.source != "college" or event.end_at is None:
        return []

    duration = event.end_at - event.start_at
    if duration <= timedelta(0):
        return []
    current_conflicts = _campus_conflicts(event, schedule)
    current_score, _ = _campus_risk_score(event, current_conflicts)
    if not current_score:
        return []

    day_start = DateTimeType.combine(event.start_at.date(), TimeType.min)
    latest_start = DateTimeType.combine(event.start_at.date(), TimeType.max) - duration
    candidates = []
    slot = day_start
    while slot <= latest_start:
        if slot != event.start_at:
            candidate = _CampusScheduleEntry(
                id=event.id,
                college=event.college,
                team_name=event.team_name,
                name=event.name,
                category=event.category,
                source=event.source,
                start_at=slot,
                end_at=slot + duration,
                location=event.location,
            )
            conflicts = _campus_conflicts(candidate, schedule)
            score, _ = _campus_risk_score(candidate, conflicts)
            if score < current_score:
                candidates.append((score, conflicts, candidate))
        slot += timedelta(minutes=30)

    candidates.sort(key=lambda item: (
        item[0],
        abs((item[2].start_at - event.start_at).total_seconds()),
        item[2].start_at,
    ))

    recommendations = []
    for score, conflicts, candidate in candidates:
        if any(
            abs((candidate.start_at - item.start_at).total_seconds()) < duration.total_seconds()
            for item in recommendations
        ):
            continue
        recommendations.append(CampusTimeRecommendationOut(
            start_at=candidate.start_at,
            end_at=candidate.end_at,
            risk_score=score,
            risk_level=risk_level(score),
            risk_weight=_campus_event_type_weight(event),
            overlaps_with=[
                CampusConflictOut(
                    id=other.id,
                    name=other.name,
                    team_name=other.team_name,
                    location=other.location,
                    start_at=other.start_at,
                    end_at=other.end_at,
                    overlap_type=overlap_type,
                    overlap_minutes=_campus_overlap_minutes(candidate, other),
                )
                for other, overlap_type in conflicts
            ],
        ))
        if len(recommendations) == 3:
            break
    return recommendations


def _campus_event_out(
    event: _CampusScheduleEntry,
    conflicts: list[tuple[_CampusScheduleEntry, str]],
    recommendations: Optional[list[CampusTimeRecommendationOut]] = None,
) -> CampusEventOut:
    score, peak_overlap = _campus_risk_score(event, conflicts)
    return CampusEventOut(
        id=event.id,
        college=event.college,
        team_name=event.team_name,
        name=event.name,
        category=event.category,
        source=event.source,
        start_at=event.start_at,
        end_at=event.end_at,
        duration_known=event.end_at is not None,
        location=event.location,
        risk_score=score,
        risk_level=risk_level(score),
        risk_weight=_campus_event_type_weight(event),
        peak_overlap_minutes=peak_overlap,
        reschedulable=event.source == "college",
        overlaps_with=[
            CampusConflictOut(
                id=conflict.id,
                name=conflict.name,
                team_name=conflict.team_name,
                location=conflict.location,
                start_at=conflict.start_at,
                end_at=conflict.end_at,
                overlap_type=overlap_type,
                overlap_minutes=_campus_overlap_minutes(event, conflict),
            )
            for conflict, overlap_type in conflicts
        ],
        recommendations=recommendations or [],
    )


def _campus_schedule_entries(db: Session, college: str) -> list[_CampusScheduleEntry]:
    campus_events = (
        db.query(CampusEvent)
        .filter(func.lower(CampusEvent.college) == college.lower())
        .all()
    )
    entries = [_campus_entry(event, college) for event in campus_events]
    if college.casefold() == SATURNALIA_COLLEGE.casefold():
        entries.extend(
            _saturnalia_entry(event)
            for event in db.query(SaturnaliaEvent).all()
        )
    return sorted(entries, key=lambda event: (event.start_at, event.name.casefold()))


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


@app.get("/api/campus/colleges", response_model=list[str])
def list_campuses(db: Session = Depends(get_db)):
    colleges = {
        college.casefold(): college
        for (college,) in (
        db.query(CampusEvent.college)
        .distinct()
        .order_by(CampusEvent.college)
        .all()
        )
    }
    if db.query(SaturnaliaEvent).first() is not None:
        colleges[SATURNALIA_COLLEGE.casefold()] = SATURNALIA_COLLEGE
    return sorted(colleges.values(), key=str.casefold)


@app.post("/api/campus/saturnalia/sync")
def refresh_saturnalia_events(db: Session = Depends(get_db)):
    try:
        result = sync_saturnalia_events(db)
        return {
            "status": "ok",
            "college": SATURNALIA_COLLEGE,
            "location_count": len(list_campus_locations(db)),
            **result,
        }
    except (httpx.HTTPError, ValueError) as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Could not sync Saturnalia events: {error}",
        ) from error


@app.get("/api/campus/locations", response_model=list[str])
def list_campus_locations(db: Session = Depends(get_db)):
    values = [
        location
        for (location,) in db.query(CampusEvent.location).distinct().all()
    ]
    values.extend(
        location
        for (location,) in db.query(SaturnaliaEvent.location).distinct().all()
    )

    locations = {}
    for value in values:
        normalized = " ".join(value.split())
        if normalized:
            locations.setdefault(normalized.casefold(), normalized)
    return sorted(locations.values(), key=str.casefold)


@app.get("/api/campus/events", response_model=list[CampusEventOut])
def list_campus_events(
    college: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    college = college.strip()
    if not college:
        raise HTTPException(status_code=422, detail="College is required.")

    events = _campus_schedule_entries(db, college)
    return [
        _campus_event_out(
            event,
            _campus_conflicts(event, events),
            _campus_recommendations(event, events),
        )
        for event in events
    ]


@app.post("/api/campus/events", response_model=CampusEventOut, status_code=201)
def register_campus_event(
    req: CampusEventRequest,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(CampusEvent)
        .filter(func.lower(CampusEvent.college) == req.college.lower())
        .all()
    )
    is_saturnalia_college = req.college.casefold() == SATURNALIA_COLLEGE.casefold()
    college = SATURNALIA_COLLEGE if is_saturnalia_college else (
        existing[0].college if existing else req.college
    )

    event = CampusEvent(
        college=college,
        team_name=req.team_name,
        name=req.name,
        event_type=req.event_type,
        date=req.date,
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    entry = _campus_entry(event, college)
    schedule = _campus_schedule_entries(db, college)
    return _campus_event_out(
        entry,
        _campus_conflicts(entry, schedule),
        _campus_recommendations(entry, schedule),
    )


@app.patch("/api/campus/events/{event_id}/reschedule", response_model=CampusEventOut)
def reschedule_campus_event(
    event_id: int,
    req: CampusRescheduleRequest,
    db: Session = Depends(get_db),
):
    event = (
        db.query(CampusEvent)
        .filter(
            CampusEvent.id == event_id,
            func.lower(CampusEvent.college) == req.college.lower(),
        )
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Registered campus event not found.")

    original_duration = (
        DateTimeType.combine(event.date, event.end_time)
        - DateTimeType.combine(event.date, event.start_time)
    )
    proposed_duration = (
        DateTimeType.combine(event.date, req.end_time)
        - DateTimeType.combine(event.date, req.start_time)
    )
    if proposed_duration != original_duration:
        raise HTTPException(
            status_code=422,
            detail="Rescheduling must preserve the event duration.",
        )

    event.start_time = req.start_time
    event.end_time = req.end_time
    db.commit()
    db.refresh(event)

    entry = _campus_entry(event, event.college)
    schedule = _campus_schedule_entries(db, event.college)
    return _campus_event_out(
        entry,
        _campus_conflicts(entry, schedule),
        _campus_recommendations(entry, schedule),
    )


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
