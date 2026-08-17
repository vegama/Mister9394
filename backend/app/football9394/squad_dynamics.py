from __future__ import annotations

"""Squad hierarchy, playing-time expectations and football tension.

No conversation minigame is required: tension is generated from role, minutes,
results, leadership and source fan affection, then exposed as decisions.
"""

from datetime import date
from typing import Any, Iterable

from .player_identity import age_on


def ensure_squad_dynamics_state(state: dict[str, Any]) -> None:
    state.setdefault("player_dynamics", {})


def _overall(player: dict[str, Any], development: dict[str, dict[str, Any]]) -> int:
    pid = str(int(player["source_id"]))
    return int(development.get(pid, {}).get("overall") or player.get("overall") or player.get("category") or 60)


def hierarchy_for_squad(players: Iterable[dict[str, Any]], development: dict[str, dict[str, Any]], *, game_date: date) -> dict[int, dict[str, Any]]:
    rows = list(players)
    if not rows:
        return {}
    ranked = sorted(rows, key=lambda p: (
        -_overall(p, development),
        -int((p.get("attributes") or {}).get("leadership") or 60),
        -int(p.get("fan_affection") or 0),
        int(p.get("source_id") or 0),
    ))
    n = len(ranked)
    output: dict[int, dict[str, Any]] = {}
    for index, player in enumerate(ranked):
        percentile = 1 - index / max(1, n - 1)
        age = age_on(player, game_date) or 25
        leadership = int((player.get("attributes") or {}).get("leadership") or 60)
        affection = int(player.get("fan_affection") or 0)
        if index < min(3, n):
            role, expected = "Figura", .78
        elif percentile >= .60:
            role, expected = "Titular", .62
        elif age <= 21 and int(player.get("progression_mean") or 0) >= 5:
            role, expected = "Promesa", .24
        elif percentile >= .30:
            role, expected = "Rotación", .34
        else:
            role, expected = "Fondo de plantilla", .14
        influence = min(100, round(_overall(player, development) * .52 + leadership * .30 + affection * 2.0 + (5 if age >= 29 else 0)))
        output[int(player["source_id"])] = {
            "role": role,
            "expected_start_share": expected,
            "influence": influence,
            "age": age,
        }
    return output


def sync_team_dynamics(
    state: dict[str, Any],
    *,
    players: Iterable[dict[str, Any]],
    development: dict[str, dict[str, Any]],
    game_date: date,
) -> dict[int, dict[str, Any]]:
    ensure_squad_dynamics_state(state)
    effective_date = date(1993, 10, 23) if str(state.get("age_policy") or "") == "frozen_attributes_dynamic" else game_date
    hierarchy = hierarchy_for_squad(players, development, game_date=effective_date)
    store = state["player_dynamics"]
    for pid, info in hierarchy.items():
        row = store.setdefault(str(pid), {"satisfaction": 70, "wants_move": False, "reasons": [], "team_matches": 0})
        row.update(info)
        row.setdefault("satisfaction", 70)
        row.setdefault("wants_move", False)
        row.setdefault("reasons", [])
        row.setdefault("team_matches", 0)
    return hierarchy


def update_after_match(
    state: dict[str, Any],
    *,
    players: Iterable[dict[str, Any]],
    development: dict[str, dict[str, Any]],
    starter_ids: Iterable[str],
    appeared_ids: Iterable[str],
    won: bool,
    drew: bool,
    game_date: date,
) -> None:
    hierarchy = sync_team_dynamics(state, players=players, development=development, game_date=game_date)
    starters = {str(x) for x in starter_ids}
    appeared = {str(x) for x in appeared_ids}
    for player in players:
        pid = str(int(player["source_id"]))
        if int(player["source_id"]) not in hierarchy:
            continue
        dyn = state["player_dynamics"][pid]
        dev = development.get(pid) or {}
        dyn["team_matches"] = int(dyn.get("team_matches") or 0) + 1
        team_matches = max(1, int(dyn["team_matches"]))
        starts = int(dev.get("season_starts") or 0)
        share = starts / team_matches
        expected = float(dyn.get("expected_start_share") or .3)
        delta = 0
        reasons: list[str] = []
        if pid in starters:
            delta += 2 if share <= expected + .10 else 1
        elif pid in appeared:
            delta += 0
        elif team_matches >= 4:
            gap = expected - share
            if gap >= .35: delta -= 4; reasons.append("Muy por debajo de los minutos que espera")
            elif gap >= .18: delta -= 2; reasons.append("Quiere jugar más")
        if won: delta += 1
        elif not drew: delta -= 1
        # Club symbols tolerate short dips better, but become louder when badly underused.
        affection = int(player.get("fan_affection") or 0)
        if affection >= 7 and expected - share > .30:
            delta -= 1; reasons.append("Su peso en el club aumenta la tensión por falta de minutos")
        satisfaction = max(0, min(100, int(dyn.get("satisfaction") or 70) + delta))
        dyn["satisfaction"] = satisfaction
        dyn["reasons"] = reasons[-3:]
        dyn["wants_move"] = bool(team_matches >= 8 and satisfaction <= 32)
        # Dynamics affect morale, never hidden base ability.
        if dev:
            dev["morale"] = max(0, min(100, int(dev.get("morale") or 70) + (1 if satisfaction >= 78 else -2 if satisfaction <= 35 else 0)))


def dynamics_api(state: dict[str, Any], player_id: int) -> dict[str, Any]:
    ensure_squad_dynamics_state(state)
    row = dict(state["player_dynamics"].get(str(int(player_id))) or {})
    if not row:
        return {"role": "Sin jerarquía", "satisfaction": 70, "wants_move": False, "reasons": []}
    return row


def season_rollover_dynamics(state: dict[str, Any]) -> None:
    ensure_squad_dynamics_state(state)
    for row in state["player_dynamics"].values():
        satisfaction = int(row.get("satisfaction") or 70)
        # Summer cools extremes without erasing the previous relationship.
        row["satisfaction"] = round(satisfaction * .72 + 70 * .28)
        row["reasons"] = []
        row["team_matches"] = 0
        if row["satisfaction"] >= 42:
            row["wants_move"] = False
