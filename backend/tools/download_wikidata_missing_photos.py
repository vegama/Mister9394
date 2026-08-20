from __future__ import annotations

"""Recover missing portraits from Wikidata P569 (birth date) + P18 (image)."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
PUBLIC = ROOT / "frontend" / "public" / "historical9394" / "players"
API = "https://www.wikidata.org/w/api.php"
FILE = "https://commons.wikimedia.org/wiki/Special:FilePath/"
HEADERS = {"User-Agent": "Mister9394AssetRecovery/1.0 (historical football database)"}


def norm(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def tokens(value: str | None) -> set[str]:
    return set(norm(value).split())


def api(params: dict[str, str]) -> dict:
    for attempt in range(4):
        request = Request(API + "?" + urlencode({**params, "format": "json", "formatversion": "2"}), headers=HEADERS)
        try:
            with urlopen(request, timeout=25) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if "429" not in str(exc) or attempt == 3:
                raise
            time.sleep(2.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def valid_image(data: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(data)) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((300, 300))
            pixels = list(rgb.getdata())
            return bool(pixels) and sum(1 for p in pixels if max(p) <= 8) / len(pixels) < 0.8
    except Exception:
        return False


def save(data: bytes, destination: Path) -> None:
    with Image.open(io.BytesIO(data)) as image:
        out = ImageOps.fit(image.convert("RGB"), (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        destination.parent.mkdir(parents=True, exist_ok=True)
        out.save(destination, "JPEG", quality=88, optimize=True)


def process(row: dict) -> dict:
    destination = PUBLIC / f"{row['source_id']}.jpg"
    result = {"source_id": row["source_id"], "name": row["name"], "status": "skipped", "source": "Wikidata P569/P18"}
    if destination.exists():
        result["reason"] = "already_exists"
        return result
    try:
        birth = str(row.get("birth_date") or "")[:10]
        search = api({"action": "wbsearchentities", "search": row["name"], "language": "en", "uselang": "en", "type": "item", "limit": "10"})
        ids = [item["id"] for item in search.get("search", []) if item.get("id", "").startswith("Q")]
        if not ids:
            result["status"] = "no_exact_match"
            return result
        entities = api({"action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels|aliases", "languages": "en|es|it|fr|de|pt"}).get("entities", {})
        if isinstance(entities, dict):
            entities = list(entities.values())
        expected = tokens(row["name"])
        for entity in entities:
            labels = [v.get("value", "") for v in (entity.get("labels") or {}).values()]
            for values in (entity.get("aliases") or {}).values():
                labels.extend(v.get("value", "") for v in values)
            if not any(expected == tokens(label) or expected.issubset(tokens(label)) for label in labels):
                continue
            claims = entity.get("claims") or {}
            dates = []
            for claim in claims.get("P569", []):
                value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
                dates.append(str(value.get("time", "")).lstrip("+")[:10])
            if birth not in dates:
                continue
            images = []
            for claim in claims.get("P18", []):
                value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if value:
                    images.append(value)
            for filename in images:
                try:
                    data = urlopen(Request(FILE + quote(filename, safe=""), headers=HEADERS), timeout=25).read()
                    if not valid_image(data):
                        continue
                    save(data, destination)
                    result.update({"status": "downloaded", "wikidata_id": entity.get("id"), "filename": filename})
                    return result
                except Exception:
                    continue
        result["status"] = "no_exact_match"
    except Exception as exc:
        result.update({"status": "failed", "reason": str(exc)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DATA / "missing_assets_1993_94_bdfutbol_global_final.json")
    parser.add_argument("--report", type=Path, default=DATA / "wikidata_missing_photo_full.json")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = payload.get("players", [])[args.offset :]
    if args.limit:
        rows = rows[: args.limit]
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(process, row) for row in rows]
        for index, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            if index % 250 == 0:
                print(f"processed {index}/{len(rows)}")
    results.sort(key=lambda item: int(item["source_id"]))
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "candidates": len(rows), "downloaded": sum(r["status"] == "downloaded" for r in results), "no_exact_match": sum(r["status"] == "no_exact_match" for r in results), "failed": sum(r["status"] == "failed" for r in results), "results": results}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("candidates", "downloaded", "no_exact_match", "failed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
