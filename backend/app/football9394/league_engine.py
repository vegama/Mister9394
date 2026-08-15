from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .match_engine import FootballMatchEngine9394, MatchResult9394, TeamSheet9394
from .rules import CompetitionRules9394
from .schedule import LeagueFixture9394, generate_round_robin_cycles
from .standings import LeagueMatch9394, StandingRow9394, build_league_table


@dataclass(slots=True)
class LeagueSeason9394:
    rules: CompetitionRules9394
    team_sheets: Mapping[str, TeamSheet9394]
    match_engine: FootballMatchEngine9394
    fixtures: tuple[LeagueFixture9394, ...] = field(init=False)
    results: list[LeagueMatch9394] = field(default_factory=list)
    _played_fixture_ids: set[tuple[int, str, str]] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        self.rules.validate()
        if self.rules.competition_type != "league":
            raise ValueError("LeagueSeason9394 sólo admite ligas")
        team_ids = tuple(self.team_sheets)
        if self.rules.teams is not None and len(team_ids) != self.rules.teams:
            raise ValueError(f"{self.rules.id}: esperaba {self.rules.teams} equipos y recibió {len(team_ids)}")
        rounds_per_cycle = (len(team_ids) - 1) if len(team_ids) > 1 else 0
        if not rounds_per_cycle:
            cycles = 1
        elif self.rules.rounds is None:
            cycles = 2
        else:
            if self.rules.rounds % rounds_per_cycle:
                raise ValueError(
                    f"{self.rules.id}: {self.rules.rounds} jornadas no forman ciclos completos de {rounds_per_cycle}; "
                    "necesita un formato específico"
                )
            cycles = self.rules.rounds // rounds_per_cycle
            if cycles < 1:
                raise ValueError(f"{self.rules.id}: número de ciclos inválido")
        self.fixtures = generate_round_robin_cycles(team_ids, cycles)

    @property
    def played_matches(self) -> int:
        return len(self.results)

    @property
    def total_matches(self) -> int:
        return len(self.fixtures)

    def play_round(self, round_number: int, *, seed_base: int = 1) -> tuple[MatchResult9394, ...]:
        round_fixtures = [f for f in self.fixtures if f.round_number == round_number]
        outputs: list[MatchResult9394] = []
        for index, fixture in enumerate(round_fixtures):
            fixture_id = (fixture.round_number, fixture.home_team_id, fixture.away_team_id)
            if fixture_id in self._played_fixture_ids:
                continue
            result = self.match_engine.simulate(
                self.team_sheets[fixture.home_team_id],
                self.team_sheets[fixture.away_team_id],
                seed=seed_base + round_number * 100 + index,
            )
            self.results.append(
                LeagueMatch9394(
                    fixture.home_team_id,
                    fixture.away_team_id,
                    result.home.goals,
                    result.away.goals,
                )
            )
            self._played_fixture_ids.add(fixture_id)
            outputs.append(result)
        return tuple(outputs)

    def play_all(self, *, seed_base: int = 1) -> None:
        rounds = sorted({f.round_number for f in self.fixtures})
        for round_number in rounds:
            self.play_round(round_number, seed_base=seed_base)

    def table(self) -> tuple[StandingRow9394, ...]:
        return build_league_table(tuple(self.team_sheets), tuple(self.results), self.rules)

    def finalize_table(self, *, seed_base: int = 939400):
        """Resolve historical season-end deciders and return the official table."""
        from .season_decisions import resolve_season_end_decisive_playoffs
        return resolve_season_end_decisive_playoffs(
            self.table(), self.rules, dict(self.team_sheets), self.match_engine, seed_base=seed_base
        )
