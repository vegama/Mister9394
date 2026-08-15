from __future__ import annotations

"""Executable Campeonato Brasileiro Série A 1993.

The supplied MDB labels Série A as a 20-club league, but the admitted 1993
competition actually used 32 clubs and a multi-stage format.  Thirty of those
clubs are source-backed in the mixed-era MDB; Fortaleza is source-backed but
stored under a later league row, and the two absent clubs are explicit audited
source repairs.  No modern league fallback is used.
"""

from dataclasses import dataclass

from .league_engine import LeagueSeason9394
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, FootballTactics9394, Footballer9394, TeamSheet9394
from .rules import CompetitionRules9394
from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet_with_repair


BRAZIL_1993_GROUPS: dict[str, tuple[str, ...]] = {
    "A": ("723", "717", "1024", "708", "712", "709", "825", "711"),
    "B": ("749", "719", "715", "713", "748", "705", "724", "722"),
    "C": ("718", "1824", "714", "725", "750", "1825", "2340", "1984"),
    "D": ("827", "828", "1022", "1014", "706", "hist:uniao-sao-joao", "hist:desportiva", "710"),
}

HISTORICAL_REPAIR_CLUBS = {
    "hist:uniao-sao-joao": "União São João",
    "hist:desportiva": "Desportiva Ferroviária",
}


@dataclass(frozen=True, slots=True)
class BrazilTie9394:
    team_a_id: str
    team_b_id: str
    winner_team_id: str
    loser_team_id: str
    aggregate: tuple[int, int]
    resolved_by: str


@dataclass(frozen=True, slots=True)
class BrazilSeasonResult9394:
    first_phase_tables: dict[str, tuple]
    intermediate_ties: tuple[BrazilTie9394, ...]
    second_phase_tables: dict[str, tuple]
    final_tie: BrazilTie9394
    champion_team_id: str
    runner_up_team_id: str
    relegated_team_ids: tuple[str, ...]
    simulated_matches: int
    repaired_players: int
    source_repair_club_ids: tuple[str, ...]


def _group_rules(group: str, teams: int, rounds: int) -> CompetitionRules9394:
    return CompetitionRules9394(
        id=f"bra_1993_group_{group.lower()}", name=f"Brasileirão 1993 · Grupo {group}", country="Brasil",
        points_win=2, points_draw=1, points_loss=0, teams=teams, rounds=rounds,
        tie_breakers=("overall_wins", "overall_goal_difference", "overall_goals_scored"),
    )


def _synthetic_sheet(team_id: str, name: str, overall: int = 62) -> TeamSheet9394:
    positions = ("GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "MF", "ST", "ST")
    players = []
    for i, pos in enumerate(positions, 1):
        players.append(Footballer9394(
            id=f"repair:{team_id}:{i}", name=f"{name} · dato histórico pendiente {i}", position=pos,
            overall=overall, pace=overall, stamina=overall, technique=overall,
            short_pass=overall, long_pass=overall, creativity=overall,
            finishing=overall, heading=overall, tackling=overall, marking=overall,
            positioning=overall, discipline=70, leadership=65,
            goalkeeping=overall if pos == "GK" else 8,
        ))
    sheet = TeamSheet9394(team_id=team_id, team_name=name, starters=tuple(players), bench=(), tactics=FootballTactics9394())
    return sheet


def _build_sheets(universe: FootballUniverseSnapshot9394) -> tuple[dict[str, TeamSheet9394], int]:
    sheets: dict[str, TeamSheet9394] = {}
    repairs = 0
    all_ids = {tid for ids in BRAZIL_1993_GROUPS.values() for tid in ids}
    for tid in sorted(all_ids):
        if tid in HISTORICAL_REPAIR_CLUBS:
            sheets[tid] = _synthetic_sheet(tid, HISTORICAL_REPAIR_CLUBS[tid])
            repairs += 11
        else:
            sheet, count = build_snapshot_team_sheet_with_repair(universe, int(tid))
            sheets[tid] = sheet
            repairs += count
    return sheets, repairs


def _play_group(ids: tuple[str, ...] | list[str], sheets: dict[str, TeamSheet9394], *, name: str, seed: int):
    rules = _group_rules(name, len(ids), (len(ids) - 1) * 2)
    season = LeagueSeason9394(rules, {tid: sheets[tid] for tid in ids}, FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
    season.play_all(seed_base=seed)
    return season.table(), season.played_matches


def _campaign_key(row) -> tuple[int, int, int, int]:
    return (row.points, row.wins, row.goal_difference, row.goals_for)


def _two_leg_draw_advantage(
    a: str, b: str, sheets: dict[str, TeamSheet9394], engine: FootballMatchEngine9394,
    *, seed: int, advantage: str,
) -> BrazilTie9394:
    leg1 = engine.simulate(sheets[a], sheets[b], seed=seed)
    leg2 = engine.simulate(sheets[b], sheets[a], seed=seed + 1)
    agg_a = leg1.home.goals + leg2.away.goals
    agg_b = leg1.away.goals + leg2.home.goals
    if agg_a > agg_b:
        winner, reason = a, "aggregate"
    elif agg_b > agg_a:
        winner, reason = b, "aggregate"
    else:
        if advantage not in (a, b):
            raise ValueError("la ventaja histórica debe pertenecer a la eliminatoria")
        winner, reason = advantage, "better_campaign_draw_advantage"
    loser = b if winner == a else a
    return BrazilTie9394(a, b, winner, loser, (agg_a, agg_b), reason)


def _combined_campaign_key(first_row, second_row) -> tuple[int, int, int, int]:
    return (
        first_row.points + second_row.points,
        first_row.wins + second_row.wins,
        first_row.goal_difference + second_row.goal_difference,
        first_row.goals_for + second_row.goals_for,
    )


def simulate_brazil_serie_a_1993(
    *, universe: FootballUniverseSnapshot9394 | None = None, seed_base: int = 479394,
) -> BrazilSeasonResult9394:
    universe = universe or default_runtime_snapshot()
    sheets, repairs = _build_sheets(universe)
    if len(sheets) != 32:
        raise AssertionError(f"Brasil 1993: se esperaban 32 clubes y hay {len(sheets)}")

    first_tables: dict[str, tuple] = {}
    first_rows: dict[str, object] = {}
    matches = 0
    for offset, group in enumerate(("A", "B", "C", "D")):
        table, played = _play_group(BRAZIL_1993_GROUPS[group], sheets, name=group, seed=seed_base + offset * 1000)
        first_tables[group] = table; matches += played
        first_rows.update({row.team_id: row for row in table})
        if len(table) != 8 or any(row.played != 14 for row in table):
            raise AssertionError(f"Brasil 1993 grupo {group}: calendario inválido")

    # A/B contribute their top three directly. C/D contribute top two to the
    # cross-group intermediate ties. On aggregate equality the better first-phase
    # campaign advances; this reproduces the Paraná-Vitória 1-1 aggregate case.
    c1, c2 = first_tables["C"][0].team_id, first_tables["C"][1].team_id
    d1, d2 = first_tables["D"][0].team_id, first_tables["D"][1].team_id
    engine = FootballMatchEngine9394(profile=ERA_BASELINE_1993_94)
    pairings = ((c1, d2), (c2, d1))
    intermediate: list[BrazilTie9394] = []
    for idx, (a, b) in enumerate(pairings):
        ka, kb = _campaign_key(first_rows[a]), _campaign_key(first_rows[b])
        if ka == kb:
            raise RuntimeError("Brasil 1993: empate absoluto de campaña en fase intermedia; falta criterio histórico adicional")
        advantage = a if ka > kb else b
        intermediate.append(_two_leg_draw_advantage(a, b, sheets, engine, seed=seed_base + 10000 + idx * 10, advantage=advantage))
        matches += 2

    a1, a2, a3 = [row.team_id for row in first_tables["A"][:3]]
    b1, b2, b3 = [row.team_id for row in first_tables["B"][:3]]
    w1, w2 = intermediate[0].winner_team_id, intermediate[1].winner_team_id
    second_groups = {
        "E": (a1, a3, b2, w1),
        "F": (b1, b3, a2, w2),
    }
    second_tables: dict[str, tuple] = {}
    second_rows: dict[str, object] = {}
    for offset, group in enumerate(("E", "F")):
        table, played = _play_group(second_groups[group], sheets, name=group, seed=seed_base + 20000 + offset * 1000)
        second_tables[group] = table; matches += played
        second_rows.update({row.team_id: row for row in table})
        if len(table) != 4 or any(row.played != 6 for row in table):
            raise AssertionError(f"Brasil 1993 grupo {group}: segunda fase inválida")

    finalist_a = second_tables["E"][0].team_id
    finalist_b = second_tables["F"][0].team_id
    ka = _combined_campaign_key(first_rows[finalist_a], second_rows[finalist_a])
    kb = _combined_campaign_key(first_rows[finalist_b], second_rows[finalist_b])
    if ka == kb:
        raise RuntimeError("Brasil 1993: finalistas con campaña absolutamente igual; falta criterio histórico adicional")
    advantage = finalist_a if ka > kb else finalist_b
    final = _two_leg_draw_advantage(finalist_a, finalist_b, sheets, engine, seed=seed_base + 30000, advantage=advantage)
    matches += 2

    relegated = tuple(row.team_id for group in ("C", "D") for row in first_tables[group][4:])
    if len(relegated) != 8 or matches != 254:
        raise AssertionError(f"Brasil 1993: cierre inválido, {matches} partidos y {len(relegated)} descensos")
    return BrazilSeasonResult9394(
        first_phase_tables=first_tables, intermediate_ties=tuple(intermediate), second_phase_tables=second_tables,
        final_tie=final, champion_team_id=final.winner_team_id, runner_up_team_id=final.loser_team_id,
        relegated_team_ids=relegated, simulated_matches=matches, repaired_players=repairs,
        source_repair_club_ids=tuple(HISTORICAL_REPAIR_CLUBS),
    )
