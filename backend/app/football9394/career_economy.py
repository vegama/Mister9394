from __future__ import annotations

"""Career economy and contract policy for Míster 93/94.

The supplied MDB does not expose usable contract dates/salaries for the 1993
slice, so gameplay contracts are explicitly *career inferred*.  They are never
presented as historical facts.  The important contract is determinism: a save
always reconstructs the same baseline until an actual career event overrides it.
"""

from dataclasses import dataclass
from typing import Any


def inferred_annual_salary(player: dict[str, Any], *, overall: int | None = None) -> int:
    rating = int(overall or player.get("overall") or player.get("category") or 60)
    # Source budgets are denominated in pesetas but heterogeneous.  This curve
    # keeps a normal first-team wage bill in the same order of magnitude as the
    # club budgets without claiming historical salary accuracy.
    return max(240_000, (max(8, rating - 44) ** 2) * 2_200)


def inferred_contract(player: dict[str, Any], *, overall: int | None = None) -> dict[str, Any]:
    pid = int(player.get("source_id") or player.get("id") or 0)
    end_year = 1994 + (pid % 4)  # 1994..1997, stable and evenly distributed.
    salary = inferred_annual_salary(player, overall=overall)
    return {
        "start": "1993",
        "end": str(end_year),
        "end_year": end_year,
        "salary": salary,
        "salary_display": f"{salary:,} ptas.".replace(",", "."),
        "loan": bool(player.get("loan")),
        "career_inferred": True,
        "historical_contract_data_available": False,
    }


def effective_contract(
    player: dict[str, Any],
    *,
    overall: int | None = None,
    override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = inferred_contract(player, overall=overall)
    if override:
        base.update(override)
        base["career_inferred"] = bool(override.get("career_inferred", True))
    if "end_year" not in base:
        try:
            base["end_year"] = int(str(base.get("end") or "0")[:4])
        except ValueError:
            base["end_year"] = 0
    return base


def initial_club_finances(team: dict[str, Any]) -> dict[str, int]:
    budget = int(team.get("budget") or 0)
    debt = int(team.get("debt") or 0)
    return {
        "cash": budget,
        "starting_budget": budget,
        "debt": debt,
        "transfer_spend": 0,
        "transfer_income": 0,
        "matchday_income": 0,
        "commercial_income": 0,
        "wage_expense": 0,
        "operating_expense": 0,
        "debt_service": 0,
        "net_operating": 0,
    }


def monthly_commercial_income(team: dict[str, Any]) -> int:
    members = int(team.get("members") or 0)
    budget = int(team.get("budget") or 0)
    return max(120_000, members * 115 + round(budget * 0.006))


def monthly_operating_expense(team: dict[str, Any], *, squad_size: int) -> int:
    budget = int(team.get("budget") or 0)
    members = int(team.get("members") or 0)
    # Training ground, travel, staff and stadium operations.  The curve is kept
    # deliberately compact because the fun loop should be transfer/football led.
    return max(110_000, round(budget * 0.0045) + squad_size * 18_000 + members * 6)


def monthly_debt_service(finances: dict[str, Any]) -> int:
    debt = max(0, int(finances.get("debt") or 0))
    return round(debt * 0.004) if debt else 0


def monthly_wage_bill(
    players: list[dict[str, Any]],
    *,
    development: dict[str, dict[str, Any]],
    contract_overrides: dict[str, dict[str, Any]],
) -> int:
    annual = 0
    for player in players:
        pid = str(int(player["source_id"]))
        overall = int(development.get(pid, {}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract = effective_contract(player, overall=overall, override=contract_overrides.get(pid))
        annual += int(contract.get("salary") or 0)
    return round(annual / 12)


def apply_monthly_club_finances(
    *,
    team: dict[str, Any],
    finances: dict[str, Any],
    players: list[dict[str, Any]],
    development: dict[str, dict[str, Any]],
    contract_overrides: dict[str, dict[str, Any]],
) -> dict[str, int]:
    commercial = monthly_commercial_income(team)
    wages = monthly_wage_bill(players, development=development, contract_overrides=contract_overrides)
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt_service = monthly_debt_service(finances)
    net = commercial - wages - operations - debt_service
    finances["cash"] = int(finances.get("cash") or 0) + net
    finances["commercial_income"] = int(finances.get("commercial_income") or 0) + commercial
    finances["wage_expense"] = int(finances.get("wage_expense") or 0) + wages
    finances["operating_expense"] = int(finances.get("operating_expense") or 0) + operations
    finances["debt_service"] = int(finances.get("debt_service") or 0) + debt_service
    finances["net_operating"] = int(finances.get("net_operating") or 0) + net
    return {
        "commercial_income": commercial,
        "wage_expense": wages,
        "operating_expense": operations,
        "debt_service": debt_service,
        "net": net,
        "cash": int(finances["cash"]),
    }
