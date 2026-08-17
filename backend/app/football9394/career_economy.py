from __future__ import annotations

"""Career economy and contract policy for Míster 93/94.

The supplied MDB does not expose usable contract dates/salaries for the 1993
slice, so gameplay contracts are explicitly *career inferred*.  They are never
presented as historical facts.  The important contract is determinism: a save
always reconstructs the same baseline until an actual career event overrides it.
"""

from dataclasses import dataclass
from hashlib import sha256
from functools import lru_cache
from typing import Any


# Career-inferred annual wage anchors in period pesetas.  Like transfer values,
# these are not historical salary records for individual players; the upper end
# is calibrated to the order of magnitude paid to genuine 1993-94 superstars.
_SALARY_ANCHORS: tuple[tuple[int, int], ...] = (
    (40, 350_000), (45, 500_000), (50, 800_000), (55, 1_200_000),
    (60, 1_800_000), (65, 3_000_000), (70, 5_000_000), (75, 9_000_000),
    (80, 18_000_000), (85, 45_000_000), (89, 125_000_000), (90, 145_000_000),
    (95, 200_000_000), (100, 275_000_000),
)


def _salary_from_rating(rating: int) -> int:
    rating = max(1, min(100, int(rating)))
    if rating <= _SALARY_ANCHORS[0][0]:
        return _SALARY_ANCHORS[0][1]
    for (r0, v0), (r1, v1) in zip(_SALARY_ANCHORS, _SALARY_ANCHORS[1:]):
        if rating <= r1:
            ratio = (rating - r0) / max(1, r1 - r0)
            value = v0 + (v1 - v0) * ratio
            return int(round(value / 50_000.0) * 50_000)
    return _SALARY_ANCHORS[-1][1]


def inferred_annual_salary(player: dict[str, Any], *, overall: int | None = None) -> int:
    rating = int(overall or player.get("overall") or player.get("category") or 60)
    return _salary_from_rating(rating)


@lru_cache(maxsize=32768)
def _inferred_contract_baseline(source_id: int, display_name: str, birth_date: str, team_id: int, source_rating: int, reserve: bool, loan: bool, prior_years: int) -> tuple[int, int]:
    try:
        age_1993 = 1993 - int(birth_date[:4]) if len(birth_date) >= 4 else 25
    except ValueError:
        age_1993 = 25
    identity = f"{source_id}|{display_name}|{birth_date}|{team_id}"
    noise = int.from_bytes(sha256(identity.encode("utf-8")).digest()[:2], "big") % 3
    if loan:
        years = 1
    elif age_1993 >= 33:
        years = 1 + (1 if noise == 2 else 0)
    elif reserve:
        years = 1 + (1 if noise else 0)
    elif source_rating >= 80 or prior_years >= 4:
        years = 3 + (1 if noise == 2 else 0)
    else:
        years = 2 + (1 if noise == 2 else 0)
    end_year = 1993 + max(1, min(4, years))
    salary = _salary_from_rating(source_rating)
    return end_year, salary


def inferred_contract(player: dict[str, Any], *, overall: int | None = None) -> dict[str, Any]:
    # Contract dates/salary are missing from the usable 1993 player slice.  The
    # baseline is inferred once from source-era circumstances and stays fixed;
    # match development must never silently rewrite a player's wage or expiry.
    source_rating = int(player.get("overall") or player.get("category") or overall or 60)
    source_id = int(player.get("source_id") or player.get("id") or 0)
    end_year, salary = _inferred_contract_baseline(
        source_id, str(player.get("display_name") or ""), str(player.get("birth_date") or ""),
        int(player.get("team_id") or 0), source_rating, bool(player.get("initially_reserve")),
        bool(player.get("loan")), max(0, int(player.get("previous_team_years") or 0)),
    )
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


def monthly_commercial_income(team: dict[str, Any], *, stature_score: float | None = None) -> int:
    members = max(0, int(team.get("members") or 0))
    budget = max(0, int(team.get("budget") or 0))
    # Historical source scales differ a lot by country.  Linear use of either
    # field created runaway billion-peseta cash piles for a handful of clubs.
    # Square-root scaling keeps the hierarchy visible but compresses extremes.
    supporter_pull = round((members ** 0.5) * 7_000)
    institutional_pull = round((budget ** 0.5) * 150)
    base = max(350_000, supporter_pull + institutional_pull)
    if stature_score is None:
        return base
    factor = max(0.86, min(1.20, 1.0 + (float(stature_score) - 50.0) * 0.004))
    return round(base * factor)


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
    stature_score: float | None = None,
) -> dict[str, int]:
    wages = monthly_wage_bill(players, development=development, contract_overrides=contract_overrides)
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt_service = monthly_debt_service(finances)
    commercial = monthly_commercial_income(team, stature_score=stature_score)
    # Local sponsorship/ordinary football income keeps a viable club from losing
    # half its historical budget every season merely because the source did not
    # split all revenue categories.  Matchday revenue still decides whether the
    # club actually runs a surplus.
    # The historical source does not split all operating income.  With period-
    # scale wages, guarantee that omitted ordinary revenue covers most fixed
    # monthly costs; gate receipts and sporting/market decisions still decide
    # whether the club finishes in surplus.
    commercial = max(commercial, round((wages + operations + debt_service) * 0.96))
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
