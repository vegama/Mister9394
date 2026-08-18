from __future__ import annotations

from typing import Any

from .career_economy import (
    PESETA_CURRENCY_CODE,
    PESETA_CURRENCY_LABEL,
    PESETA_CURRENCY_NAME,
    annual_wage_commitment,
    effective_contract,
    monthly_debt_breakdown,
    monthly_operating_expense,
    monthly_revenue_breakdown,
    monthly_wage_bill,
    transfer_spending_power,
)


def economy_snapshot(*, team: dict[str, Any], finances: dict[str, Any], players: list[dict[str, Any]],
                     development: dict[str, dict[str, Any]], contract_overrides: dict[str, dict[str, Any]], ledger: list[dict[str, Any]],
                     stature_score: float | None = None, accounting_month: int = 8) -> dict[str, Any]:
    wages = monthly_wage_bill(players, development=development, contract_overrides=contract_overrides)
    annual_wages = annual_wage_commitment(players, development=development, contract_overrides=contract_overrides)
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt = monthly_debt_breakdown(finances)
    debt_service = int(debt["total"])
    revenue = monthly_revenue_breakdown(
        team, fixed_costs=wages + operations + debt_service,
        revenue_base=int(finances.get("recurring_revenue_base_monthly") or 0) or None,
        stature_score=stature_score, month=accounting_month,
    )
    commercial = sum(revenue.values())
    projected = commercial - wages - operations - debt_service
    cash = int(finances.get("cash") or 0)
    calculated_reserve = max(500_000, round((wages + operations + debt_service) * 2.0))
    safety_reserve = max(calculated_reserve, int(finances.get("operating_reserve_target") or 0))
    # Keep the stored reserve synchronized with the current squad/debt burden.
    finances["operating_reserve_target"] = safety_reserve
    transfer_room = transfer_spending_power(finances)
    wage_budget = max(0, int(finances.get("wage_budget_annual") or annual_wages))
    wage_room = max(0, wage_budget - annual_wages)
    salaries=[]
    for player in players:
        pid=str(int(player["source_id"])); overall=int(development.get(pid,{}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract=effective_contract(player, overall=overall, override=contract_overrides.get(pid))
        salaries.append({"player_id":int(pid),"name":player.get("display_name"),"salary":int(contract.get("salary") or 0),"end_year":int(contract.get("end_year") or 0),"career_inferred":bool(contract.get("career_inferred",True))})
    salaries.sort(key=lambda r:(-r["salary"],r["name"] or ""))
    return {
        "currency": {"code": PESETA_CURRENCY_CODE, "name": PESETA_CURRENCY_NAME, "label": PESETA_CURRENCY_LABEL},
        "cash": cash, "debt": int(finances.get("debt") or 0), "monthly_wages": wages, "annual_wages": annual_wages,
        "wage_budget_annual": wage_budget, "wage_room_annual": wage_room,
        "wage_budget_usage_pct": round((annual_wages / max(1, wage_budget)) * 100, 1),
        "source_budget": int(finances.get("source_budget") or team.get("budget") or 0),
        "transfer_budget_total": int(finances.get("transfer_budget_total") or 0),
        "transfer_budget_remaining": int(finances.get("transfer_budget_remaining") or 0),
        "monthly_commercial_income": commercial,
        "monthly_membership_income": int(revenue["memberships"]),
        "monthly_television_income": int(revenue["television"]),
        "monthly_sponsorship_income": int(revenue["sponsorship"]),
        "monthly_operating_expense": operations, "monthly_debt_service": debt_service,
        "monthly_debt_interest": int(debt["interest"]), "monthly_debt_principal": int(debt["principal"]),
        "projected_monthly_net": projected, "safety_reserve": safety_reserve, "transfer_room": transfer_room,
        "status": "Sólida" if projected >= 0 and cash >= safety_reserve else "Vigilancia" if cash > 0 else "Tensión",
        "top_salaries": salaries[:8], "recent_ledger": list(ledger)[-24:],
        "contract_data_note": "Salarios, presupuestos salariales y fechas contractuales son estimaciones de carrera en pesetas cuando la MDB no ofrece una fuente histórica utilizable; la cifra fuente del club se conserva por separado.",
    }
