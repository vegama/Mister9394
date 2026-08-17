from __future__ import annotations

"""Compact managed-squad match history and ratings.

Only the user's footballers receive detailed per-match history.  This keeps a
multi-season save small while making the squad memorable through performance.
"""

from typing import Any

from .match_signatures import player_match_boxscore, player_signature


def _clip(value: float, lo: float = 4.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def ensure_performance_state(state: dict[str, Any]) -> None:
    state.setdefault("player_match_history", {})
    state.setdefault("player_season_archive", {})


def record_managed_match(
    state: dict[str, Any], *, result: Any, home_sheet: Any, away_sheet: Any,
    competition: str = "Partido", match_date: str | None = None,
) -> None:
    ensure_performance_state(state)
    controlled = str(int(state["team_id"]))
    if controlled not in (str(result.home_team_id), str(result.away_team_id)):
        return
    own_home = controlled == str(result.home_team_id)
    sheet = home_sheet if own_home else away_sheet
    goals_for = int(result.home.goals if own_home else result.away.goals)
    goals_against = int(result.away.goals if own_home else result.home.goals)
    outcome = "V" if goals_for > goals_against else "E" if goals_for == goals_against else "D"
    events = list(result.events)
    participant_ids = {str(p.id) for p in sheet.starters}
    participant_ids.update(str(e.player_id) for e in events if e.team_id == controlled and e.kind in {"substitution", "injury_substitution"} and e.player_id)
    starter_ids = {str(p.id) for p in sheet.starters}
    goal_count: dict[str, int] = {}; assist_count: dict[str, int] = {}; yellows: dict[str, int] = {}; reds: set[str] = set(); injured: set[str] = set()
    boxscore = player_match_boxscore(result, home_sheet, away_sheet).get(controlled, {})
    for event in events:
        if event.team_id != controlled or not event.player_id:
            continue
        pid = str(event.player_id)
        if event.kind == "goal": goal_count[pid] = goal_count.get(pid, 0) + 1
        elif event.kind == "assist": assist_count[pid] = assist_count.get(pid, 0) + 1
        elif event.kind == "yellow": yellows[pid] = yellows.get(pid, 0) + 1
        elif event.kind in {"red", "second_yellow_red"}: reds.add(pid)
        elif event.kind == "injury": injured.add(pid)

    dev = state.get("player_development") or {}
    history = state["player_match_history"]
    for pid in participant_ids:
        base = 6.35 + (0.42 if outcome == "V" else 0.08 if outcome == "E" else -0.22)
        rating = base + goal_count.get(pid, 0) * 1.15 + assist_count.get(pid, 0) * 0.65
        if goals_against == 0:
            player = next((p for p in (*sheet.starters, *sheet.bench) if str(p.id) == pid), None)
            if player and player.position.upper() in {"GK", "DF", "CB", "LB", "RB"}: rating += 0.35
        rating -= yellows.get(pid, 0) * 0.20
        if pid in reds: rating -= 1.35
        if pid in injured: rating -= 0.30
        if pid not in starter_ids: rating -= 0.08
        rating = round(_clip(rating), 1)
        row = dev.setdefault(pid, {})
        if pid in starter_ids:
            row["season_starts"] = int(row.get("season_starts") or 0) + 1
        row["season_rating_total"] = round(float(row.get("season_rating_total") or 0.0) + rating, 2)
        row["season_rating_count"] = int(row.get("season_rating_count") or 0) + 1
        row["season_yellows"] = int(row.get("season_yellows") or 0) + yellows.get(pid, 0)
        row["season_reds"] = int(row.get("season_reds") or 0) + (1 if pid in reds else 0)
        player_obj = next((p for p in (*sheet.starters, *sheet.bench) if str(p.id) == pid), None)
        observable = dict(boxscore.get(pid) or {})
        entry = {
            "season": str(state.get("season") or ""), "date": match_date or str(state.get("current_date") or ""),
            "competition": competition, "opponent_team_id": int(result.away_team_id if own_home else result.home_team_id),
            "home": own_home, "result": f"{goals_for}-{goals_against}", "outcome": outcome,
            "rating": rating, "started": pid in starter_ids, "goals": goal_count.get(pid, 0), "assists": assist_count.get(pid, 0),
            "yellow": yellows.get(pid, 0), "red": pid in reds,
            "observable": observable, "signature": (player_signature(player_obj) if player_obj is not None else None),
        }
        history.setdefault(pid, []).append(entry)
        history[pid] = history[pid][-60:]


def archive_managed_season(state: dict[str, Any], season: str) -> None:
    ensure_performance_state(state)
    controlled = str(int(state["team_id"]))
    # The caller owns roster knowledge; archive every player with a detailed
    # history in this season so transferred-out footballers do not disappear.
    for pid, history in list(state["player_match_history"].items()):
        season_rows = [row for row in history if row.get("season") == season]
        if not season_rows:
            continue
        dev = (state.get("player_development") or {}).get(pid, {})
        archive = {
            "season": season, "appearances": int(dev.get("season_appearances") or len(season_rows)),
            "starts": int(dev.get("season_starts") or sum(1 for row in season_rows if row.get("started"))),
            "minutes": int(dev.get("season_minutes") or 0), "goals": int(dev.get("season_goals") or 0),
            "assists": int(dev.get("season_assists") or 0), "yellow_cards": int(dev.get("season_yellows") or 0),
            "red_cards": int(dev.get("season_reds") or 0),
            "average_rating": round(float(dev.get("season_rating_total") or 0.0) / max(1, int(dev.get("season_rating_count") or 0)), 2),
        }
        state["player_season_archive"].setdefault(pid, []).append(archive)
