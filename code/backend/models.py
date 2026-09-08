from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime
from database import Base


class ExternalEvent(Base):
    __tablename__ = "external_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)          # ISO date string YYYY-MM-DD
    industry = Column(String, nullable=False)      # tech | entertainment | finance | sports | media | general
    audience_tags = Column(JSON, default=list)     # list of strings
    magnitude = Column(Integer, default=3)         # 1-5 scale
    source = Column(String, default="seed")


class SubmittedEvent(Base):
    __tablename__ = "submitted_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    proposed_date = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    audience_tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class CollisionReport(Base):
    __tablename__ = "collision_reports"

    id = Column(Integer, primary_key=True, index=True)
    submitted_event_id = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)    # High | Medium | Low
    score = Column(Float, nullable=False)          # 0–100
    conflicting_events = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
