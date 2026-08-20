from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def fold(value: str) -> str:
    raw = unicodedata.normalize("NFKD", str(value or "")).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in raw if not unicodedata.combining(c))).split())


def main() -> None:
    snapshot = json.loads((DATA / "historical_snapshot.json").read_text(encoding="utf-8"))
    source = {}
    for filename in ("mondefootball_squads_1993.json", "mondefootball_squads_1993_extra.json"):
        payload = json.loads((DATA / filename).read_text(encoding="utf-8"))
        for block in payload.values():
            for club in block.get("clubs", []):
                for row in club.get("squad", []):
                    source[(fold(row.get("full_name")), str(row.get("birth_date") or "")[:10])] = row
    linked = []
    for player in snapshot["players"]:
        if player.get("creation_batch") != "transfermarkt_roster_completion_v114" or player.get("bdfutbol_id") or player.get("mondefootball_id"):
            continue
        row = source.get((fold(player.get("display_name")), str(player.get("birth_date") or "")[:10]))
        if row and row.get("mondefootball_id"):
            player["mondefootball_id"] = str(row["mondefootball_id"])
            player["mondefootball_photo_source_url"] = row.get("photo_url")
            linked.append(int(player["source_id"]))
    (DATA / "historical_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"linked": len(linked), "source_ids": linked}, ensure_ascii=False))


if __name__ == "__main__":
    main()
