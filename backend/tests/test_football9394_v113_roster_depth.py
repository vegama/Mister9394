from __future__ import annotations

import json
from pathlib import Path

from backend.tools.audit_roster_depth_v113 import audit

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def test_v113_admitted_roster_depth_did_not_regress_during_identity_cleanup():
    report = audit()
    assert report["status"] == "pass_with_backlog"
    assert report["minimum_admitted_squad"] >= 16
    assert report["short_team_count"] <= 20
    assert report["total_deficit_to_18"] <= 30


def test_v113_roster_backlog_contains_only_active_admitted_real_teams():
    report = json.loads((DATA / "database_roster_depth_backlog_v113.json").read_text(encoding="utf-8"))
    snapshot = json.loads((DATA / "historical_snapshot.json").read_text(encoding="utf-8"))
    teams = {int(row["source_id"]): row for row in snapshot["teams"]}
    leagues = {int(row["source_id"]): row for row in snapshot["leagues"]}
    for row in report["shortages"]:
        team = teams[int(row["team_id"])]
        league = leagues[int(row["league_id"])]
        assert not team.get("market_container")
        assert league.get("admitted") is True
        assert 11 <= int(row["active_players"]) < 18
        assert int(row["deficit_to_18"]) == 18 - int(row["active_players"])
