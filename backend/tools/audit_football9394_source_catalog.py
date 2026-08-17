from __future__ import annotations

"""Repeatable gate for the deep source recovery from basedatos.mdb.

Runs against the derived JSON files so normal CI never needs the proprietary/
user-supplied MDB itself.  Rebuild those files with build_football9394_source_data.py
whenever a source database is supplied again.
"""

import json
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.football9394.snapshot_runtime import load_runtime_snapshot
from backend.app.football9394.source_catalog_runtime import load_source_catalog


def main() -> int:
    universe = load_runtime_snapshot(REPO_ROOT / "data/football9394/historical_snapshot.json")
    catalog = load_source_catalog(REPO_ROOT / "data/football9394/historical_source_catalog.json")
    active_league_ids = {int(row["source_id"]) for row in universe.payload["leagues"]}
    domestic = [team for team in universe.payload["teams"] if team.get("league_id") in active_league_ids]
    manager_ids = {int(team["manager_id"]) for team in domestic if isinstance(team.get("manager_id"), int)}
    all_manager_ids = {int(team["manager_id"]) for team in universe.payload["teams"] if isinstance(team.get("manager_id"), int)}
    stadium_missing = [int(team["source_id"]) for team in domestic if catalog.stadium(team.get("stadium_id")) is None]
    referee_missing = [league_id for league_id in active_league_ids if not catalog.referees_for_league(league_id)]
    role_players = [p for p in universe.payload["players"] if any(int(v or 0) > 0 for v in (p.get("role_ratings") or {}).values())]
    basque = [p for p in universe.payload["players"] if p.get("basque_origin")]
    traits = Counter(k for p in universe.payload["players"] for k, v in (p.get("hidden_traits") or {}).items() if v)
    dob_conflicts = sum(bool(row.get("birth_date_conflict")) for row in catalog.payload["referees"])
    athletic = [p for p in universe.payload["players"] if int(p.get("team_id") or 0) == 6]

    report = {
        "snapshot": universe.counts,
        "source_catalog": catalog.counts,
        "domestic_teams": len(domestic),
        "domestic_manager_ids": len(manager_ids),
        "domestic_manager_missing": sorted(manager_ids - set(catalog.managers_by_id)),
        "all_loaded_manager_ids": len(all_manager_ids),
        "all_loaded_manager_missing": sorted(all_manager_ids - set(catalog.managers_by_id)),
        "historical_leagues": len(active_league_ids),
        "leagues_without_referees": sorted(referee_missing),
        "domestic_clubs_without_stadium": sorted(stadium_missing),
        "players_with_explicit_secondary_roles": len(role_players),
        "hidden_trait_counts": dict(sorted(traits.items())),
        "basque_origin_players": len(basque),
        "athletic_squad": len(athletic),
        "athletic_squad_basque_origin": sum(bool(p.get("basque_origin")) for p in athletic),
        "referee_birth_date_conflicts_arbitro_vs_arbitro2": dob_conflicts,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))

    assert len(domestic) == 410
    assert len(manager_ids) == 404
    assert not report["domestic_manager_missing"]
    assert not report["all_loaded_manager_missing"]
    assert len(active_league_ids) == 23
    assert not referee_missing
    assert not stadium_missing
    assert len(athletic) == 22 and all(bool(p.get("basque_origin")) for p in athletic)
    assert dob_conflicts == 1064
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
