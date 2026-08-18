from __future__ import annotations

"""Best-effort asset micro-pass to run alongside every development checkpoint.

The asset lane must never block the main product work.  This command first
normalizes any verified BDFutbol portraits already present locally, then makes a
small bounded download attempt, normalizes successful downloads, and writes one
traceable JSON report.  Network/source failures are recorded rather than raised
as a checkpoint failure.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.tools.download_bdfutbol_photos import (  # noqa: E402
    DEFAULT_GAME_DIR,
    DEFAULT_QUEUE,
    DEFAULT_RAW_DIR,
    download_queue,
)
from backend.tools.normalize_bdfutbol_photos import normalize_directory  # noqa: E402


def _photo_count(path: Path) -> int:
    return sum(1 for p in path.glob("*.jpg") if p.is_file()) if path.exists() else 0


def run_asset_pass(*, limit: int, delay: float) -> dict:
    before = _photo_count(DEFAULT_GAME_DIR)
    normalized_before = normalize_directory(DEFAULT_RAW_DIR, DEFAULT_GAME_DIR, queue_path=DEFAULT_QUEUE)
    download = download_queue(
        DEFAULT_QUEUE,
        DEFAULT_RAW_DIR,
        DEFAULT_GAME_DIR,
        limit=max(0, int(limit)),
        delay=max(0.0, float(delay)),
    )
    normalized_after = normalize_directory(DEFAULT_RAW_DIR, DEFAULT_GAME_DIR, queue_path=DEFAULT_QUEUE)
    after = _photo_count(DEFAULT_GAME_DIR)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "best_effort_non_blocking_every_development_pass",
        "asset_lane": "historical_player_portraits_bdfutbol",
        "runtime_player_photos_before": before,
        "runtime_player_photos_after": after,
        "runtime_player_photos_added": max(0, after - before),
        "normalize_existing": {
            key: normalized_before.get(key)
            for key in ("status", "converted", "skipped_existing", "unresolved", "invalid")
        },
        "download_attempt": download,
        "normalize_downloads": {
            key: normalized_after.get(key)
            for key in ("status", "converted", "skipped_existing", "unresolved", "invalid")
        },
        "checkpoint_blocked": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the non-blocking Míster 93/94 asset micro-pass")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run_asset_pass(limit=args.limit, delay=args.delay)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
