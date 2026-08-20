from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "bdfutbol_tm_added_crosscheck_v114.json"


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    by_id = {int(p["source_id"]): p for p in snapshot.get("players", [])}
    applied = []
    for row in report.get("results", []):
        if row.get("status") != "downloaded" or not row.get("bdfutbol_id"):
            continue
        player = by_id.get(int(row["source_id"]))
        if not player:
            continue
        player["bdfutbol_id"] = str(row["bdfutbol_id"])
        player["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{row['bdfutbol_id']}.html"
        player["photo_status"] = "bundled_normalized_bdfutbol_v114"
        player["photo_source_url"] = row.get("source_url") or player["bdfutbol_url"]
        applied.append(int(row["source_id"]))
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"applied": len(applied), "source_ids": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
