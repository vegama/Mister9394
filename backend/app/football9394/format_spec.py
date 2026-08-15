from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

StageKind = Literal["league", "group", "knockout", "final", "promotion_playoff", "qualifying"]


@dataclass(frozen=True, slots=True)
class CompetitionStageRules9394:
    """One explicit historical stage; there are intentionally no modern defaults."""

    id: str
    name: str
    kind: StageKind
    entrants: int
    qualifiers: int
    legs_per_tie: int | None = None
    round_robin_cycles: int | None = None
    points_win: int | None = None
    points_draw: int | None = None
    points_loss: int | None = None
    away_goals: bool | None = None
    replay_on_draw: bool | None = None
    extra_time: bool | None = None
    penalties: bool | None = None
    neutral_venue: bool | None = None

    def validate(self) -> None:
        if self.entrants < 2:
            raise ValueError(f"{self.id}: entrants debe ser >= 2")
        if not 1 <= self.qualifiers <= self.entrants:
            raise ValueError(f"{self.id}: qualifiers fuera de rango")
        if self.kind in {"league", "group"}:
            if self.round_robin_cycles is None or self.round_robin_cycles < 1:
                raise ValueError(f"{self.id}: fase de liga/grupo necesita ciclos explícitos")
            if None in (self.points_win, self.points_draw, self.points_loss):
                raise ValueError(f"{self.id}: fase de liga/grupo necesita puntuación explícita")
        if self.kind in {"knockout", "final", "promotion_playoff", "qualifying"}:
            if self.legs_per_tie not in (1, 2):
                raise ValueError(f"{self.id}: eliminatoria necesita legs_per_tie 1 o 2")
            if self.away_goals is None:
                raise ValueError(f"{self.id}: debe declarar explícitamente away_goals")
            if self.replay_on_draw is None or self.extra_time is None or self.penalties is None:
                raise ValueError(f"{self.id}: debe declarar explícitamente cómo resuelve empates")
            if self.neutral_venue is None:
                raise ValueError(f"{self.id}: debe declarar explícitamente neutral_venue")


@dataclass(frozen=True, slots=True)
class CompetitionFormatSpec9394:
    competition_id: str
    season: str
    stages: tuple[CompetitionStageRules9394, ...]

    def validate(self) -> None:
        if self.season != "1993-94":
            raise ValueError("este formato sólo admite temporada 1993-94")
        if not self.stages:
            raise ValueError(f"{self.competition_id}: formato sin fases")
        ids: set[str] = set()
        for stage in self.stages:
            stage.validate()
            if stage.id in ids:
                raise ValueError(f"{self.competition_id}: fase duplicada {stage.id}")
            ids.add(stage.id)
        for current, following in zip(self.stages, self.stages[1:]):
            if current.qualifiers != following.entrants:
                raise ValueError(
                    f"{self.competition_id}: {current.id} clasifica {current.qualifiers} pero {following.id} espera {following.entrants}"
                )
