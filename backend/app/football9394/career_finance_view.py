from __future__ import annotations

from typing import Any

from .career_economy import effective_contract, monthly_commercial_income, monthly_debt_service, monthly_operating_expense, monthly_wage_bill


def economy_snapshot(*, team: dict[str, Any], finances: dict[str, Any], players: list[dict[str, Any]],
                     development: dict[str, dict[str, Any]], contract_overrides: dict[str, dict[str, Any]], ledger: list[dict[str, Any]],
                     stature_score: float | None = None) -> dict[str, Any]:
    wages = monthly_wage_bill(players, development=development, contract_overrides=contract_overrides)
    commercial = monthly_commercial_income(team, stature_score=stature_score)
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt_service = monthly_debt_service(finances)
    projected = commercial - wages - operations - debt_service
    annual_wages = wages * 12
    cash = int(finances.get("cash") or 0)
    safety_reserve = max(500_000, round((wages + operations + debt_service) * 2.0))
    transfer_room = max(0, cash - safety_reserve)
    salaries=[]
    for player in players:
        pid=str(int(player["source_id"])); overall=int(development.get(pid,{}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract=effective_contract(player, overall=overall, override=contract_overrides.get(pid))
        salaries.append({"player_id":int(pid),"name":player.get("display_name"),"salary":int(contract.get("salary") or 0),"end_year":int(contract.get("end_year") or 0),"career_inferred":bool(contract.get("career_inferred",True))})
    salaries.sort(key=lambda r:(-r["salary"],r["name"] or ""))
    return {
        "cash": cash, "debt": int(finances.get("debt") or 0), "monthly_wages": wages, "annual_wages": annual_wages,
        "monthly_commercial_income": commercial, "monthly_operating_expense": operations, "monthly_debt_service": debt_service,
        "projected_monthly_net": projected, "safety_reserve": safety_reserve, "transfer_room": transfer_room,
        "status": "Sólida" if projected >= 0 and cash >= safety_reserve else "Vigilancia" if cash > 0 else "Tensión",
        "top_salaries": salaries[:8], "recent_ledger": list(ledger)[-24:],
        "contract_data_note": "Salarios y fechas contractuales son datos generados por la carrera cuando la MDB no ofrece una fuente histórica utilizable.",
    }
