from __future__ import annotations

"""Coupled Netherlands 1993-94 league/promotion runtime.

The nacompetitie is deliberately modelled across both divisions.  It cannot be
represented as a generic relegation flag on either league in isolation.
"""

from dataclasses import dataclass
from random import Random

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394
from .rules import (
    NETHERLANDS_EERSTE_1993_94,
    NETHERLANDS_EREDIVISIE_1993_94,
    NETHERLANDS_NACOMPETITIE_GROUP_1993_94,
)
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import LeagueMatch9394, StandingRow9394, build_league_table
from .team_builder import build_snapshot_team_sheet


@dataclass(frozen=True, slots=True)
class DutchPlayoffGroup9394:
    group_id: str
    team_ids: tuple[str, ...]
    table: tuple[StandingRow9394, ...]
    matches: int
    winner_team_id: str


@dataclass(frozen=True, slots=True)
class NetherlandsSeason9394:
    eredivisie_table: tuple[StandingRow9394, ...]
    eerste_table: tuple[StandingRow9394, ...]
    period_winners: tuple[str, ...]
    playoff_qualifiers_eerste: tuple[str, ...]
    playoff_groups: tuple[DutchPlayoffGroup9394, ...]
    direct_promoted_team_id: str
    direct_relegated_team_id: str
    promoted_team_ids: tuple[str, ...]
    relegated_team_ids: tuple[str, ...]
    eredivisie_matches: int
    eerste_matches: int
    playoff_matches: int


def _build_league(universe: FootballUniverseSnapshot9394, source_id: int, rules) -> LeagueSeason9394:
    teams = universe.teams(league_id=source_id)
    sheets = {str(int(t['source_id'])): build_snapshot_team_sheet(universe, int(t['source_id'])) for t in teams}
    return LeagueSeason9394(rules, sheets, FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))


def _matches_for_round_window(season: LeagueSeason9394, first_round: int, last_round: int) -> tuple[LeagueMatch9394, ...]:
    # play_all appends results in round/fixture order, the same stable order as fixtures.
    if len(season.results) != len(season.fixtures):
        raise ValueError('los periodos sólo pueden calcularse tras completar la Eerste Divisie')
    return tuple(
        result for fixture, result in zip(season.fixtures, season.results)
        if first_round <= fixture.round_number <= last_round
    )


def _period_qualifiers(season: LeagueSeason9394, overall: tuple[StandingRow9394, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    direct_champion = overall[0].team_id
    period_winners: list[str] = []
    # The four period competitions cover rounds 1-8, 9-16, 17-24, 25-32.
    # If a club has already won a period (or later holds direct promotion), the
    # berth passes down that period table to the next eligible club.
    period_tables: list[tuple[StandingRow9394, ...]] = []
    for start in (1, 9, 17, 25):
        matches = _matches_for_round_window(season, start, start + 7)
        table = build_league_table(tuple(season.team_sheets), matches, NETHERLANDS_EERSTE_1993_94)
        period_tables.append(table)

    used: set[str] = {direct_champion}
    for table in period_tables:
        winner = next((row.team_id for row in table if row.team_id not in used), None)
        if winner is None:
            raise ValueError('no se pudo transferir una plaza de periodo neerlandesa')
        period_winners.append(winner)
        used.add(winner)

    # Two best overall clubs without direct promotion or a period title.
    extras = [row.team_id for row in overall if row.team_id not in used][:2]
    if len(extras) != 2:
        raise ValueError('faltan clasificados de Eerste Divisie para nacompetitie')
    qualifiers = tuple(period_winners + extras)
    return tuple(period_winners), qualifiers


def _play_group(group_id: str, team_ids: tuple[str, ...], sheets: dict[str, object], *, seed_base: int) -> DutchPlayoffGroup9394:
    group_sheets = {team_id: sheets[team_id] for team_id in team_ids}
    season = LeagueSeason9394(
        NETHERLANDS_NACOMPETITIE_GROUP_1993_94,
        group_sheets,
        FootballMatchEngine9394(profile=ERA_BASELINE_1993_94),
    )
    season.play_all(seed_base=seed_base)
    table = season.table()
    if any(row.requires_playoff for row in table[:2]):
        # A fully unresolved first-place tie is exceptionally possible in a
        # procedural save. Resolve it explicitly instead of adding a hidden rule.
        resolution = season.finalize_table(seed_base=seed_base + 9000)
        table = resolution.table
    return DutchPlayoffGroup9394(group_id, team_ids, table, season.played_matches, table[0].team_id)


def simulate_netherlands_1993_94(*, seed_base: int = 319394, universe: FootballUniverseSnapshot9394 | None = None) -> NetherlandsSeason9394:
    universe = universe or default_runtime_snapshot()
    ered = _build_league(universe, 31, NETHERLANDS_EREDIVISIE_1993_94)
    eerste = _build_league(universe, 54, NETHERLANDS_EERSTE_1993_94)
    ered.play_all(seed_base=seed_base)
    eerste.play_all(seed_base=seed_base + 50000)
    ered_table = ered.table()
    eerste_table = eerste.table()

    periods, six = _period_qualifiers(eerste, eerste_table)
    direct_promoted = eerste_table[0].team_id
    direct_relegated = ered_table[17].team_id
    top_playoff = (ered_table[15].team_id, ered_table[16].team_id)

    rng = Random(seed_base ^ 0x199394)
    candidates = list(six)
    rng.shuffle(candidates)
    group_a_ids = (top_playoff[0], *candidates[:3])
    group_b_ids = (top_playoff[1], *candidates[3:])

    all_sheets = {**ered.team_sheets, **eerste.team_sheets}
    group_a = _play_group('A', group_a_ids, all_sheets, seed_base=seed_base + 100000)
    group_b = _play_group('B', group_b_ids, all_sheets, seed_base=seed_base + 110000)
    winners = (group_a.winner_team_id, group_b.winner_team_id)

    promoted = [direct_promoted]
    for winner in winners:
        if winner in eerste.team_sheets:
            promoted.append(winner)
    relegated = [direct_relegated]
    for top_id, group in zip(top_playoff, (group_a, group_b)):
        if group.winner_team_id != top_id:
            relegated.append(top_id)

    return NetherlandsSeason9394(
        eredivisie_table=ered_table,
        eerste_table=eerste_table,
        period_winners=periods,
        playoff_qualifiers_eerste=six,
        playoff_groups=(group_a, group_b),
        direct_promoted_team_id=direct_promoted,
        direct_relegated_team_id=direct_relegated,
        promoted_team_ids=tuple(promoted),
        relegated_team_ids=tuple(relegated),
        eredivisie_matches=ered.played_matches,
        eerste_matches=eerste.played_matches,
        playoff_matches=group_a.matches + group_b.matches,
    )
