from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PendingDecider = Literal["replay", "extra_time_penalties", "extra_time", "penalties"]


@dataclass(frozen=True, slots=True)
class KnockoutRoundRules9394:
    name: str
    legs: Literal[1, 2]
    away_goals: bool = False
    replay_on_draw: bool = False
    extra_time: bool = True
    penalties: bool = True
    neutral_venue: bool = False

    def validate(self) -> None:
        if self.legs not in (1, 2):
            raise ValueError("una eliminatoria sólo puede declararse a uno o dos partidos")
        if self.away_goals and self.legs != 2:
            raise ValueError("el valor doble/factor de goles fuera sólo tiene sentido a doble partido")
        if self.replay_on_draw and self.legs != 1:
            raise ValueError("el replay sólo se admite aquí para rondas a partido único")
        if not self.replay_on_draw and not self.extra_time and not self.penalties:
            raise ValueError("la ronda no declara cómo resolver un empate")


@dataclass(frozen=True, slots=True)
class KnockoutLeg9394:
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
class KnockoutResolution9394:
    winner_team_id: str | None
    loser_team_id: str | None
    aggregate: tuple[int, int]
    away_goals: tuple[int, int]
    resolved_by: str | None
    pending_decider: PendingDecider | None = None


def resolve_knockout_tie(
    first_leg: KnockoutLeg9394,
    rules: KnockoutRoundRules9394,
    second_leg: KnockoutLeg9394 | None = None,
) -> KnockoutResolution9394:
    """Resolve only what the declared historical round rules actually resolve.

    If regulation/aggregate does not determine a winner, the function returns
    `pending_decider` instead of inventing a modern penalty shootout or replay.
    The caller must then play the historically declared decider.
    """

    rules.validate()
    team_a = first_leg.home_team_id
    team_b = first_leg.away_team_id

    if rules.legs == 1:
        if second_leg is not None:
            raise ValueError("una ronda a partido único no acepta segundo partido")
        a_goals, b_goals = first_leg.home_goals, first_leg.away_goals
        if a_goals != b_goals:
            winner, loser = (team_a, team_b) if a_goals > b_goals else (team_b, team_a)
            return KnockoutResolution9394(winner, loser, (a_goals, b_goals), (0, 0), "single_leg")
        if rules.replay_on_draw:
            pending: PendingDecider = "replay"
        elif rules.extra_time and rules.penalties:
            pending = "extra_time_penalties"
        elif rules.extra_time:
            pending = "extra_time"
        else:
            pending = "penalties"
        return KnockoutResolution9394(None, None, (a_goals, b_goals), (0, 0), None, pending)

    if second_leg is None:
        raise ValueError("una ronda a doble partido necesita segundo partido")
    if second_leg.home_team_id != team_b or second_leg.away_team_id != team_a:
        raise ValueError("el segundo partido debe invertir local y visitante")

    a_aggregate = first_leg.home_goals + second_leg.away_goals
    b_aggregate = first_leg.away_goals + second_leg.home_goals
    a_away = second_leg.away_goals
    b_away = first_leg.away_goals

    if a_aggregate != b_aggregate:
        winner, loser = (team_a, team_b) if a_aggregate > b_aggregate else (team_b, team_a)
        return KnockoutResolution9394(winner, loser, (a_aggregate, b_aggregate), (a_away, b_away), "aggregate")

    if rules.away_goals and a_away != b_away:
        winner, loser = (team_a, team_b) if a_away > b_away else (team_b, team_a)
        return KnockoutResolution9394(winner, loser, (a_aggregate, b_aggregate), (a_away, b_away), "away_goals")

    pending: PendingDecider
    if rules.extra_time and rules.penalties:
        pending = "extra_time_penalties"
    elif rules.extra_time:
        pending = "extra_time"
    else:
        pending = "penalties"
    return KnockoutResolution9394(None, None, (a_aggregate, b_aggregate), (a_away, b_away), None, pending)
