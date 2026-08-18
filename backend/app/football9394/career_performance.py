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


def match_ratings_for_side(*, result: Any, sheet: Any, side_team_id: str) -> dict[str, dict[str, Any]]:
    """Return deterministic 0-10 ratings and card facts for one side.

    The calculation is intentionally compact, but it is shared by the managed
    match history and the league-wide season counters.  This is important for
    awards: every footballer in the detailed playable league is judged by the
    same scale, not only the user's squad.
    """
    side_team_id = str(side_team_id)
    own_home = side_team_id == str(result.home_team_id)
    goals_for = int(result.home.goals if own_home else result.away.goals)
    goals_against = int(result.away.goals if own_home else result.home.goals)
    outcome = "V" if goals_for > goals_against else "E" if goals_for == goals_against else "D"
    events = list(result.events)
    participant_ids = {str(p.id) for p in sheet.starters}
    participant_ids.update(str(e.player_id) for e in events if e.team_id == side_team_id and e.kind in {"substitution", "injury_substitution"} and e.player_id)
    starter_ids = {str(p.id) for p in sheet.starters}
    goal_count: dict[str, int] = {}; assist_count: dict[str, int] = {}; yellows: dict[str, int] = {}; reds: set[str] = set(); injured: set[str] = set()
    players = {str(p.id): p for p in (*sheet.starters, *sheet.bench)}
    for event in events:
        if event.team_id != side_team_id or not event.player_id:
            continue
        pid = str(event.player_id)
        if event.kind == "goal": goal_count[pid] = goal_count.get(pid, 0) + 1
        elif event.kind == "assist": assist_count[pid] = assist_count.get(pid, 0) + 1
        elif event.kind == "yellow": yellows[pid] = yellows.get(pid, 0) + 1
        elif event.kind == "second_yellow_red":
            yellows[pid] = yellows.get(pid, 0) + 1
            reds.add(pid)
        elif event.kind == "red": reds.add(pid)
        elif event.kind == "injury": injured.add(pid)

    rows: dict[str, dict[str, Any]] = {}
    for pid in participant_ids:
        base = 6.35 + (0.42 if outcome == "V" else 0.08 if outcome == "E" else -0.22)
        rating = base + goal_count.get(pid, 0) * 1.15 + assist_count.get(pid, 0) * 0.65
        player = players.get(pid)
        if goals_against == 0 and player and player.position.upper() in {"GK", "POR", "PORTERO", "DF", "CB", "LB", "RB"}:
            rating += 0.35
        rating -= yellows.get(pid, 0) * 0.20
        if pid in reds: rating -= 1.35
        if pid in injured: rating -= 0.30
        if pid not in starter_ids: rating -= 0.08
        rows[pid] = {
            "rating": round(_clip(rating), 1), "started": pid in starter_ids,
            "goals": goal_count.get(pid, 0), "assists": assist_count.get(pid, 0),
            "yellow": yellows.get(pid, 0), "red": pid in reds, "injured": pid in injured,
            "outcome": outcome, "goals_for": goals_for, "goals_against": goals_against,
        }
    return rows


def record_managed_match(
    state: dict[str, Any], *, result: Any, home_sheet: Any, away_sheet: Any,
    competition: str = "Partido", match_date: str | None = None, counts_for_league_stats: bool = False,
) -> None:
    ensure_performance_state(state)
    controlled = str(int(state["team_id"]))
    if controlled not in (str(result.home_team_id), str(result.away_team_id)):
        return
    own_home = controlled == str(result.home_team_id)
    sheet = home_sheet if own_home else away_sheet
    goals_for = int(result.home.goals if own_home else result.away.goals)
    goals_against = int(result.away.goals if own_home else result.home.goals)
    rating_rows = match_ratings_for_side(result=result, sheet=sheet, side_team_id=controlled)
    boxscore = player_match_boxscore(result, home_sheet, away_sheet).get(controlled, {})
    history = state["player_match_history"]
    for pid, facts in rating_rows.items():
        rating = float(facts["rating"])
        player_obj = next((p for p in (*sheet.starters, *sheet.bench) if str(p.id) == pid), None)
        observable = dict(boxscore.get(pid) or {})
        entry = {
            "season": str(state.get("season") or ""), "date": match_date or str(state.get("current_date") or ""),
            "competition": competition, "opponent_team_id": int(result.away_team_id if own_home else result.home_team_id),
            "home": own_home, "result": f"{goals_for}-{goals_against}", "outcome": facts["outcome"],
            "rating": rating, "started": bool(facts["started"]), "goals": int(facts["goals"]), "assists": int(facts["assists"]),
            "counts_for_league_stats": bool(counts_for_league_stats),
            "yellow": int(facts["yellow"]), "red": bool(facts["red"]),
            "observable": observable, "signature": (player_signature(player_obj) if player_obj is not None else None),
        }
        history.setdefault(pid, []).append(entry)
        history[pid] = history[pid][-60:]


def archive_managed_season(state: dict[str, Any], season: str) -> None:
    """Archive league-only season lines for every player who recorded one.

    Detailed match history remains intentionally limited to the managed squad,
    but the persistent career line is not.  This lets a player move clubs and
    still carry his league appearances/goals/rating into later profile views.
    """
    ensure_performance_state(state)
    histories = state.get("player_match_history") or {}
    development = state.get("player_development") or {}
    candidate_ids = {
        str(pid) for pid, dev in development.items()
        if int((dev or {}).get("season_appearances") or 0) > 0
        or int((dev or {}).get("season_rating_count") or 0) > 0
        or int((dev or {}).get("season_goals") or 0) > 0
        or int((dev or {}).get("season_assists") or 0) > 0
    }
    candidate_ids.update(
        str(pid) for pid, history in histories.items()
        if any(row.get("season") == season and row.get("counts_for_league_stats") for row in history)
    )
    archive_root = state["player_season_archive"]
    for pid in candidate_ids:
        dev = development.get(pid, {})
        league_rows = [
            row for row in histories.get(pid, [])
            if row.get("season") == season and row.get("counts_for_league_stats")
        ]
        rating_count = int(dev.get("season_rating_count") or 0)
        archive = {
            "season": season, "appearances": int(dev.get("season_appearances") or 0),
            "starts": int(dev.get("season_starts") or sum(1 for row in league_rows if row.get("started"))),
            "minutes": int(dev.get("season_minutes") or 0), "goals": int(dev.get("season_goals") or 0),
            "assists": int(dev.get("season_assists") or 0), "yellow_cards": int(dev.get("season_yellows") or 0),
            "red_cards": int(dev.get("season_reds") or 0),
            "average_rating": (round(float(dev.get("season_rating_total") or 0.0) / rating_count, 2) if rating_count else None),
            "competition_scope": "league_only",
        }
        existing = [row for row in archive_root.setdefault(pid, []) if row.get("season") != season]
        existing.append(archive)
        archive_root[pid] = existing[-30:]

