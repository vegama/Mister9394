from __future__ import annotations

"""Match form and evidence-driven development for the long career.

Ageing/retirement is applied at season rollover by ``long_career``; this module
handles match sharpness, confidence, injuries and sustained performance.
"""

from dataclasses import dataclass
from datetime import date
from random import Random
from typing import Any, Iterable

from .coaching import coaching_development_factor
from .medical import recover_medical_day, register_match_injury

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
            "training_load": 0,
            "fatigue": 0,
            "injury_risk": 12,
            "last_training_session": None,
            "injury_days": 0,
            "current_injury": None,
            "injury_history": [],
            "season_minutes": 0,
            "season_appearances": 0,
            "season_starts": 0,
            "season_goals": 0,
            "season_assists": 0,
            "season_rating_total": 0.0,
            "season_rating_count": 0,
            "season_yellows": 0,
            "season_reds": 0,
            "development_points": 0.0,
            "physical_delta": 0,
            "technical_delta": 0,
            "attribute_deltas": {},
            "attribute_points": {},
            "retired": False,
            "frozen_age": False,
        }
    return state


def recover_one_day(state: dict[str, dict[str, Any]], *, game_date: date | None = None) -> bool:
    """Advance recovery and report whether match availability changed.

    Medical incidents retain their source-backed identity until recovery.  The
    legacy ``injury_days`` field remains canonical for availability so old saves
    continue to load without migration failures.
    """
    availability_changed = False
    for row in state.values():
        previous_injury = max(0, int(row.get("injury_days") or 0))
        recover_medical_day(row, game_date=game_date)
        injury = max(0, int(row.get("injury_days") or 0))
        if previous_injury > 0 and injury == 0:
            availability_changed = True
        recovery = 2 if injury == 0 else 1
        row["condition"] = int(_clamp(int(row.get("condition") or 0) + recovery, 0, 100))
        # Daily recovery clears part of accumulated workload. Training later in
        # the day may add it back depending on the club plan.
        row["training_load"] = max(0, int(row.get("training_load") or 0) - (5 if injury == 0 else 3))
        row["fatigue"] = max(0, int(row.get("fatigue") or 0) - (4 if injury == 0 else 2))
        row.setdefault("injury_risk", 12)
        row.setdefault("last_training_session", None)
        form = int(row.get("form") or 70)
        if form > 70:
            form -= 1
        elif form < 70:
            form += 1
        row["form"] = form
    return availability_changed


def _add_attribute_evidence(row: dict[str, Any], keys: Iterable[str], amount: float) -> None:
    points = row.setdefault("attribute_points", {})
    for key in keys:
        points[key] = round(float(points.get(key) or 0.0) + float(amount), 4)


def _settle_attribute_evidence(row: dict[str, Any]) -> None:
    points = row.setdefault("attribute_points", {})
    deltas = row.setdefault("attribute_deltas", {})
    for key in list(points):
        value = float(points.get(key) or 0.0)
        delta = int(deltas.get(key) or 0)
        while value >= 1.8 and delta < 12:
            delta += 1; value -= 1.8
        while value <= -1.2 and delta > -12:
            delta -= 1; value += 1.2
        deltas[key] = delta
        points[key] = round(value, 4)


def apply_match_development(
    state: dict[str, dict[str, Any]],
    *,
    player_ids: Iterable[str],
    starter_ids: Iterable[str] = (),
    won: bool,
    drew: bool,
    goal_ids: Iterable[str] = (),
    assist_ids: Iterable[str] = (),
    injury_ids: Iterable[str] = (),
    seed: int = 9394,
    coach_profile: dict[str, Any] | None = None,
    source_players: dict[int, dict[str, Any]] | None = None,
    game_date=None,
    age_reference_date=None,
) -> None:
    """Apply a restrained per-match development pulse.

    This is not age/potential progression. It represents confidence, match
    sharpness and performance-driven drift. Permanent overall movement only
    happens when accumulated evidence crosses a threshold.
    """
    rng = Random(seed)
    goal_set = {str(x) for x in goal_ids}
    assist_set = {str(x) for x in assist_ids}
    injury_set = {str(x) for x in injury_ids}
    starter_set = {str(x) for x in starter_ids}
    for pid_raw in player_ids:
        pid = str(pid_raw)
        row = state.get(pid)
        if row is None:
            continue
        row["season_appearances"] = int(row.get("season_appearances") or 0) + 1
        if pid in starter_set:
            row["season_starts"] = int(row.get("season_starts") or 0) + 1
            minutes = 90
        else:
            minutes = 28
        row["season_minutes"] = int(row.get("season_minutes") or 0) + minutes
        row["condition"] = int(_clamp(int(row.get("condition") or 100) - rng.randint(7, 13), 0, 100))
        # Match load feeds the same persistent workload model used by training.
        match_load = 18 if pid in starter_set else 8
        row["training_load"] = max(0, min(100, int(row.get("training_load") or 0) + match_load))
        row["fatigue"] = max(0, min(100, int(row.get("fatigue") or 0) + (14 if pid in starter_set else 6)))
        form_delta = 2 if won else 1 if drew else -2
        morale_delta = 2 if won else 0 if drew else -1
        dev = 0.13 if won else 0.05 if drew else -0.08
        # Attribute development is evidence-driven and sparse. Frozen-age
        # careers can therefore evolve forever without age-based decay while
        # players remain recognisable rather than receiving uniform +1s.
        if pid in starter_set:
            _add_attribute_evidence(row, ("consistency", "work_rate"), 0.018 if won else 0.008 if drew else -0.006)
        if pid in goal_set:
            row["season_goals"] = int(row.get("season_goals") or 0) + 1
            form_delta += 3
            morale_delta += 2
            dev += 0.22
            _add_attribute_evidence(row, ("finishing", "off_ball"), 0.16)
            _add_attribute_evidence(row, ("shot_power",), 0.05)
        if pid in assist_set:
            row["season_assists"] = int(row.get("season_assists") or 0) + 1
            form_delta += 1
            dev += 0.08
            _add_attribute_evidence(row, ("vision", "short_pass"), 0.12)
            _add_attribute_evidence(row, ("technique",), 0.04)
        if pid in injury_set:
            source_player = source_players.get(int(pid)) if source_players and pid.isdigit() else None
            if source_player is not None and isinstance(game_date, date):
                injury = register_match_injury(row, source_player, seed=seed + int(pid), game_date=game_date)
                days = int(injury.get("expected_days") or 0)
            else:
                proneness = max(0, min(3, int((source_player or {}).get("injury_proneness") or 0)))
                days = rng.randint(5, 30) + proneness * rng.randint(4, 10)
                row["injury_days"] = max(int(row.get("injury_days") or 0), days)
                # Old saves/tests without a date still get a compatible generic
                # incident instead of silently losing the medical context.
                if not row.get("current_injury"):
                    row["current_injury"] = {"name": "Problemas físicos", "expected_days": days, "days": days, "provenance": "career_generated_fallback"}
            if days >= 28:
                _add_attribute_evidence(row, ("pace", "acceleration", "stamina"), -0.40)
            elif days >= 14:
                _add_attribute_evidence(row, ("stamina", "acceleration"), -0.18)
            row["condition"] = min(int(row["condition"]), 45)
            form_delta -= 4
            morale_delta -= 2
            dev -= 0.55
        if dev > 0 and coach_profile and source_players and pid.isdigit():
            source_player = source_players.get(int(pid))
            if source_player is not None:
                dev *= coaching_development_factor(coach_profile, source_player, game_date=(age_reference_date or game_date))
        row["form"] = int(_clamp(int(row.get("form") or 70) + form_delta, 0, 100))
        row["morale"] = int(_clamp(int(row.get("morale") or 70) + morale_delta, 0, 100))
        row["development_points"] = float(row.get("development_points") or 0.0) + dev
        _settle_overall(row)
        _settle_attribute_evidence(row)


def _settle_overall(row: dict[str, Any]) -> None:
    points = float(row.get("development_points") or 0.0)
    overall = int(row.get("overall") or 60)
    # Deliberately slow: sustained evidence, not every good match, changes CA.
    while points >= 2.5 and overall < MAX_OVERALL:
        overall += 1
        points -= 2.5
    # Match-form decline represents performance evidence; age-driven decline lives in long_career.
    # from a sustained bad spell or physical damage rather than ageing. It is
    # deliberately a little easier to lose one point than to gain one, so real
    # career adversity is visible within a season without creating rapid growth.
    while points <= -1.0 and overall > MIN_OVERALL:
        overall -= 1
        points += 1.0
    row["overall"] = overall
    row["development_points"] = round(points, 4)


def season_rollover(state: dict[str, dict[str, Any]]) -> None:
    """Reset seasonal counters while preserving long-term ability state."""
    for row in state.values():
        row["season_minutes"] = 0
        row["season_appearances"] = 0
        row["season_starts"] = 0
        row["season_goals"] = 0
        row["season_assists"] = 0
        row["season_rating_total"] = 0.0
        row["season_rating_count"] = 0
        row["season_yellows"] = 0
        row["season_reds"] = 0
        row.setdefault("attribute_deltas", {})
        row.setdefault("attribute_points", {})
