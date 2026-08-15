from __future__ import annotations

"""Executable 1993-94 Spanish Segunda B: four groups + promotion/survival."""

from dataclasses import dataclass
from random import Random

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, TeamSheet9394
from .rules import SPAIN_SEGUNDA_B_1993_94, SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import StandingRow9394
from .team_builder import build_snapshot_team_sheet

GROUP_SOURCE_IDS = (3, 10, 11, 9)


@dataclass(frozen=True, slots=True)
class SegundaBGroupResult9394:
    source_id: int
    table: tuple[StandingRow9394, ...]
    matches: int
    promotion_qualifiers: tuple[str, ...]
    direct_relegated: tuple[str, ...]
    survival_playoff_team_id: str


@dataclass(frozen=True, slots=True)
class PromotionMiniLeague9394:
    group_id: str
    team_ids: tuple[str, ...]
    table: tuple[StandingRow9394, ...]
    matches: int
    promoted_team_id: str


@dataclass(frozen=True, slots=True)
class SurvivalPlayoff9394:
    semifinal_pairs: tuple[tuple[str, str], ...]
    semifinal_winners: tuple[str, ...]
    final_pair: tuple[str, str]
    relegated_team_id: str
    matches: int


@dataclass(frozen=True, slots=True)
class SpainSegundaBSeason9394:
    regular_groups: tuple[SegundaBGroupResult9394, ...]
    promotion_groups: tuple[PromotionMiniLeague9394, ...]
    survival: SurvivalPlayoff9394
    promoted_team_ids: tuple[str, ...]
    relegated_team_ids: tuple[str, ...]
    regular_matches: int
    promotion_matches: int
    survival_matches: int


def _build_group(universe: FootballUniverseSnapshot9394, source_id: int) -> tuple[LeagueSeason9394, tuple[StandingRow9394, ...]]:
    teams = universe.teams(league_id=source_id)
    sheets = {str(int(t['source_id'])): build_snapshot_team_sheet(universe, int(t['source_id'])) for t in teams}
    season = LeagueSeason9394(SPAIN_SEGUNDA_B_1993_94, sheets, FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
    season.play_all(seed_base=939400 + source_id * 1000)
    return season, season.table()


def _promotion_eligible(universe: FootballUniverseSnapshot9394, team_id: str) -> bool:
    team = universe.team(int(team_id))
    if not team:
        return False
    reserve_of = team.get('reserve_of')
    reserve_step = int(team.get('reserve_step') or 0)
    if not reserve_of or reserve_step <= 0:
        return True
    parent = universe.team(int(reserve_of))
    # A reserve can only rise to Segunda while its first team is in Primera.
    # Global rollover can still cancel the promotion if the parent is relegated
    # into Segunda in the same simulated season.
    return bool(parent and int(parent.get('league_id') or 0) == 1)


def _top_four_eligible(universe: FootballUniverseSnapshot9394, table: tuple[StandingRow9394, ...]) -> tuple[str, ...]:
    selected = [row.team_id for row in table if _promotion_eligible(universe, row.team_id)][:4]
    if len(selected) != 4:
        raise ValueError('un grupo de Segunda B no tiene cuatro clubes elegibles para la promoción')
    return tuple(selected)


def _play_promotion_group(group_id: str, team_ids: tuple[str, ...], sheets: dict[str, TeamSheet9394], *, seed_base: int) -> PromotionMiniLeague9394:
    season = LeagueSeason9394(
        SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94,
        {tid: sheets[tid] for tid in team_ids},
        FootballMatchEngine9394(profile=ERA_BASELINE_1993_94),
    )
    season.play_all(seed_base=seed_base)
    table = season.table()
    # The historical competition requires exactly one winner.  If all declared
    # tiebreaks are exhausted, resolve the final unresolved tie explicitly.
    if table[0].requires_playoff:
        resolution = season.finalize_table(seed_base=seed_base + 7000)
        table = resolution.table
    return PromotionMiniLeague9394(group_id, team_ids, table, season.played_matches, table[0].team_id)


def _decide_neutral(a: str, b: str, sheets: dict[str, TeamSheet9394], *, seed: int) -> str:
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    result = engine.simulate(sheets[a], sheets[b], seed=seed)
    if result.home.goals != result.away.goals:
        return a if result.home.goals > result.away.goals else b
    rng = Random(seed ^ 0xB9394)
    la = sum(p.overall for p in sheets[a].starters) / len(sheets[a].starters)
    lb = sum(p.overall for p in sheets[b].starters) / len(sheets[b].starters)
    pa = max(.35, min(.65, .5 + (la-lb)/140))
    return a if rng.random() < pa else b


def simulate_spain_segunda_b_1993_94(*, seed_base: int = 8839394, universe: FootballUniverseSnapshot9394 | None = None) -> SpainSegundaBSeason9394:
    universe = universe or default_runtime_snapshot()
    group_results: list[SegundaBGroupResult9394] = []
    sheets: dict[str, TeamSheet9394] = {}
    qualifier_matrix: list[tuple[str, ...]] = []
    survivalists: list[str] = []
    direct_down: list[str] = []

    for source_id in GROUP_SOURCE_IDS:
        season, table = _build_group(universe, source_id)
        sheets.update(season.team_sheets)
        qualifiers = _top_four_eligible(universe, table)
        qualifier_matrix.append(qualifiers)
        survivalists.append(table[15].team_id)
        down = tuple(row.team_id for row in table[16:20])
        direct_down.extend(down)
        group_results.append(SegundaBGroupResult9394(source_id, table, season.played_matches, qualifiers, down, table[15].team_id))

    # Latin-square draw: every mini-league receives one club from every source
    # group and one 1st/2nd/3rd/4th qualifying position. Seed rotates the draw
    # while preserving both historical constraints.
    rng = Random(seed_base)
    offsets = [0, 1, 2, 3]
    rng.shuffle(offsets)
    promotion_groups: list[PromotionMiniLeague9394] = []
    for pool in range(4):
        ids = tuple(qualifier_matrix[src_index][(pool + offsets[src_index]) % 4] for src_index in range(4))
        promotion_groups.append(_play_promotion_group(chr(65 + pool), ids, sheets, seed_base=seed_base + 10000 + pool*1000))

    # Four 16th placed clubs: neutral single-match semis; the two losers meet
    # once more and only that final loser is relegated.
    shuffled = survivalists[:]
    rng.shuffle(shuffled)
    semi_pairs = ((shuffled[0], shuffled[1]), (shuffled[2], shuffled[3]))
    semi_winners=[]; semi_losers=[]
    for idx,(a,b) in enumerate(semi_pairs):
        winner=_decide_neutral(a,b,sheets,seed=seed_base+30000+idx)
        semi_winners.append(winner); semi_losers.append(b if winner==a else a)
    final_pair=(semi_losers[0],semi_losers[1])
    final_winner=_decide_neutral(*final_pair,sheets,seed=seed_base+31000)
    survival_relegated=final_pair[1] if final_winner==final_pair[0] else final_pair[0]
    survival=SurvivalPlayoff9394(semi_pairs,tuple(semi_winners),final_pair,survival_relegated,3)

    promoted=tuple(group.promoted_team_id for group in promotion_groups)
    relegated=tuple(direct_down+[survival_relegated])
    return SpainSegundaBSeason9394(
        tuple(group_results), tuple(promotion_groups), survival, promoted, relegated,
        regular_matches=sum(g.matches for g in group_results),
        promotion_matches=sum(g.matches for g in promotion_groups),
        survival_matches=3,
    )
