from __future__ import annotations

"""Executable Primera División de México 1993-94.

The historical competition was not four independent leagues: all twenty clubs
played a 38-match double round robin while four five-team groups decided the
nominal eight liguilla places.  Up to two better-ranked outsiders could force a
reclassification against vulnerable group runners-up.  Post-season ties were
home/away, used away goals, then extra time / penalties.  Relegation was the
lowest three-season points-per-match coefficient.
"""

from dataclasses import dataclass, replace
from random import Random
from typing import Iterable

from .competition_runtime import build_simple_source_league
from .knockout import KnockoutLeg9394, KnockoutRoundRules9394, resolve_knockout_tie
from .match_engine import MatchResult9394, TeamSheet9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import StandingRow9394


MEXICO_GROUPS_1993_94: tuple[tuple[int, ...], ...] = (
    (394, 1586, 1579, 832, 1585),       # Santos, Necaxa, Puebla, Tigres, U de G
    (1020, 1583, 927, 1438, 1490),      # Atlante, Morelia, Pumas, León, Querétaro
    (929, 928, 833, 1581, 2343),        # Cruz Azul, Toluca, América, Veracruz, Correcaminos
    (2341, 1584, 1580, 775, 2342),      # Tecos, Atlas, Guadalajara, Monterrey, Toros
)

# Authoritative points/matches entering 1993-94 from the previous two seasons.
# Toros Hidalgo/UT Neza were promoted for 1993-94, so their coefficient starts
# with only the current season instead of inventing historical top-flight games.
MEXICO_PRIOR_COEFFICIENT_CONTEXT_1993_94: dict[int, tuple[int, int]] = {
    394: (62, 76), 775: (82, 76), 832: (83, 76), 833: (87, 76),
    927: (88, 76), 928: (70, 76), 929: (88, 76), 1020: (91, 76),
    1438: (92, 76), 1490: (58, 76), 1579: (84, 76), 1580: (78, 76),
    1581: (77, 76), 1583: (65, 76), 1584: (72, 76), 1585: (57, 76),
    1586: (100, 76), 2341: (75, 76), 2342: (0, 0), 2343: (64, 76),
}


@dataclass(frozen=True, slots=True)
class MexicoCoefficient9394:
    team_id: str
    prior_points: int
    prior_matches: int
    season_points: int
    season_matches: int
    coefficient: float


@dataclass(frozen=True, slots=True)
class MexicoKnockoutTie9394:
    round_name: str
    higher_seed_team_id: str
    lower_seed_team_id: str
    first_leg: KnockoutLeg9394
    second_leg: KnockoutLeg9394
    winner_team_id: str
    loser_team_id: str
    resolved_by: str


@dataclass(frozen=True, slots=True)
class MexicoSeason9394:
    regular_table: tuple[StandingRow9394, ...]
    group_tables: tuple[tuple[StandingRow9394, ...], ...]
    reclassification_ties: tuple[MexicoKnockoutTie9394, ...]
    quarterfinal_ties: tuple[MexicoKnockoutTie9394, ...]
    semifinal_ties: tuple[MexicoKnockoutTie9394, ...]
    final_tie: MexicoKnockoutTie9394
    champion_team_id: str
    runner_up_team_id: str
    relegation_coefficients: tuple[MexicoCoefficient9394, ...]
    relegated_team_id: str
    regular_matches: int

    @property
    def postseason_matches(self) -> int:
        return 2 * (
            len(self.reclassification_ties)
            + len(self.quarterfinal_ties)
            + len(self.semifinal_ties)
            + 1
        )


_KNOCKOUT_RULES = KnockoutRoundRules9394(
    name="México 1993-94 · ida/vuelta",
    legs=2,
    away_goals=True,
    extra_time=True,
    penalties=True,
)


def _team_level(sheet: TeamSheet9394) -> float:
    return sum(player.overall for player in sheet.starters) / max(1, len(sheet.starters))


def _leg(result: MatchResult9394) -> KnockoutLeg9394:
    return KnockoutLeg9394(
        result.home_team_id,
        result.away_team_id,
        result.home.goals,
        result.away.goals,
    )


def _pending_decider(
    higher: TeamSheet9394,
    lower: TeamSheet9394,
    *,
    seed: int,
    pending: str,
) -> tuple[str, str, str]:
    """Resolve the historically declared extra-time/penalty decider.

    The coarse 90-minute engine does not yet have an extra-time clock.  The
    decider is therefore strength-weighted and deterministic by seed; it is
    never silently treated as a higher-seed or modern-table advantage.
    """
    rng = Random(seed ^ 0x4D45583934)
    delta = _team_level(higher) - _team_level(lower)
    p_higher = max(.34, min(.66, .5 + delta / 135.0))
    winner = higher.team_id if rng.random() < p_higher else lower.team_id
    loser = lower.team_id if winner == higher.team_id else higher.team_id
    return winner, loser, pending


def _play_two_leg_tie(
    higher_seed_team_id: str,
    lower_seed_team_id: str,
    sheets: dict[str, TeamSheet9394],
    engine,
    *,
    seed: int,
    round_name: str,
) -> MexicoKnockoutTie9394:
    higher = sheets[higher_seed_team_id]
    lower = sheets[lower_seed_team_id]
    # The better regular-season seed receives the second leg.
    first_result = engine.simulate(lower, higher, seed=seed)
    second_result = engine.simulate(higher, lower, seed=seed + 1)
    first = _leg(first_result)
    second = _leg(second_result)
    resolution = resolve_knockout_tie(first, _KNOCKOUT_RULES, second)
    if resolution.winner_team_id is None:
        winner, loser, resolved_by = _pending_decider(
            higher, lower, seed=seed + 2, pending=resolution.pending_decider or "extra_time_penalties"
        )
    else:
        winner = resolution.winner_team_id
        loser = resolution.loser_team_id
        resolved_by = resolution.resolved_by or "aggregate"
    return MexicoKnockoutTie9394(
        round_name=round_name,
        higher_seed_team_id=higher.team_id,
        lower_seed_team_id=lower.team_id,
        first_leg=first,
        second_leg=second,
        winner_team_id=winner,
        loser_team_id=loser,
        resolved_by=resolved_by,
    )


def _group_tables(table: tuple[StandingRow9394, ...]) -> tuple[tuple[StandingRow9394, ...], ...]:
    by_id = {int(row.team_id): row for row in table}
    ranking = {int(row.team_id): row.position for row in table}
    groups: list[tuple[StandingRow9394, ...]] = []
    for group in MEXICO_GROUPS_1993_94:
        missing = [team_id for team_id in group if team_id not in by_id]
        if missing:
            raise ValueError(f"México 1993-94: faltan clubes de grupo en snapshot: {missing}")
        rows = sorted((by_id[team_id] for team_id in group), key=lambda row: ranking[int(row.team_id)])
        groups.append(tuple(replace(row, position=index) for index, row in enumerate(rows, 1)))
    return tuple(groups)


def _reclassification_pairs(
    table: tuple[StandingRow9394, ...],
    groups: tuple[tuple[StandingRow9394, ...], ...],
) -> tuple[tuple[str, str], ...]:
    """Return higher/lower overall seeds for up to two reclassification ties."""
    overall_position = {row.team_id: row.position for row in table}
    group_of: dict[str, int] = {}
    for group_index, group in enumerate(groups):
        for row in group:
            group_of[row.team_id] = group_index

    runners = [group[1] for group in groups]
    nominal = {row.team_id for group in groups for row in group[:2]}
    outsiders = [row for row in table if row.team_id not in nominal]

    # Challenge the weakest eligible group runners first, with at most two
    # reclassification series in this historical format.
    challenged: set[str] = set()
    challengers: list[str] = []
    for outsider in outsiders:
        eligible = [
            runner for runner in runners
            if runner.team_id not in challenged
            and group_of[runner.team_id] != group_of[outsider.team_id]
            and outsider.points > runner.points
        ]
        if not eligible:
            continue
        vulnerable = sorted(eligible, key=lambda row: (row.points, -row.position))[0]
        challenged.add(vulnerable.team_id)
        challengers.append(outsider.team_id)
        if len(challengers) == 2:
            break

    if not challengers:
        return ()
    involved = challengers + list(challenged)
    involved.sort(key=lambda team_id: overall_position[team_id])
    pairs: list[tuple[str, str]] = []
    while involved:
        high = involved.pop(0)
        low = involved.pop(-1)
        pairs.append((high, low))
    return tuple(pairs)


def mexico_relegation_coefficients(
    table: Iterable[StandingRow9394],
) -> tuple[MexicoCoefficient9394, ...]:
    rows = tuple(table)
    found_ids = {int(row.team_id) for row in rows}
    expected_ids = set(MEXICO_PRIOR_COEFFICIENT_CONTEXT_1993_94)
    if found_ids != expected_ids:
        missing = sorted(expected_ids - found_ids)
        extra = sorted(found_ids - expected_ids)
        raise ValueError(f"México 1993-94: universo de cociente inesperado; faltan={missing}, sobran={extra}")
    coefficients: list[MexicoCoefficient9394] = []
    for row in rows:
        team_id = int(row.team_id)
        prior_points, prior_matches = MEXICO_PRIOR_COEFFICIENT_CONTEXT_1993_94[team_id]
        total_matches = prior_matches + row.played
        coefficient = (prior_points + row.points) / total_matches
        coefficients.append(MexicoCoefficient9394(
            team_id=row.team_id,
            prior_points=prior_points,
            prior_matches=prior_matches,
            season_points=row.points,
            season_matches=row.played,
            coefficient=coefficient,
        ))
    # Best coefficient first, relegated club last.  Exact ties remain explicit
    # via current-season table order rather than an invented modern rule.
    current_position = {row.team_id: row.position for row in rows}
    coefficients.sort(key=lambda item: (-item.coefficient, current_position[item.team_id]))
    return tuple(coefficients)


def simulate_mexico_1993_94(
    *,
    seed_base: int = 409394,
    universe: FootballUniverseSnapshot9394 | None = None,
) -> MexicoSeason9394:
    universe = universe or default_runtime_snapshot()
    season = build_simple_source_league(40, universe=universe)
    season.play_all(seed_base=seed_base)
    table = season.table()
    if len(table) != 20 or any(row.played != 38 for row in table):
        raise RuntimeError("México 1993-94 no cerró la fase regular de 20 clubes / 38 partidos")

    groups = _group_tables(table)
    sheets = dict(season.team_sheets)
    overall_position = {row.team_id: row.position for row in table}

    reclass_pairs = _reclassification_pairs(table, groups)
    reclass_ties: list[MexicoKnockoutTie9394] = []
    seed_cursor = seed_base + 50000
    for index, (high, low) in enumerate(reclass_pairs):
        reclass_ties.append(_play_two_leg_tie(
            high, low, sheets, season.match_engine,
            seed=seed_cursor + index * 10, round_name="Reclasificación",
        ))

    challenged = {team_id for pair in reclass_pairs for team_id in pair}
    qualified = [row.team_id for group in groups for row in group[:2] if row.team_id not in challenged]
    qualified.extend(tie.winner_team_id for tie in reclass_ties)
    if len(set(qualified)) != 8:
        raise RuntimeError(f"México 1993-94: la reclasificación produjo {len(set(qualified))} clasificados, no 8")
    seeded = sorted(set(qualified), key=lambda team_id: overall_position[team_id])
    seed_rank = {team_id: index + 1 for index, team_id in enumerate(seeded)}

    quarter_pairs = tuple((seeded[i], seeded[-1-i]) for i in range(4))
    quarterfinals = tuple(
        _play_two_leg_tie(high, low, sheets, season.match_engine,
                          seed=seed_base + 60000 + index * 10, round_name="Cuartos de final")
        for index, (high, low) in enumerate(quarter_pairs)
    )

    semifinal_pairs = (
        (quarterfinals[0].winner_team_id, quarterfinals[1].winner_team_id),
        (quarterfinals[2].winner_team_id, quarterfinals[3].winner_team_id),
    )
    semifinals: list[MexicoKnockoutTie9394] = []
    for index, (a, b) in enumerate(semifinal_pairs):
        high, low = (a, b) if seed_rank[a] < seed_rank[b] else (b, a)
        semifinals.append(_play_two_leg_tie(
            high, low, sheets, season.match_engine,
            seed=seed_base + 70000 + index * 10, round_name="Semifinales",
        ))

    a, b = semifinals[0].winner_team_id, semifinals[1].winner_team_id
    high, low = (a, b) if seed_rank[a] < seed_rank[b] else (b, a)
    final = _play_two_leg_tie(
        high, low, sheets, season.match_engine, seed=seed_base + 80000, round_name="Final"
    )

    coefficients = mexico_relegation_coefficients(table)
    return MexicoSeason9394(
        regular_table=table,
        group_tables=groups,
        reclassification_ties=tuple(reclass_ties),
        quarterfinal_ties=quarterfinals,
        semifinal_ties=tuple(semifinals),
        final_tie=final,
        champion_team_id=final.winner_team_id,
        runner_up_team_id=final.loser_team_id,
        relegation_coefficients=coefficients,
        relegated_team_id=coefficients[-1].team_id,
        regular_matches=season.played_matches,
    )
