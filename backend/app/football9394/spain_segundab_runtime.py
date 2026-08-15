from __future__ import annotations

"""Coupled Segunda / Segunda B 1993-94 movement runtime.

Four regional Segunda B tables feed four promotion mini-leagues.  The four
16th-placed clubs also play the one-off neutral permanence series introduced
in 1993-94.  Reserve-team forced drops are applied before sporting relegation
slots so a parent club falling into the reserve's division does not create an
extra relegation by table.
"""

from dataclasses import dataclass
from itertools import permutations
from random import Random

from .competition_runtime import build_simple_source_league
from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, TeamSheet9394
from .rules import CompetitionRules9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import LeagueMatch9394, StandingRow9394


SEGUNDA_B_SOURCE_IDS_1993_94 = (3, 10, 11, 9)


@dataclass(frozen=True, slots=True)
class SegundaBPromotionGroup9394:
    group_id: str
    team_ids: tuple[str, str, str, str]
    source_group_ids: tuple[int, int, int, int]
    regular_positions: tuple[int, int, int, int]
    table: tuple[StandingRow9394, ...]
    matches: int
    promoted_team_id: str


@dataclass(frozen=True, slots=True)
class SegundaBPermanenceMatch9394:
    stage: str
    team_a_id: str
    team_b_id: str
    winner_team_id: str
    loser_team_id: str
    regulation_score: tuple[int, int]
    resolved_by: str


@dataclass(frozen=True, slots=True)
class SegundaBGroupMovement9394:
    source_id: int
    direct_relegated_team_ids: tuple[str, ...]
    forced_reserve_relegated_team_ids: tuple[str, ...]
    permanence_team_id: str


@dataclass(frozen=True, slots=True)
class SpainSegundaBSeason9394:
    segunda_table: tuple[StandingRow9394, ...]
    group_tables: dict[int, tuple[StandingRow9394, ...]]
    promotion_groups: tuple[SegundaBPromotionGroup9394, ...]
    permanence_matches: tuple[SegundaBPermanenceMatch9394, ...]
    promoted_to_segunda: tuple[str, str, str, str]
    relegated_from_segunda: tuple[str, str, str, str]
    relegated_to_tercera: tuple[str, ...]
    group_movements: tuple[SegundaBGroupMovement9394, ...]
    regular_matches_segunda: int
    regular_matches_segundab: int
    promotion_matches: int


def _team_meta(universe: FootballUniverseSnapshot9394) -> dict[str, dict]:
    return {str(int(team["source_id"])): team for team in universe.teams()}


def _reserve_parent(team: dict) -> str | None:
    if int(team.get("reserve_step") or 0) <= 0:
        return None
    parent = team.get("reserve_of")
    if parent in (None, 0, "0"):
        return None
    return str(int(parent))


def _family_root_and_step(team_id: str, meta: dict[str, dict]) -> tuple[str, int]:
    team = meta[team_id]
    parent = _reserve_parent(team)
    return (parent or team_id, int(team.get("reserve_step") or 0) if parent else 0)


def _higher_family_member_in_division(
    team_id: str, meta: dict[str, dict], division_team_ids: set[str]
) -> bool:
    root, step = _family_root_and_step(team_id, meta)
    if step <= 0:
        return False
    for other_id in division_team_ids:
        if other_id == team_id or other_id not in meta:
            continue
        other_root, other_step = _family_root_and_step(other_id, meta)
        if other_root == root and other_step < step:
            return True
    return False


def _eligible_for_segunda(
    team_id: str, meta: dict[str, dict], segunda_team_ids: set[str], incoming_segunda_team_ids: set[str] | None = None
) -> bool:
    division = set(segunda_team_ids) | set(incoming_segunda_team_ids or ())
    return not _higher_family_member_in_division(team_id, meta, division)


def _top_four_eligible(
    table: tuple[StandingRow9394, ...], meta: dict[str, dict], segunda_team_ids: set[str],
    incoming_segunda_team_ids: set[str] | None = None,
) -> tuple[tuple[str, int], ...]:
    selected: list[tuple[str, int]] = []
    for row in table:
        if not _eligible_for_segunda(row.team_id, meta, segunda_team_ids, incoming_segunda_team_ids):
            continue
        selected.append((row.team_id, row.position))
        if len(selected) == 4:
            return tuple(selected)
    raise ValueError("Segunda B: no hay cuatro clubes elegibles para la liguilla")


def _draw_promotion_groups(
    qualifiers: dict[int, tuple[tuple[str, int], ...]], *, seed: int
) -> tuple[tuple[tuple[int, str, int], ...], ...]:
    """Draw four pools: one club from every regional group and every rank band."""
    rng = Random(seed)
    source_ids = list(SEGUNDA_B_SOURCE_IDS_1993_94)
    rng.shuffle(source_ids)
    pools: list[list[tuple[int, str, int]]] = [[(sid, qualifiers[sid][0][0], 1)] for sid in source_ids]

    # Each subsequent rank must occupy every pool exactly once while avoiding
    # the regional group already present there.  Try all 24 permutations; the
    # randomised candidate order turns this into a seeded historical draw.
    for rank_index in range(1, 4):
        candidates = [(sid, qualifiers[sid][rank_index][0], rank_index + 1) for sid in SEGUNDA_B_SOURCE_IDS_1993_94]
        perms = list(permutations(candidates))
        rng.shuffle(perms)
        chosen = next(
            (perm for perm in perms if all(perm[i][0] not in {item[0] for item in pools[i]} for i in range(4))),
            None,
        )
        if chosen is None:
            raise AssertionError("no se pudo construir el sorteo histórico de liguillas")
        for i, item in enumerate(chosen):
            pools[i].append(item)

    for pool in pools:
        if len({x[0] for x in pool}) != 4 or len({x[2] for x in pool}) != 4:
            raise AssertionError("liguilla inválida: debe tener cuatro grupos/registros de posición distintos")
    return tuple(tuple(pool) for pool in pools)


def _play_promotion_group(
    group_id: str,
    entries: tuple[tuple[int, str, int], ...],
    sheets: dict[str, TeamSheet9394],
    rules: CompetitionRules9394,
    *, seed_base: int,
) -> SegundaBPromotionGroup9394:
    group_rules = CompetitionRules9394(
        id=f"esp_segundab_promocion_{group_id.lower()}_1993_94",
        name=f"Ascenso a Segunda · Grupo {group_id}", country="España",
        points_win=2, points_draw=1, points_loss=0, teams=4, rounds=6,
        tie_breakers=rules.tie_breakers,
        direct_promotion_places=(1,),
    )
    ids = tuple(item[1] for item in entries)
    season = LeagueSeason9394(group_rules, {team_id: sheets[team_id] for team_id in ids}, FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
    season.play_all(seed_base=seed_base)
    resolution = season.finalize_table(seed_base=seed_base + 7000)
    table = resolution.table
    return SegundaBPromotionGroup9394(
        group_id=group_id, team_ids=ids,
        source_group_ids=tuple(item[0] for item in entries),
        regular_positions=tuple(item[2] for item in entries),
        table=table, matches=season.played_matches, promoted_team_id=table[0].team_id,
    )


def _neutral_decider(
    stage: str, a: str, b: str, sheets: dict[str, TeamSheet9394], *, seed: int
) -> SegundaBPermanenceMatch9394:
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    result = engine.simulate(sheets[a], sheets[b], seed=seed)
    ga, gb = result.home.goals, result.away.goals
    if ga != gb:
        winner, loser = (a, b) if ga > gb else (b, a)
        return SegundaBPermanenceMatch9394(stage, a, b, winner, loser, (ga, gb), "90_min")
    # Single neutral tie: extra time and, if still required, penalties.  The
    # match engine does not yet expose a separate ET state, so the decider is
    # strength-weighted and explicitly labelled rather than hidden in the score.
    rng = Random(seed ^ 0x53B9394)
    sa = sum(p.overall for p in sheets[a].starters) / len(sheets[a].starters)
    sb = sum(p.overall for p in sheets[b].starters) / len(sheets[b].starters)
    p_a = max(.30, min(.70, .5 + (sa - sb) / 140.0))
    winner = a if rng.random() < p_a else b
    loser = b if winner == a else a
    resolved_by = "extra_time" if rng.random() < .48 else "penalties"
    return SegundaBPermanenceMatch9394(stage, a, b, winner, loser, (ga, gb), resolved_by)


def _direct_relegations_with_forced_reserves(
    table: tuple[StandingRow9394, ...], forced: set[str], *, slots: int = 4
) -> tuple[str, ...]:
    selected: list[str] = list(sorted(forced))
    for row in reversed(table):
        if row.team_id in selected:
            continue
        if len(selected) >= slots:
            break
        selected.append(row.team_id)
    # Every forced reserve must drop even in the pathological case of more
    # forced reserves than nominal direct slots.
    return tuple(selected)


def simulate_spain_segunda_b_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 889394,
    incoming_segunda_team_ids: tuple[str, ...] = (),
) -> SpainSegundaBSeason9394:
    universe = universe or default_runtime_snapshot()
    meta = _team_meta(universe)

    segunda = build_simple_source_league(2, universe=universe)
    segunda.play_all(seed_base=seed_base)
    segunda_table = segunda.table()
    segunda_team_ids = set(segunda.team_sheets)
    incoming_segunda = set(incoming_segunda_team_ids)
    forced_in_segunda = {
        row.team_id for row in segunda_table
        if _higher_family_member_in_division(row.team_id, meta, incoming_segunda)
    }
    relegated_from_segunda = _direct_relegations_with_forced_reserves(
        segunda_table, forced_in_segunda, slots=4
    )

    group_seasons: dict[int, LeagueSeason9394] = {}
    tables: dict[int, tuple[StandingRow9394, ...]] = {}
    all_sheets: dict[str, TeamSheet9394] = dict(segunda.team_sheets)
    for offset, source_id in enumerate(SEGUNDA_B_SOURCE_IDS_1993_94):
        season = build_simple_source_league(source_id, universe=universe)
        season.play_all(seed_base=seed_base + 10000 * (offset + 1))
        group_seasons[source_id] = season
        tables[source_id] = season.table()
        all_sheets.update(season.team_sheets)

    qualifiers = {
        sid: _top_four_eligible(tables[sid], meta, segunda_team_ids, incoming_segunda)
        for sid in SEGUNDA_B_SOURCE_IDS_1993_94
    }
    draw = _draw_promotion_groups(qualifiers, seed=seed_base + 80000)
    reference_rules = group_seasons[SEGUNDA_B_SOURCE_IDS_1993_94[0]].rules
    promotion_groups = tuple(
        _play_promotion_group(chr(65+i), entries, all_sheets, reference_rules, seed_base=seed_base + 90000 + i*1000)
        for i, entries in enumerate(draw)
    )
    promoted = tuple(group.promoted_team_id for group in promotion_groups)

    # Parent clubs relegated from Segunda force their reserve down from Segunda B.
    relegated_second = set(relegated_from_segunda)
    movements: list[SegundaBGroupMovement9394] = []
    direct_by_group: dict[int, tuple[str, ...]] = {}
    permanence_ids: list[str] = []
    for sid in SEGUNDA_B_SOURCE_IDS_1993_94:
        forced = {
            row.team_id for row in tables[sid]
            if _higher_family_member_in_division(row.team_id, meta, relegated_second)
        }
        direct = _direct_relegations_with_forced_reserves(tables[sid], forced, slots=4)
        direct_by_group[sid] = direct
        # The permanence place is the 16th sporting position unless that club
        # is already forced/directly down; then use the nearest higher survivor.
        candidate_rows = list(reversed(tables[sid][:16]))
        permanence = next(row.team_id for row in candidate_rows if row.team_id not in direct)
        permanence_ids.append(permanence)
        movements.append(SegundaBGroupMovement9394(sid, direct, tuple(sorted(forced)), permanence))

    rng = Random(seed_base ^ 0x1600B)
    rng.shuffle(permanence_ids)
    semi1 = _neutral_decider("semifinal", permanence_ids[0], permanence_ids[1], all_sheets, seed=seed_base + 120001)
    semi2 = _neutral_decider("semifinal", permanence_ids[2], permanence_ids[3], all_sheets, seed=seed_base + 120002)
    final_survival = _neutral_decider("descenso_final", semi1.loser_team_id, semi2.loser_team_id, all_sheets, seed=seed_base + 120003)
    permanence_matches = (semi1, semi2, final_survival)
    relegated_to_tercera = tuple(
        dict.fromkeys([team for sid in SEGUNDA_B_SOURCE_IDS_1993_94 for team in direct_by_group[sid]] + [final_survival.loser_team_id])
    )

    if len(promoted) != 4 or len(set(promoted)) != 4:
        raise AssertionError("la promoción de Segunda B debe producir cuatro ascendidos distintos")
    if len(relegated_from_segunda) != 4:
        raise AssertionError("Segunda debe entregar cuatro descensos a Segunda B")
    if sum(group.matches for group in promotion_groups) != 48:
        raise AssertionError("cuatro liguillas de cuatro a doble vuelta deben sumar 48 partidos")

    return SpainSegundaBSeason9394(
        segunda_table=segunda_table,
        group_tables=tables,
        promotion_groups=promotion_groups,
        permanence_matches=permanence_matches,
        promoted_to_segunda=promoted,
        relegated_from_segunda=relegated_from_segunda,
        relegated_to_tercera=relegated_to_tercera,
        group_movements=tuple(movements),
        regular_matches_segunda=segunda.played_matches,
        regular_matches_segundab=sum(season.played_matches for season in group_seasons.values()),
        promotion_matches=sum(group.matches for group in promotion_groups),
    )
