from __future__ import annotations

"""Argentina 1993-94: Apertura + Clausura + three-season relegation averages."""

from dataclasses import dataclass

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394
from .rules import ARGENTINA_PRIMERA_1993_94, ARGENTINA_SHORT_TOURNAMENT_1993_94
from .season_decisions import resolve_season_end_decisive_playoffs
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import LeagueMatch9394, StandingRow9394, build_league_table
from .team_builder import build_snapshot_team_sheet

# Fixed historical context that exists before a new 1993-94 save begins.
# Values are points/matches accumulated in 1991-92 and 1992-93. Newly promoted
# clubs only carry seasons actually played in Primera, exactly as the promedio did.
_PRIOR_AVERAGE_CONTEXT = {
    104:(101,76), 103:(98,76), 108:(96,76), 105:(77,76), 111:(81,76), 107:(79,76),
    117:(0,0), 140:(86,76), 112:(37,38), 106:(75,76), 1699:(75,76), 110:(73,76),
    91:(75,76), 123:(73,76), 99:(70,76), 109:(69,76), 116:(68,76), 2338:(70,76),
    113:(67,76), 2339:(0,0),
}


@dataclass(frozen=True, slots=True)
class RelegationAverage9394:
    team_id: str
    prior_points: int
    prior_matches: int
    season_points: int
    season_matches: int
    average: float


@dataclass(frozen=True, slots=True)
class ArgentinaSeason9394:
    apertura_table: tuple[StandingRow9394, ...]
    clausura_table: tuple[StandingRow9394, ...]
    apertura_champion_team_id: str
    clausura_champion_team_id: str
    championship_playoffs: int
    relegation_averages: tuple[RelegationAverage9394, ...]
    relegated_team_ids: tuple[str, str]
    matches: int


def _phase_matches(season: LeagueSeason9394, first_round: int, last_round: int) -> tuple[LeagueMatch9394, ...]:
    if len(season.results) != len(season.fixtures):
        raise ValueError('la temporada argentina debe completarse antes de cerrar Apertura/Clausura')
    return tuple(result for fixture,result in zip(season.fixtures,season.results) if first_round <= fixture.round_number <= last_round)


def _phase_table(season: LeagueSeason9394, first_round: int, last_round: int, *, seed: int):
    table=build_league_table(tuple(season.team_sheets), _phase_matches(season,first_round,last_round), ARGENTINA_SHORT_TOURNAMENT_1993_94)
    resolved=resolve_season_end_decisive_playoffs(table,ARGENTINA_SHORT_TOURNAMENT_1993_94,dict(season.team_sheets),season.match_engine,seed_base=seed)
    return resolved


def simulate_argentina_1993_94(*, seed_base: int=169394, universe: FootballUniverseSnapshot9394|None=None) -> ArgentinaSeason9394:
    universe=universe or default_runtime_snapshot()
    teams=universe.teams(league_id=16)
    sheets={str(int(t['source_id'])):build_snapshot_team_sheet(universe,int(t['source_id'])) for t in teams}
    season=LeagueSeason9394(ARGENTINA_PRIMERA_1993_94,sheets,FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
    season.play_all(seed_base=seed_base)
    apertura=_phase_table(season,1,19,seed=seed_base+50000)
    clausura=_phase_table(season,20,38,seed=seed_base+60000)

    annual=build_league_table(tuple(sheets),tuple(season.results),ARGENTINA_PRIMERA_1993_94)
    points={r.team_id:r.points for r in annual}
    averages=[]
    for team_id in sheets:
        prior_points,prior_matches=_PRIOR_AVERAGE_CONTEXT.get(int(team_id),(0,0))
        total_points=prior_points+points[team_id]
        total_matches=prior_matches+38
        averages.append(RelegationAverage9394(team_id,prior_points,prior_matches,points[team_id],38,total_points/total_matches))
    averages.sort(key=lambda row:(row.average,row.team_id),reverse=True)
    relegated=tuple(row.team_id for row in averages[-2:])
    return ArgentinaSeason9394(
        apertura.table,clausura.table,apertura.table[0].team_id,clausura.table[0].team_id,
        len(apertura.playoffs)+len(clausura.playoffs),tuple(averages),relegated,season.played_matches,
    )
