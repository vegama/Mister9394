from __future__ import annotations

"""Coupled Italian Serie A / Serie B 1993-94 source-pyramid runtime."""

from dataclasses import dataclass

from .competition_runtime import build_simple_source_league
from .season_decisions import DecisivePlayoffResult9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import StandingRow9394


@dataclass(frozen=True, slots=True)
class ItalyPyramidSeason9394:
    serie_a_table: tuple[StandingRow9394, ...]
    serie_b_table: tuple[StandingRow9394, ...]
    serie_a_playoffs: tuple[DecisivePlayoffResult9394, ...]
    serie_b_playoffs: tuple[DecisivePlayoffResult9394, ...]
    relegated_from_serie_a: tuple[str, ...]
    promoted_from_serie_b: tuple[str, ...]
    relegated_from_serie_b: tuple[str, ...]
    serie_a_matches: int
    serie_b_matches: int


def simulate_italy_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 49394
) -> ItalyPyramidSeason9394:
    universe = universe or default_runtime_snapshot()

    serie_a = build_simple_source_league(4, universe=universe)
    serie_a.play_all(seed_base=seed_base)
    a_resolution = serie_a.finalize_table(seed_base=seed_base + 100000)

    serie_b = build_simple_source_league(102, universe=universe)
    serie_b.play_all(seed_base=seed_base + 200000)
    b_resolution = serie_b.finalize_table(seed_base=seed_base + 300000)

    a_table = a_resolution.table
    b_table = b_resolution.table
    relegated_a = tuple(row.team_id for row in a_table[14:18])
    promoted_b = tuple(row.team_id for row in b_table[:4])
    relegated_b = tuple(row.team_id for row in b_table[16:20])

    if len(a_table) != 18 or any(row.played != 34 for row in a_table):
        raise AssertionError("Serie A 1993-94 debe cerrar con 18 clubes y 34 partidos por club")
    if len(b_table) != 20 or any(row.played != 38 for row in b_table):
        raise AssertionError("Serie B 1993-94 debe cerrar con 20 clubes y 38 partidos por club")
    if len(relegated_a) != 4 or len(promoted_b) != 4:
        raise AssertionError("Italia 1993-94 debe intercambiar cuatro clubes entre Serie A y Serie B")
    if len(set(relegated_a)) != 4 or len(set(promoted_b)) != 4:
        raise AssertionError("los movimientos italianos deben contener cuatro clubes distintos")

    return ItalyPyramidSeason9394(
        serie_a_table=a_table,
        serie_b_table=b_table,
        serie_a_playoffs=a_resolution.playoffs,
        serie_b_playoffs=b_resolution.playoffs,
        relegated_from_serie_a=relegated_a,
        promoted_from_serie_b=promoted_b,
        relegated_from_serie_b=relegated_b,
        serie_a_matches=serie_a.played_matches,
        serie_b_matches=serie_b.played_matches,
    )
