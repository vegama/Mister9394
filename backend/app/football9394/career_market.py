from __future__ import annotations

"""Compact but real transfer/contract economy for the playable 93/94 career."""

from dataclasses import dataclass
from typing import Any


def estimated_transfer_value(player: dict[str, Any], *, overall: int | None = None) -> int:
    rating = int(overall or player.get("overall") or player.get("category") or 60)
    # Career-internal peseta scale calibrated to source club budgets. This is a
    # gameplay estimate, not presented as a historical market-value fact.
    return max(250_000, (max(1, rating - 42) ** 2) * 20_000)


def initial_finances(team: dict[str, Any]) -> dict[str, int]:
    budget = int(team.get("budget") or 0)
    debt = int(team.get("debt") or 0)
    return {"cash": budget, "starting_budget": budget, "debt": debt, "transfer_spend": 0, "transfer_income": 0, "matchday_income": 0}


def matchday_income(team: dict[str, Any]) -> int:
    members = int(team.get("members") or 0)
    # Conservative operating pulse because MDB monetary scales are heterogeneous.
    return max(100_000, members * 85)


def negotiate_transfer(
    *, player: dict[str, Any], current_overall: int, buyer_cash: int,
    fee_offer: int, salary_offer: int, contract_years: int,
) -> dict[str, Any]:
    value = estimated_transfer_value(player, overall=current_overall)
    minimum = round(value * (0.88 if player.get("contract", {}).get("end") else 0.72))
    accepted = fee_offer >= minimum and fee_offer <= buyer_cash and contract_years >= 1 and salary_offer >= 0
    if accepted:
        return {"accepted": True, "fee": int(fee_offer), "salary": int(salary_offer), "contract_years": int(contract_years), "estimated_value": value, "minimum": minimum}
    counter = min(max(minimum, fee_offer), max(minimum, value))
    reason = "presupuesto_insuficiente" if fee_offer > buyer_cash else "oferta_insuficiente" if fee_offer < minimum else "contrato_invalido"
    return {"accepted": False, "counter_fee": int(counter), "estimated_value": value, "minimum": minimum, "reason": reason}
