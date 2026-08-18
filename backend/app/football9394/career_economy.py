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


PESETA_CURRENCY_CODE = "ESP"
PESETA_CURRENCY_NAME = "pesetas"
PESETA_CURRENCY_LABEL = "ptas."
ECONOMY_MODEL_9394 = "peseta-1993-v2"


def _round_period_money(value: float | int, step: int = 50_000) -> int:
    return max(0, int(round(float(value) / step) * step))


def _baseline_squad_annual_wages(players: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> int:
    return sum(inferred_annual_salary(player) for player in players)


def _baseline_squad_market_value(players: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> int:
    # Local import avoids coupling the contract module to the market at import time.
    from .career_market import estimated_transfer_value
    return sum(estimated_transfer_value(player) for player in players)


def baseline_wage_budget(
    team: dict[str, Any],
    *,
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> int:
    """Career wage ceiling in 1993-94 pesetas.

    The MDB does not contain a reliable historical wage budget.  We therefore
    derive a conservative envelope from the existing squad, rather than letting
    cash on hand become an unlimited salary budget.  The opening squad always
    fits, with roughly 12% headroom for renewals and selective recruitment.
    """
    annual_wages = _baseline_squad_annual_wages(players)
    source_budget = max(0, int(team.get("budget") or 0))
    floor = max(6_000_000, round(source_budget * 0.55))
    return _round_period_money(max(floor, annual_wages * 1.12), step=50_000)


def annual_wage_commitment(
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    development: dict[str, dict[str, Any]] | None = None,
    contract_overrides: dict[str, dict[str, Any]] | None = None,
    exclude_player_id: int | None = None,
) -> int:
    development = development or {}
    contract_overrides = contract_overrides or {}
    annual = 0
    for player in players:
        pid = int(player.get("source_id") or player.get("id") or 0)
        if exclude_player_id is not None and pid == int(exclude_player_id):
            continue
        key = str(pid)
        overall = int(development.get(key, {}).get("overall") or player.get("overall") or player.get("category") or 60)
        contract = effective_contract(player, overall=overall, override=contract_overrides.get(key))
        annual += max(0, int(contract.get("salary") or 0))
    return annual


def wage_budget_headroom(
    finances: dict[str, Any],
    *,
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    development: dict[str, dict[str, Any]] | None = None,
    contract_overrides: dict[str, dict[str, Any]] | None = None,
    exclude_player_id: int | None = None,
) -> int:
    used = annual_wage_commitment(
        players, development=development, contract_overrides=contract_overrides,
        exclude_player_id=exclude_player_id,
    )
    raw_budget = int(finances.get("wage_budget_annual") or 0)
    if raw_budget > 0:
        budget = raw_budget
    else:
        # Legacy/minimal finance states predate the explicit wage envelope.
        # Derive the same conservative opening headroom instead of interpreting
        # a missing field as a hard zero that would freeze transfers/renewals.
        budget = max(6_000_000, _round_period_money(used * 1.12, step=50_000))
    return max(0, budget - used)


def normalized_transfer_budget(
    team: dict[str, Any],
    *,
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> int:
    """Return a playable 1993-94 transfer allocation in period pesetas.

    The historical ``budget`` field is preserved as source data, but source
    conventions differ sharply by country.  It therefore acts as a floor and
    hierarchy signal rather than as the club's entire annual treasury.  A small
    squad-economics floor prevents a club with a 100M-ptas wage bill from being
    assigned only a few hundred thousand pesetas of usable market budget.
    """
    source_budget = max(0, int(team.get("budget") or 0))
    annual_wages = _baseline_squad_annual_wages(players)
    squad_value = _baseline_squad_market_value(players)
    wage_floor = _round_period_money(annual_wages * 0.10)
    value_floor = _round_period_money(squad_value * 0.025)
    return max(source_budget, 2_000_000, wage_floor, value_floor)


def initial_club_finances(
    team: dict[str, Any],
    *,
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    source_budget = max(0, int(team.get("budget") or 0))
    debt = max(0, int(team.get("debt") or 0))
    transfer_budget = normalized_transfer_budget(team, players=players)
    annual_wages = _baseline_squad_annual_wages(players)
    wage_budget = baseline_wage_budget(team, players=players)
    monthly_wages = round(annual_wages / 12) if annual_wages else 0
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt_service = round(debt * 0.004) if debt else 0
    fixed_monthly = monthly_wages + operations + debt_service
    # Opening ordinary income is anchored to the club's historical-scale squad
    # and structure.  It must NOT rise automatically when the user increases
    # wages later, otherwise overspending would finance itself.
    recurring_revenue_base = max(350_000, _round_period_money(fixed_monthly * 0.94, step=50_000))
    operating_reserve = max(500_000, _round_period_money(fixed_monthly * 2.0))
    # Treasury is not the source ``Presupuesto``.  The transfer envelope sits
    # on top of a protected operating reserve, so the whole advertised market
    # budget is genuinely spendable on day one without consuming payroll cash.
    starting_cash = transfer_budget + operating_reserve
    return {
        "economy_model": ECONOMY_MODEL_9394,
        "currency_code": PESETA_CURRENCY_CODE,
        "currency_name": PESETA_CURRENCY_NAME,
        "currency_label": PESETA_CURRENCY_LABEL,
        "source_budget": source_budget,
        "cash": starting_cash,
        "starting_cash": starting_cash,
        # Compatibility: older consumers use starting_budget as the financial
        # scale denominator.  It now means opening treasury, not source budget.
        "starting_budget": starting_cash,
        "transfer_budget_total": transfer_budget,
        "transfer_budget_remaining": transfer_budget,
        "wage_budget_annual": wage_budget,
        "opening_wage_commitment_annual": annual_wages,
        "budget_constraint_multiplier": 1.0,
        "operating_reserve_target": operating_reserve,
        "recurring_revenue_base_monthly": recurring_revenue_base,
        "debt": debt,
        "transfer_spend": 0,
        "transfer_income": 0,
        "matchday_income": 0,
        "commercial_income": 0,
        "membership_income": 0,
        "television_income": 0,
        "sponsorship_income": 0,
        "wage_expense": 0,
        "operating_expense": 0,
        "debt_service": 0,
        "debt_interest_expense": 0,
        "debt_principal_repayment": 0,
        "financing_draws": 0,
        "net_operating": 0,
    }


def merge_finances_with_peseta_baseline(
    baseline: dict[str, Any],
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    """Migrate old saves without inventing euros or erasing real career history."""
    existing = dict(existing or {})
    migrated = {**baseline, **existing}
    migrated.update({
        "economy_model": ECONOMY_MODEL_9394,
        "currency_code": PESETA_CURRENCY_CODE,
        "currency_name": PESETA_CURRENCY_NAME,
        "currency_label": PESETA_CURRENCY_LABEL,
        "source_budget": int(baseline.get("source_budget") or 0),
        "operating_reserve_target": int(baseline.get("operating_reserve_target") or 0),
    })
    if "transfer_budget_total" not in existing:
        migrated["transfer_budget_total"] = int(baseline.get("transfer_budget_total") or 0)
    if "wage_budget_annual" not in existing:
        migrated["wage_budget_annual"] = int(baseline.get("wage_budget_annual") or 0)
    migrated.setdefault("opening_wage_commitment_annual", int(baseline.get("opening_wage_commitment_annual") or 0))
    migrated.setdefault("budget_constraint_multiplier", 1.0)
    migrated.setdefault("recurring_revenue_base_monthly", int(baseline.get("recurring_revenue_base_monthly") or 350_000))
    migrated.setdefault("membership_income", 0)
    migrated.setdefault("television_income", 0)
    migrated.setdefault("sponsorship_income", 0)
    migrated.setdefault("debt_interest_expense", 0)
    migrated.setdefault("debt_principal_repayment", 0)
    migrated.setdefault("financing_draws", 0)
    if "transfer_budget_remaining" not in existing:
        opening = int(migrated.get("transfer_budget_total") or 0)
        spent = max(0, int(existing.get("transfer_spend") or 0))
        income = max(0, int(existing.get("transfer_income") or 0))
        migrated["transfer_budget_remaining"] = max(0, opening - spent + income)
    if "starting_cash" not in existing:
        migrated["starting_cash"] = int(existing.get("starting_budget") or baseline.get("starting_cash") or 0)
    # Do not refill an old career's current cash.  Only the semantic envelopes
    # are migrated; the ledger remains authoritative.
    migrated["starting_budget"] = int(migrated.get("starting_cash") or baseline.get("starting_cash") or 0)
    return migrated


def transfer_spending_power(finances: dict[str, Any]) -> int:
    cash = max(0, int(finances.get("cash") or 0))
    reserve = max(0, int(finances.get("operating_reserve_target") or 0))
    available_cash = max(0, cash - reserve)
    if "transfer_budget_remaining" not in finances:
        return available_cash
    return max(0, min(int(finances.get("transfer_budget_remaining") or 0), available_cash))


def spend_transfer_funds(finances: dict[str, Any], amount: int, *, recorded_fee: int | None = None) -> None:
    amount = max(0, int(amount))
    if amount > transfer_spending_power(finances):
        raise ValueError("el coste supera el presupuesto de fichajes utilizable")
    finances["cash"] = int(finances.get("cash") or 0) - amount
    if "transfer_budget_remaining" in finances:
        finances["transfer_budget_remaining"] = max(0, int(finances.get("transfer_budget_remaining") or 0) - amount)
    fee = amount if recorded_fee is None else max(0, int(recorded_fee))
    finances["transfer_spend"] = int(finances.get("transfer_spend") or 0) + fee


def receive_transfer_funds(finances: dict[str, Any], amount: int, *, reinvestment_rate: float = 1.0) -> None:
    amount = max(0, int(amount))
    finances["cash"] = int(finances.get("cash") or 0) + amount
    finances["transfer_income"] = int(finances.get("transfer_income") or 0) + amount
    reinvested = max(0, int(round(amount * max(0.0, min(1.0, float(reinvestment_rate))))))
    if "transfer_budget_remaining" in finances:
        finances["transfer_budget_remaining"] = int(finances.get("transfer_budget_remaining") or 0) + reinvested
        finances["transfer_budget_total"] = max(int(finances.get("transfer_budget_total") or 0), int(finances["transfer_budget_remaining"]))


def grant_transfer_budget(finances: dict[str, Any], amount: int) -> None:
    amount = max(0, int(amount))
    finances["cash"] = int(finances.get("cash") or 0) + amount
    finances["transfer_budget_total"] = int(finances.get("transfer_budget_total") or 0) + amount
    finances["transfer_budget_remaining"] = int(finances.get("transfer_budget_remaining") or 0) + amount


def board_financial_constraint_multiplier(finances: dict[str, Any]) -> float:
    """Board prudence applied to the next season's discretionary envelopes.

    Historical debt is not treated as instant insolvency, but repeated emergency
    financing and debt large relative to opening treasury reduce fresh transfer
    freedom.  Existing contracts remain payable; this is a spending brake, not
    a silent rewrite of the source budget.
    """
    starting=max(1,int(finances.get("starting_cash") or finances.get("starting_budget") or 1))
    debt=max(0,int(finances.get("debt") or 0))
    debt_ratio=debt/starting
    draws=max(0,int(finances.get("financing_draws") or 0))
    if draws>0:
        return 0.55 if debt_ratio>=1.0 else 0.70
    if debt_ratio>=1.25:
        return 0.65
    if debt_ratio>=0.80:
        return 0.80
    if debt_ratio>=0.40:
        return 0.90
    return 1.0


def refresh_season_transfer_budget(
    finances: dict[str, Any],
    *,
    team: dict[str, Any],
    players: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    current_wage_commitment: int | None = None,
) -> dict[str, Any]:
    baseline = initial_club_finances(team, players=players)
    constraint = board_financial_constraint_multiplier(finances)
    baseline_allocation = int(baseline["transfer_budget_total"])
    allocation = max(0, round(baseline_allocation * constraint))
    previous_remaining=max(0,int(finances.get("transfer_budget_remaining") or 0))
    # Healthy clubs can preserve unused authority; indebted/restructured clubs
    # can have that discretionary envelope cut by the board for the new season.
    remaining = max(previous_remaining, allocation) if constraint>=1.0 else min(previous_remaining, allocation)
    finances["transfer_budget_total"] = max(allocation, remaining)
    finances["transfer_budget_remaining"] = remaining
    baseline_wages = int(baseline.get("wage_budget_annual") or 0)
    previous_wages = max(0, int(finances.get("wage_budget_annual") or 0))
    committed=max(0,int(current_wage_commitment or baseline.get("opening_wage_commitment_annual") or 0))
    wage_constraint=max(0.90,constraint)
    target_wages=round(baseline_wages*wage_constraint)
    # Never pretend an already signed contract does not exist.  Financial stress
    # removes headroom first; it does not rewrite wages downward.
    finances["wage_budget_annual"] = max(committed,target_wages,round(previous_wages*0.96) if constraint>=1.0 else committed)
    finances["budget_constraint_multiplier"] = round(constraint,2)
    finances["operating_reserve_target"] = int(baseline["operating_reserve_target"])
    baseline_revenue=max(350_000,int(baseline.get("recurring_revenue_base_monthly") or 350_000))
    previous_revenue=max(350_000,int(finances.get("recurring_revenue_base_monthly") or baseline_revenue))
    # Commercial/TV scale can adapt between seasons to the structural quality
    # of the squad, but it never keys off negotiated salary overrides.  A 50/50
    # blend avoids both instant self-financing and decade-long stale revenue.
    finances["recurring_revenue_base_monthly"] = _round_period_money(previous_revenue*0.50 + baseline_revenue*0.50,step=50_000)
    finances["source_budget"] = int(baseline["source_budget"])
    finances["economy_model"] = ECONOMY_MODEL_9394
    finances["currency_code"] = PESETA_CURRENCY_CODE
    finances["currency_name"] = PESETA_CURRENCY_NAME
    finances["currency_label"] = PESETA_CURRENCY_LABEL
    return finances


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


def monthly_debt_breakdown(finances: dict[str, Any]) -> dict[str, int]:
    debt = max(0, int(finances.get("debt") or 0))
    if not debt:
        return {"interest": 0, "principal": 0, "total": 0}
    # Same ~0.4% monthly cash burden as H1-v1, but it is no longer a black box:
    # part is financing cost and part really reduces the outstanding principal.
    interest = max(0, round(debt * 0.0025))
    principal = min(debt, max(1, round(debt * 0.0015)))
    return {"interest": interest, "principal": principal, "total": interest + principal}


def monthly_debt_service(finances: dict[str, Any]) -> int:
    return int(monthly_debt_breakdown(finances)["total"])


def monthly_revenue_breakdown(
    team: dict[str, Any],
    *,
    fixed_costs: int = 0,
    revenue_base: int | None = None,
    stature_score: float | None = None,
    month: int = 8,
) -> dict[str, int]:
    """Estimated recurring football revenue, split into period-facing buckets.

    Exact historical accounts are unavailable for most clubs in the database, so
    these are gameplay estimates.  Socios/abonos are front-loaded around summer,
    television is comparatively restrained for the era, and sponsorship carries
    the remaining ordinary-income floor that the old model hid as `commercial`.
    """
    members = max(0, int(team.get("members") or 0))
    source_budget = max(0, int(team.get("budget") or 0))
    stature = max(30.0, min(90.0, float(stature_score if stature_score is not None else 50.0)))
    memberships_raw = round((members ** 0.5) * 3_200) if int(month) in {7, 8, 9} else 0
    television_raw = max(100_000, round((source_budget ** 0.5) * 42 * max(.72, min(1.28, stature / 60))))
    sponsorship_raw = max(150_000, round((members ** 0.5) * 2_300 + (source_budget ** 0.5) * 34 * max(.82, stature / 60)))
    raw = {"memberships": memberships_raw, "television": television_raw, "sponsorship": sponsorship_raw}
    raw_total = max(1, sum(raw.values()))
    # Recurring income is anchored independently from CURRENT expenditure.
    # Legacy callers without a stored base fall back to the old 94% opening-cost
    # estimate, but career states persist the base so wage inflation hurts.
    anchor = max(0, int(revenue_base)) if revenue_base is not None else round(max(0, int(fixed_costs)) * 0.94)
    target = max(raw_total, anchor)
    allocated = {key: round(target * value / raw_total) for key, value in raw.items()}
    allocated["sponsorship"] += target - sum(allocated.values())
    return {key: max(0, int(value)) for key, value in allocated.items()}


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
    month: int = 8,
) -> dict[str, int]:
    wages = monthly_wage_bill(players, development=development, contract_overrides=contract_overrides)
    operations = monthly_operating_expense(team, squad_size=len(players))
    debt = monthly_debt_breakdown(finances)
    debt_service = int(debt["total"])
    revenues = monthly_revenue_breakdown(
        team, fixed_costs=wages + operations + debt_service,
        revenue_base=int(finances.get("recurring_revenue_base_monthly") or 0) or None,
        stature_score=stature_score, month=int(month),
    )
    commercial = sum(revenues.values())
    net = commercial - wages - operations - debt_service
    finances["cash"] = int(finances.get("cash") or 0) + net
    if int(debt.get("principal") or 0):
        finances["debt"] = max(0, int(finances.get("debt") or 0) - int(debt["principal"]))
    finances["commercial_income"] = int(finances.get("commercial_income") or 0) + commercial
    finances["membership_income"] = int(finances.get("membership_income") or 0) + int(revenues["memberships"])
    finances["television_income"] = int(finances.get("television_income") or 0) + int(revenues["television"])
    finances["sponsorship_income"] = int(finances.get("sponsorship_income") or 0) + int(revenues["sponsorship"])
    finances["wage_expense"] = int(finances.get("wage_expense") or 0) + wages
    finances["operating_expense"] = int(finances.get("operating_expense") or 0) + operations
    finances["debt_service"] = int(finances.get("debt_service") or 0) + debt_service
    finances["debt_interest_expense"] = int(finances.get("debt_interest_expense") or 0) + int(debt["interest"])
    finances["debt_principal_repayment"] = int(finances.get("debt_principal_repayment") or 0) + int(debt["principal"])
    finances["net_operating"] = int(finances.get("net_operating") or 0) + net
    return {
        "commercial_income": commercial,
        "membership_income": int(revenues["memberships"]),
        "television_income": int(revenues["television"]),
        "sponsorship_income": int(revenues["sponsorship"]),
        "wage_expense": wages,
        "operating_expense": operations,
        "debt_service": debt_service,
        "debt_interest": int(debt["interest"]),
        "debt_principal": int(debt["principal"]),
        "net": net,
        "cash": int(finances["cash"]),
        "debt_remaining": int(finances.get("debt") or 0),
    }
