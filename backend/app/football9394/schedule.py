from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Sequence


@dataclass(frozen=True, slots=True)
class LeagueFixture9394:
    round_number: int
    home_team_id: str
    away_team_id: str


def _single_round_robin(team_ids: Sequence[str]) -> tuple[LeagueFixture9394, ...]:
    teams = list(dict.fromkeys(str(team_id) for team_id in team_ids))
    if len(teams) != len(team_ids):
        raise ValueError("hay identificadores de equipo duplicados")
    if len(teams) < 2:
        return ()

    bye = None
    if len(teams) % 2:
        bye = "__BYE__"
        teams.append(bye)

    n = len(teams)
    rotating = teams[:]
    fixtures: list[LeagueFixture9394] = []
    for round_index in range(n - 1):
        pairs = [(rotating[i], rotating[n - 1 - i]) for i in range(n // 2)]
        for pair_index, (a, b) in enumerate(pairs):
            if bye in (a, b):
                continue
            if (round_index + pair_index) % 2:
                home, away = b, a
            else:
                home, away = a, b
            fixtures.append(LeagueFixture9394(round_index + 1, home, away))
        rotating = [rotating[0], rotating[-1], *rotating[1:-1]]
    return tuple(fixtures)


def generate_round_robin_cycles(team_ids: Sequence[str], cycles: int) -> tuple[LeagueFixture9394, ...]:
    """Generate one or more full round-robin cycles.

    This is required by historical formats such as Scotland 1993-94, where 12
    clubs met four times (44 matches each).  Odd cycles are supported too for
    split/single-round historical competitions.  Home venue is inverted on
    alternating cycles so even-cycle competitions remain perfectly balanced.
    """
    if cycles < 1:
        raise ValueError("cycles debe ser >= 1")
    teams = tuple(dict.fromkeys(str(team_id) for team_id in team_ids))
    if len(teams) != len(team_ids):
        raise ValueError("hay identificadores de equipo duplicados")
    base = _single_round_robin(teams)
    if not base:
        return ()
    rounds_per_cycle = max(f.round_number for f in base)
    fixtures: list[LeagueFixture9394] = []
    for cycle in range(cycles):
        invert = cycle % 2 == 1
        offset = cycle * rounds_per_cycle
        for fixture in base:
            home, away = (fixture.away_team_id, fixture.home_team_id) if invert else (fixture.home_team_id, fixture.away_team_id)
            fixtures.append(LeagueFixture9394(fixture.round_number + offset, home, away))
    validate_round_robin_cycles(tuple(fixtures), teams, cycles=cycles)
    return tuple(fixtures)


def generate_double_round_robin(team_ids: Sequence[str]) -> tuple[LeagueFixture9394, ...]:
    """Generate the usual two-cycle home/away calendar."""
    fixtures = generate_round_robin_cycles(team_ids, 2)
    validate_league_fixtures(fixtures, tuple(dict.fromkeys(str(team_id) for team_id in team_ids)))
    return fixtures


def validate_round_robin_cycles(
    fixtures: Sequence[LeagueFixture9394], team_ids: Sequence[str], *, cycles: int
) -> None:
    teams = tuple(dict.fromkeys(team_ids))
    team_set = set(teams)
    by_round: dict[int, set[str]] = {}
    pair_counter: Counter[frozenset[str]] = Counter()
    home_counter: Counter[tuple[str, str]] = Counter()
    for fixture in fixtures:
        if fixture.home_team_id == fixture.away_team_id:
            raise ValueError("un club no puede jugar contra sí mismo")
        if fixture.home_team_id not in team_set or fixture.away_team_id not in team_set:
            raise ValueError("el calendario contiene un club ajeno a la liga")
        occupied = by_round.setdefault(fixture.round_number, set())
        if fixture.home_team_id in occupied or fixture.away_team_id in occupied:
            raise ValueError(f"un club aparece dos veces en la jornada {fixture.round_number}")
        occupied.update((fixture.home_team_id, fixture.away_team_id))
        pair_counter[frozenset((fixture.home_team_id, fixture.away_team_id))] += 1
        home_counter[(fixture.home_team_id, fixture.away_team_id)] += 1

    for i, home in enumerate(teams):
        for away in teams[i + 1:]:
            if pair_counter[frozenset((home, away))] != cycles:
                raise ValueError(f"pareja {home}-{away} aparece {pair_counter[frozenset((home, away))]} veces; esperaba {cycles}")
            if cycles % 2 == 0 and home_counter[(home, away)] != home_counter[(away, home)]:
                raise ValueError(f"pareja {home}-{away} no tiene localía equilibrada")


def validate_league_fixtures(fixtures: Sequence[LeagueFixture9394], team_ids: Sequence[str]) -> None:
    teams = tuple(dict.fromkeys(team_ids))
    team_set = set(teams)
    by_round: dict[int, set[str]] = {}
    pair_counter: Counter[tuple[str, str]] = Counter()

    for fixture in fixtures:
        if fixture.home_team_id == fixture.away_team_id:
            raise ValueError("un club no puede jugar contra sí mismo")
        if fixture.home_team_id not in team_set or fixture.away_team_id not in team_set:
            raise ValueError("el calendario contiene un club ajeno a la liga")
        occupied = by_round.setdefault(fixture.round_number, set())
        if fixture.home_team_id in occupied or fixture.away_team_id in occupied:
            raise ValueError(f"un club aparece dos veces en la jornada {fixture.round_number}")
        occupied.update((fixture.home_team_id, fixture.away_team_id))
        pair_counter[(fixture.home_team_id, fixture.away_team_id)] += 1

    if not teams:
        return
    for home in teams:
        for away in teams:
            if home == away:
                continue
            if pair_counter[(home, away)] != 1:
                raise ValueError(f"emparejamiento {home}-{away} aparece {pair_counter[(home, away)]} veces")
