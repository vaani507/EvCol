from sqlalchemy import Column, Date, Integer, String, Float, DateTime, Time, Text, JSON
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


class CampusEvent(Base):
    __tablename__ = "campus_events"

    id = Column(Integer, primary_key=True, index=True)
    college = Column(String(160), nullable=False, index=True)
    team_name = Column(String(160), nullable=False)
    name = Column(String(200), nullable=False)
    event_type = Column(String(32), nullable=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(200), nullable=False)


class SaturnaliaEvent(Base):
    __tablename__ = "saturnalia_events"

    source_id = Column(String(120), primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(80), nullable=False)
    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=True)
    location = Column(String(200), nullable=False)


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
