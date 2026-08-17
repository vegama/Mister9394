from __future__ import annotations

"""NF9 · Complete professional career for the human manager.

This module owns the manager's *personal* professional state. Club-specific
state stays in ``ManagerCareerRuntime9394`` so changing employer never erases
world results, while reputation, contracts, applications, interviews and
relationships travel with the manager.
"""

from datetime import date, timedelta
from typing import Any


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def ensure_professional_state(state: dict[str, Any], *, team: dict[str, Any] | None = None) -> None:
    profile = state.setdefault("user_manager", {})
    profile.setdefault("reputation", 50.0)
    profile.setdefault("reputation_by_country", {})
    profile.setdefault("applications", [])
    profile.setdefault("interviews", [])
    profile.setdefault("career_offers", [])
    profile.setdefault("relationships", {})
    profile.setdefault("career_memories", [])
    profile.setdefault("active_contract", None)
    profile.setdefault("available_jobs", [])
    profile.setdefault("last_job_search_on", None)
    if team:
        league = team.get("league") or {}
        country = str(league.get("country") or "").strip()
        if country:
            profile["reputation_by_country"].setdefault(country, round(float(profile.get("reputation") or 50.0), 1))


def country_reputation(profile: dict[str, Any], country: str | None) -> float:
    base = float(profile.get("reputation") or 50.0)
    if not country:
        return base
    return float((profile.get("reputation_by_country") or {}).get(str(country), max(20.0, base - 12.0)))


def update_country_reputation(state: dict[str, Any], *, country: str | None, delta: float, date_text: str, reason: str) -> dict[str, Any] | None:
    ensure_professional_state(state)
    if not country:
        return None
    profile = state["user_manager"]
    values = profile.setdefault("reputation_by_country", {})
    before = country_reputation(profile, country)
    after = round(_clip(before + float(delta), 12.0, 95.0), 2)
    values[str(country)] = after
    row = {"date": date_text, "country": str(country), "before": round(before, 1), "after": round(after, 1), "delta": round(after-before, 2), "reason": reason}
    profile["career_memories"].append({"kind": "country_reputation", **row})
    profile["career_memories"] = profile["career_memories"][-120:]
    return row


def relationship_key(team_id: int) -> str:
    return str(int(team_id))


def manager_club_relationship(state: dict[str, Any], team_id: int) -> dict[str, Any]:
    ensure_professional_state(state)
    row = (state["user_manager"].get("relationships") or {}).get(relationship_key(team_id)) or {}
    return {
        "team_id": int(team_id),
        "trust": int(row.get("trust") or 50),
        "respect": int(row.get("respect") or 50),
        "last_reason": row.get("last_reason"),
        "last_changed_on": row.get("last_changed_on"),
    }


def adjust_club_relationship(state: dict[str, Any], *, team_id: int, trust_delta: int = 0, respect_delta: int = 0, date_text: str, reason: str) -> dict[str, Any]:
    ensure_professional_state(state)
    relationships = state["user_manager"].setdefault("relationships", {})
    key = relationship_key(team_id)
    current = manager_club_relationship(state, team_id)
    current["trust"] = int(_clip(current["trust"] + int(trust_delta)))
    current["respect"] = int(_clip(current["respect"] + int(respect_delta)))
    current["last_reason"] = reason
    current["last_changed_on"] = date_text
    relationships[key] = current
    return dict(current)


def build_manager_contract(*, team_id: int, team_name: str, league_id: int, league_name: str, date_text: str, reputation: float, club_score: float, expected_position: int) -> dict[str, Any]:
    started = date.fromisoformat(date_text)
    years = 1 if expected_position >= 15 else 2 if reputation < 68 else 3
    annual_salary = round(max(4_000_000, (club_score * 650_000 + reputation * 350_000)) / 250_000) * 250_000
    return {
        "team_id": int(team_id), "team_name": team_name, "league_id": int(league_id), "league_name": league_name,
        "started_on": date_text, "expires_on": date(started.year + years, 6, 30).isoformat(), "years": years,
        "annual_salary": int(annual_salary), "annual_salary_display": f"{int(annual_salary):,} ptas.".replace(",", "."),
        "expected_position": int(expected_position), "status": "active", "career_inferred": True,
    }


def register_contract(state: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    ensure_professional_state(state)
    state["user_manager"]["active_contract"] = dict(contract)
    return dict(contract)


def close_contract(state: dict[str, Any], *, date_text: str, reason: str) -> dict[str, Any] | None:
    ensure_professional_state(state)
    current = state["user_manager"].get("active_contract")
    if not current:
        return None
    closed = {**current, "status": "closed", "ended_on": date_text, "end_reason": reason}
    state["user_manager"]["active_contract"] = None
    state["user_manager"]["career_memories"].append({"kind": "contract_closed", **closed})
    state["user_manager"]["career_memories"] = state["user_manager"]["career_memories"][-120:]
    return closed


def prior_tenure_modifier(profile: dict[str, Any], team_id: int) -> float:
    rows = [row for row in (profile.get("tenures") or []) if int(row.get("team_id") or 0) == int(team_id)]
    if not rows:
        return 0.0
    latest = rows[-1]
    reason = str(latest.get("reason") or "")
    if reason == "resigned":
        return -7.0
    if reason == "dismissed":
        return -3.0
    return 5.0


def job_suitability(*, profile: dict[str, Any], team_id: int, country: str | None, club_score: float, pressure: int, position: int, expected_position: int, currently_employed: bool) -> float:
    global_rep = float(profile.get("reputation") or 50.0)
    local_rep = country_reputation(profile, country)
    reputation = global_rep * .58 + local_rep * .42
    fit = 100.0 - abs(float(club_score) - reputation) * 1.45
    fit += min(18.0, max(0, int(pressure)) * .18)
    fit += max(0, int(position) - int(expected_position)) * 1.6
    fit += prior_tenure_modifier(profile, team_id)
    if currently_employed:
        fit -= 8.0
    return round(fit, 2)


def application_interview(*, state: dict[str, Any], opportunity: dict[str, Any], day: date) -> dict[str, Any]:
    ensure_professional_state(state)
    profile = state["user_manager"]
    app_id = f"application:{day.isoformat()}:{int(opportunity['team_id'])}:{len(profile['applications'])}"
    suitability = float(opportunity.get("suitability") or 0.0)
    application = {
        "id": app_id, "date": day.isoformat(), "team_id": int(opportunity["team_id"]), "team_name": opportunity.get("team_name"),
        "league_id": int(opportunity["league_id"]), "league_name": opportunity.get("league_name"), "country": opportunity.get("country"),
        "status": "interview", "suitability": suitability,
    }
    profile["applications"].append(application)
    profile["applications"] = profile["applications"][-80:]
    interview_score = suitability + manager_club_relationship(state, int(opportunity["team_id"]))["respect"] * .12
    interview = {
        "id": f"interview:{app_id}", "application_id": app_id, "date": day.isoformat(), "team_id": int(opportunity["team_id"]),
        "team_name": opportunity.get("team_name"), "project_fit": round(interview_score, 1),
        "questions": [
            "¿Puedes cumplir el objetivo deportivo sin hipotecar la plantilla?",
            "¿Cómo encaja tu idea de fútbol con el proyecto del club?",
            "¿Qué necesitas del consejo para competir?",
        ],
        "status": "passed" if interview_score >= 59 else "rejected",
    }
    profile["interviews"].append(interview)
    profile["interviews"] = profile["interviews"][-80:]
    application["status"] = "offered" if interview["status"] == "passed" else "rejected"
    return {"application": dict(application), "interview": dict(interview), "passed": interview["status"] == "passed"}


def expire_job_market(state: dict[str, Any], *, day: date) -> None:
    ensure_professional_state(state)
    profile = state["user_manager"]
    for row in profile.get("career_offers") or []:
        if row.get("status") == "open" and row.get("expires_on") and date.fromisoformat(str(row["expires_on"])) < day:
            row["status"] = "expired"
    for row in profile.get("available_jobs") or []:
        if row.get("status") == "open" and row.get("expires_on") and date.fromisoformat(str(row["expires_on"])) < day:
            row["status"] = "expired"


def professional_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    ensure_professional_state(state)
    profile = state["user_manager"]
    return {
        "employment_status": "employed" if str(state.get("job_status") or "active") == "active" else "unemployed",
        "reputation": round(float(profile.get("reputation") or 50.0), 1),
        "reputation_by_country": dict(sorted((profile.get("reputation_by_country") or {}).items(), key=lambda item: (-float(item[1]), item[0]))),
        "active_contract": dict(profile.get("active_contract") or {}),
        "available_jobs": [dict(row) for row in profile.get("available_jobs") or [] if row.get("status") == "open"],
        "career_offers": [dict(row) for row in profile.get("career_offers") or [] if row.get("status") == "open"],
        "applications": [dict(row) for row in profile.get("applications") or []][-20:],
        "interviews": [dict(row) for row in profile.get("interviews") or []][-20:],
        "relationships": [dict(row) for row in (profile.get("relationships") or {}).values()],
        "career_memories": [dict(row) for row in profile.get("career_memories") or []][-30:],
        "tenures": [dict(row) for row in profile.get("tenures") or []],
        "current_tenure": dict(profile.get("current_tenure") or {}),
    }
