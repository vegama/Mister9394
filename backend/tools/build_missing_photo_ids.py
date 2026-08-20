from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=Path("data/football9394/historical_snapshot.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("frontend/public/historical9394/players"))
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    ids = [int(row["source_id"]) for row in snapshot.get("players", []) if row.get("source_id") and not (args.root / f"{int(row['source_id'])}.jpg").exists()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ids, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"missing_player_ids": len(ids)})


if __name__ == "__main__":
    main()
