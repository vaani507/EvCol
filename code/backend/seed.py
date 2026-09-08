"""
Seed the SQLite database with realistic external events.
Run once: python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, SessionLocal
from models import Base, ExternalEvent

EVENTS = [
    # ── TECH ─────────────────────────────────────────────────────────────────
    {"name": "Apple WWDC 2026",           "date": "2026-06-08", "industry": "tech",          "audience_tags": ["developers", "apple", "consumer"],       "magnitude": 5},
    {"name": "Google I/O 2026",           "date": "2026-05-20", "industry": "tech",          "audience_tags": ["developers", "android", "ai"],           "magnitude": 5},
    {"name": "AWS re:Invent 2026",        "date": "2026-12-01", "industry": "tech",          "audience_tags": ["enterprise", "cloud", "developers"],     "magnitude": 5},
    {"name": "Microsoft Build 2026",      "date": "2026-05-13", "industry": "tech",          "audience_tags": ["developers", "enterprise", "ai"],        "magnitude": 4},
    {"name": "CES 2026",                  "date": "2026-01-07", "industry": "tech",          "audience_tags": ["consumer", "hardware", "media"],         "magnitude": 5},
    {"name": "Mobile World Congress",     "date": "2026-03-02", "industry": "tech",          "audience_tags": ["mobile", "telecom", "enterprise"],       "magnitude": 4},
    {"name": "OpenAI DevDay 2026",        "date": "2026-11-03", "industry": "tech",          "audience_tags": ["ai", "developers"],                      "magnitude": 4},
    {"name": "Meta Connect 2026",         "date": "2026-09-22", "industry": "tech",          "audience_tags": ["vr", "consumer", "developers"],          "magnitude": 4},
    {"name": "Salesforce Dreamforce",     "date": "2026-09-15", "industry": "tech",          "audience_tags": ["enterprise", "crm", "business"],         "magnitude": 4},
    {"name": "GitHub Universe 2026",      "date": "2026-10-22", "industry": "tech",          "audience_tags": ["developers", "open-source"],             "magnitude": 3},
    {"name": "TechCrunch Disrupt 2026",   "date": "2026-10-07", "industry": "tech",          "audience_tags": ["startups", "investors", "developers"],   "magnitude": 3},
    {"name": "Black Hat USA 2026",        "date": "2026-08-03", "industry": "tech",          "audience_tags": ["security", "enterprise", "developers"],  "magnitude": 3},
    {"name": "Google Cloud Next 2026",    "date": "2026-04-08", "industry": "tech",          "audience_tags": ["cloud", "enterprise", "developers"],     "magnitude": 4},

    # ── ENTERTAINMENT ─────────────────────────────────────────────────────────
    {"name": "Coachella Valley Music Festival", "date": "2026-04-11", "industry": "entertainment", "audience_tags": ["music", "consumer", "media"],  "magnitude": 5},
    {"name": "Oscars 2026",               "date": "2026-03-15", "industry": "entertainment", "audience_tags": ["film", "media", "celebrity"],           "magnitude": 5},
    {"name": "Grammy Awards 2026",        "date": "2026-02-01", "industry": "entertainment", "audience_tags": ["music", "media", "celebrity"],          "magnitude": 5},
    {"name": "Cannes Film Festival",      "date": "2026-05-13", "industry": "entertainment", "audience_tags": ["film", "media", "celebrity"],           "magnitude": 4},
    {"name": "E3 Gaming Expo 2026",       "date": "2026-06-10", "industry": "entertainment", "audience_tags": ["gaming", "consumer", "media"],         "magnitude": 4},
    {"name": "Comic-Con San Diego",       "date": "2026-07-22", "industry": "entertainment", "audience_tags": ["gaming", "film", "consumer"],           "magnitude": 4},
    {"name": "Burning Man 2026",          "date": "2026-08-30", "industry": "entertainment", "audience_tags": ["consumer", "art", "media"],             "magnitude": 3},
    {"name": "VMAs 2026",                 "date": "2026-09-07", "industry": "entertainment", "audience_tags": ["music", "media", "celebrity"],          "magnitude": 4},

    # ── SPORTS ────────────────────────────────────────────────────────────────
    {"name": "FIFA World Cup 2026 Final", "date": "2026-07-19", "industry": "sports",        "audience_tags": ["sports", "consumer", "media"],          "magnitude": 5},
    {"name": "Super Bowl LXI",            "date": "2026-02-08", "industry": "sports",        "audience_tags": ["sports", "consumer", "media"],          "magnitude": 5},
    {"name": "IPL Final 2026",            "date": "2026-05-30", "industry": "sports",        "audience_tags": ["sports", "consumer", "india"],          "magnitude": 4},
    {"name": "NBA Finals Game 1",         "date": "2026-06-04", "industry": "sports",        "audience_tags": ["sports", "consumer", "media"],          "magnitude": 4},
    {"name": "Wimbledon Finals 2026",     "date": "2026-07-12", "industry": "sports",        "audience_tags": ["sports", "consumer", "media"],          "magnitude": 4},
    {"name": "US Open Tennis Final",      "date": "2026-09-13", "industry": "sports",        "audience_tags": ["sports", "consumer", "media"],          "magnitude": 3},

    # ── FINANCE ───────────────────────────────────────────────────────────────
    {"name": "Berkshire Hathaway Annual Meeting", "date": "2026-05-02", "industry": "finance", "audience_tags": ["investors", "enterprise", "finance"], "magnitude": 4},
    {"name": "World Economic Forum Davos",  "date": "2026-01-21", "industry": "finance",     "audience_tags": ["business", "investors", "enterprise"],   "magnitude": 5},
    {"name": "Fed Rate Decision Q1",      "date": "2026-03-18", "industry": "finance",       "audience_tags": ["finance", "investors", "enterprise"],   "magnitude": 4},
    {"name": "Fed Rate Decision Q2",      "date": "2026-06-17", "industry": "finance",       "audience_tags": ["finance", "investors", "enterprise"],   "magnitude": 4},
    {"name": "Fed Rate Decision Q3",      "date": "2026-09-16", "industry": "finance",       "audience_tags": ["finance", "investors", "enterprise"],   "magnitude": 4},
    {"name": "Fed Rate Decision Q4",      "date": "2026-12-09", "industry": "finance",       "audience_tags": ["finance", "investors", "enterprise"],   "magnitude": 4},
    {"name": "Goldman Sachs Financial Summit", "date": "2026-02-24", "industry": "finance",  "audience_tags": ["investors", "enterprise", "business"],  "magnitude": 3},

    # ── MEDIA / MARKETING ─────────────────────────────────────────────────────
    {"name": "Super Bowl Halftime Show",  "date": "2026-02-08", "industry": "media",         "audience_tags": ["consumer", "media", "celebrity"],        "magnitude": 5},
    {"name": "Black Friday 2026",         "date": "2026-11-27", "industry": "media",         "audience_tags": ["consumer", "retail", "media"],           "magnitude": 5},
    {"name": "Cyber Monday 2026",         "date": "2026-11-30", "industry": "media",         "audience_tags": ["consumer", "retail", "tech"],            "magnitude": 4},
    {"name": "Amazon Prime Day 2026",     "date": "2026-07-09", "industry": "media",         "audience_tags": ["consumer", "retail", "tech"],            "magnitude": 4},
    {"name": "Cannes Lions 2026",         "date": "2026-06-22", "industry": "media",         "audience_tags": ["marketing", "creative", "business"],     "magnitude": 4},
    {"name": "SXSW 2026",                 "date": "2026-03-09", "industry": "media",         "audience_tags": ["tech", "entertainment", "startups"],     "magnitude": 4},

    # ── GENERAL / PUBLIC HOLIDAYS ─────────────────────────────────────────────
    {"name": "Diwali 2026",               "date": "2026-11-08", "industry": "general",       "audience_tags": ["consumer", "india", "media"],            "magnitude": 4},
    {"name": "Christmas 2026",            "date": "2026-12-25", "industry": "general",       "audience_tags": ["consumer", "media", "retail"],           "magnitude": 5},
    {"name": "New Year's Day 2027",       "date": "2027-01-01", "industry": "general",       "audience_tags": ["consumer", "media"],                     "magnitude": 4},
    {"name": "US Independence Day",       "date": "2026-07-04", "industry": "general",       "audience_tags": ["consumer", "media"],                     "magnitude": 3},
    {"name": "US Thanksgiving",           "date": "2026-11-26", "industry": "general",       "audience_tags": ["consumer", "media", "retail"],           "magnitude": 4},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    existing = db.query(ExternalEvent).count()
    if existing > 0:
        print(f"Database already seeded with {existing} events. Skipping.")
        db.close()
        return

    for ev in EVENTS:
        db.add(ExternalEvent(**ev))
    db.commit()
    print(f"Seeded {len(EVENTS)} events successfully.")
    db.close()


if __name__ == "__main__":
    seed()
