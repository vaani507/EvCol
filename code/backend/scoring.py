"""
Heuristic collision scoring engine.

Score formula per competing event:
  component = temporal_weight * industry_weight * audience_weight * magnitude_weight

Temporal weight  : Gaussian decay centred on the proposed date, σ = 7 days.
Industry weight  : 1.0 (same), 0.6 (adjacent), 0.15 (unrelated).
Audience weight  : Jaccard similarity of audience tag sets, in [0,1].
Magnitude weight : Linear scale from 0.8 (mag=1) to 2.0 (mag=5).

Aggregate score  : min(100, Σ(component) * 20)
Risk level       : High ≥ 65 | Medium ≥ 30 | Low < 30
"""

import math
from datetime import date, timedelta
from typing import Any

# Industry adjacency map
INDUSTRY_ADJACENCY: dict[str, list[str]] = {
    "tech":          ["tech", "finance", "media"],
    "entertainment": ["entertainment", "media", "sports"],
    "finance":       ["finance", "tech"],
    "sports":        ["sports", "entertainment"],
    "media":         ["media", "tech", "entertainment"],
    "general":       ["general"],
}


def _temporal_weight(delta_days: int, sigma: float = 7.0) -> float:
    """Gaussian decay on |delta_days|."""
    return math.exp(-0.5 * (delta_days / sigma) ** 2)


def _industry_weight(proposed: str, competing: str) -> float:
    adjacent = INDUSTRY_ADJACENCY.get(proposed, [])
    if proposed == competing:
        return 1.0
    if competing in adjacent:
        return 0.6
    return 0.15


def _audience_weight(proposed_tags: list[str], competing_tags: list[str]) -> float:
    a, b = set(proposed_tags), set(competing_tags)
    if not a and not b:
        return 0.5          # no tags → neutral
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _magnitude_weight(magnitude: int) -> float:
    # Linear: mag 1 → 0.8, mag 5 → 2.0
    return 0.8 + (magnitude - 1) * 0.3


def compute_score(
    proposed_date: date,
    proposed_industry: str,
    proposed_tags: list[str],
    external_events: list[Any],
    window_days: int = 14,
) -> tuple[float, list[dict]]:
    """
    Returns (score 0-100, list of contributing event dicts with per-event contribution).
    Only events within ±window_days of proposed_date are considered.
    """
    contributions: list[dict] = []
    raw_total = 0.0

    for evt in external_events:
        try:
            evt_date = date.fromisoformat(evt.date)
        except (ValueError, AttributeError):
            continue

        delta = abs((evt_date - proposed_date).days)
        if delta > window_days:
            continue

        tw = _temporal_weight(delta)
        iw = _industry_weight(proposed_industry, evt.industry)
        aw = _audience_weight(proposed_tags, evt.audience_tags or [])
        mw = _magnitude_weight(evt.magnitude or 3)

        component = tw * iw * aw * mw
        raw_total += component

        contributions.append({
            "id": evt.id,
            "name": evt.name,
            "date": evt.date,
            "industry": evt.industry,
            "magnitude": evt.magnitude,
            "delta_days": (evt_date - proposed_date).days,
            "contribution": round(component * 20, 2),   # scaled contribution
        })

    score = min(100.0, round(raw_total * 20, 2))
    # Sort contributions descending
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    return score, contributions


def risk_level(score: float) -> str:
    if score >= 65:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def recommend_dates(
    proposed_date: date,
    proposed_industry: str,
    proposed_tags: list[str],
    external_events: list[Any],
    search_window: int = 30,
    n: int = 3,
) -> list[dict]:
    """Scan ±search_window days, return top-n lowest-risk alternatives."""
    candidates = []
    for offset in range(-search_window, search_window + 1):
        if offset == 0:
            continue
        candidate = proposed_date + timedelta(days=offset)
        # Skip weekends (optional quality filter)
        if candidate.weekday() >= 5:
            continue
        s, _ = compute_score(
            candidate, proposed_industry, proposed_tags, external_events
        )
        candidates.append({"date": candidate.isoformat(), "score": round(s, 2)})

    candidates.sort(key=lambda x: x["score"])
    return candidates[:n]
