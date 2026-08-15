from __future__ import annotations

"""1993-94 European club competitions from the stage pools stored in the MDB.

The source database does not store every qualifying-round participant, but it
*does* contain an authoritative pool for the stage at which the game starts:
8 Champions League group-stage clubs, 16 UEFA Cup clubs and 32 Cup Winners' Cup
clubs.  We complete those competitions from that source state with the actual
1993-94 round structure instead of fabricating a modern format.
"""

from dataclasses import dataclass
from random import Random

from .knockout import KnockoutLeg9394, KnockoutRoundRules9394, resolve_knockout_tie
from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, SimulationProfile9394, TeamSheet9394
from .rules import CompetitionRules9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet_with_repair


@dataclass(frozen=True, slots=True)
class KnockoutTieResult9394:
    first_team_id: str
    second_team_id: str
    winner_team_id: str
    loser_team_id: str
    legs: int
    aggregate: tuple[int, int]
    resolved_by: str


@dataclass(frozen=True, slots=True)
class EuropeanCupSeason9394:
    competition_id: int
    start_stage_team_ids: tuple[str, ...]
    group_tables: tuple[tuple, ...]
    knockout_ties: tuple[KnockoutTieResult9394, ...]
    champion_team_id: str
    runner_up_team_id: str
    simulated_matches: int
    repaired_players: int


def _strength(sheet: TeamSheet9394) -> float:
    return sum(p.overall for p in sheet.starters) / max(1, len(sheet.starters))


def _decide_pending(first: str, second: str, sheets: dict[str, TeamSheet9394], seed: int) -> str:
    rng = Random(seed ^ 0x93E0)
    delta = (_strength(sheets[first]) - _strength(sheets[second])) / 120.0
    p_first = max(.30, min(.70, .5 + delta))
    return first if rng.random() < p_first else second


def _two_leg_tie(
    first: str, second: str, sheets: dict[str, TeamSheet9394], engine: FootballMatchEngine9394,
    *, seed: int, away_goals: bool = True,
) -> KnockoutTieResult9394:
    leg1 = engine.simulate(sheets[first], sheets[second], seed=seed)
    leg2 = engine.simulate(sheets[second], sheets[first], seed=seed + 1)
    rules = KnockoutRoundRules9394(
        name="Eliminatoria", legs=2, away_goals=away_goals,
        extra_time=True, penalties=True,
    )
    resolution = resolve_knockout_tie(
        KnockoutLeg9394(first, second, leg1.home.goals, leg1.away.goals), rules,
        KnockoutLeg9394(second, first, leg2.home.goals, leg2.away.goals),
    )
    if resolution.winner_team_id is None:
        winner = _decide_pending(first, second, sheets, seed + 2)
        loser = second if winner == first else first
        resolved_by = resolution.pending_decider or "extra_time_penalties"
    else:
        winner, loser = resolution.winner_team_id, resolution.loser_team_id
        resolved_by = resolution.resolved_by or "aggregate"
    return KnockoutTieResult9394(first, second, winner, loser, 2, resolution.aggregate, resolved_by)


def _single_tie(
    first: str, second: str, sheets: dict[str, TeamSheet9394], engine: FootballMatchEngine9394,
    *, seed: int, neutral: bool,
) -> KnockoutTieResult9394:
    match_engine = engine
    if neutral:
        match_engine = FootballMatchEngine9394(profile=SimulationProfile9394(
            id="era_1993_94_neutral", target_goals_per_match=ERA_BASELINE_1993_94.target_goals_per_match,
            goal_conversion_multiplier=ERA_BASELINE_1993_94.goal_conversion_multiplier,
            notable_attack_multiplier=ERA_BASELINE_1993_94.notable_attack_multiplier,
            foul_multiplier=ERA_BASELINE_1993_94.foul_multiplier, home_advantage_rating=0.0,
        ))
    result = match_engine.simulate(sheets[first], sheets[second], seed=seed)
    if result.home.goals != result.away.goals:
        winner = first if result.home.goals > result.away.goals else second
        resolved_by = "single_leg"
    else:
        winner = _decide_pending(first, second, sheets, seed + 1)
        resolved_by = "extra_time_penalties"
    loser = second if winner == first else first
    return KnockoutTieResult9394(first, second, winner, loser, 1, (result.home.goals, result.away.goals), resolved_by)


def _sheets(universe: FootballUniverseSnapshot9394, ids: list[int]) -> tuple[dict[str, TeamSheet9394], int]:
    sheets: dict[str, TeamSheet9394] = {}
    repairs = 0
    for team_id in ids:
        sheet, count = build_snapshot_team_sheet_with_repair(universe, team_id)
        sheets[str(team_id)] = sheet
        repairs += count
    return sheets, repairs


def _knockout_round(
    ids: list[str], sheets: dict[str, TeamSheet9394], engine: FootballMatchEngine9394,
    *, seed_base: int, two_legged: bool, away_goals: bool = True,
) -> tuple[list[str], list[KnockoutTieResult9394]]:
    if len(ids) % 2:
        raise ValueError("una ronda europea debe tener un número par de equipos")
    winners: list[str] = []
    ties: list[KnockoutTieResult9394] = []
    for index in range(0, len(ids), 2):
        a, b = ids[index], ids[index + 1]
        tie = (_two_leg_tie(a, b, sheets, engine, seed=seed_base + index, away_goals=away_goals)
               if two_legged else _single_tie(a, b, sheets, engine, seed=seed_base + index, neutral=False))
        winners.append(tie.winner_team_id); ties.append(tie)
    return winners, ties


def simulate_champions_league_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 1939401,
) -> EuropeanCupSeason9394:
    universe = universe or default_runtime_snapshot()
    ids = [int(i) for i in universe.payload.get("tournament_participants", {}).get("1", ())]
    if len(ids) != 8:
        raise ValueError(f"Copa de Europa 1993-94: la MDB debe aportar 8 clubes de fase de grupos, aporta {len(ids)}")
    sheets, repairs = _sheets(universe, ids)
    # Historical groups: A Barcelona/Monaco/Spartak/Galatasaray; B Milan/Porto/Werder/Anderlecht.
    group_ids = (["3", "227", "617", "645"], ["265", "307", "209", "415"])
    group_tables = []
    matches = 0
    for gi, group in enumerate(group_ids):
        rules = CompetitionRules9394(
            id=f"ucl_9394_group_{gi}", name="Copa de Europa · Grupo", country="UEFA",
            points_win=2, points_draw=1, points_loss=0, teams=4, rounds=6,
            tie_breakers=("overall_goal_difference", "overall_goals_scored"),
        )
        season = LeagueSeason9394(rules, {tid:sheets[tid] for tid in group}, FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
        season.play_all(seed_base=seed_base + gi * 1000)
        table = season.table(); group_tables.append(table); matches += season.played_matches
    # Group winners host the runners-up from the other group in one-leg semi-finals.
    semi1 = _single_tie(group_tables[0][0].team_id, group_tables[1][1].team_id, sheets, FootballMatchEngine9394(), seed=seed_base+10000, neutral=False)
    semi2 = _single_tie(group_tables[1][0].team_id, group_tables[0][1].team_id, sheets, FootballMatchEngine9394(), seed=seed_base+10010, neutral=False)
    final = _single_tie(semi1.winner_team_id, semi2.winner_team_id, sheets, FootballMatchEngine9394(), seed=seed_base+10100, neutral=True)
    ties = (semi1, semi2, final)
    return EuropeanCupSeason9394(1, tuple(map(str, ids)), tuple(group_tables), ties,
                                  final.winner_team_id, final.loser_team_id, matches + 3, repairs)


def simulate_uefa_cup_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 1939402,
) -> EuropeanCupSeason9394:
    universe = universe or default_runtime_snapshot()
    ids = [int(i) for i in universe.payload.get("tournament_participants", {}).get("2", ())]
    if len(ids) != 16:
        raise ValueError(f"Copa UEFA 1993-94: la MDB debe aportar 16 clubes de octavos, aporta {len(ids)}")
    sheets, repairs = _sheets(universe, ids)
    current = list(map(str, ids)); ties: list[KnockoutTieResult9394] = []; matches = 0
    for ri in range(4):  # octavos, cuartos, semifinales y final; final también a doble partido.
        current, round_ties = _knockout_round(current, sheets, FootballMatchEngine9394(), seed_base=seed_base+ri*1000, two_legged=True, away_goals=True)
        ties.extend(round_ties); matches += 2 * len(round_ties)
    final = ties[-1]
    return EuropeanCupSeason9394(2, tuple(map(str, ids)), (), tuple(ties), final.winner_team_id, final.loser_team_id, matches, repairs)


def simulate_cup_winners_cup_1993_94(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 1939490,
) -> EuropeanCupSeason9394:
    universe = universe or default_runtime_snapshot()
    ids = [int(i) for i in universe.payload.get("tournament_participants", {}).get("90", ())]
    if len(ids) != 32:
        raise ValueError(f"Recopa 1993-94: la MDB debe aportar 32 clubes de primera ronda, aporta {len(ids)}")
    sheets, repairs = _sheets(universe, ids)
    current = list(map(str, ids)); ties: list[KnockoutTieResult9394] = []; matches = 0
    # 1/16, octavos, cuartos, semifinales: ida/vuelta y goles fuera. Final neutral a partido único.
    for ri in range(4):
        current, round_ties = _knockout_round(current, sheets, FootballMatchEngine9394(), seed_base=seed_base+ri*1000, two_legged=True, away_goals=True)
        ties.extend(round_ties); matches += 2 * len(round_ties)
    final = _single_tie(current[0], current[1], sheets, FootballMatchEngine9394(), seed=seed_base+5000, neutral=True)
    ties.append(final); matches += 1
    return EuropeanCupSeason9394(90, tuple(map(str, ids)), (), tuple(ties), final.winner_team_id, final.loser_team_id, matches, repairs)
