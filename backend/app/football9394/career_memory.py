from __future__ import annotations

"""Persistent football memory for the managed career.

The world already simulates results, transfers and squad mood.  This module
makes those facts accumulate meaning: rivalries gain heat, the controlled
manager builds trust/friction with players, and memorable events remain
queryable instead of disappearing after the next click on Continue.
"""

from datetime import date
from typing import Any, Iterable


def _pair(a: int, b: int) -> tuple[int, int]:
    return tuple(sorted((int(a), int(b))))


def _pair_key(a: int, b: int) -> str:
    x, y = _pair(a, b)
    return f"{x}:{y}"


def ensure_career_memory(state: dict[str, Any], universe: Any) -> None:
    state.setdefault("manager_player_relationships", {})
    state.setdefault("football_memories", [])
    rivalries = state.setdefault("club_rivalries", {})
    if rivalries:
        return
    for team in universe.payload.get("teams", []):
        tid = int(team["source_id"])
        for field, heat, label in (("main_rival_id", 72, "rival histórico"), ("regional_rival_id", 48, "rival regional")):
            other = team.get(field)
            if not isinstance(other, int) or other <= 0 or other == tid:
                continue
            key = _pair_key(tid, other)
            row = rivalries.setdefault(key, {
                "team_a_id": min(tid, other), "team_b_id": max(tid, other),
                "heat": heat, "source_heat": heat, "source": label,
                "meetings": 0, "last_meeting": None, "history": [],
            })
            row["heat"] = max(int(row.get("heat") or 0), heat)
            row["source_heat"] = max(int(row.get("source_heat") or 0), heat)


def _remember(state: dict[str, Any], item: dict[str, Any]) -> None:
    rows = state.setdefault("football_memories", [])
    rows.append(item)
    state["football_memories"] = rows[-400:]


def record_match_memory(
    state: dict[str, Any], universe: Any, *, date_text: str, home_team_id: int, away_team_id: int,
    home_goals: int, away_goals: int, competition: str = "Partido",
) -> dict[str, Any] | None:
    ensure_career_memory(state, universe)
    key = _pair_key(home_team_id, away_team_id)
    rivalries = state["club_rivalries"]
    row = rivalries.get(key)
    goal_gap = abs(int(home_goals) - int(away_goals))
    # Non-source rivalries can emerge after repeated high-stakes meetings; we
    # only create them once the clubs have met before in career memory.
    if row is None:
        controlled = int(state.get("team_id") or 0)
        if controlled not in (int(home_team_id), int(away_team_id)):
            return None
        prior = [m for m in state.get("football_memories", []) if m.get("kind") == "meeting" and m.get("pair") == key]
        _remember(state, {"kind": "meeting", "date": date_text, "pair": key})
        if len(prior) < 2:
            return None
        row = rivalries.setdefault(key, {
            "team_a_id": min(int(home_team_id), int(away_team_id)),
            "team_b_id": max(int(home_team_id), int(away_team_id)),
            "heat": 18, "source_heat": 0, "source": "rivalidad nacida en la partida",
            "meetings": len(prior), "last_meeting": None, "history": [],
        })
    delta = 1
    if goal_gap <= 1:
        delta += 2
    if "copa" in competition.casefold() or "final" in competition.casefold() or "europa" in competition.casefold():
        delta += 3
    if goal_gap >= 4:
        delta += 1  # humiliations are remembered too
    row["meetings"] = int(row.get("meetings") or 0) + 1
    row["heat"] = max(int(row.get("source_heat") or 0), min(100, int(row.get("heat") or 0) + delta))
    row["last_meeting"] = date_text
    history = row.setdefault("history", [])
    history.append({
        "date": date_text, "competition": competition,
        "home_team_id": int(home_team_id), "away_team_id": int(away_team_id),
        "home_goals": int(home_goals), "away_goals": int(away_goals), "heat_delta": delta,
    })
    row["history"] = history[-12:]
    _remember(state, {"kind": "rivalry_match", "date": date_text, "pair": key, "heat": row["heat"], "competition": competition})
    return row


def record_transfer_memory(
    state: dict[str, Any], universe: Any, *, date_text: str, player_id: int,
    from_team_id: int, to_team_id: int, fee: int = 0, player_overall: int = 60,
) -> dict[str, Any] | None:
    ensure_career_memory(state, universe)
    if not from_team_id or not to_team_id or int(from_team_id) == int(to_team_id):
        return None
    key = _pair_key(from_team_id, to_team_id)
    row = state["club_rivalries"].get(key)
    if row is None:
        return None
    delta = 2 + (2 if int(player_overall) >= 78 else 0) + (1 if int(fee) > 0 else 0)
    row["heat"] = min(100, int(row.get("heat") or 0) + delta)
    history = row.setdefault("history", [])
    history.append({"date": date_text, "kind": "transfer", "player_id": int(player_id), "from_team_id": int(from_team_id), "to_team_id": int(to_team_id), "fee": int(fee), "heat_delta": delta})
    row["history"] = history[-12:]
    _remember(state, {"kind": "rival_transfer", "date": date_text, "pair": key, "player_id": int(player_id), "heat": row["heat"]})
    return row


def rivalry_between(state: dict[str, Any], team_a_id: int, team_b_id: int) -> dict[str, Any] | None:
    return (state.get("club_rivalries") or {}).get(_pair_key(team_a_id, team_b_id))


def rivalry_snapshot(state: dict[str, Any], universe: Any, team_id: int, *, limit: int = 6) -> list[dict[str, Any]]:
    ensure_career_memory(state, universe)
    tid = int(team_id)
    out = []
    for row in (state.get("club_rivalries") or {}).values():
        a, b = int(row["team_a_id"]), int(row["team_b_id"])
        if tid not in (a, b):
            continue
        other = b if a == tid else a
        team = universe.team(other) or {}
        out.append({**row, "opponent_id": other, "opponent_name": team.get("name") or str(other)})
    out.sort(key=lambda r: (-int(r.get("heat") or 0), str(r.get("opponent_name") or "")))
    return out[:max(1, int(limit))]


def _relationship_row(state: dict[str, Any], player_id: int) -> dict[str, Any]:
    rows = state.setdefault("manager_player_relationships", {})
    return rows.setdefault(str(int(player_id)), {"trust": 55, "history": [], "last_change": None})


def adjust_player_manager_relationship(
    state: dict[str, Any], *, player_id: int, date_text: str, delta: int, reason: str,
) -> dict[str, Any]:
    row = _relationship_row(state, player_id)
    before = int(row.get("trust") or 55)
    after = max(0, min(100, before + int(delta)))
    row["trust"] = after
    row["last_change"] = {"date": date_text, "delta": int(delta), "reason": reason}
    history = row.setdefault("history", [])
    history.append(dict(row["last_change"]))
    row["history"] = history[-16:]
    return relationship_api(state, player_id)


def update_relationships_after_match(
    state: dict[str, Any], *, date_text: str, squad: Iterable[dict[str, Any]],
    starter_ids: Iterable[int | str], appeared_ids: Iterable[int | str], won: bool, drew: bool,
) -> None:
    starters = {int(x) for x in starter_ids if str(x).isdigit()}
    appeared = {int(x) for x in appeared_ids if str(x).isdigit()}
    dynamics = state.get("player_dynamics") or {}
    for player in squad:
        pid = int(player["source_id"])
        dyn = dynamics.get(str(pid)) or {}
        role = str(dyn.get("role") or "")
        if pid in starters:
            delta = 2 if won else 1 if drew else 0
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=delta, reason="confianza en el once")
        elif pid in appeared:
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=1, reason="participación desde el banquillo")
        elif role == "Figura":
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=-2, reason="figura sin minutos")
        elif role == "Titular":
            adjust_player_manager_relationship(state, player_id=pid, date_text=date_text, delta=-1, reason="titular sin minutos")


def relationship_api(state: dict[str, Any], player_id: int) -> dict[str, Any]:
    row = _relationship_row(state, player_id)
    trust = int(row.get("trust") or 55)
    if trust >= 82:
        label = "Leal al mánager"
    elif trust >= 68:
        label = "Buena relación"
    elif trust >= 48:
        label = "Profesional"
    elif trust >= 30:
        label = "Relación tensa"
    else:
        label = "Ruptura de confianza"
    return {"trust": trust, "label": label, "last_change": row.get("last_change"), "history": list(row.get("history") or [])[-6:]}
