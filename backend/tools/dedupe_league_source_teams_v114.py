from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
CATALOG = DATA / "historical_source_catalog.json"
REPORT = DATA / "league_source_team_dedupe_v114.json"
LEAGUE_NAMES = {"Divizia A", "A Grupa", "Ekstraklasa", "Allsvenskan", "Tippeligaen", "Superligaen", "Bundesliga", "Nationalliga A", "Vyshcha Liha"}


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    teams = snapshot["teams"]
    players = snapshot["players"]
    groups = defaultdict(list)
    for team in teams:
        if team.get("activation_reason") == "league_source_only" and (team.get("pending_activation") or {}).get("league") in LEAGUE_NAMES or team.get("activation_reason") == "league_source_only":
            groups[str(team.get("name") or "").casefold()].append(team)
    removed = []
    redirects = {}
    for _, rows in groups.items():
        if len(rows) < 2:
            continue
        # The lowest generated ID is the first canonical row; enrich it from all copies.
        rows.sort(key=lambda x: int(x["source_id"]))
        keep = rows[0]
        for duplicate in rows[1:]:
            old_id = int(duplicate["source_id"]); new_id = int(keep["source_id"])
            redirects[old_id] = new_id
            if not keep.get("stadium_id") and duplicate.get("stadium_id"):
                keep["stadium_id"] = duplicate["stadium_id"]
                keep["venue_source_status"] = duplicate.get("venue_source_status")
                keep["venue_source_url"] = duplicate.get("venue_source_url")
                keep["venue_source_label"] = duplicate.get("venue_source_label")
            for player in players:
                if int(player.get("team_id") or 0) == old_id:
                    player["team_id"] = new_id
            removed.append({"removed_team_id": old_id, "kept_team_id": new_id, "team": keep.get("name")})
    snapshot["teams"] = [t for t in teams if int(t["source_id"]) not in redirects]
    for row in catalog.get("stadiums", []):
        if int(row.get("historical_team_id") or 0) in redirects:
            row["historical_team_id"] = redirects[int(row["historical_team_id"])]
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"status": "complete", "duplicate_teams_removed": len(removed), "redirects": redirects, "removed": removed}
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"duplicate_teams_removed": len(removed), "canonical_teams": len(groups)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
