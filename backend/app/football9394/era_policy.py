from __future__ import annotations

"""P8 · immutable 1993-94 regulatory contract for alternate-history careers."""

from datetime import date
from typing import Any

from .laws import LAWS_1993_94
from .registry import default_registry_9394, UnresolvedHistoricalRulesError
from .transfer_periods import transfer_period_status
from .foreign_rules import competition_foreign_rule

RULES_POLICY_FROZEN_9394 = "frozen_1993_94"


def enforce_frozen_rules_policy(state: dict[str, Any]) -> None:
    # Save data is not allowed to opt into a later historical ruleset.  This is
    # a product rule, not a migration preference.
    state["rules_policy"] = RULES_POLICY_FROZEN_9394
    state.setdefault("regulatory_epoch", "1993-94")
    state["regulatory_epoch"] = "1993-94"


def regulatory_integrity_report(universe: Any, *, season: str = "1993-94", sample_years: tuple[int, ...] = (1993, 2003, 2023)) -> dict[str, Any]:
    registry=default_registry_9394()
    issues=[];samples=[]
    if LAWS_1993_94.max_used_substitutes != 2 or LAWS_1993_94.max_named_substitutes != 5:
        issues.append("ley de sustituciones fuera del contrato 1993-94")
    if LAWS_1993_94.halftime_max_minutes != 5:
        issues.append("descanso fuera del contrato 1993-94")
    for league in universe.payload.get("leagues", []):
        lid=int(league["source_id"])
        try:
            rules=registry.resolve_source("league",lid)
        except UnresolvedHistoricalRulesError:
            # Special runtimes can be historically explicit without using the
            # simple registry.  They are covered by their dedicated gates.
            continue
        samples.append({"league_id":lid,"points_win":rules.points_win,"points_draw":rules.points_draw,"points_loss":rules.points_loss})
    # Same calendar phase must return the same era semantics regardless of how
    # far the alternate history has advanced.
    countries=sorted({int(row.get("country_id")) for row in universe.payload.get("leagues",[]) if isinstance(row.get("country_id"),int)})
    for country in countries[:20]:
        baseline=transfer_period_status(date(sample_years[0],2,15),country_id=country,season=f"{sample_years[0]}-{str(sample_years[0]+1)[-2:]}")
        for year in sample_years[1:]:
            probe=transfer_period_status(date(year,2,15),country_id=country,season=f"{year}-{str(year+1)[-2:]}")
            if (baseline.open,baseline.phase,baseline.registration_kind)!=(probe.open,probe.phase,probe.registration_kind):
                issues.append(f"deriva de mercado en país {country} para {year}")
    foreign_samples=[]
    for league in universe.payload.get("leagues",[])[:80]:
        lid=int(league["source_id"])
        rule=competition_foreign_rule(universe,kind="league",source_id=lid)
        foreign_samples.append({"league_id":lid,"max_starting":rule.max_starting,"max_squad":rule.max_squad,"home_country_id":rule.home_country_id})
    return {
        "policy":RULES_POLICY_FROZEN_9394,"epoch":"1993-94","passed":not issues,"issues":issues,
        "laws":{"players":LAWS_1993_94.players_per_team,"named_substitutes":LAWS_1993_94.max_named_substitutes,"used_substitutes":LAWS_1993_94.max_used_substitutes},
        "league_samples":samples,"foreign_rule_samples":foreign_samples,"sample_years":list(sample_years),
    }
