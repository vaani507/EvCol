from datetime import date, datetime, time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import _campus_events_overlap, _ensure_campus_event_type_column, app
from models import SaturnaliaEvent


def make_event(college, event_date, start, end, location):
    return SimpleNamespace(
        college=college,
        start_at=datetime.combine(event_date, start),
        end_at=datetime.combine(event_date, end) if end else None,
        location=location,
    )


@pytest.fixture
def campus_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client, test_session
    finally:
        client.close()
        app.dependency_overrides.clear()
        engine.dispose()


def register_event(
    client, college, name, start_time, end_time, location, event_type="Cultural"
):
    return client.post(
        "/api/campus/events",
        json={
            "college": college,
            "team_name": "Robotics Club",
            "name": name,
            "event_type": event_type,
            "date": "2026-12-01",
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
        },
    )


def test_events_overlap_even_at_different_locations():
    first = make_event("Example College", date(2026, 12, 1), time(10), time(12), "Hall A")
    second = make_event("Example College", date(2026, 12, 1), time(11), time(13), "Hall B")

    assert _campus_events_overlap(first, second)


def test_events_touching_at_end_time_do_not_overlap():
    first = make_event("Example College", date(2026, 12, 1), time(10), time(11), "Hall A")
    second = make_event("Example College", date(2026, 12, 1), time(11), time(12), "Hall A")

    assert not _campus_events_overlap(first, second)


def test_events_from_different_colleges_do_not_overlap():
    first = make_event("College A", date(2026, 12, 1), time(10), time(12), "Hall A")
    second = make_event("College B", date(2026, 12, 1), time(10), time(12), "Hall A")

    assert not _campus_events_overlap(first, second)


def test_unknown_duration_only_overlaps_at_the_exact_start_time():
    known = make_event("Example College", date(2026, 12, 1), time(10), time(12), "Hall A")
    unknown_same_start = make_event("Example College", date(2026, 12, 1), time(10), None, "Hall B")
    unknown_during_known_event = make_event("Example College", date(2026, 12, 1), time(11), None, "Hall C")

    assert _campus_events_overlap(known, unknown_same_start)
    assert not _campus_events_overlap(known, unknown_during_known_event)


def test_registering_events_reports_overlaps_on_separate_college_boards(campus_client):
    client, _ = campus_client
    first = register_event(client, "Example College", "Club Fair", "10:00", "12:00", "Main Hall")
    assert first.status_code == 201
    assert first.json()["overlaps_with"] == []

    overlapping = register_event(client, "Example College", "Coding Workshop", "11:00", "13:00", "Lab 2")
    assert overlapping.status_code == 201
    assert overlapping.json()["overlaps_with"][0]["location"] == "Main Hall"

    other_college = register_event(client, "Another College", "Club Fair", "11:00", "13:00", "Main Hall")
    assert other_college.status_code == 201
    assert other_college.json()["overlaps_with"] == []

    board = client.get("/api/campus/events", params={"college": "Example College"})
    assert len(board.json()) == 2
    assert all(event["overlaps_with"] for event in board.json())


def test_registration_includes_campus_risk_and_same_day_recommendations(campus_client):
    client, _ = campus_client
    register_event(client, "Example College", "Club Fair", "10:00", "12:00", "Main Hall")

    response = register_event(
        client, "Example College", "Coding Workshop", "11:00", "13:00", "Lab 2"
    )

    event = response.json()
    assert event["risk_score"] == 60
    assert event["risk_level"] == "Medium"
    assert event["peak_overlap_minutes"] == 60
    assert event["recommendations"]
    assert all(
        item["start_at"][:10] == "2026-12-01"
        and item["risk_score"] < event["risk_score"]
        and not item["overlaps_with"]
        for item in event["recommendations"]
    )


@pytest.mark.parametrize(
    ("event_type", "expected_score", "expected_weight"),
    [
        ("Cultural", 60, 1.0),
        ("Business", 69, 1.15),
        ("Technical", 78, 1.3),
    ],
)
def test_event_type_weights_the_schedule_risk_score(
    campus_client, event_type, expected_score, expected_weight
):
    client, _ = campus_client
    register_event(client, "Example College", "Club Fair", "10:00", "12:00", "Main Hall")

    response = register_event(
        client,
        "Example College",
        "Department Event",
        "11:00",
        "13:00",
        "Lab 2",
        event_type=event_type,
    )

    assert response.status_code == 201
    assert response.json()["category"] == event_type
    assert response.json()["risk_score"] == expected_score
    assert response.json()["risk_weight"] == expected_weight


def test_existing_database_gets_nullable_event_type_column():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE campus_events (id INTEGER PRIMARY KEY)"
        )

    _ensure_campus_event_type_column(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("campus_events")}
    assert "event_type" in columns
    engine.dispose()


def test_directors_cut_is_included_in_the_campus_schedule(campus_client):
    client, test_session = campus_client
    db = test_session()
    db.add(SaturnaliaEvent(
        source_id="directors-cut",
        name="Director's Cut",
        category="Cultural",
        start_at=datetime(2026, 12, 1, 10),
        end_at=datetime(2026, 12, 1, 12),
        location="Entire Campus",
    ))
    db.commit()
    db.close()

    board = client.get(
        "/api/campus/events",
        params={"college": "Thapar Institute of Engineering and Technology"},
    )

    assert board.status_code == 200
    assert len(board.json()) == 1
    assert board.json()[0]["name"] == "Director's Cut"
    assert board.json()[0]["category"] == "Cultural"


def test_reschedule_preserves_day_and_duration_and_refreshes_risk(campus_client):
    client, _ = campus_client
    register_event(client, "Example College", "Club Fair", "10:00", "12:00", "Main Hall")
    event = register_event(
        client, "Example College", "Coding Workshop", "11:00", "13:00", "Lab 2"
    ).json()

    response = client.patch(
        f"/api/campus/events/{event['id']}/reschedule",
        json={
            "college": "Example College",
            "start_time": "12:00",
            "end_time": "14:00",
        },
    )

    assert response.status_code == 200
    rescheduled = response.json()
    assert rescheduled["start_at"] == "2026-12-01T12:00:00"
    assert rescheduled["end_at"] == "2026-12-01T14:00:00"
    assert rescheduled["overlaps_with"] == []
    assert rescheduled["risk_score"] == 0


def test_reschedule_rejects_duration_changes(campus_client):
    client, _ = campus_client
    event = register_event(
        client, "Example College", "Workshop", "11:00", "13:00", "Lab 2"
    ).json()

    response = client.patch(
        f"/api/campus/events/{event['id']}/reschedule",
        json={
            "college": "Example College",
            "start_time": "12:00",
            "end_time": "13:00",
        },
    )

    assert response.status_code == 422


def test_registration_rejects_end_time_before_start_time(campus_client):
    client, _ = campus_client
    response = register_event(client, "Example College", "Invalid Event", "13:00", "12:00", "Main Hall")

    assert response.status_code == 422


def test_saturnalia_events_and_venues_are_available_to_the_thapar_board(campus_client):
    client, test_session = campus_client
    db = test_session()
    db.add(SaturnaliaEvent(
        source_id="sat-event-1",
        name="Saturnalia Test Event",
        category="Technical",
        start_at=datetime(2026, 12, 1, 10),
        end_at=datetime(2026, 12, 1, 12),
        location="OAT",
    ))
    db.commit()
    db.close()

    board = client.get(
        "/api/campus/events",
        params={"college": "Thapar Institute of Engineering and Technology"},
    )
    assert board.status_code == 200
    assert board.json()[0]["source"] == "Saturnalia"

    registration = register_event(
        client,
        "Thapar Institute of Engineering and Technology",
        "College Team Event",
        "11:00",
        "13:00",
        "Another venue",
    )
    assert registration.status_code == 201
    assert registration.json()["overlaps_with"][0]["location"] == "OAT"

    locations = client.get("/api/campus/locations")
    assert "OAT" in locations.json()
