from __future__ import annotations

"""The human manager as a persistent actor in the football world.

The game historically treated a board dismissal as game over.  From v0.11 the
manager owns a career that survives clubs.  The first safe mobility step keeps
mid-season offers inside the same league so existing results/calendar remain
authoritative instead of being rebuilt when the user changes employer.
"""

from typing import Any


def ensure_user_manager_state(state: dict[str, Any]) -> None:
    team_id = int(state.get("team_id") or 0)
    current_date = str(state.get("current_date") or "1993-07-01")
    profile = state.setdefault("user_manager", {})
    profile.setdefault("reputation", 50.0)
    profile.setdefault("job_offers", [])
    profile.setdefault("tenures", [])
    profile.setdefault("current_tenure", {"team_id": team_id, "started_on": current_date})
    profile.setdefault("last_reputation_change", None)


def manager_profile_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    ensure_user_manager_state(state)
    profile = state["user_manager"]
    return {
        "reputation": round(float(profile.get("reputation") or 50.0), 1),
        "job_offers": [dict(row) for row in profile.get("job_offers") or [] if row.get("status") == "open"],
        "tenures": [dict(row) for row in profile.get("tenures") or []],
        "current_tenure": dict(profile.get("current_tenure") or {}),
        "last_reputation_change": profile.get("last_reputation_change"),
    }


def update_reputation_after_match(
    state: dict[str, Any], *, date_text: str, won: bool, drew: bool,
    own_strength: float, opponent_strength: float, rivalry_heat: int = 0,
) -> dict[str, Any]:
    ensure_user_manager_state(state)
    profile = state["user_manager"]
    before = float(profile.get("reputation") or 50.0)
    difficulty = max(-1.5, min(1.5, (float(opponent_strength) - float(own_strength)) / 12.0))
    if won:
        delta = 0.65 + max(0.0, difficulty) * 0.35 + (0.15 if int(rivalry_heat) >= 60 else 0.0)
    elif drew:
        delta = 0.12 + difficulty * 0.16
    else:
        delta = -0.38 + min(0.0, difficulty) * 0.12
    after = max(20.0, min(92.0, before + delta))
    profile["reputation"] = round(after, 2)
    profile["last_reputation_change"] = {
        "date": date_text, "before": round(before, 1), "after": round(after, 1), "delta": round(after-before, 2),
    }
    return dict(profile["last_reputation_change"])


def close_current_tenure(
    state: dict[str, Any], *, date_text: str, team_name: str, reason: str,
    record_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_user_manager_state(state)
    profile = state["user_manager"]
    current = dict(profile.get("current_tenure") or {"team_id": int(state.get("team_id") or 0), "started_on": date_text})
    if current.get("ended_on"):
        return current
    current.update({"team_name": team_name, "ended_on": date_text, "reason": reason})
    if record_snapshot:
        current["career_record_at_exit"] = dict(record_snapshot)
    profile.setdefault("tenures", []).append(current)
    profile["tenures"] = profile["tenures"][-30:]
    profile["current_tenure"] = {}
    return current


def open_new_tenure(state: dict[str, Any], *, date_text: str, team_id: int, team_name: str) -> dict[str, Any]:
    ensure_user_manager_state(state)
    row = {"team_id": int(team_id), "team_name": team_name, "started_on": date_text}
    state["user_manager"]["current_tenure"] = row
    return dict(row)


def set_job_offers(state: dict[str, Any], offers: list[dict[str, Any]]) -> None:
    ensure_user_manager_state(state)
    state["user_manager"]["job_offers"] = [dict(row) for row in offers]


def accept_offer(state: dict[str, Any], offer_id: str) -> dict[str, Any]:
    ensure_user_manager_state(state)
    offers = state["user_manager"].get("job_offers") or []
    target = next((row for row in offers if str(row.get("id")) == str(offer_id) and row.get("status") == "open"), None)
    if target is None:
        raise KeyError("oferta de trabajo no encontrada o ya cerrada")
    for row in offers:
        row["status"] = "accepted" if row is target else "declined"
    return dict(target)
