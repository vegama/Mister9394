from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "mondefootball_tm_added_photo_report_v114.json"


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    applied = 0
    for row in report.get("rows", []):
        if row.get("status") != "downloaded":
            continue
        player = by_id.get(int(row["source_id"]))
        if not player or player.get("bdfutbol_id"):
            continue
        player["photo_status"] = "bundled_normalized_mondefootball_v114"
        player["photo_source_url"] = row.get("source_url")
        applied += 1
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"applied": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
