from __future__ import annotations

"""Executable historical competition runtime for source-scoped simple leagues.

Complex competitions (split seasons, groups feeding knockouts, liguillas, etc.)
remain on their dedicated format graphs.  This factory exists only for source
rows that have an explicit `CompetitionRules9394` binding and a true double
round-robin topology.
"""

from dataclasses import dataclass

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, SPAIN_PRIMERA_SIMULATION_1993_94
from .registry import HistoricalCompetitionRegistry9394, default_registry_9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet


@dataclass(frozen=True, slots=True)
class SourceLeagueRuntimeInfo9394:
    source_id: int
    ruleset_id: str
    team_count: int
    rounds: int
    matches: int


def build_simple_source_league(
    source_id: int,
    *,
    universe: FootballUniverseSnapshot9394 | None = None,
    registry: HistoricalCompetitionRegistry9394 | None = None,
) -> LeagueSeason9394:
    universe = universe or default_runtime_snapshot()
    registry = registry or default_registry_9394()
    rules = registry.resolve_source("league", source_id)
    teams = universe.teams(league_id=source_id)
    if rules.teams is not None and len(teams) != rules.teams:
        raise ValueError(
            f"league:{source_id}/{rules.id}: snapshot con {len(teams)} equipos, reglamento con {rules.teams}"
        )
    sheets = {
        str(int(team["source_id"])): build_snapshot_team_sheet(universe, int(team["source_id"]))
        for team in teams
    }
    profile = SPAIN_PRIMERA_SIMULATION_1993_94 if source_id == 1 else ERA_BASELINE_1993_94
    return LeagueSeason9394(rules, sheets, FootballMatchEngine9394(profile=profile))


def source_league_runtime_info(source_id: int) -> SourceLeagueRuntimeInfo9394:
    season = build_simple_source_league(source_id)
    return SourceLeagueRuntimeInfo9394(
        source_id=source_id,
        ruleset_id=season.rules.id,
        team_count=len(season.team_sheets),
        rounds=max((fixture.round_number for fixture in season.fixtures), default=0),
        matches=len(season.fixtures),
    )
