from __future__ import annotations

"""Executable Colombian Primera A 1993.

1993 is intentionally not represented as a normal annual double round robin.
The runtime models Copa Mustang I (two groups), its bonus allocation ties,
Copa Mustang II, the 44-match reclasificación, semifinal quadrangulars and the
final quadrangular.  Season bonuses behave differently in the two final stages:
they are added to points in the semifinals, but are the first tiebreak after raw
points in the final quadrangular.
"""

from dataclasses import dataclass
from random import Random
from typing import Iterable, Mapping

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, TeamSheet9394
from .rules import (
    COLOMBIA_APERTURA_GROUP_1993,
    COLOMBIA_FINALIZACION_1993,
    COLOMBIA_QUADRANGULAR_1993,
)
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import LeagueMatch9394, StandingRow9394
from .team_builder import build_snapshot_team_sheet_with_repair


# Actual 1993 Copa Mustang I group membership, mapped to MDB source team IDs.
COLOMBIA_APERTURA_GROUPS_1993: tuple[tuple[int, ...], tuple[int, ...]] = (
    (1407, 1416, 930, 1959, 1408, 949, 1412, 1405),
    (1413, 931, 1956, 1411, 1409, 2252, 2236, 1495),
)

BONUS_BY_PLACE: tuple[float, ...] = (1.00, 0.75, 0.50, 0.25)


@dataclass(frozen=True, slots=True)
class ColombiaPhaseRow9394:
    team_id: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    away_goals_for: int
    away_goals_against: int
    raw_points: int
    bonus: float = 0.0
    effective_points: float = 0.0
    position: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def as_standing(self) -> StandingRow9394:
        return StandingRow9394(
            team_id=self.team_id,
            played=self.played,
            wins=self.wins,
            draws=self.draws,
            losses=self.losses,
            goals_for=self.goals_for,
            goals_against=self.goals_against,
            points=self.raw_points,
            position=self.position,
        )


@dataclass(frozen=True, slots=True)
class ColombiaBonusTie9394:
    label: str
    team_a_id: str
    team_b_id: str
    matches: tuple[LeagueMatch9394, LeagueMatch9394]
    winner_team_id: str
    loser_team_id: str


@dataclass(frozen=True, slots=True)
class ColombiaSeason9394:
    apertura_groups: tuple[tuple[ColombiaPhaseRow9394, ...], tuple[ColombiaPhaseRow9394, ...]]
    apertura_bonus_ties: tuple[ColombiaBonusTie9394, ColombiaBonusTie9394]
    finalizacion_table: tuple[ColombiaPhaseRow9394, ...]
    bonuses: tuple[tuple[str, float], ...]
    aggregate_table: tuple[ColombiaPhaseRow9394, ...]
    semifinal_groups: tuple[tuple[ColombiaPhaseRow9394, ...], tuple[ColombiaPhaseRow9394, ...]]
    final_table: tuple[ColombiaPhaseRow9394, ...]
    champion_team_id: str
    runner_up_team_id: str
    relegated_team_id: str
    official_matches: int
    bonus_allocation_matches: int
    simulated_matches: int
    repaired_players: int
    repaired_team_ids: tuple[str, ...]


def _stats(team_ids: Iterable[str], matches: Iterable[LeagueMatch9394]) -> dict[str, dict[str, int]]:
    rows = {
        str(team_id): {
            "played": 0, "wins": 0, "draws": 0, "losses": 0,
            "gf": 0, "ga": 0, "away_gf": 0, "away_ga": 0, "points": 0,
        }
        for team_id in team_ids
    }
    for match in matches:
        home = rows[match.home_team_id]
        away = rows[match.away_team_id]
        home["played"] += 1; away["played"] += 1
        home["gf"] += match.home_goals; home["ga"] += match.away_goals
        away["gf"] += match.away_goals; away["ga"] += match.home_goals
        away["away_gf"] += match.away_goals; away["away_ga"] += match.home_goals
        if match.home_goals > match.away_goals:
            home["wins"] += 1; away["losses"] += 1; home["points"] += 2
        elif match.home_goals < match.away_goals:
            away["wins"] += 1; home["losses"] += 1; away["points"] += 2
        else:
            home["draws"] += 1; away["draws"] += 1
            home["points"] += 1; away["points"] += 1
    return rows


def _base_key(row: Mapping[str, int]) -> tuple[int, int, int, int, int, int, int]:
    # 1993 order: points, wins, goal difference, goals for, away goals for,
    # fewer goals against, fewer away goals against.
    return (
        row["points"], row["wins"], row["gf"] - row["ga"], row["gf"],
        row["away_gf"], -row["ga"], -row["away_ga"],
    )


def _lot_order(ids: list[str], *, seed: int) -> list[str]:
    rng = Random(seed)
    ids = list(ids)
    rng.shuffle(ids)
    return ids


def _rank_phase(
    team_ids: Iterable[str],
    matches: Iterable[LeagueMatch9394],
    *,
    bonuses: Mapping[str, float] | None = None,
    bonus_mode: str = "none",  # none | add | tiebreak
    full_season_rows: Mapping[str, ColombiaPhaseRow9394] | None = None,
    seed: int = 1,
) -> tuple[ColombiaPhaseRow9394, ...]:
    ids = [str(team_id) for team_id in team_ids]
    data = _stats(ids, matches)
    bonuses = bonuses or {}

    def key(team_id: str):
        row = data[team_id]
        bonus = float(bonuses.get(team_id, 0.0))
        base = _base_key(row)
        if bonus_mode == "add":
            primary = (row["points"] + bonus, *base[1:])
        elif bonus_mode == "tiebreak":
            primary = (row["points"], bonus, *base[1:])
        else:
            primary = base
        if full_season_rows is not None:
            fs = full_season_rows[team_id]
            primary = (*primary, fs.raw_points, fs.wins, fs.goal_difference, fs.goals_for,
                       fs.away_goals_for, -fs.goals_against, -fs.away_goals_against)
        return primary

    grouped: dict[tuple, list[str]] = {}
    for team_id in ids:
        grouped.setdefault(key(team_id), []).append(team_id)
    ordered: list[str] = []
    for group_key in sorted(grouped, reverse=True):
        tied = grouped[group_key]
        ordered.extend(tied if len(tied) == 1 else _lot_order(tied, seed=seed + len(ordered) * 37))

    result = []
    for position, team_id in enumerate(ordered, start=1):
        row = data[team_id]
        bonus = float(bonuses.get(team_id, 0.0))
        effective = row["points"] + bonus if bonus_mode == "add" else float(row["points"])
        result.append(ColombiaPhaseRow9394(
            team_id=team_id, played=row["played"], wins=row["wins"], draws=row["draws"], losses=row["losses"],
            goals_for=row["gf"], goals_against=row["ga"], away_goals_for=row["away_gf"],
            away_goals_against=row["away_ga"], raw_points=row["points"], bonus=bonus,
            effective_points=effective, position=position,
        ))
    return tuple(result)


def _play_league(
    rules,
    sheets: Mapping[str, TeamSheet9394],
    engine: FootballMatchEngine9394,
    *,
    seed: int,
) -> tuple[tuple[LeagueMatch9394, ...], tuple[ColombiaPhaseRow9394, ...]]:
    season = LeagueSeason9394(rules, sheets, engine)
    season.play_all(seed_base=seed)
    matches = tuple(season.results)
    return matches, _rank_phase(sheets, matches, seed=seed + 9000)


def _play_bonus_tie(
    label: str,
    team_a_id: str,
    team_b_id: str,
    sheets: Mapping[str, TeamSheet9394],
    engine: FootballMatchEngine9394,
    *,
    seed: int,
) -> ColombiaBonusTie9394:
    a = sheets[team_a_id]; b = sheets[team_b_id]
    results = (engine.simulate(a, b, seed=seed), engine.simulate(b, a, seed=seed + 1))
    matches = tuple(
        LeagueMatch9394(result.home_team_id, result.away_team_id, result.home.goals, result.away.goals)
        for result in results
    )
    table = _rank_phase((team_a_id, team_b_id), matches, seed=seed + 2)
    return ColombiaBonusTie9394(label, team_a_id, team_b_id, matches, table[0].team_id, table[1].team_id)


def _phase_sheets(ids: Iterable[str], sheets: Mapping[str, TeamSheet9394]) -> dict[str, TeamSheet9394]:
    return {str(team_id): sheets[str(team_id)] for team_id in ids}


def simulate_colombia_1993(
    *,
    seed_base: int = 1289393,
    universe: FootballUniverseSnapshot9394 | None = None,
) -> ColombiaSeason9394:
    universe = universe or default_runtime_snapshot()
    source_teams = universe.teams(league_id=128)
    if len(source_teams) != 16:
        raise RuntimeError(f"Colombia 1993: esperaba 16 clubes en la MDB, recibió {len(source_teams)}")
    sheets: dict[str, TeamSheet9394] = {}
    repair_counts: dict[str, int] = {}
    for team in source_teams:
        team_id = int(team["source_id"])
        sheet, repaired = build_snapshot_team_sheet_with_repair(universe, team_id)
        sheets[str(team_id)] = sheet
        if repaired:
            repair_counts[str(team_id)] = repaired
    expected = {team for group in COLOMBIA_APERTURA_GROUPS_1993 for team in group}
    if {int(team_id) for team_id in sheets} != expected:
        raise RuntimeError("Colombia 1993: los 16 clubes MDB no coinciden con los grupos históricos del Apertura")

    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)

    apertura_matches: list[LeagueMatch9394] = []
    apertura_tables: list[tuple[ColombiaPhaseRow9394, ...]] = []
    for index, group in enumerate(COLOMBIA_APERTURA_GROUPS_1993):
        group_sheets = _phase_sheets((str(team_id) for team_id in group), sheets)
        matches, table = _play_league(COLOMBIA_APERTURA_GROUP_1993, group_sheets, engine,
                                      seed=seed_base + index * 10000)
        apertura_matches.extend(matches)
        apertura_tables.append(table)

    # Group winners play for bonuses 1.00/0.75 and runners-up for 0.50/0.25.
    winners_tie = _play_bonus_tie(
        "Ganadores de grupo", apertura_tables[0][0].team_id, apertura_tables[1][0].team_id,
        sheets, engine, seed=seed_base + 30000,
    )
    runners_tie = _play_bonus_tie(
        "Segundos de grupo", apertura_tables[0][1].team_id, apertura_tables[1][1].team_id,
        sheets, engine, seed=seed_base + 31000,
    )
    apertura_bonus = {
        winners_tie.winner_team_id: 1.00, winners_tie.loser_team_id: 0.75,
        runners_tie.winner_team_id: 0.50, runners_tie.loser_team_id: 0.25,
    }

    finalizacion_matches, finalizacion_table = _play_league(
        COLOMBIA_FINALIZACION_1993, sheets, engine, seed=seed_base + 40000,
    )
    finalizacion_bonus = {
        row.team_id: BONUS_BY_PLACE[index] for index, row in enumerate(finalizacion_table[:4])
    }
    total_bonus = {team_id: apertura_bonus.get(team_id, 0.0) + finalizacion_bonus.get(team_id, 0.0) for team_id in sheets}

    aggregate_matches = tuple(apertura_matches) + tuple(finalizacion_matches)
    aggregate = _rank_phase(sheets, aggregate_matches, seed=seed_base + 50000)
    if any(row.played != 44 for row in aggregate):
        raise RuntimeError("Colombia 1993: la reclasificación no cerró con 44 partidos por club")
    aggregate_by_id = {row.team_id: row for row in aggregate}
    top8 = [row.team_id for row in aggregate[:8]]

    # Historical seeding: 1-3-6-8 and 2-4-5-7 from Reclasificación.
    semifinal_ids = (
        (top8[0], top8[2], top8[5], top8[7]),
        (top8[1], top8[3], top8[4], top8[6]),
    )
    semifinal_tables: list[tuple[ColombiaPhaseRow9394, ...]] = []
    semifinal_matches = 0
    finalists: list[str] = []
    for index, ids in enumerate(semifinal_ids):
        phase_sheets = _phase_sheets(ids, sheets)
        season = LeagueSeason9394(COLOMBIA_QUADRANGULAR_1993, phase_sheets, engine)
        season.play_all(seed_base=seed_base + 60000 + index * 10000)
        table = _rank_phase(
            ids, season.results, bonuses=total_bonus, bonus_mode="add",
            full_season_rows=aggregate_by_id, seed=seed_base + 60500 + index * 10000,
        )
        semifinal_tables.append(table)
        semifinal_matches += season.played_matches
        finalists.extend(row.team_id for row in table[:2])

    final_sheets = _phase_sheets(finalists, sheets)
    final_season = LeagueSeason9394(COLOMBIA_QUADRANGULAR_1993, final_sheets, engine)
    final_season.play_all(seed_base=seed_base + 80000)
    final_table = _rank_phase(
        finalists, final_season.results, bonuses=total_bonus, bonus_mode="tiebreak",
        full_season_rows=aggregate_by_id, seed=seed_base + 81000,
    )

    official_matches = len(apertura_matches) + len(finalizacion_matches) + semifinal_matches + final_season.played_matches
    bonus_matches = len(winners_tie.matches) + len(runners_tie.matches)
    if official_matches != 388 or bonus_matches != 4:
        raise RuntimeError(f"Colombia 1993: conteo inesperado {official_matches}+{bonus_matches} partidos")

    return ColombiaSeason9394(
        apertura_groups=(apertura_tables[0], apertura_tables[1]),
        apertura_bonus_ties=(winners_tie, runners_tie),
        finalizacion_table=finalizacion_table,
        bonuses=tuple(sorted(total_bonus.items())),
        aggregate_table=aggregate,
        semifinal_groups=(semifinal_tables[0], semifinal_tables[1]),
        final_table=final_table,
        champion_team_id=final_table[0].team_id,
        runner_up_team_id=final_table[1].team_id,
        relegated_team_id=aggregate[-1].team_id,
        official_matches=official_matches,
        bonus_allocation_matches=bonus_matches,
        simulated_matches=official_matches + bonus_matches,
        repaired_players=sum(repair_counts.values()),
        repaired_team_ids=tuple(sorted(repair_counts)),
    )
