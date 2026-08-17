from __future__ import annotations

"""AI coach employment market for long careers.

Manager assignments are already part of the save and already drive AI tactics.
This module gives that state a life cycle: pressure, dismissals and replacement
selection.  Source coaches are used, but the pool is filtered conservatively so
modern-era names are not freely injected into 1993 simply because the mixed-
edition MDB happens to contain them.
"""

from datetime import date, datetime
from random import Random
from typing import Any, Iterable

from .coaching import tactics_from_source_manager
from .player_identity import tactical_fit
from .source_catalog_runtime import HistoricalSourceCatalog9394, default_source_catalog


def _birth_age(manager: dict[str, Any], when: date) -> int | None:
    raw = manager.get("birth_date")
    if not isinstance(raw, str) or len(raw) < 10:
        return None
    try:
        born = datetime.fromisoformat(raw).date()
    except (TypeError, ValueError):
        return None
    return when.year - born.year - ((when.month, when.day) < (born.month, born.day))


def ensure_manager_market_state(state: dict[str, Any]) -> None:
    state.setdefault("manager_history", [])
    state.setdefault("manager_unemployed", [])
    state.setdefault("manager_pressure", {})
    state.setdefault("manager_last_change", {})


def pressure_score(*, position: int, expected_position: int, team_count: int, played: int, recent_points: int = 5) -> int:
    if played < 8:
        return 0
    gap = int(position) - int(expected_position)
    score = max(0, gap) * 9
    if position >= max(1, team_count - 2) and expected_position <= max(5, team_count // 2):
        score += 24
    if recent_points <= 2:
        score += 22
    elif recent_points <= 4:
        score += 10
    elif recent_points >= 10:
        score -= 12
    return max(0, min(100, score))


def _candidate_pool(
    state: dict[str, Any], *, when: date, catalog: HistoricalSourceCatalog9394,
    assigned_ids: set[int], target_quality: int,
) -> list[dict[str, Any]]:
    explicit = {int(x) for x in state.get("manager_unemployed") or [] if str(x).isdigit()}
    rows = []
    for manager in catalog.payload.get("managers", []):
        mid = manager.get("source_id")
        if not isinstance(mid, int) or mid <= 1 or mid in assigned_ids:
            continue
        name = str(manager.get("display_name") or "")
        if not name or "VACIO" in name.upper():
            continue
        age = _birth_age(manager, when)
        # Explicitly unemployed managers already lived in this career. For new
        # source entrants we require a mature coaching age to reduce obvious
        # anachronisms from the mixed-edition source database.
        if mid not in explicit and (age is None or age < 40):
            continue
        quality = int(manager.get("coaching_quality") or manager.get("reputation_category") or 55)
        if abs(quality - target_quality) > 32 and mid not in explicit:
            continue
        rows.append(manager)
    rows.sort(key=lambda m: (0 if int(m.get("source_id") or 0) in explicit else 1, abs(int(m.get("coaching_quality") or m.get("reputation_category") or 55) - target_quality), -int(m.get("coaching_quality") or 0), int(m.get("source_id") or 0)))
    return rows[:120]


def choose_replacement(
    state: dict[str, Any], *, when: date, team_id: int, squad: list[dict[str, Any]],
    club_score: float, seed: int, catalog: HistoricalSourceCatalog9394 | None = None,
) -> dict[str, Any] | None:
    ensure_manager_market_state(state)
    catalog = catalog or default_source_catalog()
    assigned = {int(x) for x in (state.get("manager_assignments") or {}).values() if isinstance(x, int)}
    target_quality = max(45, min(94, round(46 + float(club_score) * .48)))
    candidates = _candidate_pool(state, when=when, catalog=catalog, assigned_ids=assigned, target_quality=target_quality)
    if not candidates:
        return None
    rng = Random(int(seed) ^ int(team_id) * 131 ^ when.toordinal())
    core = sorted(squad, key=lambda p: -int(p.get("overall") or p.get("category") or 60))[:16]
    scored = []
    for manager in candidates:
        quality = int(manager.get("coaching_quality") or manager.get("reputation_category") or 55)
        plan = tactics_from_source_manager(catalog.manager_with_tactics(int(manager["source_id"])))
        fits = [float(tactical_fit(player, plan)["score"]) for player in core]
        fit = sum(fits) / len(fits) if fits else 55.0
        youth = str(manager.get("youth_usage") or "normal")
        youth_bonus = 2.5 if youth == "high" and any(int(p.get("age") or 99) <= 22 for p in core) else 0.0
        score = quality * .56 + fit * .34 + youth_bonus + rng.random() * 4.0 - abs(quality - target_quality) * .12
        scored.append((score, manager))
    scored.sort(key=lambda x: (-x[0], int(x[1]["source_id"])))
    return catalog.manager_with_tactics(int(scored[0][1]["source_id"]))


def register_manager_change(
    state: dict[str, Any], *, when: date, team_id: int, old_manager_id: int | None,
    new_manager_id: int, reason: str, pressure: int,
) -> dict[str, Any]:
    ensure_manager_market_state(state)
    assignments = state.setdefault("manager_assignments", {})
    assignments[str(int(team_id))] = int(new_manager_id)
    unemployed = {int(x) for x in state.get("manager_unemployed") or [] if str(x).isdigit()}
    if isinstance(old_manager_id, int) and old_manager_id > 1:
        unemployed.add(old_manager_id)
    unemployed.discard(int(new_manager_id))
    state["manager_unemployed"] = sorted(unemployed)
    state["manager_last_change"][str(int(team_id))] = when.isoformat()
    event = {
        "kind": "manager_change", "date": when.isoformat(), "team_id": int(team_id),
        "from_manager_id": old_manager_id, "to_manager_id": int(new_manager_id),
        "reason": reason, "pressure": int(pressure),
        "provenance": "career_generated_from_mdb_manager_pool",
    }
    state["manager_history"].append(event)
    state["manager_history"] = state["manager_history"][-300:]
    return event
