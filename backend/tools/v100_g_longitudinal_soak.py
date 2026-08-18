from __future__ import annotations

"""Reanudable QA soak for V1.0-G long careers.

The normal pytest suite protects individual rules.  This tool deliberately runs
real season closures and can be resumed from JSON checkpoints so 3/10/20/30-year
career audits do not depend on a single long-lived CI process.
"""

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys
from statistics import median
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.football9394.career_special_world import process_special_competitions
from backend.app.football9394.career_tournaments import process_daily_tournaments
from backend.app.football9394.manager_career import ManagerCareerRuntime9394, _league_match_payload
from backend.app.football9394.position_roles import role_for_player


def close_season(career: ManagerCareerRuntime9394, end_year: int, offset: int = 0) -> None:
    """Close one complete season through the same July-1 career transition."""
    for player in career.squad():
        pid = str(int(player["id"]))
        contract = dict(player.get("contract") or {})
        salary = int(contract.get("salary") or 0)
        career.state["contract_overrides"][pid] = {
            **contract,
            "start": str(end_year - 1),
            "end": str(end_year + 2),
            "end_year": end_year + 2,
            "salary": salary,
            "career_inferred": True,
            "v100_g_soak_renewal": True,
        }

    schedule = career._league_schedule()
    controlled = int(career.state["team_id"])
    career.state["results"] = []
    for index, row in enumerate(schedule):
        home, away = int(row["home_team_id"]), int(row["away_team_id"])
        if home == controlled:
            home_goals, away_goals = 3, 0
        elif away == controlled:
            home_goals, away_goals = 0, 3
        else:
            home_goals = 1 if (index + offset) % 3 else 0
            away_goals = 0 if (index + offset) % 4 else 1
        career.state["results"].append(
            _league_match_payload(row["matchday"], row["id"], home, away, home_goals, away_goals)
        )
    career.state["completed_matchday"] = career._controlled_total_rounds()
    career._bootstrap_background_world(99)
    process_special_competitions(career, date(end_year, 6, 30), bootstrap=True)
    process_daily_tournaments(career, date(end_year, 6, 30), bootstrap=True)
    for month in range(1, 7):
        career._process_monthly_economy_and_ai(date(end_year, month, 1))
    career.state["current_date"] = f"{end_year}-06-30"
    result = career.advance_day()
    if result["date"] != f"{end_year}-07-01":
        raise RuntimeError(f"Unexpected rollover date: {result['date']}")


def audit(career: ManagerCareerRuntime9394, *, audit_xi: bool = False) -> dict[str, Any]:
    active = career._active_club_ids()
    controlled = int(career.state["team_id"])
    ai_clubs = [tid for tid in active if tid != controlled]
    sizes = [len(career._career_players_by_team.get(tid, [])) for tid in active]
    illegal_xi: list[int] = []
    xi_seconds = None
    if audit_xi:
        started = perf_counter()
        for tid in ai_clubs:
            if len(career._sheet(tid).starters) != 11:
                illegal_xi.append(tid)
        xi_seconds = round(perf_counter() - started, 3)

    finances = [career.state.get("club_finances", {}).get(str(tid), {}) for tid in active]
    statuses = [
        career.state["club_status"][str(tid)]
        for tid in active
        if str(tid) in career.state.get("club_status", {})
    ]
    shifts = [
        float(row.get("score") or 0) - float(row.get("initial_score") or row.get("score") or 0)
        for row in statuses
    ]
    annual = [abs(float(hist.get("change") or 0)) for row in statuses for hist in row.get("history") or []]
    health = (career.state.get("longitudinal_health") or [{}])[-1]
    return {
        "season": career.state.get("season"),
        "active_clubs": len(active),
        "illegal_ai_xi": len(illegal_xi) if audit_xi else None,
        "xi_audit_seconds": xi_seconds,
        "squad_min": min(sizes) if sizes else 0,
        "squad_median": median(sizes) if sizes else 0,
        "squad_max": max(sizes) if sizes else 0,
        "negative_cash_clubs": sum(int(row.get("cash") or 0) < 0 for row in finances),
        "max_cash": max((int(row.get("cash") or 0) for row in finances), default=0),
        "archive_seasons": len(career.state.get("season_archive") or []),
        "manager_recaps": len(career.state.get("season_recaps") or []),
        "honours": len(career.state.get("honours") or []),
        "transitions": len(career.state.get("season_transition_log") or []),
        "generated_players": len(career.state.get("generated_players") or {}),
        "health": health.get("status"),
        "save_megabytes": health.get("save_megabytes"),
        "news": len(career.state.get("news_feed") or []),
        "job_status": career.state.get("job_status"),
        "max_hierarchy_shift": round(max(map(abs, shifts)), 2) if shifts else 0,
        "max_annual_hierarchy_shift": round(max(annual), 2) if annual else 0,
        "tiers": dict(Counter(str(row.get("tier")) for row in statuses)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="V1.0-G resumable long-career soak")
    parser.add_argument("--state", type=Path, help="Input JSON checkpoint. Omit to create a new 1993-94 career.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON checkpoint")
    parser.add_argument("--start-year", type=int, required=True, help="First season end year to close, e.g. 1994")
    parser.add_argument("--seasons", type=int, default=1, help="Number of seasons to close")
    parser.add_argument("--offset", type=int, default=0, help="Deterministic result-pattern offset")
    parser.add_argument("--audit-xi", action="store_true", help="Build every AI starting XI at the final horizon")
    args = parser.parse_args()

    if args.state:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        career = ManagerCareerRuntime9394(state)
    else:
        career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=159394, through_matchday=0)

    for index, end_year in enumerate(range(args.start_year, args.start_year + args.seasons)):
        started = perf_counter()
        close_season(career, end_year, args.offset + index)
        elapsed = round(perf_counter() - started, 3)
        health = (career.state.get("longitudinal_health") or [{}])[-1]
        print(json.dumps({
            "end_year": end_year,
            "season": career.state.get("season"),
            "seconds": elapsed,
            "health": health.get("status"),
            "save_megabytes": health.get("save_megabytes"),
        }, ensure_ascii=False), flush=True)
        # Materialize each step so a long soak is crash/runner-limit resumable.
        args.output.write_text(json.dumps(career.state, ensure_ascii=False), encoding="utf-8")
        career = ManagerCareerRuntime9394(json.loads(args.output.read_text(encoding="utf-8")))

    print(json.dumps({"final_audit": audit(career, audit_xi=args.audit_xi)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
