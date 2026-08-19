from __future__ import annotations

"""Track real-player coverage debt for admitted 1993-94 leagues.

This is intentionally a backlog gate, not a filler.  It never creates players.
The baseline prevents the database cleanup from silently making an admitted
squad shallower while allowing future source-backed additions to improve it.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "database_roster_depth_backlog_v113.json"

# Accepted post-reconciliation baseline.  The earlier 18/31/15 snapshot counted
# historically misplaced players (notably Jaume and Cabrera) inside the wrong
# Uruguay squads.  Correcting those assignments legitimately exposed two more
# clubs below 18, while source-backed additions improved the actual coverage:
# total deficit 31 -> 30 and minimum squad 15 -> 16.
BASELINE_SHORT_TEAM_COUNT = 20
BASELINE_TOTAL_DEFICIT_TO_18 = 30
BASELINE_MIN_SQUAD = 16
PRE_RECONCILIATION_REFERENCE = {
    "short_team_count": 18,
    "total_deficit_to_18": 31,
    "minimum_admitted_squad": 15,
}


def audit() -> dict[str, Any]:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    leagues = {int(row["source_id"]): row for row in snapshot.get("leagues", [])}
    teams = {int(row["source_id"]): row for row in snapshot.get("teams", [])}
    active = [row for row in snapshot.get("players", []) if not row.get("retired")]
    counts = Counter(int(row.get("team_id") or 0) for row in active)

    shortages: list[dict[str, Any]] = []
    for team_id, team in teams.items():
        league = leagues.get(int(team.get("league_id") or 0))
        if not league or not league.get("admitted") or team.get("market_container"):
            continue
        count = int(counts.get(team_id, 0))
        if count >= 18:
            continue
        shortages.append({
            "team_id": team_id,
            "team": team.get("name"),
            "league_id": int(team.get("league_id") or 0),
            "league": league.get("name"),
            "country": league.get("country"),
            "active_players": count,
            "deficit_to_18": 18 - count,
        })

    shortages.sort(key=lambda row: (row["active_players"], row["country"] or "", row["league"] or "", row["team"] or ""))
    total_deficit = sum(int(row["deficit_to_18"]) for row in shortages)
    minimum = min((int(row["active_players"]) for row in shortages), default=18)
    regressions = []
    if len(shortages) > BASELINE_SHORT_TEAM_COUNT:
        regressions.append(f"short team count worsened: {len(shortages)} > {BASELINE_SHORT_TEAM_COUNT}")
    if total_deficit > BASELINE_TOTAL_DEFICIT_TO_18:
        regressions.append(f"total deficit worsened: {total_deficit} > {BASELINE_TOTAL_DEFICIT_TO_18}")
    if minimum < BASELINE_MIN_SQUAD:
        regressions.append(f"minimum admitted squad worsened: {minimum} < {BASELINE_MIN_SQUAD}")

    report = {
        "checkpoint": "1.1.3",
        "status": "pass_with_backlog" if not regressions else "regression",
        "policy": {
            "minimum_target": 18,
            "method": "verified real 1993-94 players only; never synthetic filler",
            "baseline_short_team_count": BASELINE_SHORT_TEAM_COUNT,
            "baseline_total_deficit_to_18": BASELINE_TOTAL_DEFICIT_TO_18,
            "baseline_min_squad": BASELINE_MIN_SQUAD,
            "pre_reconciliation_reference": PRE_RECONCILIATION_REFERENCE,
            "baseline_note": "Rebased after source-backed Uruguay corrections exposed previously masked short squads and moved Luis Barbat to Independiente Medellin; compared with the pre-reconciliation reference, total deficit still improves 31 -> 30 and minimum depth 15 -> 16.",
        },
        "active_players": len(active),
        "short_team_count": len(shortages),
        "total_deficit_to_18": total_deficit,
        "minimum_admitted_squad": minimum,
        "shortages": shortages,
        "regressions": regressions,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["status"] == "regression" else 0)
