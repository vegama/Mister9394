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


FORMATION_SHAPES: dict[str, tuple[int, int, int]] = {
    "4-4-2": (4, 4, 2),
    "4-3-3": (4, 3, 3),
    "3-5-2": (3, 5, 2),
    "5-3-2": (5, 3, 2),
}

_POSITION = {"POR": "GK", "DEF": "DF", "MED": "MF", "DEL": "ST"}


def _clip(value: Any, fallback: int = 60) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = fallback
    return max(1, min(100, number))


def footballer_from_snapshot(row: dict[str, Any]) -> Footballer9394:
    attrs = row.get("attributes") or {}
    broad = str(row.get("broad_position") or "").upper()
    overall = _clip(row.get("overall") or row.get("category"), 60)
    is_goalkeeper = broad == "POR"

    # The source database does not expose one normalized goalkeeper-rating
    # column in the historical slice.  For a goalkeeper the source overall is
    # therefore the safest authoritative aggregate; we never derive it from a
    # modern model or invent a separate hidden rating.
    goalkeeping = overall if is_goalkeeper else 8
    creativity = attrs.get("vision") if attrs.get("vision") is not None else attrs.get("technique")

    return Footballer9394(
        id=str(row["source_id"]),
        name=str(row.get("display_name") or f"Jugador {row['source_id']}"),
        position=_POSITION.get(broad, broad or "MF"),
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
    )


def _rank(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda p: (
            -int(p.get("overall") or p.get("category") or 0),
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

    buckets = {kind: _rank(row for row in eligible if str(row.get("broad_position") or "").upper() == kind)
               for kind in ("POR", "DEF", "MED", "DEL")}
    selected: list[dict[str, Any]] = []

    def take(kind: str, amount: int) -> None:
        while amount > 0 and buckets[kind]:
            row = buckets[kind].pop(0)
            if row not in selected:
                selected.append(row)
                amount -= 1
        if amount:
            remaining = _rank(row for row in eligible if row not in selected)
            for row in remaining[:amount]:
                selected.append(row)

    take("POR", 1)
    take("DEF", defenders)
    take("MED", midfielders)
    take("DEL", forwards)
    selected = selected[:11]

    # Enforce a real goalkeeper even if fallback selection was necessary.
    if not any(str(row.get("broad_position") or "").upper() == "POR" for row in selected):
        keeper = _rank(row for row in eligible if str(row.get("broad_position") or "").upper() == "POR")
        if not keeper:
            raise ValueError(f"{team['name']}: la plantilla histórica no contiene portero")
        selected[-1] = keeper[0]

    remaining = [row for row in eligible if row not in selected]
    bench: list[dict[str, Any]] = []
    reserve_keeper = _rank(row for row in remaining if str(row.get("broad_position") or "").upper() == "POR")
    if reserve_keeper:
        bench.append(reserve_keeper[0])
    for row in _rank(remaining):
        if row in bench:
            continue
        bench.append(row)
        if len(bench) >= LAWS_1993_94.max_named_substitutes:
            break

    sheet = TeamSheet9394(
        team_id=str(team_id),
        team_name=team["name"],
        starters=tuple(footballer_from_snapshot(row) for row in selected),
        bench=tuple(footballer_from_snapshot(row) for row in bench),
        tactics=tactics,
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
