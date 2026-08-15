from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .rules import CompetitionRules9394


@dataclass(frozen=True, slots=True)
class LeagueMatch9394:
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int

    def __post_init__(self) -> None:
        if self.home_team_id == self.away_team_id:
            raise ValueError("un equipo no puede jugar contra sí mismo")
        if self.home_goals < 0 or self.away_goals < 0:
            raise ValueError("los goles no pueden ser negativos")


@dataclass(frozen=True, slots=True)
class StandingRow9394:
    team_id: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    position: int = 0
    requires_playoff: bool = False

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


@dataclass(slots=True)
class _MutableRow:
    team_id: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    def freeze(self, *, position: int = 0, requires_playoff: bool = False) -> StandingRow9394:
        return StandingRow9394(
            team_id=self.team_id,
            played=self.played,
            wins=self.wins,
            draws=self.draws,
            losses=self.losses,
            goals_for=self.goals_for,
            goals_against=self.goals_against,
            points=self.points,
            position=position,
            requires_playoff=requires_playoff,
        )


def _apply_match(row: _MutableRow, goals_for: int, goals_against: int, rules: CompetitionRules9394) -> None:
    row.played += 1
    row.goals_for += goals_for
    row.goals_against += goals_against
    if goals_for > goals_against:
        row.wins += 1
        row.points += int(rules.points_win)
    elif goals_for == goals_against:
        row.draws += 1
        row.points += int(rules.points_draw)
    else:
        row.losses += 1
        row.points += int(rules.points_loss)


def _mini_table(
    tied_ids: Sequence[str],
    matches: Sequence[LeagueMatch9394],
    rules: CompetitionRules9394,
) -> dict[str, _MutableRow]:
    tied = set(tied_ids)
    rows = {team_id: _MutableRow(team_id) for team_id in tied_ids}
    for match in matches:
        if match.home_team_id not in tied or match.away_team_id not in tied:
            continue
        _apply_match(rows[match.home_team_id], match.home_goals, match.away_goals, rules)
        _apply_match(rows[match.away_team_id], match.away_goals, match.home_goals, rules)
    return rows


def _split_by_value(ids: Sequence[str], values: dict[str, int], *, reverse: bool = True) -> list[list[str]]:
    ordered = sorted(ids, key=lambda team_id: values[team_id], reverse=reverse)
    groups: list[list[str]] = []
    previous: int | None = None
    for team_id in ordered:
        value = values[team_id]
        if not groups or previous != value:
            groups.append([team_id])
        else:
            groups[-1].append(team_id)
        previous = value
    return groups


def _resolve_tied_group(
    tied_ids: Sequence[str],
    rows: dict[str, _MutableRow],
    matches: Sequence[LeagueMatch9394],
    rules: CompetitionRules9394,
) -> tuple[list[str], set[str]]:
    """Resolve one points-tied group using only this competition's rule order.

    Head-to-head criteria are calculated as a mini-league containing only the
    tied clubs.  If all declared numerical criteria are exhausted and the
    ruleset declares a playoff, the unresolved clubs are kept in stable input
    order and marked `requires_playoff`; the caller can then schedule that
    historical decider rather than silently applying an extra modern rule.
    """

    groups: list[list[str]] = [list(tied_ids)]
    mini: dict[str, _MutableRow] | None = None

    for criterion in rules.tie_breakers:
        if criterion == "playoff":
            unresolved = {team_id for group in groups if len(group) > 1 for team_id in group}
            return [team_id for group in groups for team_id in group], unresolved

        next_groups: list[list[str]] = []
        for group in groups:
            if len(group) <= 1:
                next_groups.append(group)
                continue

            if criterion.startswith("head_to_head"):
                # Recompute the mini-table for the *current* subgroup. This is
                # important when one criterion splits a three-way tie and the
                # historical next criterion must be applied among the clubs
                # that remain tied.
                mini = _mini_table(group, matches, rules)
                if criterion == "head_to_head_points":
                    values = {team_id: mini[team_id].points for team_id in group}
                elif criterion == "head_to_head_goal_difference":
                    values = {team_id: mini[team_id].goals_for - mini[team_id].goals_against for team_id in group}
                else:  # defensive guard for future Literal extensions
                    raise ValueError(f"desempate no implementado: {criterion}")
            elif criterion == "overall_wins":
                values = {team_id: rows[team_id].wins for team_id in group}
            elif criterion == "overall_goal_difference":
                values = {team_id: rows[team_id].goals_for - rows[team_id].goals_against for team_id in group}
            elif criterion == "overall_goals_scored":
                values = {team_id: rows[team_id].goals_for for team_id in group}
            elif criterion == "overall_goals_against":
                values = {team_id: rows[team_id].goals_against for team_id in group}
                next_groups.extend(_split_by_value(group, values, reverse=False))
                continue
            elif criterion in {"overall_away_goals_scored", "overall_away_goals_against"}:
                # These location-sensitive historical criteria are resolved by
                # runtimes that retain home/away splits (Colombia 1993).  The
                # generic compact standings object deliberately does not invent them.
                next_groups.append(group)
                continue
            else:
                raise ValueError(f"desempate no implementado: {criterion}")

            next_groups.extend(_split_by_value(group, values, reverse=True))
        groups = next_groups
        if all(len(group) == 1 for group in groups):
            return [group[0] for group in groups], set()

    # No undeclared fallback.  A ruleset without a final resolver leaves the
    # tie visible for the competition audit instead of inventing a criterion.
    unresolved = {team_id for group in groups if len(group) > 1 for team_id in group}
    return [team_id for group in groups for team_id in group], unresolved


def build_league_table(
    team_ids: Iterable[str],
    matches: Iterable[LeagueMatch9394],
    rules: CompetitionRules9394,
) -> tuple[StandingRow9394, ...]:
    """Build a historical league table with the ruleset's own scoring/ties."""

    rules.validate()
    if rules.competition_type != "league":
        raise ValueError(f"{rules.id}: no es una competición de liga")

    ordered_ids = list(dict.fromkeys(str(team_id) for team_id in team_ids))
    if not ordered_ids:
        return ()
    rows = {team_id: _MutableRow(team_id) for team_id in ordered_ids}
    match_list = tuple(matches)

    for match in match_list:
        if match.home_team_id not in rows or match.away_team_id not in rows:
            raise ValueError("el partido contiene un equipo ajeno a la competición")
        _apply_match(rows[match.home_team_id], match.home_goals, match.away_goals, rules)
        _apply_match(rows[match.away_team_id], match.away_goals, match.home_goals, rules)

    by_points = _split_by_value(ordered_ids, {team_id: rows[team_id].points for team_id in ordered_ids})
    ranking: list[str] = []
    playoff_ids: set[str] = set()
    for group in by_points:
        if len(group) == 1:
            ranking.extend(group)
            continue
        resolved, unresolved = _resolve_tied_group(group, rows, match_list, rules)
        ranking.extend(resolved)
        playoff_ids.update(unresolved)

    return tuple(
        rows[team_id].freeze(position=index, requires_playoff=team_id in playoff_ids)
        for index, team_id in enumerate(ranking, start=1)
    )
