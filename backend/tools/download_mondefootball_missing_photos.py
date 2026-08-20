from __future__ import annotations

"""Download missing portraits with an exact Mondefootball person id.

The historical snapshot already carries the Mondefootball id for these rows, so
this tool never guesses by name. It only accepts a real image response from the
stable hs-data URL and normalizes it to the runtime portrait contract.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import io
import json
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "football9394" / "historical_snapshot.json"
OUTPUT = ROOT / "frontend" / "public" / "historical9394" / "players"
RAW = ROOT / "data" / "football9394" / "asset_recovery_raw" / "player_mondefootball"
PHOTO_URL = "https://s.hs-data.com/gfx/person/cropped/250x250/{monde_id}.png"
HEADERS = {"User-Agent": "Mister9394HistoricalGame/1.0"}


def normalize(content: bytes, destination: Path) -> None:
    with Image.open(io.BytesIO(content)) as im:
        rgb = im.convert("RGB")
        out = ImageOps.fit(rgb, (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        destination.parent.mkdir(parents=True, exist_ok=True)
        out.save(destination, "JPEG", quality=88, optimize=True)


def is_black_placeholder(content: bytes) -> bool:
    with Image.open(io.BytesIO(content)) as im:
        rgb = im.convert("RGB").resize((20, 20))
        pixels = list(rgb.getdata())
        if not pixels:
            return True
        black_ratio = sum(1 for pixel in pixels if max(pixel) <= 8) / len(pixels)
        mean = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3)
        return black_ratio >= 0.8 or mean <= 3.0


def fetch(row: dict[str, Any], timeout: float) -> dict[str, Any]:
    source_id = int(row["source_id"])
    monde_id = str(row["mondefootball_id"])
    destination = OUTPUT / f"{source_id}.jpg"
    if destination.exists():
        return {"source_id": source_id, "status": "already_present"}
    url = PHOTO_URL.format(monde_id=monde_id)
    try:
        response = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        if response.status_code != 200 or not response.content:
            return {"source_id": source_id, "name": row.get("display_name"), "mondefootball_id": monde_id, "status": "missing", "http": response.status_code}
        with Image.open(io.BytesIO(response.content)) as im:
            im.verify()
        if is_black_placeholder(response.content):
            return {"source_id": source_id, "name": row.get("display_name"), "mondefootball_id": monde_id, "status": "placeholder_black", "source_url": url}
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / f"{source_id}_{monde_id}.png").write_bytes(response.content)
        normalize(response.content, destination)
        return {"source_id": source_id, "name": row.get("display_name"), "team_id": row.get("team_id"), "mondefootball_id": monde_id, "status": "downloaded", "source_url": url}
    except Exception as exc:
        return {"source_id": source_id, "name": row.get("display_name"), "mondefootball_id": monde_id, "status": "failed", "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "football9394" / "mondefootball_missing_photo_report.json")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    rows = [row for row in snapshot.get("players", []) if row.get("mondefootball_id") and not (OUTPUT / f"{int(row['source_id'])}.jpg").exists()]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(32, int(args.workers)))) as pool:
        futures = [pool.submit(fetch, row, float(args.timeout)) for row in rows]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: int(row["source_id"]))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Mondefootball exact person id / hs-data image endpoint",
        "candidates": len(rows),
        "downloaded": sum(row["status"] == "downloaded" for row in results),
        "already_present": sum(row["status"] == "already_present" for row in results),
        "missing": sum(row["status"] == "missing" for row in results),
        "failed": sum(row["status"] == "failed" for row in results),
        "rows": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("candidates", "downloaded", "already_present", "missing", "failed")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
