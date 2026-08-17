from __future__ import annotations

"""NF12 · Longitudinal football economy without an accounting mini-game."""

from typing import Any


def ensure_longitudinal_economy(state: dict[str, Any]) -> None:
    state.setdefault("economy_seasons", {})
    state.setdefault("economy_commitments", {})
    state.setdefault("economy_structural_events", [])


def season_bucket(state: dict[str, Any], *, team_id: int, season: str) -> dict[str, Any]:
    ensure_longitudinal_economy(state)
    key = f"{season}:{int(team_id)}"
    return state["economy_seasons"].setdefault(key, {
        "season": season, "team_id": int(team_id), "gate_receipts": 0, "memberships": 0, "television": 0,
        "prize_money": 0, "sponsorship": 0, "wages": 0, "bonuses": 0, "transfer_spend": 0,
        "transfer_income": 0, "operations": 0, "debt_service": 0, "board_injections": 0, "net": 0,
    })


def post(state: dict[str, Any], *, team_id: int, season: str, category: str, amount: int) -> dict[str, Any]:
    bucket = season_bucket(state, team_id=team_id, season=season)
    category = str(category)
    if category not in bucket:
        bucket[category] = 0
    bucket[category] = int(bucket.get(category) or 0) + int(amount)
    income_keys = {"gate_receipts", "memberships", "television", "prize_money", "sponsorship", "transfer_income", "board_injections"}
    expense_keys = {"wages", "bonuses", "transfer_spend", "operations", "debt_service"}
    bucket["net"] = sum(int(bucket.get(k) or 0) for k in income_keys) - sum(int(bucket.get(k) or 0) for k in expense_keys)
    return dict(bucket)


def monthly_revenue_mix(*, team: dict[str, Any], club_score: float, month: int) -> dict[str, int]:
    members = max(0, int(team.get("members") or 0))
    budget = max(0, int(team.get("budget") or 0))
    # Period-appropriate compact categories. They are career estimates where
    # source accounts are absent, not historical claims about a real club.
    memberships = round((members ** .5) * 2400) if month in {7, 8, 9} else 0
    television = max(120_000, round((budget ** .5) * 48 * max(.75, min(1.35, club_score / 60))))
    sponsorship = max(160_000, round((members ** .5) * 2600 + (budget ** .5) * 35))
    return {"memberships": int(memberships), "television": int(television), "sponsorship": int(sponsorship)}


def season_prize_money(*, position: int | None, team_count: int, club_score: float, champion: bool = False) -> int:
    if not position:
        return 0
    base = max(1_000_000, round(club_score * 220_000))
    merit = max(.20, (team_count - int(position) + 1) / max(1, team_count))
    return int(round(base * merit * (1.9 if champion else 1.0)))


def financial_health(*, cash: int, debt: int, projected_monthly_net: int, safety_reserve: int, annual_wages: int, starting_budget: int) -> dict[str, Any]:
    reserve_ratio = cash / max(1, safety_reserve)
    debt_ratio = debt / max(1, starting_budget or cash or 1)
    wage_pressure = annual_wages / max(1, starting_budget or annual_wages)
    score = 58 + min(18, (reserve_ratio - 1) * 12) - min(24, debt_ratio * 10) - (10 if projected_monthly_net < 0 else -4)
    score -= min(8, max(0, wage_pressure - 1.2) * 5)
    score = max(0, min(100, round(score)))
    label = "Sólida" if score >= 68 else "Controlada" if score >= 52 else "Vigilancia" if score >= 34 else "Crisis"
    return {"score": score, "label": label, "reserve_ratio": round(reserve_ratio, 2), "debt_ratio": round(debt_ratio, 2), "wage_pressure": round(wage_pressure, 2)}



def register_structural_event(state: dict[str, Any], *, team_id: int, season: str, date_text: str, kind: str, detail: str, from_league_id: int | None = None, to_league_id: int | None = None) -> dict[str, Any]:
    ensure_longitudinal_economy(state)
    row = {"id": f"economy-structure:{date_text}:{team_id}:{kind}:{len(state['economy_structural_events'])}", "team_id": int(team_id), "season": str(season), "date": date_text, "kind": str(kind), "detail": str(detail), "from_league_id": from_league_id, "to_league_id": to_league_id}
    state["economy_structural_events"].append(row)
    state["economy_structural_events"] = state["economy_structural_events"][-500:]
    return dict(row)

def longitudinal_snapshot(state: dict[str, Any], *, team_id: int, season: str) -> dict[str, Any]:
    current = dict(season_bucket(state, team_id=team_id, season=season))
    history = [dict(row) for key, row in (state.get("economy_seasons") or {}).items() if int(row.get("team_id") or 0) == int(team_id)]
    history.sort(key=lambda row: str(row.get("season") or ""))
    structural = [dict(row) for row in state.get("economy_structural_events") or [] if int(row.get("team_id") or 0) == int(team_id)]
    structural.sort(key=lambda row: (str(row.get("date") or ""), str(row.get("id") or "")))
    return {"current_season": current, "history": history[-12:], "structural_events": structural[-20:]}
