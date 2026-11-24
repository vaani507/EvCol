from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from sqlalchemy.orm import Session

from models import SaturnaliaEvent

SATURNALIA_EVENTS_URL = "https://api.saturnalia.in/api/v1/events"
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def parse_source_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(INDIA_TIMEZONE).replace(tzinfo=None)
    return parsed


def fetch_saturnalia_events() -> Tuple[List[Dict[str, Any]], int]:
    records: List[Dict[str, Any]] = []
    offset = 0
    limit = 2000
    total = 0

    with httpx.Client(timeout=30.0) as client:
        while True:
            response = client.get(
                SATURNALIA_EVENTS_URL,
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items") if isinstance(payload, dict) else None
            page_total = payload.get("total") if isinstance(payload, dict) else None
            if not isinstance(items, list) or not isinstance(page_total, int):
                raise ValueError("Saturnalia returned an unexpected events response.")

            records.extend(item for item in items if isinstance(item, dict))
            total = page_total
            offset += len(items)
            if not items or offset >= total:
                break

    if total and not records:
        raise ValueError("Saturnalia returned no event records.")
    return records, total


def sync_saturnalia_events(db: Session) -> dict:
    records, source_total = fetch_saturnalia_events()
    existing = {
        event.source_id: event
        for event in db.query(SaturnaliaEvent).all()
    }
    source_ids: Set[str] = set()
    imported = 0
    skipped = 0
    unknown_duration = 0

    for record in records:
        source_id = str(record.get("eventId") or record.get("id") or "").strip()
        if not source_id:
            skipped += 1
            continue
        source_ids.add(source_id)

        name = str(record.get("title") or "").strip()
        start_at = parse_source_datetime(record.get("startDateTime"))
        location = str(record.get("venueName") or "").strip()
        if not name or start_at is None or not location:
            skipped += 1
            continue

        end_at = parse_source_datetime(record.get("endDateTime"))
        if end_at is None or end_at <= start_at:
            end_at = None
            unknown_duration += 1

        event = existing.get(source_id)
        if event is None:
            event = SaturnaliaEvent(source_id=source_id)
            db.add(event)
            existing[source_id] = event

        event.name = name
        event.category = str(record.get("category") or "Other").strip() or "Other"
        event.start_at = start_at
        event.end_at = end_at
        event.location = location
        imported += 1

    if imported == 0:
        raise ValueError("No valid Saturnalia events could be imported.")

    if source_ids:
        db.query(SaturnaliaEvent).filter(
            ~SaturnaliaEvent.source_id.in_(source_ids)
        ).delete(synchronize_session=False)
    db.commit()
    return {
        "imported": imported,
        "source_total": source_total,
        "skipped": skipped,
        "unknown_duration": unknown_duration,
    }
