"""
Live event ingestion from the Nager.Date public holiday API.
No API key required. Documentation: https://date.nager.at/Api

Strategy
--------
Fetch public holidays for the current year + next year for three countries:
  US  (United States)   → general / consumer audience
  IN  (India)           → general / india audience
  GB  (United Kingdom)  → general / consumer audience

Each holiday is stored as an ExternalEvent with:
  industry      = "general"
  audience_tags = derived from country
  magnitude     = 3 for most holidays, 5 for globally significant ones
  source        = "nager-date-api"

Existing Nager.Date events (source="nager-date-api") are deleted before
each refresh so duplicates never accumulate.
"""

import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from models import ExternalEvent

NAGER_BASE = "https://date.nager.at/api/v3"

# Countries to fetch: (countryCode, audience_tags, label)
COUNTRIES = [
    ("US", ["consumer", "media", "retail"],    "US"),
    ("IN", ["consumer", "india", "retail"],    "India"),
    ("GB", ["consumer", "media", "retail"],    "UK"),
]

# Holidays that are globally well-known get magnitude 5
HIGH_MAGNITUDE_KEYWORDS = {
    "christmas", "new year", "easter", "diwali", "halloween",
    "thanksgiving", "independence day", "republic day",
}


def _magnitude(name: str) -> int:
    lower = name.lower()
    for kw in HIGH_MAGNITUDE_KEYWORDS:
        if kw in lower:
            return 5
    return 3


def fetch_holidays_for_country(country_code: str, year: int) -> list[dict]:
    """
    Returns a list of holiday dicts from the Nager.Date v3 API.
    Endpoint: GET /api/v3/PublicHolidays/{year}/{countryCode}
    """
    url = f"{NAGER_BASE}/PublicHolidays/{year}/{country_code}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        print(f"[ingestion] Failed to fetch {country_code}/{year}: {e}")
        return []


def ingest(db: Session) -> dict:
    """
    Fetch public holidays from Nager.Date and upsert into ExternalEvent table.
    Returns a summary dict: {fetched, skipped, total_live}.
    """
    current_year = datetime.utcnow().year
    years = [current_year, current_year + 1]

    # Remove stale Nager.Date records before re-ingesting
    deleted = db.query(ExternalEvent).filter(
        ExternalEvent.source == "nager-date-api"
    ).delete()
    db.flush()

    fetched = 0
    skipped = 0

    for country_code, audience_tags, label in COUNTRIES:
        for year in years:
            holidays = fetch_holidays_for_country(country_code, year)
            for h in holidays:
                date_str = h.get("date")
                name     = h.get("name") or h.get("localName") or "Holiday"
                if not date_str:
                    skipped += 1
                    continue

                # Skip regional/county-level holidays (not global enough)
                if h.get("counties"):
                    skipped += 1
                    continue

                evt = ExternalEvent(
                    name=f"{name} ({label})",
                    date=date_str,
                    industry="general",
                    audience_tags=audience_tags,
                    magnitude=_magnitude(name),
                    source="nager-date-api",
                )
                db.add(evt)
                fetched += 1

    db.commit()

    total_live = db.query(ExternalEvent).filter(
        ExternalEvent.source == "nager-date-api"
    ).count()

    print(f"[ingestion] Nager.Date: fetched={fetched}, skipped={skipped}, live={total_live}")
    return {"fetched": fetched, "skipped": skipped, "total_live": total_live}
