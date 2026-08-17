from __future__ import annotations

"""Records and milestones from the player's own managerial spell."""

from typing import Any


def ensure_record_state(state: dict[str, Any]) -> None:
    state.setdefault("career_records", {
        "biggest_win": None, "biggest_defeat": None, "highest_scoring_match": None,
        "longest_win_streak": 0, "longest_unbeaten_streak": 0,
        "current_win_streak": 0, "current_unbeaten_streak": 0,
        "matches_managed": 0, "wins": 0, "draws": 0, "losses": 0,
    })


def update_after_controlled_match(
    state: dict[str, Any], *, date_text: str, competition: str, controlled_team_id: int,
    home_team_id: int, away_team_id: int, home_goals: int, away_goals: int,
    home_name: str, away_name: str,
) -> list[dict[str, Any]]:
    ensure_record_state(state)
    r = state["career_records"]
    home = int(home_team_id) == int(controlled_team_id)
    mine = int(home_goals) if home else int(away_goals)
    theirs = int(away_goals) if home else int(home_goals)
    opponent_id = int(away_team_id) if home else int(home_team_id)
    opponent_name = away_name if home else home_name
    result = f"{int(home_goals)}-{int(away_goals)}"
    margin = mine - theirs
    total_goals = int(home_goals) + int(away_goals)
    events: list[dict[str, Any]] = []
    r["matches_managed"] = int(r.get("matches_managed") or 0) + 1
    if margin > 0:
        r["wins"] = int(r.get("wins") or 0) + 1
        r["current_win_streak"] = int(r.get("current_win_streak") or 0) + 1
        r["current_unbeaten_streak"] = int(r.get("current_unbeaten_streak") or 0) + 1
    elif margin == 0:
        r["draws"] = int(r.get("draws") or 0) + 1
        r["current_win_streak"] = 0
        r["current_unbeaten_streak"] = int(r.get("current_unbeaten_streak") or 0) + 1
    else:
        r["losses"] = int(r.get("losses") or 0) + 1
        r["current_win_streak"] = 0
        r["current_unbeaten_streak"] = 0

    if margin > 0:
        old = r.get("biggest_win") or {}
        if margin > int(old.get("margin") or 0):
            row = {"date": date_text, "competition": competition, "opponent_id": opponent_id, "opponent_name": opponent_name, "result": result, "margin": margin}
            r["biggest_win"] = row
            if int(r["matches_managed"]) >= 3:
                events.append({"kind": "career_record", "record": "biggest_win", **row})
    if margin < 0:
        old = r.get("biggest_defeat") or {}
        if abs(margin) > int(old.get("margin") or 0):
            r["biggest_defeat"] = {"date": date_text, "competition": competition, "opponent_id": opponent_id, "opponent_name": opponent_name, "result": result, "margin": abs(margin)}
    old_high = r.get("highest_scoring_match") or {}
    if total_goals > int(old_high.get("total_goals") or -1):
        r["highest_scoring_match"] = {"date": date_text, "competition": competition, "opponent_id": opponent_id, "opponent_name": opponent_name, "result": result, "total_goals": total_goals}

    for field, current, label in (
        ("longest_win_streak", int(r.get("current_win_streak") or 0), "victorias seguidas"),
        ("longest_unbeaten_streak", int(r.get("current_unbeaten_streak") or 0), "partidos sin perder"),
    ):
        previous = int(r.get(field) or 0)
        if current > previous:
            r[field] = current
            if current in {5, 8, 10, 15, 20}:
                events.append({"kind": "career_record", "record": field, "date": date_text, "value": current, "label": label, "competition": competition})
    return events


def reset_season_streaks(state: dict[str, Any]) -> None:
    ensure_record_state(state)
    state["career_records"]["current_win_streak"] = 0
    state["career_records"]["current_unbeaten_streak"] = 0


def records_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    ensure_record_state(state)
    return dict(state["career_records"])
