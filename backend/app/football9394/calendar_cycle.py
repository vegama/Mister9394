from __future__ import annotations

"""Season-relative calendar helpers for persistent Míster 93/94 careers.

The first campaign is anchored to the historical 1993-94 cadence already used
by the runtime. Future campaigns reuse that era format/cadence shifted by whole
season years; they are generated career dates, not claims about exact 1994-95
historical fixture dates.
"""

from datetime import date, timedelta
from typing import Any, Iterable

REFERENCE_START_YEAR = 1993


def season_start_year(state: dict[str, Any]) -> int:
    label = str(state.get("season") or "1993-94")
    try:
        return int(label.split("-", 1)[0])
    except (TypeError, ValueError):
        return REFERENCE_START_YEAR


def season_label(start_year: int) -> str:
    return f"{int(start_year):04d}-{(int(start_year) + 1) % 100:02d}"


def shift_reference_date(state: dict[str, Any], reference: date) -> date:
    delta = season_start_year(state) - REFERENCE_START_YEAR
    try:
        return reference.replace(year=reference.year + delta)
    except ValueError:
        # Defensive leap-day handling; none of the current 93-94 anchors rely on
        # it, but keeping this total makes future calendar additions safe.
        return reference.replace(month=2, day=28, year=reference.year + delta)


def generated_round_dates(state: dict[str, Any], total_rounds: int) -> tuple[date, ...]:
    """Return playable round dates for the controlled regular league.

    1993-94 keeps the already-certified weekly anchor (5 September 1993). From
    1994-95 onward, rounds are distributed across late-August -> late-May so
    formats with 34, 38, 42 or 44 rounds all close comfortably before June.
    """
    total_rounds = max(0, int(total_rounds))
    if not total_rounds:
        return ()
    start_year = season_start_year(state)
    if start_year == REFERENCE_START_YEAR:
        first = date(1993, 9, 5)
        return tuple(first + timedelta(days=7 * index) for index in range(total_rounds))
    first = date(start_year, 8, 21)
    last = date(start_year + 1, 5, 29)
    if total_rounds == 1:
        return (first,)
    span = (last - first).days
    return tuple(first + timedelta(days=round(span * index / (total_rounds - 1))) for index in range(total_rounds))


def shift_reference_dates(state: dict[str, Any], values: Iterable[date | None]) -> tuple[date | None, ...]:
    return tuple(shift_reference_date(state, value) if value is not None else None for value in values)
