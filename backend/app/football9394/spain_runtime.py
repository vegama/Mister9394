from __future__ import annotations

"""Full Spanish 1993-94 pyramid runtime.

Primera, Segunda and the four Segunda B groups are closed as one sporting
system.  The Primera/Segunda promotion is deliberately not modelled as a
modern away-goals tie: in 1993-94 an aggregate draw could require a third
match, as happened in the Rayo Vallecano-Compostela promotion.

Reserve-team constraints are applied to the *final target divisions* before
Segunda/Segunda B movement is closed, so a parent relegation can force its B
side down and can cascade to a C side belonging to the same club family.
"""

from dataclasses import dataclass
from random import Random

from .competition_runtime import build_simple_source_league
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, TeamSheet9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .spain_segundab_runtime import (
    SpainSegundaBSeason9394,
    _family_root_and_step,
    _reserve_parent,
    simulate_spain_segunda_b_1993_94,
)
from .standings import StandingRow9394
from .team_builder import build_snapshot_team_sheet


@dataclass(frozen=True, slots=True)
class SpainPromotionTie9394:
    primera_team_id: str
    segunda_team_id: str
    first_leg_score: tuple[int, int]
    second_leg_score: tuple[int, int]
    aggregate: tuple[int, int]
    winner_team_id: str
    loser_team_id: str
    resolved_by: str
    matches: int


@dataclass(frozen=True, slots=True)
class SpainPyramidSeason9394:
    primera_table: tuple[StandingRow9394, ...]
    segunda_table: tuple[StandingRow9394, ...]
    segundab: SpainSegundaBSeason9394
    direct_promoted_to_primera: tuple[str, str]
    promotion_ties: tuple[SpainPromotionTie9394, SpainPromotionTie9394]
    promoted_to_primera: tuple[str, str, str, str]
    relegated_to_segunda: tuple[str, str, str, str]
    promoted_to_segunda: tuple[str, str, str, str]
    relegated_to_segundab: tuple[str, str, str, str]
    primera_matches: int
    segunda_matches: int
    primera_segunda_playoff_matches: int


def _team_meta(universe: FootballUniverseSnapshot9394) -> dict[str, dict]:
    return {str(int(team["source_id"])): team for team in universe.teams()}


def _eligible_segunda_clubs_for_primera(
    table: tuple[StandingRow9394, ...], meta: dict[str, dict]
) -> tuple[str, ...]:
    selected: list[str] = []
    for row in table:
        # A reserve side is never promoted into Primera while its club family
        # has a senior team above it.  If that senior team is relegated in the
        # same season the user's historical rule forces the reserve downward,
        # rather than allowing a category swap.
        if _reserve_parent(meta[row.team_id]) is not None:
            continue
        selected.append(row.team_id)
        if len(selected) == 4:
            break
    if len(selected) != 4:
        raise ValueError("Segunda 1993-94 no tiene cuatro clubes elegibles para ascenso/promoción")
    return tuple(selected)


def _decide_drawn_single_match(
    a: str, b: str, sheets: dict[str, TeamSheet9394], *, seed: int
) -> tuple[str, str, str]:
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    result = engine.simulate(sheets[a], sheets[b], seed=seed)
    if result.home.goals != result.away.goals:
        winner = a if result.home.goals > result.away.goals else b
        return winner, b if winner == a else a, "tiebreak_90_min"
    rng = Random(seed ^ 0x939417)
    la = sum(p.overall for p in sheets[a].starters) / len(sheets[a].starters)
    lb = sum(p.overall for p in sheets[b].starters) / len(sheets[b].starters)
    pa = max(.33, min(.67, .5 + (la - lb) / 140.0))
    winner = a if rng.random() < pa else b
    return winner, b if winner == a else a, "tiebreak_extra_time_penalties"


def _play_primera_segunda_tie(
    primera_id: str, segunda_id: str, sheets: dict[str, TeamSheet9394], *, seed: int
) -> SpainPromotionTie9394:
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    # Historical home order: the Primera club opens at home, Segunda hosts the
    # return leg.  No away-goal resolver is applied to this promotion.
    first = engine.simulate(sheets[primera_id], sheets[segunda_id], seed=seed)
    second = engine.simulate(sheets[segunda_id], sheets[primera_id], seed=seed + 1)
    p_total = first.home.goals + second.away.goals
    s_total = first.away.goals + second.home.goals
    if p_total != s_total:
        winner = primera_id if p_total > s_total else segunda_id
        loser = segunda_id if winner == primera_id else primera_id
        return SpainPromotionTie9394(
            primera_id, segunda_id,
            (first.home.goals, first.away.goals),
            (second.home.goals, second.away.goals),
            (p_total, s_total), winner, loser, "aggregate", 2,
        )
    winner, loser, decided = _decide_drawn_single_match(
        primera_id, segunda_id, sheets, seed=seed + 2
    )
    return SpainPromotionTie9394(
        primera_id, segunda_id,
        (first.home.goals, first.away.goals),
        (second.home.goals, second.away.goals),
        (p_total, s_total), winner, loser, decided, 3,
    )


def _validate_family_separation(
    universe: FootballUniverseSnapshot9394,
    target_leagues: dict[str, int],
) -> None:
    meta = _team_meta(universe)
    by_root: dict[str, list[tuple[int, int, str]]] = {}
    for team_id, target in target_leagues.items():
        if team_id not in meta:
            continue
        root, step = _family_root_and_step(team_id, meta)
        by_root.setdefault(root, []).append((step, target, team_id))
    for root, rows in by_root.items():
        league_to_steps: dict[int, list[tuple[int, str]]] = {}
        for step, league_id, team_id in rows:
            league_to_steps.setdefault(league_id, []).append((step, team_id))
        clashes = {league: values for league, values in league_to_steps.items() if len(values) > 1}
        if clashes:
            raise AssertionError(f"familia {root} comparte categoría tras el cierre: {clashes}")


def simulate_spain_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 119394
) -> SpainPyramidSeason9394:
    universe = universe or default_runtime_snapshot()
    meta = _team_meta(universe)

    primera = build_simple_source_league(1, universe=universe)
    primera.play_all(seed_base=seed_base)
    primera_table = primera.table()

    # Produce the exact Segunda table that the lower-pyramid runtime will use.
    lower_seed = seed_base + 300000
    segunda_probe = build_simple_source_league(2, universe=universe)
    segunda_probe.play_all(seed_base=lower_seed)
    segunda_table = segunda_probe.table()
    eligible = _eligible_segunda_clubs_for_primera(segunda_table, meta)
    direct_up = (eligible[0], eligible[1])
    playoff_candidates = (eligible[2], eligible[3])

    primera_playoff = (primera_table[16].team_id, primera_table[17].team_id)
    direct_down = (primera_table[18].team_id, primera_table[19].team_id)

    all_ids = set(primera.team_sheets) | set(segunda_probe.team_sheets)
    sheets = {
        team_id: (primera.team_sheets.get(team_id) or segunda_probe.team_sheets.get(team_id))
        for team_id in all_ids
    }
    tie1 = _play_primera_segunda_tie(
        primera_playoff[0], playoff_candidates[0], sheets, seed=seed_base + 200000
    )
    tie2 = _play_primera_segunda_tie(
        primera_playoff[1], playoff_candidates[1], sheets, seed=seed_base + 210000
    )
    ties = (tie1, tie2)
    playoff_promoted = tuple(
        tie.winner_team_id for tie in ties if tie.winner_team_id in playoff_candidates
    )
    playoff_relegated = tuple(
        tie.loser_team_id for tie in ties if tie.loser_team_id in primera_playoff
    )
    # Every tie exchanges a place only if Segunda wins. If Primera wins it keeps
    # its place; therefore promoted/relegated totals can be 2..4, not fixed at 4.
    promoted_to_primera = tuple(direct_up + playoff_promoted)
    relegated_to_segunda = tuple(direct_down + playoff_relegated)

    lower = simulate_spain_segunda_b_1993_94(
        universe=universe,
        seed_base=lower_seed,
        incoming_segunda_team_ids=relegated_to_segunda,
    )
    if lower.segunda_table != segunda_table:
        raise AssertionError("el cierre español usó dos tablas de Segunda distintas")

    # Net exchange between Primera and Segunda must balance exactly.
    if len(promoted_to_primera) != len(relegated_to_segunda):
        raise AssertionError("Primera/Segunda no equilibran entradas y salidas")
    if len(lower.promoted_to_segunda) != len(lower.relegated_from_segunda):
        raise AssertionError("Segunda/Segunda B no equilibran entradas y salidas")

    # Construct final target divisions for all clubs in the three represented
    # tiers and prove that no club family shares a category after the movement.
    targets: dict[str, int] = {}
    for lid in (1, 2, 3, 9, 10, 11):
        for team in universe.teams(league_id=lid):
            targets[str(int(team["source_id"]))] = 3 if lid in (3, 9, 10, 11) else lid
    for team_id in relegated_to_segunda:
        targets[team_id] = 2
    for team_id in promoted_to_primera:
        targets[team_id] = 1
    for team_id in lower.relegated_from_segunda:
        targets[team_id] = 3  # category-level marker; regional allocation occurs at fixture build
    for team_id in lower.promoted_to_segunda:
        targets[team_id] = 2
    for team_id in lower.relegated_to_tercera:
        targets[team_id] = 4
    _validate_family_separation(universe, targets)

    return SpainPyramidSeason9394(
        primera_table=primera_table,
        segunda_table=segunda_table,
        segundab=lower,
        direct_promoted_to_primera=direct_up,
        promotion_ties=ties,
        promoted_to_primera=promoted_to_primera,
        relegated_to_segunda=relegated_to_segunda,
        promoted_to_segunda=lower.promoted_to_segunda,
        relegated_to_segundab=lower.relegated_from_segunda,
        primera_matches=primera.played_matches,
        segunda_matches=segunda_probe.played_matches,
        primera_segunda_playoff_matches=sum(t.matches for t in ties),
    )
