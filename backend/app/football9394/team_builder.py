from __future__ import annotations

"""Build match-day team sheets from the normalized 1993-94 MDB snapshot.

The match engine must feel the actual footballers in the database rather than a
single synthetic club rating.  This module is deliberately small and
predictable: it picks an XI by broad historical positions and maps the imported
attributes onto the football-native simulator contract.
"""

from dataclasses import replace
from typing import Any, Iterable

from .laws import LAWS_1993_94
from .match_engine import Footballer9394, FootballTactics9394, TeamSheet9394
from .position_roles import (
    assign_players_to_formation,
    assign_players_to_formation_with_foreign_limit,
    position_penalty,
    role_for_player,
)
from .foreign_rules import ForeignPlayerRule9394, validate_matchday_foreigners
from .player_identity import tactical_fit


FORMATION_SHAPES: dict[str, tuple[int, int, int]] = {
    "4-4-2": (4, 4, 2), "4-3-3": (4, 3, 3), "4-2-3-1": (4, 5, 1),
    "4-5-1": (4, 5, 1), "4-4-1-1": (4, 5, 1), "4-3-1-2": (4, 4, 2),
    "4-2-4": (4, 2, 4), "3-5-2": (3, 5, 2), "3-4-3": (3, 4, 3),
    "3-4-1-2": (3, 5, 2), "5-3-2": (5, 3, 2), "5-4-1": (5, 4, 1),
    "5-2-3": (5, 2, 3),
}

_POSITION = {"POR": "GK", "DEF": "DF", "MED": "MF", "DEL": "ST"}


def _clip(value: Any, fallback: int = 60) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = fallback
    return max(1, min(100, number))


def footballer_from_snapshot(row: dict[str, Any], *, assigned_slot: str | None = None) -> Footballer9394:
    attrs = row.get("attributes") or {}
    broad = str(row.get("broad_position") or "").upper()
    specialist = role_for_player(row)
    source_overall = _clip(row.get("overall") or row.get("category"), 60)
    fit_penalty = position_penalty(row, assigned_slot) if assigned_slot else 0
    overall = max(1, source_overall - fit_penalty)
    is_goalkeeper = specialist.squad_slot == "GK"

    # The source database does not expose one normalized goalkeeper-rating
    # column in the historical slice.  For a goalkeeper the source overall is
    # therefore the safest authoritative aggregate; we never derive it from a
    # modern model or invent a separate hidden rating.
    goalkeeping = source_overall if is_goalkeeper else 8
    creativity = attrs.get("vision") if attrs.get("vision") is not None else attrs.get("technique")

    return Footballer9394(
        id=str(row["source_id"]),
        name=str(row.get("display_name") or f"Jugador {row['source_id']}"),
        position=("GK" if (assigned_slot or specialist.squad_slot) == "GK" else "DF" if (assigned_slot or specialist.squad_slot) in {"RB","LB","CB"} else "ST" if (assigned_slot or specialist.squad_slot) in {"ST","RW","LW"} else "MF"),
        overall=overall,
        pace=_clip(attrs.get("pace"), overall),
        stamina=_clip(attrs.get("stamina"), overall),
        technique=_clip(attrs.get("technique"), overall),
        short_pass=_clip(attrs.get("short_pass"), overall),
        long_pass=_clip(attrs.get("long_pass"), overall),
        creativity=_clip(creativity, overall),
        finishing=_clip(attrs.get("finishing"), overall),
        heading=_clip(attrs.get("heading"), overall),
        tackling=_clip(attrs.get("tackling"), overall),
        marking=_clip(attrs.get("marking"), overall),
        positioning=_clip(attrs.get("positioning"), overall),
        discipline=_clip(attrs.get("discipline"), 70),
        leadership=_clip(attrs.get("leadership"), 65),
        goalkeeping=goalkeeping,
        acceleration=_clip(attrs.get("acceleration"), overall),
        strength=_clip(attrs.get("strength"), overall),
        work_rate=_clip(attrs.get("work_rate"), overall),
        aggression=_clip(attrs.get("aggression"), overall),
        anticipation=_clip(attrs.get("anticipation"), overall),
        consistency=_clip(attrs.get("consistency"), 70),
        vision=_clip(attrs.get("vision"), overall),
        dribbling=_clip(attrs.get("dribbling"), overall),
        off_ball=_clip(attrs.get("off_ball"), overall),
        shot_power=_clip(attrs.get("shot_power"), overall),
        free_kicks=_clip(attrs.get("free_kicks"), 50),
        penalties=_clip(attrs.get("penalties"), 50),
        jumping=_clip(attrs.get("jumping"), overall),
        injury_proneness=max(0, min(3, int(row.get("injury_proneness") or 0))),
        individualist=bool((row.get("hidden_traits") or {}).get("individualist")),
        killer_pass=bool((row.get("hidden_traits") or {}).get("killer_pass")),
        holds_ball=bool((row.get("hidden_traits") or {}).get("holds_ball")),
        long_shots=bool((row.get("hidden_traits") or {}).get("long_shots")),
        cuts_inside=bool((row.get("hidden_traits") or {}).get("cuts_inside")),
        first_time_play=bool((row.get("hidden_traits") or {}).get("first_time_play")),
        dives=bool((row.get("hidden_traits") or {}).get("dives")),
        role_code=specialist.code,
        squad_slot=(assigned_slot or specialist.squad_slot),
    )


def _rank(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda p: (
            -int(p.get("_selection_overall") or p.get("overall") or p.get("category") or 0),
            bool(p.get("initially_reserve")),
            int(p.get("shirt_number") or 999),
            str(p.get("display_name") or ""),
        ),
    )


def build_snapshot_team_sheet(
    universe: Any,
    team_id: int,
    *,
    tactics: FootballTactics9394 | None = None,
    formation: str | None = None,
    foreign_predicate=None,
    max_foreign_starters: int | None = None,
    max_foreign_squad: int | None = None,
    allow_emergency_outfield_goalkeeper: bool = False,
    coach_profile: dict[str, Any] | None = None,
) -> TeamSheet9394:
    """Select an actual XI + five-man bench from the historical snapshot.

    Broad source positions are respected first.  If a club has an imbalanced
    squad, the best remaining real player fills the missing slot rather than a
    synthetic placeholder.  A club with fewer than eleven imported players is
    rejected, which is useful for exposing incomplete historical datasets.
    """

    team = universe.team(team_id)
    if team is None:
        raise KeyError(f"Equipo MDB {team_id} no encontrado")
    rows = list(universe.players_by_team.get(team_id, ()))
    eligible = [row for row in rows if not row.get("retired")]
    if len(eligible) < LAWS_1993_94.players_per_team:
        raise ValueError(f"{team['name']}: sólo hay {len(eligible)} futbolistas históricos disponibles")

    tactics = tactics or FootballTactics9394(formation=formation or "4-4-2")
    requested_formation = formation or tactics.formation
    defenders, midfielders, forwards = FORMATION_SHAPES.get(requested_formation, FORMATION_SHAPES["4-4-2"])
    if tactics.formation != requested_formation:
        tactics = replace(tactics, formation=requested_formation)

    # AI coaches evaluate the same base footballers through their own plan.
    # This is deliberately an internal selection score: the user's visible
    # overall remains the source/career rating. Better coaches trust tactical
    # fit a little more, but positional suitability still dominates.
    selection_rows = eligible
    if coach_profile:
        quality = max(0, min(100, int(coach_profile.get("coaching_quality") or 60)))
        fit_weight = 0.035 + quality / 2500.0  # ~0.06 at quality 60, ~0.07 at 90
        selection_rows = []
        for row in eligible:
            fit = float(tactical_fit(row, tactics)["score"])
            base = int(row.get("overall") or row.get("category") or 60)
            selection_rows.append({**row, "_selection_overall": round(base + (fit - 60.0) * fit_weight, 2)})

    # The source MDB contains exact roles (right-back, left-back, centre-back,
    # holding midfielder, winger, striker...).  Formation selection therefore
    # fills actual jobs rather than four broad DEF/MED/DEL buckets.
    if foreign_predicate is not None and max_foreign_starters is not None:
        assignment = assign_players_to_formation_with_foreign_limit(
            selection_rows, requested_formation,
            foreign_predicate=foreign_predicate,
            max_foreign=int(max_foreign_starters),
            allow_emergency_outfield_goalkeeper=allow_emergency_outfield_goalkeeper,
        )
    else:
        assignment = assign_players_to_formation(selection_rows, requested_formation)
    if len(assignment) < LAWS_1993_94.players_per_team:
        qualifier = " legal con el cupo de extranjeros" if foreign_predicate is not None and max_foreign_starters is not None else " especializado"
        raise ValueError(f"{team['name']}: no se puede construir un once{qualifier} completo")
    selected = [row["player"] for row in assignment]
    if not any(role_for_player(row).squad_slot == "GK" for row in selected) and not allow_emergency_outfield_goalkeeper:
        raise ValueError(f"{team['name']}: la plantilla histórica no contiene portero")

    selected_ids = {int(row.get("source_id") or 0) for row in selected}
    remaining = [row for row in (selection_rows if coach_profile else eligible) if int(row.get("source_id") or 0) not in selected_ids]
    bench: list[dict[str, Any]] = []
    starter_foreign=sum(1 for row in selected if foreign_predicate is not None and foreign_predicate(row))
    # The on-field quota and the named-match-squad quota are different rules.
    # Spain 1993-94 is the canonical case: four foreigners could be available,
    # while only three could be on the pitch at the same time.  Therefore the
    # bench is constrained only by the squad cap; substitutions are validated
    # against the on-field cap at the moment they are made.
    foreign_bench_cap=(max(0,int(max_foreign_squad)-starter_foreign) if foreign_predicate is not None and max_foreign_squad is not None else None)
    def bench_allowed(row):
        if foreign_predicate is None or not foreign_predicate(row) or foreign_bench_cap is None: return True
        return sum(1 for p in bench if foreign_predicate(p)) < foreign_bench_cap
    reserve_keeper = _rank(row for row in remaining if role_for_player(row).squad_slot == "GK" and bench_allowed(row))
    if reserve_keeper:
        bench.append(reserve_keeper[0])
    for row in _rank(remaining):
        if row in bench or not bench_allowed(row):
            continue
        bench.append(row)
        if len(bench) >= LAWS_1993_94.max_named_substitutes:
            break

    if foreign_predicate is not None and (max_foreign_starters is not None or max_foreign_squad is not None):
        # Automatic teams must obey the same competition rule as the human.
        # We use the supplied predicate for counting so continental association
        # nationality and domestic British/Irish equivalence remain exact.
        starter_foreign_count=sum(1 for row in selected if foreign_predicate(row))
        squad_foreign_count=starter_foreign_count+sum(1 for row in bench if foreign_predicate(row))
        if max_foreign_starters is not None and starter_foreign_count > int(max_foreign_starters):
            raise ValueError(f"{team['name']}: no puede formar once legal; {starter_foreign_count} extranjeros para un máximo de {max_foreign_starters}")
        if max_foreign_squad is not None and squad_foreign_count > int(max_foreign_squad):
            raise ValueError(f"{team['name']}: no puede formar convocatoria legal; {squad_foreign_count} extranjeros para un máximo de {max_foreign_squad}")

    sheet = TeamSheet9394(
        team_id=str(team_id),
        team_name=team["name"],
        starters=tuple(footballer_from_snapshot(item["player"], assigned_slot=item["slot"]) for item in assignment),
        bench=tuple(footballer_from_snapshot(row) for row in bench),
        tactics=tactics,
        manager_source_id=(str(coach_profile["source_id"]) if coach_profile and coach_profile.get("source_id") is not None else None),
        manager_name=(str(coach_profile.get("display_name")) if coach_profile and coach_profile.get("display_name") else None),
        manager_quality=(int(coach_profile.get("coaching_quality")) if coach_profile and coach_profile.get("coaching_quality") is not None else None),
        manager_tendency=(str(coach_profile.get("game_tendency") or "normal") if coach_profile else "normal"),
        rotation_frequency=(str(coach_profile.get("rotation_frequency") or "normal") if coach_profile else "normal"),
        set_piece_usage=(str(coach_profile.get("set_piece_usage") or "normal") if coach_profile else "normal"),
        manager_discipline=(str(coach_profile.get("discipline_style") or "balanced") if coach_profile else "balanced"),
        attacking_tactics=(FootballTactics9394(**coach_profile["engine_attacking_tactics"]) if coach_profile and coach_profile.get("engine_attacking_tactics") else None),
        defensive_tactics=(FootballTactics9394(**coach_profile["engine_defensive_tactics"]) if coach_profile and coach_profile.get("engine_defensive_tactics") else None),
    )
    sheet.validate(LAWS_1993_94)
    return sheet


def build_snapshot_team_sheet_with_repair(
    universe: Any,
    team_id: int,
    *,
    tactics: FootballTactics9394 | None = None,
    formation: str | None = None,
) -> tuple[TeamSheet9394, int]:
    """Build a playable XI while *auditing* missing source-roster data.

    Normal career code should keep using ``build_snapshot_team_sheet``.  This
    helper exists for global competition certification: if the supplied MDB has
    fewer than eleven players for a club, deterministic neutral placeholders
    are injected so format/lifecycle testing can continue.  The number of
    repairs is returned and must be surfaced by the gate; it is never treated
    as historically complete data.
    """
    try:
        return build_snapshot_team_sheet(
            universe, team_id, tactics=tactics, formation=formation
        ), 0
    except ValueError as exc:
        message = str(exc)
        if "futbolistas históricos disponibles" not in message and "plantilla histórica no contiene portero" not in message:
            raise

    team = universe.team(team_id)
    if team is None:
        raise KeyError(f"Equipo MDB {team_id} no encontrado")
    rows = [row for row in universe.players_by_team.get(team_id, ()) if not row.get("retired")]
    league_id = team.get("league", {}).get("source_id") if team.get("league") else None
    peer_overalls = []
    if league_id is not None:
        for peer in universe.teams(league_id=int(league_id)):
            for player in universe.players_by_team.get(int(peer["source_id"]), ()):
                if player.get("retired"):
                    continue
                value = player.get("overall") or player.get("category")
                if value:
                    peer_overalls.append(int(value))
    peer_overalls.sort()
    neutral = peer_overalls[len(peer_overalls)//2] if peer_overalls else 65

    actual = [footballer_from_snapshot(row) for row in _rank(rows)]
    desired_positions = ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "MF", "ST", "ST"]
    players: list[Footballer9394] = []
    used: set[str] = set()
    # Preserve actual source players first when they can fill a natural slot.
    for desired in desired_positions:
        found = next((p for p in actual if p.id not in used and p.position == desired), None)
        if found is not None:
            players.append(found); used.add(found.id)
        else:
            index = len(players) + 1
            players.append(Footballer9394(
                id=f"repair:{team_id}:{index}",
                name=f"Dato de plantilla pendiente {index}",
                position=desired,
                overall=neutral,
                pace=neutral, stamina=neutral, technique=neutral,
                short_pass=neutral, long_pass=neutral, creativity=neutral,
                finishing=neutral, heading=neutral, tackling=neutral,
                marking=neutral, positioning=neutral, discipline=70,
                leadership=65, goalkeeping=(neutral if desired == "GK" else 8),
            ))
    # Ensure the XI has a goalkeeper even if a real outfield player was used in
    # the first slot due pathological source data.
    if not any(p.position == "GK" for p in players):
        players[0] = Footballer9394(
            id=f"repair:{team_id}:gk", name="Dato de portero pendiente", position="GK",
            overall=neutral, pace=neutral, stamina=neutral, technique=neutral,
            short_pass=neutral, long_pass=neutral, creativity=neutral,
            finishing=neutral, heading=neutral, tackling=neutral, marking=neutral,
            positioning=neutral, discipline=70, leadership=65, goalkeeping=neutral,
        )
    tactics = tactics or FootballTactics9394(formation=formation or "4-4-2")
    sheet = TeamSheet9394(
        team_id=str(team_id), team_name=team["name"], starters=tuple(players), bench=(), tactics=tactics
    )
    sheet.validate(LAWS_1993_94)
    repairs = sum(player.id.startswith("repair:") for player in sheet.starters)
    return sheet, repairs
