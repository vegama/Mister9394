from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

import httpx
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "football9394" / "historical_snapshot.json"
OUTPUT = ROOT / "frontend" / "public" / "historical9394" / "players"
RAW = ROOT / "data" / "football9394" / "asset_recovery_raw" / "player_nft"
SEARCH = "https://www.national-football-teams.com/search.html"
PROFILE = "https://www.national-football-teams.com/player/{id}/x.html"
HEADERS = {"User-Agent": "Mister9394HistoricalGame/1.0"}
PLAYER_RE = re.compile(r'<tr[^>]*>.*?href="/player/(\d+)\.html".*?</tr>', re.S | re.I)
PHOTO_RE = re.compile(r'(https://[^" ]*person_photos/[^" ]+)', re.I)


def norm(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def parse_candidates(html: str) -> list[dict[str, str]]:
    candidates = []
    for match in PLAYER_RE.finditer(html):
        block = match.group(0)
        full = re.search(r'<span[^>]*itemprop="givenName"[^>]*>([^<]+)</span>.*?<span[^>]*itemprop="familyName"[^>]*>([^<]+)</span>', block, re.S | re.I)
        if not full:
            full = re.search(r'<span[^>]*itemprop="familyName"[^>]*>([^<]+)</span>.*?<span[^>]*itemprop="givenName"[^>]*>([^<]+)</span>', block, re.S | re.I)
        dob = re.search(r'<td[^>]*class="dob"[^>]*>([0-9-]+)</td>', block, re.I)
        if full and dob:
            candidates.append({"id": match.group(1), "name": f"{full.group(1)} {full.group(2)}", "birth_date": dob.group(1)})
    return candidates


def black(content: bytes) -> bool:
    with Image.open(io.BytesIO(content)) as image:
        pixels = list(image.convert("RGB").resize((20, 20)).getdata())
    return not pixels or sum(1 for pixel in pixels if max(pixel) <= 8) / len(pixels) >= 0.8


def handle(row: dict[str, Any], timeout: float) -> dict[str, Any]:
    sid = int(row["source_id"])
    destination = OUTPUT / f"{sid}.jpg"
    if destination.exists():
        return {"source_id": sid, "status": "already_present"}
    try:
        with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
            response = client.get(SEARCH, params={"term": row.get("display_name") or ""})
            response.raise_for_status()
            expected_date = str(row.get("birth_date") or "")[:10]
            expected_tokens = sorted(norm(row.get("display_name")).split())
            candidates = [c for c in parse_candidates(response.text) if c["birth_date"] == expected_date and sorted(norm(c["name"]).split()) == expected_tokens]
            if len(candidates) != 1:
                return {"source_id": sid, "name": row.get("display_name"), "status": "no_exact_match", "candidate_count": len(candidates)}
            player_id = candidates[0]["id"]
            profile = client.get(PROFILE.format(id=player_id))
            profile.raise_for_status()
            photos = PHOTO_RE.findall(profile.text)
            if not photos:
                return {"source_id": sid, "name": row.get("display_name"), "status": "no_photo", "nft_id": player_id}
            image = client.get(photos[0])
            image.raise_for_status()
            if black(image.content):
                return {"source_id": sid, "name": row.get("display_name"), "status": "black_placeholder", "nft_id": player_id}
            RAW.mkdir(parents=True, exist_ok=True)
            (RAW / f"{sid}_{player_id}.jpeg").write_bytes(image.content)
            with Image.open(io.BytesIO(image.content)) as source:
                out = ImageOps.fit(source.convert("RGB"), (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
            OUTPUT.mkdir(parents=True, exist_ok=True)
            out.save(destination, "JPEG", quality=88, optimize=True)
            return {"source_id": sid, "name": row.get("display_name"), "status": "downloaded", "nft_id": player_id, "source_url": photos[0]}
    except Exception as exc:
        return {"source_id": sid, "name": row.get("display_name"), "status": "failed", "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    rows = [row for row in snapshot.get("players", []) if row.get("source_id") and not (OUTPUT / f"{int(row['source_id'])}.jpg").exists()]
    if args.limit:
        rows = rows[:args.limit]
    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(24, args.workers))) as pool:
        futures = [pool.submit(handle, row, args.timeout) for row in rows]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: int(row["source_id"]))
    report = {"source": "National-Football-Teams", "candidates": len(rows), "downloaded": sum(r["status"] == "downloaded" for r in results), "no_exact_match": sum(r["status"] == "no_exact_match" for r in results), "no_photo": sum(r["status"] == "no_photo" for r in results), "failed": sum(r["status"] == "failed" for r in results), "rows": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("candidates", "downloaded", "no_exact_match", "no_photo", "failed")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
