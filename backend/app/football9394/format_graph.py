from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

GraphStageKind9394 = Literal[
    "league", "group", "knockout", "final", "championship", "promotion_playoff", "qualifying"
]


@dataclass(frozen=True, slots=True)
class FormatStageNode9394:
    id: str
    name: str
    kind: GraphStageKind9394
    entrants: int
    qualifiers: int
    group_count: int = 1
    round_robin_cycles: int | None = None
    scoring_system_id: str | None = None
    legs_per_tie: int | None = None
    away_goals: bool | None = None
    extra_time: bool | None = None
    penalties: bool | None = None
    neutral_venue: bool | None = None
    rounds: int | None = None
    qualification_policy: str = "table_order"
    relegation_policy: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.entrants < 2:
            raise ValueError(f"{self.id}: entrants debe ser >= 2")
        if not 1 <= self.qualifiers <= self.entrants:
            raise ValueError(f"{self.id}: qualifiers fuera de rango")
        if self.group_count < 1 or self.entrants % self.group_count:
            raise ValueError(f"{self.id}: grupos incompatibles con entrants")
        if self.kind in {"league", "group"}:
            if not self.round_robin_cycles or self.round_robin_cycles < 1:
                raise ValueError(f"{self.id}: fase de liga/grupo sin ciclos")
            if not self.scoring_system_id:
                raise ValueError(f"{self.id}: fase de liga/grupo sin scoring_system_id")
        if self.kind in {"knockout", "final", "championship", "promotion_playoff", "qualifying"}:
            if self.legs_per_tie not in (1, 2):
                raise ValueError(f"{self.id}: eliminatoria sin número de partidos")
            if None in (self.away_goals, self.extra_time, self.penalties, self.neutral_venue):
                raise ValueError(f"{self.id}: resolución de eliminatoria incompleta")


@dataclass(frozen=True, slots=True)
class FormatTransition9394:
    source: str
    target: str
    slots: int

    def validate(self) -> None:
        if self.slots < 1:
            raise ValueError("una transición necesita al menos una plaza")
        if self.source == self.target:
            raise ValueError("una fase no puede alimentarse a sí misma")


@dataclass(frozen=True, slots=True)
class CompetitionFormatGraph9394:
    competition_id: str
    season: str
    stages: tuple[FormatStageNode9394, ...]
    transitions: tuple[FormatTransition9394, ...]
    champion_stage_id: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.season != "1993-94":
            raise ValueError("este grafo sólo admite temporada 1993-94")
        if not self.stages:
            raise ValueError(f"{self.competition_id}: sin fases")
        stage_by_id = {stage.id: stage for stage in self.stages}
        if len(stage_by_id) != len(self.stages):
            raise ValueError(f"{self.competition_id}: ids de fase duplicados")
        if self.champion_stage_id not in stage_by_id:
            raise ValueError(f"{self.competition_id}: fase campeona inexistente")
        incoming = {stage.id: 0 for stage in self.stages}
        outgoing = {stage.id: 0 for stage in self.stages}
        for stage in self.stages:
            stage.validate()
        for transition in self.transitions:
            transition.validate()
            if transition.source not in stage_by_id or transition.target not in stage_by_id:
                raise ValueError(f"{self.competition_id}: transición con fase desconocida")
            outgoing[transition.source] += transition.slots
            incoming[transition.target] += transition.slots
        for stage in self.stages:
            if incoming[stage.id] and incoming[stage.id] != stage.entrants:
                raise ValueError(
                    f"{self.competition_id}: {stage.id} recibe {incoming[stage.id]} plazas, espera {stage.entrants}"
                )
            if outgoing[stage.id] > stage.qualifiers:
                raise ValueError(
                    f"{self.competition_id}: {stage.id} reparte {outgoing[stage.id]} plazas, sólo clasifica {stage.qualifiers}"
                )
