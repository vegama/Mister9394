from __future__ import annotations

"""Season-end historical decisions that cannot be represented by table sorting.

Italian 1993-94 competitions are the motivating case: an ordinary points tie
was ordered via classifica avulsa, but a tie crossing a decisive title,
promotion or relegation boundary triggered a neutral playoff.  Keeping this
outside the table prevents a generic ranking function from inventing a modern
criterion or scheduling playoffs for harmless mid-table ties.
"""

from dataclasses import dataclass
from random import Random
from typing import Sequence

from .match_engine import FootballMatchEngine9394, TeamSheet9394
from .rules import CompetitionRules9394, DecisiveTieContext
from .standings import StandingRow9394


@dataclass(frozen=True, slots=True)
class DecisivePlayoffNeed9394:
    context: DecisiveTieContext
    cutoff_position: int
    upper_team_id: str
    lower_team_id: str
    points: int


@dataclass(frozen=True, slots=True)
class DecisivePlayoffResult9394:
    need: DecisivePlayoffNeed9394
    winner_team_id: str
    loser_team_id: str
    regulation_score: tuple[int, int]
    decided_by: str


def identify_decisive_playoff(
    table: Sequence[StandingRow9394],
    rules: CompetitionRules9394,
    *,
    context: DecisiveTieContext,
    cutoff_position: int,
) -> DecisivePlayoffNeed9394 | None:
    if context not in rules.decisive_playoff_contexts:
        return None
    if cutoff_position < 1 or cutoff_position >= len(table):
        raise ValueError("el corte decisivo debe separar dos posiciones de la tabla")
    upper, lower = table[cutoff_position - 1], table[cutoff_position]
    if upper.points != lower.points:
        return None
    return DecisivePlayoffNeed9394(context, cutoff_position, upper.team_id, lower.team_id, upper.points)


def season_end_decisive_playoffs(
    table: Sequence[StandingRow9394], rules: CompetitionRules9394,
) -> tuple[DecisivePlayoffNeed9394, ...]:
    needs: list[DecisivePlayoffNeed9394] = []
    if "champion" in rules.decisive_playoff_contexts:
        need = identify_decisive_playoff(table, rules, context="champion", cutoff_position=1)
        if need: needs.append(need)
    if "promotion" in rules.decisive_playoff_contexts and rules.direct_promotion_places:
        cutoff = max(rules.direct_promotion_places)
        need = identify_decisive_playoff(table, rules, context="promotion", cutoff_position=cutoff)
        if need: needs.append(need)
    if "relegation" in rules.decisive_playoff_contexts and rules.direct_relegation_places:
        cutoff = min(rules.direct_relegation_places) - 1
        need = identify_decisive_playoff(table, rules, context="relegation", cutoff_position=cutoff)
        if need: needs.append(need)
    return tuple(needs)


def play_neutral_decisive_playoff(
    need: DecisivePlayoffNeed9394,
    team_sheets: dict[str, TeamSheet9394],
    engine: FootballMatchEngine9394,
    *,
    seed: int,
) -> DecisivePlayoffResult9394:
    upper, lower = team_sheets[need.upper_team_id], team_sheets[need.lower_team_id]
    result = engine.simulate(upper, lower, seed=seed)
    hg, ag = result.home.goals, result.away.goals
    if hg != ag:
        winner = upper.team_id if hg > ag else lower.team_id
        loser = lower.team_id if winner == upper.team_id else upper.team_id
        return DecisivePlayoffResult9394(need, winner, loser, (hg, ag), "regulation")
    # Historical rule requires a decision. The coarse match engine has no
    # extra-time clock yet; resolve the declared ET/penalty decider using team
    # strength instead of leaving the season in an impossible tied state.
    rng = Random(seed ^ 0x1A71994)
    upper_level = sum(p.overall for p in upper.starters) / len(upper.starters)
    lower_level = sum(p.overall for p in lower.starters) / len(lower.starters)
    p_upper = max(.35, min(.65, .5 + (upper_level-lower_level)/140))
    winner = upper.team_id if rng.random() < p_upper else lower.team_id
    loser = lower.team_id if winner == upper.team_id else upper.team_id
    return DecisivePlayoffResult9394(need, winner, loser, (hg, ag), "extra_time_penalties")


@dataclass(frozen=True, slots=True)
class SeasonDecisionResolution9394:
    table: tuple[StandingRow9394, ...]
    playoffs: tuple[DecisivePlayoffResult9394, ...]


def resolve_season_end_decisive_playoffs(
    table: Sequence[StandingRow9394],
    rules: CompetitionRules9394,
    team_sheets: dict[str, TeamSheet9394],
    engine: FootballMatchEngine9394,
    *,
    seed_base: int = 939400,
) -> SeasonDecisionResolution9394:
    """Play every declared decisive spareggio and apply it to final positions.

    Ordinary equal-points ordering remains the table's classifica-avulsa order.
    Only a tie that crosses a historically decisive boundary is overwritten by
    the neutral playoff result.  This keeps Italy 1993-94 from either inventing
    a modern tiebreak or scheduling meaningless mid-table playoffs.
    """
    mutable = list(table)
    results: list[DecisivePlayoffResult9394] = []
    needs = season_end_decisive_playoffs(tuple(mutable), rules)
    for index, need in enumerate(needs):
        result = play_neutral_decisive_playoff(need, team_sheets, engine, seed=seed_base + index)
        results.append(result)
        upper_index = need.cutoff_position - 1
        lower_index = need.cutoff_position
        upper = mutable[upper_index]
        lower = mutable[lower_index]
        if result.winner_team_id == lower.team_id:
            mutable[upper_index], mutable[lower_index] = lower, upper
    mutable = [
        StandingRow9394(
            team_id=row.team_id, played=row.played, wins=row.wins, draws=row.draws, losses=row.losses,
            goals_for=row.goals_for, goals_against=row.goals_against, points=row.points,
            position=position, requires_playoff=False,
        )
        for position, row in enumerate(mutable, start=1)
    ]
    return SeasonDecisionResolution9394(tuple(mutable), tuple(results))
