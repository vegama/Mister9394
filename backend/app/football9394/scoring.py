from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RankingBasis9394 = Literal["points", "wins"]
DecisionKind9394 = Literal[
    "regulation_win", "extra_time_win", "shootout_win", "draw", "loss", "shootout_loss"
]


@dataclass(frozen=True, slots=True)
class LeagueScoringRules9394:
    """Historical league scoring, including non-standard 1993 systems."""

    id: str
    ranking_basis: RankingBasis9394 = "points"
    regulation_win_points: int = 2
    draw_points: int = 1
    loss_points: int = 0
    extra_time_win_points: int | None = None
    shootout_win_points: int | None = None
    shootout_loss_points: int | None = None
    goal_bonus_per_goal: int = 0
    goal_bonus_cap: int = 0
    draws_allowed: bool = True
    extra_time_on_draw: bool = False
    shootout_after_extra_time: bool = False

    def validate(self) -> None:
        if self.ranking_basis not in ("points", "wins"):
            raise ValueError(f"{self.id}: ranking_basis inválido")
        for value in (
            self.regulation_win_points, self.draw_points, self.loss_points,
            self.goal_bonus_per_goal, self.goal_bonus_cap,
        ):
            if value < 0:
                raise ValueError(f"{self.id}: la puntuación no puede ser negativa")
        if self.shootout_after_extra_time and not self.extra_time_on_draw:
            raise ValueError(f"{self.id}: no puede haber shootout tras prórroga sin prórroga")
        if not self.draws_allowed and not (self.extra_time_on_draw or self.shootout_win_points is not None):
            raise ValueError(f"{self.id}: sin empates debe declarar cómo decidir el partido")

    def points_for(self, decision: DecisionKind9394, *, goals_scored: int = 0) -> int:
        if goals_scored < 0:
            raise ValueError("goals_scored no puede ser negativo")
        if decision == "regulation_win":
            base = self.regulation_win_points
        elif decision == "extra_time_win":
            base = self.extra_time_win_points if self.extra_time_win_points is not None else self.regulation_win_points
        elif decision == "shootout_win":
            if self.shootout_win_points is None:
                raise ValueError(f"{self.id}: no declara puntuación de victoria por shootout")
            base = self.shootout_win_points
        elif decision == "shootout_loss":
            if self.shootout_loss_points is None:
                raise ValueError(f"{self.id}: no declara puntuación de derrota por shootout")
            base = self.shootout_loss_points
        elif decision == "draw":
            if not self.draws_allowed:
                raise ValueError(f"{self.id}: esta competición no admite empates")
            base = self.draw_points
        elif decision == "loss":
            base = self.loss_points
        else:  # pragma: no cover - Literal guard for external/untyped callers
            raise ValueError(f"decisión desconocida: {decision}")
        bonus = self.goal_bonus_per_goal * min(goals_scored, self.goal_bonus_cap)
        return base + bonus


STANDARD_2_1_0_9394 = LeagueScoringRules9394(id="standard_2_1_0")
STANDARD_3_1_0_9394 = LeagueScoringRules9394(
    id="standard_3_1_0", regulation_win_points=3, draw_points=1, loss_points=0
)

# 1993 APSL: 6 for a normal/extra-time win, 4 shootout win, 2 shootout loss,
# plus one bonus point per goal up to three.
APSL_1993 = LeagueScoringRules9394(
    id="apsl_1993",
    regulation_win_points=6,
    draw_points=0,
    loss_points=0,
    extra_time_win_points=6,
    shootout_win_points=4,
    shootout_loss_points=2,
    goal_bonus_per_goal=1,
    goal_bonus_cap=3,
    draws_allowed=False,
    extra_time_on_draw=True,
    shootout_after_extra_time=True,
)

# Inaugural J.League: every match produced a winner; table position was based
# on victories, irrespective of whether the win arrived in regulation, golden
# goal extra time or penalties.  Points are deliberately not used for ranking.
JLEAGUE_1993 = LeagueScoringRules9394(
    id="jleague_1993_wins",
    ranking_basis="wins",
    regulation_win_points=0,
    draw_points=0,
    loss_points=0,
    extra_time_win_points=0,
    shootout_win_points=0,
    shootout_loss_points=0,
    draws_allowed=False,
    extra_time_on_draw=True,
    shootout_after_extra_time=True,
)

for _rules in (STANDARD_2_1_0_9394, STANDARD_3_1_0_9394, APSL_1993, JLEAGUE_1993):
    _rules.validate()
