from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import SaturnaliaEvent
from saturnalia import parse_source_datetime, sync_saturnalia_events


def test_source_utc_timestamps_are_converted_to_india_local_time():
    assert parse_source_datetime("2026-11-20T14:30:00.000Z") == datetime(2026, 11, 20, 20, 0)


def test_sync_upserts_source_events_and_marks_invalid_end_time_unknown():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine)
    db = test_session()
    db.add(SaturnaliaEvent(
        source_id="stale",
        name="Stale event",
        category="Other",
        start_at=datetime(2026, 11, 1, 10),
        end_at=datetime(2026, 11, 1, 11),
        location="Old venue",
    ))
    db.commit()

    record = {
        "eventId": "source-event",
        "title": "Source event",
        "category": "Technical",
        "startDateTime": "2026-11-20T14:30:00.000Z",
        "endDateTime": "2026-11-20T14:00:00.000Z",
        "venueName": "OAT",
    }
    with patch("saturnalia.fetch_saturnalia_events", return_value=([record], 1)):
        result = sync_saturnalia_events(db)

    assert result["imported"] == 1
    assert result["unknown_duration"] == 1
    events = db.query(SaturnaliaEvent).all()
    assert len(events) == 1
    assert events[0].name == "Source event"
    assert events[0].start_at == datetime(2026, 11, 20, 20, 0)
    assert events[0].end_at is None

    db.close()
    engine.dispose()
