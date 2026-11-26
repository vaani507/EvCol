import os
import sys
from datetime import date, time

import streamlit as st
from fastapi import HTTPException
from sqlalchemy import inspect


st.set_page_config(
    page_title="Event Collision Detector",
    page_icon=":material/event:",
    layout="wide",
)

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "code", "backend")
sys.path.insert(0, BACKEND_DIR)

from database import Base, SessionLocal, engine  # noqa: E402
from ingestion import ingest  # noqa: E402
from main import (  # noqa: E402
    AnalyzeRequest,
    CampusEventRequest,
    CampusRescheduleRequest,
    SATURNALIA_COLLEGE,
    _ensure_campus_event_type_column,
    analyze,
    list_campus_events,
    list_campuses,
    list_events,
    refresh_saturnalia_events,
    register_campus_event,
    reschedule_campus_event,
)
from seed import seed  # noqa: E402


INDUSTRIES = {
    "Technology": "tech",
    "Entertainment": "entertainment",
    "Finance": "finance",
    "Sports": "sports",
    "Media & Marketing": "media",
    "General / Other": "general",
}
AUDIENCE_TAGS = [
    "developers", "enterprise", "consumer", "investors", "startups",
    "media", "mobile", "ai", "cloud", "gaming", "music", "film",
    "sports", "marketing", "retail", "india",
]


@st.cache_resource
def initialize_database():
    Base.metadata.create_all(bind=engine)
    columns = {
        column["name"]
        for column in inspect(engine).get_columns("campus_events")
    }
    if "event_type" not in columns:
        _ensure_campus_event_type_column()
    seed()
    return engine


def show_launch_analysis():
    st.subheader("Schedule your launch with confidence")
    st.write(
        "Check your proposed date against competitor launches, industry events, "
        "and public holidays."
    )

    with st.form("launch_analysis"):
        name = st.text_input("Event name", placeholder="Q3 Product Release")
        proposed_date = st.date_input(
            "Proposed date", value=date.today(), min_value=date.today()
        )
        industry_label = st.selectbox("Primary industry", list(INDUSTRIES))
        audience_tags = st.multiselect("Target audience", AUDIENCE_TAGS)
        submitted = st.form_submit_button("Analyze risk", type="primary")

    if submitted:
        if not name.strip():
            st.error("Enter an event name before analyzing.")
        else:
            with SessionLocal() as db:
                result = analyze(
                    AnalyzeRequest(
                        name=name.strip(),
                        proposed_date=proposed_date.isoformat(),
                        industry=INDUSTRIES[industry_label],
                        audience_tags=audience_tags,
                    ),
                    db,
                )
            st.session_state["launch_result"] = result

    result = st.session_state.get("launch_result")
    if not result:
        return

    st.divider()
    st.markdown("### " + result["event_name"])
    first, second = st.columns(2)
    first.metric("Collision risk", result["risk_level"])
    second.metric("Risk score", f'{result["score"]:.1f} / 100')

    st.markdown("#### Conflicting events")
    if result["conflicting_events"]:
        st.dataframe(result["conflicting_events"], use_container_width=True, hide_index=True)
    else:
        st.info("No significant events were found within 14 days of this date.")

    st.markdown("#### Lower-risk alternative dates")
    st.dataframe(result["recommendations"], use_container_width=True, hide_index=True)


def show_event_radar():
    st.subheader("Event radar")
    with SessionLocal() as db:
        events = list_events(db=db)
    if events:
        st.dataframe(
            [
                {
                    "Event": event.name,
                    "Date": event.date,
                    "Industry": event.industry.title(),
                    "Magnitude": event.magnitude,
                    "Source": event.source,
                }
                for event in events
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No events are available yet.")

    if st.button("Refresh public holidays"):
        with SessionLocal() as db:
            summary = ingest(db)
        st.success(
            f'Refreshed {summary["total_live"]} public holidays '
            f'({summary["fetched"]} added).'
        )
        st.rerun()


def show_campus_schedule():
    st.subheader("Campus event schedule")
    with SessionLocal() as db:
        colleges = list_campuses(db)

    left, right = st.columns([3, 2])
    with left:
        if st.button("Sync Saturnalia events"):
            with SessionLocal() as db:
                try:
                    summary = refresh_saturnalia_events(db)
                except HTTPException as error:
                    st.error(error.detail)
                else:
                    st.success(f'Imported {summary["imported"]} Saturnalia events.')
                    st.rerun()

    with right:
        selected_college = st.selectbox(
            "College board",
            colleges or [SATURNALIA_COLLEGE],
        )

    with SessionLocal() as db:
        schedule = list_campus_events(college=selected_college, db=db)
    if schedule:
        rows = [
            {
                "Date": event.start_at.strftime("%Y-%m-%d"),
                "Start": event.start_at.strftime("%H:%M"),
                "End": event.end_at.strftime("%H:%M") if event.end_at else "Unknown",
                "Event": event.name,
                "Team": event.team_name,
                "Type": event.category or "Other",
                "Location": event.location,
                "Risk": event.risk_level,
                "Score": event.risk_score,
                "Source": event.source,
            }
            for event in schedule
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No campus events on this board yet.")

    with st.expander("Register a campus event"):
        with st.form("campus_event"):
            college = st.text_input(
                "College", value=selected_college, max_chars=160
            )
            team_name = st.text_input("Team or club", max_chars=160)
            event_name = st.text_input("Event name", max_chars=200)
            event_type = st.selectbox(
                "Event type", ["Cultural", "Business", "Technical"]
            )
            event_date = st.date_input("Date", value=date.today())
            start_time = st.time_input("Start time", value=time(10, 0))
            end_time = st.time_input("End time", value=time(11, 0))
            location = st.text_input("Location", max_chars=200)
            register = st.form_submit_button("Register event")

        if register:
            if not all(
                value.strip()
                for value in (college, team_name, event_name, location)
            ):
                st.error("Fill in all event details.")
            elif end_time <= start_time:
                st.error("End time must be later than start time.")
            else:
                request = CampusEventRequest(
                    college=college,
                    team_name=team_name,
                    name=event_name,
                    event_type=event_type,
                    date=event_date,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                )
                with SessionLocal() as db:
                    register_campus_event(request, db)
                st.success("Campus event registered.")
                st.rerun()

    reschedulable = [event for event in schedule if event.reschedulable]
    if reschedulable:
        with st.expander("Apply a suggested time"):
            selected_event = st.selectbox(
                "Registered event",
                reschedulable,
                format_func=lambda event: (
                    f"{event.name} - {event.start_at.strftime('%Y-%m-%d %H:%M')}"
                ),
            )
            recommendations = selected_event.recommendations
            if recommendations:
                chosen = st.selectbox(
                    "Suggested slot",
                    recommendations,
                    format_func=lambda item: (
                        f'{item.start_at.strftime("%H:%M")}-'
                        f'{item.end_at.strftime("%H:%M")} (risk {item.risk_score})'
                    ),
                )
                if st.button("Reschedule event"):
                    request = CampusRescheduleRequest(
                        college=selected_college,
                        start_time=chosen.start_at.time(),
                        end_time=chosen.end_at.time(),
                    )
                    with SessionLocal() as db:
                        reschedule_campus_event(
                            event_id=int(selected_event.id),
                            req=request,
                            db=db,
                        )
                    st.success("Event rescheduled.")
                    st.rerun()
            else:
                st.info("No lower-risk time slot is available for this event.")

    conflicts = [
        {
            "Event": event.name,
            "Conflicts": ", ".join(item.name for item in event.overlaps_with),
            "Suggested slots": len(event.recommendations),
        }
        for event in schedule
        if event.overlaps_with
    ]
    if conflicts:
        st.markdown("#### Schedule conflicts")
        st.dataframe(conflicts, use_container_width=True, hide_index=True)


initialize_database()
st.title("Event Collision Detector")
st.caption("Predictive launch intelligence and campus schedule risk analysis")

launch_tab, radar_tab, campus_tab = st.tabs(
    ["Launch risk", "Event radar", "Campus schedule"]
)
with launch_tab:
    show_launch_analysis()
with radar_tab:
    show_event_radar()
with campus_tab:
    show_campus_schedule()
