from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
OUTPUT = DATA / "transfermarkt_roster_completion_photo_manifest_v114.json"


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    rows = []
    for player in snapshot.get("players", []):
        if player.get("creation_batch") != "transfermarkt_roster_completion_v114":
            continue
        rows.append({
            "source_id": int(player["source_id"]),
            "name": player.get("display_name"),
            "display_name": player.get("display_name"),
            "birth_date": player.get("birth_date"),
            "country_name": player.get("international_country_id"),
            "team_id": player.get("team_id"),
            "photo_status": "pending",
        })
    payload = {"source": "Transfermarkt roster completion v1.1.4", "players": rows}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"players": len(rows), "manifest": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
