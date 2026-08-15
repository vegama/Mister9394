from __future__ import annotations

"""Frozen-age player development for the experimental long career.

Ages stay anchored to 23 October 1993 for now. Ability is dynamic: minutes,
results, goals, assists, form and injuries can move a footballer up or down.
The state is intentionally small and serialisable so it can live inside a save.
"""

from dataclasses import dataclass
from random import Random
from typing import Any, Iterable

REFERENCE_SEASON = "1993-94"
MIN_OVERALL = 35
MAX_OVERALL = 95


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def initial_player_development(players: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for row in players:
        pid = str(int(row["source_id"]))
        overall = int(row.get("overall") or row.get("category") or 60)
        state[pid] = {
            "base_overall": overall,
            "overall": overall,
            "form": 70,
            "morale": 70,
            "condition": 100,
            "injury_days": 0,
            "season_minutes": 0,
            "season_appearances": 0,
            "season_goals": 0,
            "season_assists": 0,
            "development_points": 0.0,
            "frozen_age": True,
        }
    return state


def recover_one_day(state: dict[str, dict[str, Any]]) -> bool:
    """Advance recovery and report whether match availability changed.

    Condition and form live directly in the development map. Rebuilding the
    full 10k-player roster index is only necessary when an injury reaches zero.
    """
    availability_changed = False
    for row in state.values():
        previous_injury = max(0, int(row.get("injury_days") or 0))
        injury = max(0, previous_injury - 1)
        if previous_injury > 0 and injury == 0:
            availability_changed = True
        row["injury_days"] = injury
        recovery = 2 if injury == 0 else 1
        row["condition"] = int(_clamp(int(row.get("condition") or 0) + recovery, 0, 100))
        form = int(row.get("form") or 70)
        if form > 70:
            form -= 1
        elif form < 70:
            form += 1
        row["form"] = form
    return availability_changed


def apply_match_development(
    state: dict[str, dict[str, Any]],
    *,
    player_ids: Iterable[str],
    won: bool,
    drew: bool,
    goal_ids: Iterable[str] = (),
    injury_ids: Iterable[str] = (),
    seed: int = 9394,
) -> None:
    """Apply a restrained per-match development pulse.

    This is not age/potential progression. It represents confidence, match
    sharpness and performance-driven drift. Permanent overall movement only
    happens when accumulated evidence crosses a threshold.
    """
    rng = Random(seed)
    goal_set = {str(x) for x in goal_ids}
    injury_set = {str(x) for x in injury_ids}
    for pid_raw in player_ids:
        pid = str(pid_raw)
        row = state.get(pid)
        if row is None:
            continue
        row["season_appearances"] = int(row.get("season_appearances") or 0) + 1
        row["season_minutes"] = int(row.get("season_minutes") or 0) + 90
        row["condition"] = int(_clamp(int(row.get("condition") or 100) - rng.randint(7, 13), 0, 100))
        form_delta = 2 if won else 1 if drew else -2
        morale_delta = 2 if won else 0 if drew else -1
        dev = 0.13 if won else 0.05 if drew else -0.08
        if pid in goal_set:
            row["season_goals"] = int(row.get("season_goals") or 0) + 1
            form_delta += 3
            morale_delta += 2
            dev += 0.22
        if pid in injury_set:
            days = rng.randint(7, 42)
            row["injury_days"] = max(int(row.get("injury_days") or 0), days)
            row["condition"] = min(int(row["condition"]), 45)
            form_delta -= 4
            morale_delta -= 2
            dev -= 0.55
        row["form"] = int(_clamp(int(row.get("form") or 70) + form_delta, 0, 100))
        row["morale"] = int(_clamp(int(row.get("morale") or 70) + morale_delta, 0, 100))
        row["development_points"] = float(row.get("development_points") or 0.0) + dev
        _settle_overall(row)


def _settle_overall(row: dict[str, Any]) -> None:
    points = float(row.get("development_points") or 0.0)
    overall = int(row.get("overall") or 60)
    # Deliberately slow: sustained evidence, not every good match, changes CA.
    while points >= 2.5 and overall < MAX_OVERALL:
        overall += 1
        points -= 2.5
    # In the frozen-age prototype, decline represents loss of performance level
    # from a sustained bad spell or physical damage rather than ageing. It is
    # deliberately a little easier to lose one point than to gain one, so real
    # career adversity is visible within a season without creating rapid growth.
    while points <= -1.0 and overall > MIN_OVERALL:
        overall -= 1
        points += 1.0
    row["overall"] = overall
    row["development_points"] = round(points, 4)


def season_rollover(state: dict[str, dict[str, Any]]) -> None:
    """Reset seasonal counters without changing age.

    Overall/form history survives; age never advances in this design phase.
    """
    for row in state.values():
        row["season_minutes"] = 0
        row["season_appearances"] = 0
        row["season_goals"] = 0
        row["season_assists"] = 0
        row["frozen_age"] = True
