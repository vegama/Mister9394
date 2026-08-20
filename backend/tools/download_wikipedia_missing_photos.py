from __future__ import annotations

"""Recover missing portraits through Wikipedia's public API.

Only exact-name pages whose plain-text extract contains the catalogued birth
date are accepted.  This is intentionally conservative: a missed portrait is
preferable to assigning a similarly named player.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
PUBLIC = ROOT / "frontend" / "public" / "historical9394"
API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Mister9394AssetRecovery/1.0 (historical football database)"}


def norm(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def tokens(value: str | None) -> set[str]:
    return set(norm(value).split())


def fetch_json(params: dict[str, str]) -> dict:
    url = API + "?" + urlencode({**params, "format": "json", "formatversion": "2"})
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def valid_image(data: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(data)) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((300, 300))
            pixels = list(rgb.getdata())
            if not pixels:
                return False
            return sum(1 for p in pixels if max(p) <= 8) / len(pixels) < 0.8
    except Exception:
        return False


def normalize_portrait(data: bytes, destination: Path) -> None:
    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGB")
        image.thumbnail((600, 600))
        width, height = image.size
        # Wikipedia portraits are usually already head/torso crops.  Keep the
        # full image and center-crop only at the final game resolution.
        ratio = max(40 / width, 55 / height)
        resized = image.resize((max(40, round(width * ratio)), max(55, round(height * ratio))), Image.Resampling.LANCZOS)
        left = max(0, (resized.width - 40) // 2)
        top = max(0, (resized.height - 55) // 2)
        resized.crop((left, top, left + 40, top + 55)).save(destination, "JPEG", quality=88, optimize=True)


def process(row: dict) -> dict:
    destination = ROOT / "frontend" / "public" / row["runtime_path"].lstrip("/")
    result = {"source_id": row["source_id"], "name": row["name"], "status": "skipped", "source": "Wikipedia"}
    if destination.exists():
        result["reason"] = "already_exists"
        return result
    name_tokens = tokens(row["name"])
    if len(name_tokens) < 2:
        result["status"] = "no_exact_match"
        result["reason"] = "single_token_name"
        return result
    try:
        search = fetch_json({
            "action": "query", "list": "search", "srsearch": f'intitle:"{row["name"]}" footballer',
            "srnamespace": "0", "srlimit": "8", "srprop": "snippet|titlesnippet",
        })
        hits = search.get("query", {}).get("search", [])
        candidates = []
        for hit in hits:
            title = hit.get("title", "")
            title_tokens = tokens(re.sub(r"\s*\([^)]*\)", "", title))
            if title_tokens != name_tokens:
                continue
            candidates.append((hit.get("pageid"), title))
        if not candidates:
            result["status"] = "no_exact_match"
            return result
        # Fetch extracts and the lead image in one API call per exact title.
        for page_id, title in candidates:
            payload = fetch_json({
                "action": "query", "pageids": str(page_id),
                "prop": "extracts|pageimages", "exintro": "1", "explaintext": "1",
                "exchars": "5000", "piprop": "original",
            })
            page = (payload.get("query", {}).get("pages") or [{}])[0]
            extract = page.get("extract", "")
            birth = row.get("birth_date") or ""
            year = birth[:4]
            date_variants = {birth, f"{birth[8:10]}/{birth[5:7]}/{birth[:4]}", f"{birth[8:10]} {birth[5:7]} {birth[:4]}", year}
            if not any(v and v in extract for v in date_variants):
                continue
            image = (page.get("original") or {}).get("source")
            if not image:
                continue
            req = Request(image, headers=HEADERS)
            with urlopen(req, timeout=20) as response:
                data = response.read()
            if not valid_image(data):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            normalize_portrait(data, destination)
            result.update({"status": "downloaded", "wikipedia_title": title, "source_url": image})
            return result
        result["status"] = "no_exact_match"
        result["reason"] = "birth_date_or_portrait_missing"
    except Exception as exc:
        result["status"] = "failed"
        result["reason"] = str(exc)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DATA / "missing_assets_1993_94_alternatives_final.json")
    parser.add_argument("--report", type=Path, default=DATA / "wikipedia_missing_photo_full.json")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = [row for row in manifest.get("players", []) if row.get("asset_type") == "player"]
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(process, row) for row in rows]
        for index, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            if index % 250 == 0:
                print(f"processed {index}/{len(rows)}")
    results.sort(key=lambda item: int(item["source_id"]))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Wikipedia API",
        "candidates": len(rows),
        "downloaded": sum(r["status"] == "downloaded" for r in results),
        "no_exact_match": sum(r["status"] == "no_exact_match" for r in results),
        "failed": sum(r["status"] == "failed" for r in results),
        "results": results,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("candidates", "downloaded", "no_exact_match", "failed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
