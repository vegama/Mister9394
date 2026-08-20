from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
OUTPUT = DATA / "all_missing_bdfutbol_manifest_v114.json"
ASSETS = ROOT / "frontend" / "public" / "historical9394" / "players"


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    rows = []
    for p in snapshot.get("players", []):
        if p.get("retired") or os.path.exists(ASSETS / f"{int(p['source_id'])}.jpg"):
            continue
        rows.append({
            "source_id": int(p["source_id"]), "name": p.get("display_name"),
            "display_name": p.get("display_name"), "birth_date": p.get("birth_date"),
            "country_name": p.get("international_country_id"), "team_id": p.get("team_id"),
            "photo_status": "pending",
        })
    OUTPUT.write_text(json.dumps({"source": "global missing portraits v114", "players": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"missing": len(rows), "manifest": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
