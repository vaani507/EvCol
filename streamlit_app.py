import os
import sys
from datetime import date, time
from html import escape

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
INDUSTRY_COLORS = {
    "tech": "#3b82f6",
    "entertainment": "#a855f7",
    "finance": "#10b981",
    "sports": "#f59e0b",
    "media": "#ef4444",
    "general": "#64748b",
}


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-base: #f8fafc;
        --bg-surface: #ffffff;
        --bg-subtle: #f1f5f9;
        --border: #e2e8f0;
        --border-strong: #cbd5e1;
        --primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --red: #ef4444;
        --amber: #d97706;
        --green: #059669;
    }

    .stApp {
        background-color: var(--bg-base);
        background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
        background-size: 24px 24px;
        color: var(--primary);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .stApp > header { background: transparent; }
    [data-testid="stHeaderActionElements"] { display: none; }
    .block-container { max-width: 1200px; padding-top: 0; padding-bottom: 4rem; }
    .site-header {
        margin: 0 calc((min(1200px, 100vw) - 100vw) / 2) 2.5rem;
        padding: 0 max(32px, calc((100vw - 1200px) / 2));
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #fff;
        border-bottom: 1px solid var(--border);
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-mark {
        width: 28px; height: 28px; border-radius: 6px;
        background: var(--primary); color: #fff; display: grid; place-items: center;
        font-size: 14px; font-weight: 700; letter-spacing: -1px;
    }
    .brand-name { color: var(--primary); font-size: 15px; font-weight: 600; }
    .brand-tagline { color: var(--text-secondary); font-size: 13px; }
    .hero { text-align: center; margin: 0 auto 2.5rem; }
    .hero h1 {
        color: var(--primary); font-size: 32px; font-weight: 700;
        letter-spacing: -0.02em; margin: 0 0 12px;
    }
    .hero p {
        color: var(--text-secondary); font-size: 16px;
        max-width: 600px; margin: 0 auto;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,.05);
    }
    .card-heading { color: var(--primary); font-size: 16px; font-weight: 600; margin: 0 0 4px; }
    .muted-copy { color: var(--text-secondary); font-size: 13px; margin: 0 0 18px; }
    .result-title { color: var(--primary); font-size: 18px; font-weight: 600; margin: 0; }
    .risk-badge {
        display: inline-block; padding: 4px 10px; border-radius: 6px;
        font-size: 12px; font-weight: 600; letter-spacing: .05em; text-transform: uppercase;
    }
    .risk-high { color: #ef4444; background: #fef2f2; border: 1px solid #f87171; }
    .risk-medium { color: #d97706; background: #fffbeb; border: 1px solid #fbbf24; }
    .risk-low { color: #059669; background: #ecfdf5; border: 1px solid #34d399; }
    .score-ring {
        width: 120px; height: 120px; border-radius: 50%; display: grid; place-items: center;
        margin: 8px auto 16px;
    }
    .score-inner {
        width: 100px; height: 100px; border-radius: 50%; background: #fff;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .score-number { color: var(--primary); font-size: 32px; font-weight: 700; line-height: 1; }
    .score-scale { color: var(--text-muted); font-size: 11px; }
    .score-description { color: var(--text-secondary); text-align: center; font-size: 14px; margin: 0 auto 20px; max-width: 320px; }
    .section-heading {
        display: flex; align-items: center; justify-content: space-between;
        color: var(--primary); font-size: 14px; font-weight: 600; margin: 0 0 10px;
    }
    .section-count { color: var(--text-muted); font-size: 13px; font-weight: 400; }
    .conflict-row {
        display: flex; align-items: center; justify-content: space-between; gap: 12px;
        padding: 10px 0; border-bottom: 1px solid var(--bg-subtle);
    }
    .conflict-main { min-width: 0; display: flex; align-items: center; gap: 12px; }
    .conflict-delta {
        width: 48px; flex: 0 0 48px; text-align: center; padding: 4px 0;
        color: var(--text-secondary); background: var(--bg-subtle); border-radius: 4px; font-size: 12px;
    }
    .conflict-name { color: var(--primary); font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .conflict-date { color: var(--text-muted); font-size: 12px; }
    .industry-chip {
        padding: 2px 8px; border: 1px solid var(--border); border-radius: 6px;
        background: var(--bg-subtle); color: var(--text-secondary); font-size: 11px;
    }
    .empty-state {
        padding: 20px 12px; border-radius: 8px; text-align: center;
        background: var(--bg-subtle); color: var(--text-secondary); font-size: 13px;
    }
    .timeline-scroll { overflow-x: auto; padding: 8px 0 12px; border-bottom: 1px solid var(--bg-subtle); }
    .timeline { display: grid; grid-template-columns: repeat(29, minmax(32px, 1fr)); min-width: 928px; height: 88px; align-items: end; }
    .timeline-day { text-align: center; min-width: 0; color: var(--text-secondary); font-size: 11px; }
    .timeline-day.weekend { color: var(--text-muted); }
    .timeline-day.proposed { color: var(--primary); font-weight: 700; }
    .timeline-dots { height: 44px; display: flex; flex-direction: column; justify-content: end; align-items: center; gap: 3px; padding-bottom: 8px; }
    .timeline-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .timeline-label { border-top: 2px solid transparent; padding-top: 7px; }
    .timeline-day.proposed .timeline-label { border-color: var(--primary); }
    .legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px; color: var(--text-secondary); font-size: 12px; }
    .legend-item { display: inline-flex; gap: 6px; align-items: center; }
    .recommendation {
        position: relative; height: 100%; padding: 16px; border: 1px solid var(--border);
        border-radius: 8px; background: #fff;
    }
    .recommendation.top-pick { border-color: var(--border-strong); background: #f8fafc; margin-top: 8px; }
    .top-pick-label {
        position: absolute; top: -10px; left: 16px; padding: 2px 8px; border-radius: 10px;
        background: var(--primary); color: #fff; font-size: 10px; font-weight: 600;
        letter-spacing: .05em; text-transform: uppercase;
    }
    .recommendation-year { color: var(--text-secondary); font-size: 12px; }
    .recommendation-date { color: var(--primary); font-size: 16px; font-weight: 600; margin: 2px 0 12px; }
    .recommendation-footer { border-top: 1px solid var(--bg-subtle); padding-top: 10px; display: flex; justify-content: space-between; align-items: end; }
    .recommendation-score-label { color: var(--text-muted); font-size: 11px; }
    .recommendation-score { color: var(--primary); font-size: 18px; font-weight: 700; }
    .recommendation-improvement { color: var(--green); font-size: 12px; font-weight: 500; }
    div.stButton > button[kind="primaryFormSubmit"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: var(--primary); border-color: var(--primary); color: #fff;
        font-weight: 500; min-height: 42px;
    }
    @media (max-width: 720px) {
        .hero h1 { font-size: 26px; }
        .site-header { margin-bottom: 1.5rem; }
        .brand-tagline { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def render_risk_report(result):
    score = result["score"]
    risk_level = result["risk_level"]
    risk_class = risk_level.lower()
    descriptions = {
        "High": "Major competing events detected. High likelihood of audience dilution.",
        "Medium": "Some competing events present. Proceed with awareness.",
        "Low": "Minimal competing events detected. Optimal launch window.",
    }
    score_color = {
        "High": "#ef4444",
        "Medium": "#d97706",
        "Low": "#059669",
    }.get(risk_level, "#059669")
    score_angle = round(max(0, min(100, score)) * 3.6)
    event_date = date.fromisoformat(result["proposed_date"])
    formatted_date = event_date.strftime("%A, %B %d, %Y")

    with st.container(border=True):
        title_col, badge_col = st.columns([4, 1])
        title_col.markdown(
            f'<p class="result-title">{escape(result["event_name"])}</p>'
            f'<p class="muted-copy">{formatted_date}</p>',
            unsafe_allow_html=True,
        )
        badge_col.markdown(
            f'<span class="risk-badge risk-{risk_class}">{risk_level} Risk</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="score-ring" style="background: conic-gradient({score_color} {score_angle}deg, #f1f5f9 0deg)">
                <div class="score-inner">
                    <span class="score-number">{round(score)}</span>
                    <span class="score-scale">/ 100</span>
                </div>
            </div>
            <p class="score-description">{descriptions.get(risk_level, descriptions["Low"])}</p>
            """,
            unsafe_allow_html=True,
        )
        conflict_count = len(result["conflicting_events"])
        st.markdown(
            '<div class="section-heading"><span>Conflict Analysis</span>'
            f'<span class="section-count">{conflict_count} event'
            f'{"s" if conflict_count != 1 else ""} found</span></div>',
            unsafe_allow_html=True,
        )
        if not result["conflicting_events"]:
            st.markdown(
                '<div class="empty-state">No significant events detected in the ±14-day window.</div>',
                unsafe_allow_html=True,
            )
        else:
            for event in result["conflicting_events"]:
                delta = event["delta_days"]
                delta_label = (
                    f"+{delta}d" if delta > 0 else f"{delta}d" if delta < 0 else "Same day"
                )
                event_day = date.fromisoformat(event["date"])
                magnitude = max(0, min(5, event["magnitude"] or 0))
                stars = "★" * magnitude + "☆" * (5 - magnitude)
                st.markdown(
                    f"""
                    <div class="conflict-row">
                      <div class="conflict-main">
                        <span class="conflict-delta">{delta_label}</span>
                        <div style="min-width:0">
                          <div class="conflict-name">{escape(event["name"])}</div>
                          <div class="conflict-date">{event_day.strftime("%b %d")}</div>
                        </div>
                      </div>
                      <span class="industry-chip">{escape(event["industry"])}</span>
                      <span style="color:#64748b;font-size:12px;letter-spacing:1px">{stars}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_timeline(result):
    proposed = date.fromisoformat(result["proposed_date"])
    conflicts_by_offset = {}
    for event in result["conflicting_events"]:
        conflicts_by_offset.setdefault(event["delta_days"], []).append(event)

    days = [proposed.fromordinal(proposed.toordinal() + offset) for offset in range(-14, 15)]
    cells = []
    for offset, day in zip(range(-14, 15), days):
        dots = "".join(
            f'<span class="timeline-dot" style="background:{INDUSTRY_COLORS.get(event["industry"], "#64748b")}" title="{escape(event["name"])}"></span>'
            for event in conflicts_by_offset.get(offset, [])[:3]
        )
        extra_count = len(conflicts_by_offset.get(offset, [])) - 3
        if extra_count > 0:
            dots += f'<span style="font-size:10px;color:#64748b">+{extra_count}</span>'
        day_class = "timeline-day"
        if day.weekday() >= 5:
            day_class += " weekend"
        if offset == 0:
            day_class += " proposed"
        cells.append(
            f'<div class="{day_class}" title="{day.strftime("%A, %B %d")}">'
            f'<div class="timeline-dots">{dots}</div>'
            f'<div class="timeline-label">{day.day}</div></div>'
        )

    with st.container(border=True):
        st.markdown('<p class="card-heading">14-Day Proximity Radar</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="muted-copy">Distribution of competing events around your launch date.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="timeline-scroll"><div class="timeline">{"".join(cells)}</div></div>',
            unsafe_allow_html=True,
        )
        industries = sorted({event["industry"] for event in result["conflicting_events"]})
        if industries:
            legend = "".join(
                f'<span class="legend-item"><span class="timeline-dot" style="background:{INDUSTRY_COLORS.get(industry, "#64748b")}"></span>{escape(industry.title())}</span>'
                for industry in industries
            )
            st.markdown(f'<div class="legend">{legend}</div>', unsafe_allow_html=True)


def render_recommendations(result):
    recommendations = result["recommendations"]
    if not recommendations:
        return
    with st.container(border=True):
        st.markdown('<p class="card-heading">Alternative Launch Windows</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="muted-copy">Lower-risk dates within a ±30 day window.</p>',
            unsafe_allow_html=True,
        )
        columns = st.columns(len(recommendations))
        for index, (column, recommendation) in enumerate(zip(columns, recommendations)):
            rec_date = date.fromisoformat(recommendation["date"])
            improvement = round(result["score"] - recommendation["score"])
            badge = '<span class="top-pick-label">Top Pick</span>' if index == 0 else ""
            top_pick = " top-pick" if index == 0 else ""
            with column:
                st.markdown(
                    f"""
                    <div class="recommendation{top_pick}">
                      {badge}
                      <div class="recommendation-year">{rec_date.year}</div>
                      <div class="recommendation-date">{rec_date.strftime("%a, %b %d")}</div>
                      <div class="recommendation-footer">
                        <div><div class="recommendation-score-label">Risk Score</div>
                          <div class="recommendation-score">{round(recommendation["score"])}</div></div>
                        <div class="recommendation-improvement">↑ {improvement} pts</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def show_launch_analysis():
    st.markdown(
        '<div class="hero"><h1>Schedule your launch with confidence</h1>'
        '<p>Identify potential conflicts with competitor launches, industry conferences, '
        'and major public events before you commit to a date.</p></div>',
        unsafe_allow_html=True,
    )
    form_column, results_column = st.columns([0.85, 1.35], gap="large", vertical_alignment="top")

    with form_column:
        with st.container(border=True):
            st.markdown('<p class="card-heading">Launch Details</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="muted-copy">Configure your event to calculate collision risk.</p>',
                unsafe_allow_html=True,
            )
            with st.form("launch_analysis"):
                name = st.text_input("Event Name", placeholder="e.g. Q3 Product Release")
                proposed_date = st.date_input(
                    "Proposed Date", value=date.today(), min_value=date.today()
                )
                industry_label = st.selectbox("Primary Industry", list(INDUSTRIES))
                audience_tags = st.pills(
                    "Target Audience", AUDIENCE_TAGS, selection_mode="multi"
                )
                if not audience_tags:
                    st.caption("Select tags to improve accuracy.")
                submitted = st.form_submit_button(
                    "Analyze Risk", type="primary", use_container_width=True
                )

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

    with results_column:
        result = st.session_state.get("launch_result")
        if result:
            render_risk_report(result)
            render_timeline(result)
            render_recommendations(result)
        else:
            with st.container(border=True, height=600):
                st.markdown(
                    """
                    <div style="height:520px;display:flex;flex-direction:column;align-items:center;
                                justify-content:center;text-align:center">
                      <div style="font-size:40px;color:#cbd5e1;margin-bottom:12px">▦</div>
                      <div style="font-size:15px;font-weight:500;color:#0f172a;margin-bottom:8px">
                        No analysis yet
                      </div>
                      <div style="font-size:14px;color:#475569;max-width:250px">
                        Enter your proposed launch details on the left to generate a risk report.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


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
st.markdown(
    '<div class="site-header"><div class="brand">'
    '<div class="brand-mark">EC</div>'
    '<div class="brand-name">EventCollision</div></div>'
    '<div class="brand-tagline">Predictive Launch Intelligence</div></div>',
    unsafe_allow_html=True,
)

launch_tab, radar_tab, campus_tab = st.tabs(
    ["Launch risk", "Event radar", "Campus schedule"]
)
with launch_tab:
    show_launch_analysis()
with radar_tab:
    show_event_radar()
with campus_tab:
    show_campus_schedule()
