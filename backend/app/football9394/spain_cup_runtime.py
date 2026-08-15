from __future__ import annotations

"""Executable Copa del Rey 1993-94 over the Spanish clubs present in the MDB.

The source slice contains Primera, Segunda and Segunda B but not Tercera.  The
historical cup had 160 clubs and included Tercera; we therefore preserve the
1993-94 knockout laws (reserve exclusion, two-legged ties, away goals and a
single neutral final) while building the largest honest bracket possible from
source clubs.  Missing Tercera entrants are surfaced as a data gap, not silently
invented.
"""

from dataclasses import dataclass
from random import Random

from .europe_runtime import KnockoutTieResult9394, _single_tie, _two_leg_tie
from .match_engine import FootballMatchEngine9394, TeamSheet9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet_with_repair


@dataclass(frozen=True, slots=True)
class CopaDelReySeason9394:
    source_eligible_clubs: int
    historical_expected_clubs: int
    missing_lower_tier_slots: int
    round_sizes: tuple[tuple[str, int, int], ...]
    ties: tuple[KnockoutTieResult9394, ...]
    champion_team_id: str
    runner_up_team_id: str
    simulated_matches: int
    repaired_players: int


def _build_sheets(universe, ids):
    sheets: dict[str, TeamSheet9394] = {}
    repairs = 0
    for team_id in ids:
        sheet, count = build_snapshot_team_sheet_with_repair(universe, int(team_id))
        sheets[str(team_id)] = sheet; repairs += count
    return sheets, repairs


def _reduce_to(
    ids: list[str], target: int, sheets: dict[str, TeamSheet9394], *, seed: int,
) -> tuple[list[str], list[KnockoutTieResult9394]]:
    if target < 1 or target > len(ids):
        raise ValueError("objetivo de ronda inválido")
    eliminations = len(ids) - target
    if eliminations * 2 > len(ids):
        raise ValueError("una sola ronda no puede eliminar tantos clubes")
    rng = Random(seed)
    pool = ids[:]
    rng.shuffle(pool)
    playing = pool[:eliminations * 2]
    byes = pool[eliminations * 2:]
    winners = list(byes)
    ties: list[KnockoutTieResult9394] = []
    engine = FootballMatchEngine9394()
    for idx in range(0, len(playing), 2):
        tie = _two_leg_tie(playing[idx], playing[idx+1], sheets, engine, seed=seed+idx, away_goals=True)
        ties.append(tie); winners.append(tie.winner_team_id)
    return winners, ties


def simulate_copa_del_rey_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 39394,
) -> CopaDelReySeason9394:
    universe = universe or default_runtime_snapshot()
    tier_ids = {
        1: [str(t['source_id']) for t in universe.teams(league_id=1) if not t.get('reserve_of')],
        2: [str(t['source_id']) for t in universe.teams(league_id=2) if not t.get('reserve_of')],
        3: [str(t['source_id']) for lid in (3,9,10,11) for t in universe.teams(league_id=lid) if not t.get('reserve_of')],
    }
    all_ids = tier_ids[1] + tier_ids[2] + tier_ids[3]
    if len(set(all_ids)) != len(all_ids):
        raise AssertionError("Copa del Rey: club duplicado en el pool de fuente")
    sheets, repairs = _build_sheets(universe, all_ids)
    ties: list[KnockoutTieResult9394] = []
    sizes: list[tuple[str,int,int]] = []

    # Source-adapted staged entry. Segunda B starts; Segunda then Primera enter.
    current, r = _reduce_to(tier_ids[3], len(tier_ids[3])//2, sheets, seed=seed_base)
    ties += r; sizes.append(("Primera ronda", len(tier_ids[3]), len(current)))

    current += tier_ids[2]
    target = (len(current)+1)//2
    before = len(current); current, r = _reduce_to(current, target, sheets, seed=seed_base+1000)
    ties += r; sizes.append(("Segunda ronda", before, len(current)))

    current += tier_ids[1]
    before = len(current)
    # Reduce to the classic 32-team final bracket in one round, using historical byes where needed.
    current, r = _reduce_to(current, 32, sheets, seed=seed_base+2000)
    ties += r; sizes.append(("Entrada de Primera / ronda de 32", before, len(current)))

    for name, target, offset in (("Dieciseisavos",16,3000),("Octavos",8,4000),("Cuartos",4,5000)):
        before=len(current); current, r = _reduce_to(current,target,sheets,seed=seed_base+offset)
        ties += r; sizes.append((name,before,len(current)))

    # One more two-legged round to reach the final from four clubs.
    before=len(current); current, r = _reduce_to(current,2,sheets,seed=seed_base+6000)
    ties += r; sizes.append(("Semifinales",before,len(current)))
    final = _single_tie(current[0], current[1], sheets, FootballMatchEngine9394(), seed=seed_base+7000, neutral=True)
    ties.append(final); sizes.append(("Final",2,1))
    simulated_matches = sum(2 if tie.legs == 2 else 1 for tie in ties)
    eligible = len(all_ids)
    return CopaDelReySeason9394(
        source_eligible_clubs=eligible, historical_expected_clubs=160,
        missing_lower_tier_slots=max(0,160-eligible), round_sizes=tuple(sizes), ties=tuple(ties),
        champion_team_id=final.winner_team_id, runner_up_team_id=final.loser_team_id,
        simulated_matches=simulated_matches, repaired_players=repairs,
    )
