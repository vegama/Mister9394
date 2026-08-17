from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.football9394.mdb_import import load_historical_snapshot
from backend.app.football9394.mdb_jet4 import json_safe
from backend.app.football9394.source_catalog import build_source_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Build derived Míster 93/94 JSON sources from the supplied Jet4 MDB")
    parser.add_argument("mdb", type=Path)
    parser.add_argument("--snapshot", type=Path, default=REPO_ROOT / "data/football9394/historical_snapshot.json")
    parser.add_argument("--catalog", type=Path, default=REPO_ROOT / "data/football9394/historical_source_catalog.json")
    args = parser.parse_args()

    snapshot = json_safe(load_historical_snapshot(args.mdb).to_dict())
    catalog = build_source_catalog(args.mdb)
    args.snapshot.parent.mkdir(parents=True, exist_ok=True)
    args.snapshot.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"snapshot: {args.snapshot} ({args.snapshot.stat().st_size:,} bytes)")
    print(f"source catalog: {args.catalog} ({args.catalog.stat().st_size:,} bytes)")
    print(json.dumps(catalog.get("counts", {}), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
