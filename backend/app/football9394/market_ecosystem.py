from __future__ import annotations

"""P7 · market planning, player preferences and agent pressure.

The transfer engine already executes deals.  This layer gives those deals a
memory and an explanation: clubs carry recruitment plans across monthly pulses,
players evaluate destinations through sporting/financial/contextual motives and
sales can trigger replacement chains instead of being isolated events.
"""

from datetime import date
from typing import Any

from .career_economy import transfer_spending_power

from .career_ai import squad_audit
from .career_economy import effective_contract
from .player_identity import tactical_fit
from .coaching import tactics_from_source_manager
from .position_roles import role_for_player


def ensure_market_ecosystem_state(state: dict[str, Any]) -> None:
    state.setdefault("recruitment_plans", {})
    state.setdefault("market_storylines", [])
    state.setdefault("agent_pressure", {})


def player_market_preferences(
    player: dict[str, Any], *, overall: int, current_club_score: float, target_club_score: float,
    coach_profile: dict[str, Any] | None = None, wants_move: bool = False,
    current_salary: int = 0, offered_salary: int = 0, role_shortage: int = 0,
) -> dict[str, Any]:
    """Return a transparent destination preference model, never a rating bonus."""
    plan = tactics_from_source_manager(coach_profile) if coach_profile else None
    fit = float(tactical_fit(player, plan)["score"]) if plan is not None else 60.0
    ambition = max(0.0, min(100.0, 48.0 + (int(overall) - 65) * 1.55))
    sporting = (float(target_club_score) - float(current_club_score)) * .72 + (fit - 60.0) * .34 + int(role_shortage) * 5.0
    wage_gain = 0.0
    if offered_salary > 0:
        wage_gain = ((offered_salary / max(1, current_salary or offered_salary)) - 1.0) * 42.0
    inertia = -7.0 if not wants_move else 10.0
    openness = max(0.0, min(100.0, 50.0 + sporting + wage_gain + inertia - max(0.0, ambition - target_club_score) * .12))
    reasons=[]
    if wants_move: reasons.append("quiere cambiar de club")
    if target_club_score >= current_club_score + 8: reasons.append("salto deportivo")
    if fit >= 72: reasons.append("buen encaje con el entrenador")
    if role_shortage > 0: reasons.append("ve un camino claro hacia minutos")
    if offered_salary > current_salary * 1.15 and current_salary > 0: reasons.append("mejora salarial")
    if openness < 40: reasons.append("prefiere su situación actual")
    return {"openness": round(openness,1), "coach_fit": round(fit,1), "ambition": round(ambition,1), "reasons": reasons}


def recruitment_plan(
    *, team_id: int, players: list[dict[str, Any]], development: dict[str, dict[str, Any]],
    contracts: dict[str, dict[str, Any]], cash: int, current_date: date,
    coach_profile: dict[str, Any] | None = None, replacement_for: int | None = None,
    audit: dict[str, Any] | None = None,
    penalty_cache: dict[tuple[int, str], int] | None = None,
) -> dict[str, Any]:
    audit=audit if audit is not None else squad_audit(players,development,penalty_cache=penalty_cache)
    needs=[dict(row) for row in audit.get("needs") or [] if int(row.get("shortage") or 0)>0]
    primary=str(audit.get("primary_need") or "DEPTH")
    if replacement_for is not None:
        sold=next((p for p in players if int(p.get("source_id") or 0)==int(replacement_for)),None)
        if sold is not None: primary=role_for_player(sold).squad_slot
    expiring=[]
    season_end=current_date.year if current_date.month<=6 else current_date.year+1
    for p in players:
        pid=str(int(p["source_id"]));overall=int(development.get(pid,{}).get("overall") or p.get("overall") or p.get("category") or 60)
        contract=effective_contract(p,overall=overall,override=contracts.get(pid))
        if int(contract.get("end_year") or 9999)<=season_end+1: expiring.append(int(pid))
    urgency=min(100, 24 + int(audit.get("depth_shortage") or 0)*18 + sum(int(n.get("shortage") or 0) for n in needs)*14 + (18 if replacement_for else 0))
    return {
        "team_id":int(team_id), "updated_on":current_date.isoformat(), "primary_need":primary,
        "needs":needs, "squad_size":len(players), "cash":int(cash), "urgency":urgency,
        "expiring_player_ids":expiring[:10], "replacement_for_player_id":replacement_for,
        "coach_id":int(coach_profile["source_id"]) if coach_profile and isinstance(coach_profile.get("source_id"),int) else None,
        "status":"active", "planning_horizon_months":6,
        "contract_risk_count":len(expiring), "replacement_chain_ready":True,
    }


def refresh_recruitment_plans(
    state: dict[str, Any], *, current_date: date, team_ids: list[int], players_by_team: dict[int,list[dict[str,Any]]],
    development: dict[str,dict[str,Any]], contracts: dict[str,dict[str,Any]], club_finances: dict[str,dict[str,Any]],
    coach_profile_getter=None,
    audit_cache: dict[int, dict[str, Any]] | None = None,
    penalty_cache: dict[tuple[int, str], int] | None = None,
) -> dict[str, dict[str, Any]]:
    ensure_market_ecosystem_state(state)
    plans=state["recruitment_plans"]
    audit_cache = audit_cache if audit_cache is not None else {}
    penalty_cache = penalty_cache if penalty_cache is not None else {}
    for tid in team_ids:
        team_id=int(tid)
        coach=coach_profile_getter(team_id) if coach_profile_getter else None
        audit=audit_cache.get(team_id)
        if audit is None:
            audit=squad_audit(players_by_team.get(team_id,[]),development,penalty_cache=penalty_cache)
            audit_cache[team_id]=audit
        plans[str(tid)]=recruitment_plan(
            team_id=team_id,players=players_by_team.get(team_id,[]),development=development,contracts=contracts,
            cash=transfer_spending_power(club_finances.get(str(tid)) or {}),current_date=current_date,coach_profile=coach,
            audit=audit,penalty_cache=penalty_cache,
        )
    return plans


def register_replacement_chain(state: dict[str, Any], *, day: date, first_deals: list[dict[str,Any]], follow_up_deals: list[dict[str,Any]]) -> list[dict[str,Any]]:
    """Annotate a same-pulse purchase made by a club that has just sold."""
    ensure_market_ecosystem_state(state)
    sold_by={int(d["from_team_id"]):int(d["player_id"]) for d in first_deals if int(d.get("from_team_id") or 0)>0}
    chains=[]
    for deal in follow_up_deals:
        buyer=int(deal.get("to_team_id") or 0)
        if buyer not in sold_by: continue
        deal["replacement_chain_for_player_id"]=sold_by[buyer]
        story={"kind":"replacement_chain","date":day.isoformat(),"team_id":buyer,"sold_player_id":sold_by[buyer],"signed_player_id":int(deal["player_id"]),"fee":int(deal.get("fee") or 0)}
        state["market_storylines"].append(story);chains.append(story)
    state["market_storylines"]=state["market_storylines"][-200:]
    return chains


def agent_pressure_for_player(
    state: dict[str, Any], *, player_id: int, current_year: int, contract_end_year: int,
    satisfaction: int = 70, wants_move: bool = False, rival_interest: bool = False,
) -> dict[str, Any]:
    """Represent an agent's leverage without inventing a named historical agent.

    The pressure comes from contract horizon, player satisfaction and market
    competition.  It changes negotiation demands, never player ability.
    """
    ensure_market_ecosystem_state(state)
    years_left=max(0,int(contract_end_year)-int(current_year))
    pressure=26.0
    reasons=[]
    if years_left<=1:
        pressure+=24;reasons.append("contrato próximo a expirar")
    elif years_left>=4:
        pressure-=8
    if int(satisfaction)<50:
        pressure+=15;reasons.append("el jugador está descontento")
    if wants_move:
        pressure-=10;reasons.append("el jugador prioriza salir")
    if rival_interest:
        pressure+=22;reasons.append("hay competencia por el jugador")
    pressure=max(0.0,min(100.0,pressure))
    wage_multiplier=round(0.96+pressure/500.0,3)
    level="alta" if pressure>=65 else "media" if pressure>=40 else "baja"
    row={"player_id":int(player_id),"pressure":round(pressure,1),"level":level,"wage_multiplier":wage_multiplier,"reasons":reasons}
    state["agent_pressure"][str(int(player_id))]=row
    return row
