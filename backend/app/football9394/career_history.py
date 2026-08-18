from __future__ import annotations

"""Frozen season dossiers for the persistent Míster 93/94 career.

A dossier is deliberately independent from the live world.  It answers the
player's historical question ("what happened that season while I was there?")
without consulting today's squads, managers, cup stage or current club.
"""

from copy import deepcopy
from datetime import date
from typing import Any


def _season_years(season: str) -> tuple[int, int]:
    raw = str(season or "")
    try:
        start = int(raw.split("-", 1)[0])
    except (TypeError, ValueError):
        start = 1993
    return start, start + 1


def _date_or(value: Any, fallback: date) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return fallback


def _manager_segments(state: dict[str, Any], season: str, tables: dict[int, list[dict[str, Any]]], honours: list[dict[str, Any]], movements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start_year, end_year = _season_years(season)
    season_start = date(start_year, 7, 1)
    season_end = date(end_year, 6, 30)
    profile = state.get("user_manager") or {}
    rows = [dict(row) for row in profile.get("tenures") or []]
    current = dict(profile.get("current_tenure") or {})
    if current.get("team_id"):
        rows.append(current)

    segments: list[dict[str, Any]] = []
    for tenure in rows:
        if not tenure.get("team_id"):
            continue
        started = _date_or(tenure.get("started_on"), season_start)
        ended = _date_or(tenure.get("ended_on"), season_end) if tenure.get("ended_on") else season_end
        if ended < season_start or started > season_end:
            continue
        team_id = int(tenure["team_id"])
        league_id = None
        final_row: dict[str, Any] | None = None
        for lid, table in tables.items():
            candidate = next((row for row in table if int(row.get("team_id") or 0) == team_id), None)
            if candidate is not None:
                league_id = int(lid)
                final_row = deepcopy(candidate)
                break
        titles = [deepcopy(row) for row in honours if int(row.get("team_id") or 0) == team_id]
        movement = next((deepcopy(row) for row in movements if int(row.get("team_id") or 0) == team_id), None)
        segments.append({
            "team_id": team_id,
            "team_name": tenure.get("team_name") or (final_row or {}).get("team_name") or f"Club {team_id}",
            "started_on": max(started, season_start).isoformat(),
            "ended_on": min(ended, season_end).isoformat(),
            "reason": tenure.get("reason") if tenure.get("ended_on") else "season_end",
            "league_id": league_id,
            "final_table_row": final_row,
            "titles": titles,
            "movement": movement,
        })
    segments.sort(key=lambda row: (row.get("started_on") or "", int(row.get("team_id") or 0)))
    return segments


def build_season_dossier(
    state: dict[str, Any], *, season: str, closed_on: str,
    tables: dict[int, list[dict[str, Any]]], honours: list[dict[str, Any]],
    movements: list[dict[str, Any]], qualifiers: dict[str, list[int]],
    recap: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a deep-frozen dossier.  No returned object aliases live state."""
    segments = _manager_segments(state, season, tables, honours, movements)
    international = []
    start_year, end_year = _season_years(season)
    lo, hi = date(start_year, 7, 1), date(end_year, 6, 30)
    for row in state.get("international_history") or []:
        when = _date_or(row.get("date"), lo)
        if lo <= when <= hi:
            international.append(deepcopy(row))
    return {
        "dossier_version": 2,
        "season": str(season),
        "closed_on": str(closed_on),
        "manager_segments": segments,
        "champions": deepcopy(honours),
        "movements": deepcopy(movements),
        "continental_qualifiers": deepcopy(qualifiers),
        "league_tables": {str(lid): deepcopy(table) for lid, table in tables.items()},
        "league_awards": deepcopy((recap or {}).get("league_awards") or {}),
        "managed_recap": deepcopy(recap or {}),
        "career_milestones": deepcopy((recap or {}).get("milestones") or []),
        "international_milestones": international,
        "anomalies": {
            "no_awards": not bool((recap or {}).get("league_awards")),
            "no_movements": not bool(movements),
            "no_champions": not bool(honours),
        },
    }


def ensure_history_dossiers(state: dict[str, Any]) -> None:
    """Backfill dossiers for old saves that only had season_archive/recaps."""
    dossiers = state.setdefault("season_dossiers", [])
    known = {str(row.get("season")) for row in dossiers if row.get("season")}
    recaps = {str(row.get("season")): row for row in state.get("season_recaps") or [] if row.get("season")}
    for archive in state.get("season_archive") or []:
        season = str(archive.get("season") or "")
        if not season or season in known:
            continue
        tables = {int(k): list(v or []) for k, v in (archive.get("league_tables") or {}).items() if str(k).lstrip("-").isdigit()}
        dossier = build_season_dossier(
            state,
            season=season,
            closed_on=str(archive.get("closed_on") or ""),
            tables=tables,
            honours=list(archive.get("honours") or []),
            movements=list(archive.get("movements") or []),
            qualifiers=dict(archive.get("continental_qualifiers") or {}),
            recap=recaps.get(season),
        )
        dossier["migrated_from_legacy_archive"] = True
        dossiers.append(dossier)
        known.add(season)
    dossiers.sort(key=lambda row: str(row.get("season") or ""))
    if len(dossiers) > 60:
        state["season_dossiers"] = dossiers[-60:]
