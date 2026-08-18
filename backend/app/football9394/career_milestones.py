from __future__ import annotations

"""Persistent, proportional career milestones for Míster 93/94.

Milestones are not a parallel simulation. They are editorial projections of
canonical facts already stored by the career: titles, movements, derbies,
manager changes and season closures. The same frozen row can therefore appear
in History, news or a later pre-match without recomputing the event from the
live world.
"""

from copy import deepcopy
from typing import Any

MAX_MILESTONES = 500


def ensure_milestone_state(state: dict[str, Any]) -> None:
    state.setdefault("career_milestones", [])


def _key(parts: list[Any]) -> str:
    return ":".join(str(part) for part in parts if part not in (None, ""))


def register_milestone(
    state: dict[str, Any], *, key: str, date_text: str, season: str, kind: str,
    title: str, summary: str, importance: int = 3, team_id: int | None = None,
    opponent_team_id: int | None = None, competition_id: int | None = None,
    competition_name: str | None = None, outcome: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one immutable milestone, deduplicated by a stable canonical key."""
    ensure_milestone_state(state)
    rows = state["career_milestones"]
    existing = next((row for row in rows if str(row.get("key")) == str(key)), None)
    if existing is not None:
        return deepcopy(existing)
    row = {
        "key": str(key), "date": str(date_text), "season": str(season),
        "kind": str(kind), "title": str(title), "summary": str(summary),
        "importance": max(1, min(10, int(importance))),
        "team_id": int(team_id) if team_id else None,
        "opponent_team_id": int(opponent_team_id) if opponent_team_id else None,
        "competition_id": int(competition_id) if competition_id else None,
        "competition_name": str(competition_name) if competition_name else None,
        "outcome": str(outcome) if outcome else None,
        "metadata": deepcopy(metadata or {}),
    }
    rows.append(row)
    rows.sort(key=lambda item: (str(item.get("date") or ""), str(item.get("key") or "")))
    state["career_milestones"] = rows[-MAX_MILESTONES:]
    return deepcopy(row)


def register_season_closure(
    state: dict[str, Any], *, date_text: str, season: str, controlled_team_id: int,
    controlled_team_name: str, recap: dict[str, Any], honours: list[dict[str, Any]],
    movements: list[dict[str, Any]], team_name_lookup,
) -> list[dict[str, Any]]:
    """Project canonical end-of-season facts into a concise milestone set."""
    created: list[dict[str, Any]] = []
    controlled = int(controlled_team_id)

    for honour in honours:
        tid = int(honour.get("team_id") or 0)
        comp_id = int(honour.get("source_id") or 0)
        comp_name = str(honour.get("competition_name") or "Competición")
        own = tid == controlled
        # Global honours already live permanently in the honours archive.
        # The career milestone stream is deliberately personal and concise so
        # a 20-30 season save never pushes the user's early chapters out.
        if not own:
            continue
        created.append(register_milestone(
            state,
            key=_key([season, "champion", honour.get("competition_kind"), comp_id, tid]),
            date_text=date_text, season=season, kind="champion",
            title=(f"Campeón: {comp_name}" if own else f"{team_name_lookup(tid)} campeón de {comp_name}"),
            summary=(f"{controlled_team_name} levanta {comp_name}." if own else f"{team_name_lookup(tid)} queda archivado como campeón de {season}."),
            importance=10 if own else 5, team_id=tid, competition_id=comp_id,
            competition_name=comp_name, outcome="title",
            metadata={"champion_manager": deepcopy(honour.get("champion_manager") or {}),
                      "runner_up_team_id": honour.get("runner_up_team_id"),
                      "runner_up_team_name": honour.get("runner_up_team_name"),
                      "margin_points": honour.get("margin_points")},
        ))

    for movement in movements:
        tid = int(movement.get("team_id") or 0)
        reason = str(movement.get("reason") or "")
        if reason not in {"promotion", "relegation"} or not tid:
            continue
        own = tid == controlled
        if not own:
            continue
        title = "Ascenso" if reason == "promotion" else "Descenso"
        from_id = int(movement.get("from_league_id") or 0)
        to_id = int(movement.get("to_league_id") or 0)
        created.append(register_milestone(
            state,
            key=_key([season, reason, tid, from_id, to_id]),
            date_text=date_text, season=season, kind=reason,
            title=(f"{title}: {controlled_team_name}" if own else f"{team_name_lookup(tid)}: {title.lower()}"),
            summary=(f"{controlled_team_name} cambia de categoría al cerrar {season}." if own else f"{team_name_lookup(tid)} cambia de categoría para la temporada siguiente."),
            importance=9 if own else 4, team_id=tid, outcome=reason,
            metadata={"from_league_id": from_id, "to_league_id": to_id},
        ))

    own_titles = [row for row in honours if int(row.get("team_id") or 0) == controlled]
    own_movement = next((row for row in movements if int(row.get("team_id") or 0) == controlled), None)
    position = recap.get("position")
    if own_titles:
        summary = f"{controlled_team_name} termina {season} con {len(own_titles)} título{'s' if len(own_titles) != 1 else ''}."
        importance = 10
        outcome = "great"
    elif own_movement and own_movement.get("reason") == "promotion":
        summary = f"{controlled_team_name} cierra {season} con un ascenso."
        importance = 9
        outcome = "great"
    elif own_movement and own_movement.get("reason") == "relegation":
        summary = f"{controlled_team_name} desciende al final de {season}."
        importance = 9
        outcome = "bad"
    else:
        summary = f"{controlled_team_name} termina {season} en {position if position is not None else '—'}ª posición."
        importance = 7 if position and int(position) <= 4 else 6
        outcome = "good" if position and int(position) <= 6 else "neutral"
    created.append(register_milestone(
        state, key=_key([season, "season_end", controlled]), date_text=date_text,
        season=season, kind="season_end", title=f"Fin de temporada {season}",
        summary=summary, importance=importance, team_id=controlled, outcome=outcome,
        metadata={"position": position, "points": recap.get("points"),
                  "titles": [row.get("competition_name") for row in own_titles],
                  "top_scorer": deepcopy(recap.get("top_scorer")),
                  "player_of_season": deepcopy(recap.get("player_of_season"))},
    ))
    return created


def register_manager_milestone(
    state: dict[str, Any], *, date_text: str, season: str, kind: str,
    team_id: int, team_name: str, summary: str, from_team_id: int | None = None,
    from_team_name: str | None = None,
) -> dict[str, Any]:
    importance = 9 if kind in {"job_change", "dismissal", "resignation", "return"} else 7
    return register_milestone(
        state, key=_key([season, kind, date_text, from_team_id, team_id]),
        date_text=date_text, season=season, kind=kind, title={
            "job_change": f"Nuevo proyecto: {team_name}",
            "dismissal": f"Fin de etapa en {team_name}",
            "resignation": f"Dimisión en {team_name}",
            "return": f"Regreso a {team_name}",
        }.get(kind, team_name), summary=summary, importance=importance,
        team_id=team_id, metadata={"from_team_id": from_team_id, "from_team_name": from_team_name},
    )


def register_rivalry_result(
    state: dict[str, Any], *, date_text: str, season: str, controlled_team_id: int,
    controlled_team_name: str, opponent_team_id: int, opponent_team_name: str,
    competition_name: str, goals_for: int, goals_against: int, heat: int,
) -> dict[str, Any] | None:
    """Store only rivalry results with enough emotional weight to deserve recall."""
    margin = abs(int(goals_for) - int(goals_against))
    if int(heat) < 65 and margin < 4:
        return None
    if goals_for > goals_against:
        verdict, outcome = "Victoria", "win"
    elif goals_for < goals_against:
        verdict, outcome = "Derrota", "loss"
    else:
        verdict, outcome = "Empate", "draw"
    importance = min(9, 5 + int(heat) // 25 + (1 if margin >= 3 else 0))
    return register_milestone(
        state, key=_key([season, "rivalry", date_text, controlled_team_id, opponent_team_id, goals_for, goals_against]),
        date_text=date_text, season=season, kind="rivalry_match",
        title=f"{verdict} ante {opponent_team_name}",
        summary=f"{controlled_team_name} {goals_for}-{goals_against} {opponent_team_name} · {competition_name}. La rivalidad queda en {heat}/100.",
        importance=importance, team_id=controlled_team_id, opponent_team_id=opponent_team_id,
        competition_name=competition_name, outcome=outcome,
        metadata={"goals_for": int(goals_for), "goals_against": int(goals_against), "rivalry_heat": int(heat)},
    )


def contextual_milestones(
    state: dict[str, Any], *, team_id: int, opponent_team_id: int | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return frozen facts relevant to the current club/opponent, strongest first."""
    ensure_milestone_state(state)
    team = int(team_id)
    opponent = int(opponent_team_id or 0)
    rows = []
    for row in state.get("career_milestones") or []:
        involved = {int(x) for x in (row.get("team_id"), row.get("opponent_team_id")) if x}
        if team not in involved:
            continue
        if opponent and opponent not in involved:
            # Club-wide milestones can still add context, but opponent-linked
            # rows always outrank them in the sort below.
            if row.get("kind") not in {"champion", "promotion", "relegation", "job_change", "return"}:
                continue
        out = deepcopy(row)
        out["opponent_relevant"] = bool(opponent and opponent in involved)
        rows.append(out)
    rows.sort(key=lambda item: (
        1 if item.get("opponent_relevant") else 0,
        int(item.get("importance") or 0),
        str(item.get("date") or ""),
    ), reverse=True)
    return rows[:max(1, int(limit))]


def milestone_snapshot(state: dict[str, Any], *, limit: int = 120) -> list[dict[str, Any]]:
    ensure_milestone_state(state)
    rows = [deepcopy(row) for row in state.get("career_milestones") or []]
    rows.sort(key=lambda item: (str(item.get("date") or ""), int(item.get("importance") or 0)), reverse=True)
    return rows[:max(1, int(limit))]
