from __future__ import annotations

"""Recover missing Míster 93/94 assets from a canonical manifest.

Automatic sources:
- BDFutbol when the manifest contains an exact profile/direct-image mapping.
- Wikimedia Commons using the public MediaWiki API and conservative title matching.

The command is deliberately resumable: existing runtime assets are skipped, every
attempt is reported, and network failures never delete or overwrite good assets.
It is suitable for running from the user's own PC when the build environment has
restricted DNS/network access.
"""

import argparse
from datetime import datetime, timezone
import io
import json
import re
from pathlib import Path
import time
import unicodedata
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
PUBLIC = ROOT / "frontend" / "public" / "historical9394"
DEFAULT_MANIFEST = DATA / "missing_assets_1993_94.json"
DEFAULT_REPORT = DATA / "missing_assets_download_report.json"
RAW_DIR = DATA / "asset_recovery_raw"
HEADERS = {"User-Agent": "Mister9394AssetRecovery/1.0 (+personal historical game)"}
BDF_PHOTO_RE = re.compile(
    r"""(?:src|data-src)=["'](?:\.\./)*i/([^"'?]+\.(?:jpg|jpeg|png|webp))""",
    re.I,
)
BDF_PHOTO_BASE = "https://www.bdfutbol.com/i/"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
NETWORK_TIMEOUT = 20.0


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(text: str | None) -> str:
    text = str(text or "")
    # Several imported historical catalogues contain UTF-8 decoded once as
    # Windows-1252 (e.g. FenerbahÃ§e). Repair that reversible mojibake before
    # querying external indexes; leave genuinely invalid text untouched.
    if any(marker in text for marker in ("Ã", "Â", "â€", "Ä", "Å")):
        try:
            repaired = text.encode("cp1252").decode("utf-8")
            if repaired.count("�") <= text.count("�"):
                text = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _tokens(text: str | None) -> set[str]:
    stop = {"fc", "cf", "club", "football", "futbol", "stadium", "estadio", "manager", "coach", "the", "de", "del", "la", "el", "sk", "fk", "afc", "sc"}
    return {t for t in _norm(text).split() if len(t) >= 3 and t not in stop}


def _fetch(url: str, *, timeout: float | None = None) -> tuple[bytes, str]:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=NETWORK_TIMEOUT if timeout is None else timeout) as resp:  # nosec - controlled public sources from manifest/API
        return resp.read(), resp.headers.get_content_type()


def _fetch_text(url: str) -> str:
    data, _ = _fetch(url)
    return data.decode("utf-8", errors="replace")


def _score_image_bytes(content: bytes) -> tuple[int, int, int]:
    with Image.open(io.BytesIO(content)) as im:
        rgb = im.convert("RGB")
        rgb.thumbnail((500, 500))
        pixels = list(rgb.getdata())
        if pixels:
            black_ratio = sum(1 for pixel in pixels if max(pixel) <= 8) / len(pixels)
            mean = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3)
            if black_ratio >= 0.8 or mean <= 3.0:
                return (-100, 0, 0)
        chroma = 0.0
        if pixels:
            chroma = sum(max(p) - min(p) for p in pixels) / len(pixels)
        return (1 if chroma > 6 else 0, im.width * im.height, len(content))


def _bdfutbol_profile_image(profile_url: str) -> tuple[bytes | None, dict[str, Any]]:
    html = _fetch_text(profile_url)
    names: list[str] = []
    for match in BDF_PHOTO_RE.finditer(html):
        name = match.group(1)
        if name not in names:
            names.append(name)
    best: tuple[tuple[int, int, int], bytes, str] | None = None
    errors: list[str] = []
    for name in names:
        url = BDF_PHOTO_BASE + name
        try:
            content, _ = _fetch(url)
            score = _score_image_bytes(content)
            if best is None or score > best[0]:
                best = (score, content, url)
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    if not best:
        return None, {"profile_url": profile_url, "candidates": len(names), "errors": errors, "reason": "no_valid_bdfutbol_image"}
    return best[1], {"profile_url": profile_url, "download_url": best[2], "candidates": len(names), "score": list(best[0])}


def _commons_query(row: dict[str, Any]) -> str:
    kind = row["asset_type"]
    if kind == "player":
        return " ".join(filter(None, [row.get("name"), row.get("team"), "footballer"]))
    if kind == "manager":
        clubs = row.get("clubs") or []
        return " ".join(filter(None, [row.get("name"), clubs[0] if clubs else None, "football manager"]))
    if kind == "club_crest":
        return " ".join(filter(None, [row.get("name"), "football club logo crest"]))
    clubs = row.get("clubs") or []
    return " ".join(filter(None, [row.get("name"), row.get("city"), clubs[0] if clubs else None, "stadium"]))


def _commons_candidates(row: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": _commons_query(row),
        "gsrnamespace": 6,
        "gsrlimit": max(1, min(20, limit)),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "format": "json",
        "formatversion": 2,
    }
    raw, _ = _fetch(COMMONS_API + "?" + urlencode(params))
    payload = json.loads(raw.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    rows: list[dict[str, Any]] = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        rows.append({
            "title": page.get("title"),
            "url": info.get("url"),
            "width": info.get("width"),
            "height": info.get("height"),
            "mime": info.get("mime"),
            "license": (meta.get("LicenseShortName") or {}).get("value"),
            "license_url": (meta.get("LicenseUrl") or {}).get("value"),
            "artist": (meta.get("Artist") or {}).get("value"),
        })
    return rows


def _commons_score(row: dict[str, Any], candidate: dict[str, Any]) -> float:
    title = candidate.get("title") or ""
    expected = _tokens(row.get("name"))
    title_tokens = _tokens(title)
    if not expected:
        return 0.0
    overlap = len(expected & title_tokens)
    score = overlap * 4.0 / max(1, len(expected))
    joined = _norm(title)
    kind = row["asset_type"]
    if kind == "club_crest" and any(k in joined for k in ("logo", "crest", "badge", "emblem")):
        score += 1.25
    if kind == "stadium" and any(k in joined for k in ("stadium", "estadio", "stade", "stadion")):
        score += 1.0
    if kind in {"player", "manager"}:
        context = _tokens(row.get("team") or " ".join(row.get("clubs") or []))
        score += 0.3 * len(context & title_tokens)
    if not candidate.get("license"):
        score -= 2.0
    mime = str(candidate.get("mime") or "")
    if not mime.startswith("image/"):
        score -= 4.0
    return score


def _commons_image(row: dict[str, Any]) -> tuple[bytes | None, dict[str, Any]]:
    candidates = _commons_candidates(row)
    ranked = sorted((( _commons_score(row, c), c) for c in candidates), key=lambda x: x[0], reverse=True)
    if not ranked:
        return None, {"query": _commons_query(row), "reason": "no_commons_results"}
    score, best = ranked[0]
    # Conservative threshold: at least a meaningful name match.  Ambiguous results
    # are left for the manual URLs in the manifest rather than silently misassigned.
    if score < 2.25 or not best.get("url"):
        return None, {"query": _commons_query(row), "reason": "low_confidence", "best_score": score, "best": best, "candidates": [c for _, c in ranked[:5]]}
    content, _ = _fetch(best["url"])
    return content, {"query": _commons_query(row), "score": score, **best}


def _rgb_canvas(im: Image.Image, background=(238, 238, 238)) -> Image.Image:
    if im.mode in {"RGBA", "LA"} or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (*background, 255))
        bg.alpha_composite(rgba)
        return bg.convert("RGB")
    return im.convert("RGB")


def _normalize_portrait(content: bytes, dest: Path) -> None:
    with Image.open(io.BytesIO(content)) as im:
        rgb = _rgb_canvas(im)
        out = ImageOps.fit(rgb, (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        dest.parent.mkdir(parents=True, exist_ok=True)
        out.save(dest, "JPEG", quality=88, optimize=True)


def _normalize_stadium(content: bytes, dest: Path) -> None:
    with Image.open(io.BytesIO(content)) as im:
        rgb = _rgb_canvas(im)
        out = ImageOps.fit(rgb, (100, 75), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        dest.parent.mkdir(parents=True, exist_ok=True)
        out.save(dest, "JPEG", quality=86, optimize=True)


def _normalize_crest(content: bytes, dest: Path) -> None:
    with Image.open(io.BytesIO(content)) as im:
        rgba = im.convert("RGBA")
        rgba.thumbnail((38, 38), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
        canvas.alpha_composite(rgba, ((40-rgba.width)//2, (40-rgba.height)//2))
        pal = canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        alpha = canvas.getchannel("A")
        mask = Image.eval(alpha, lambda a: 255 if a <= 12 else 0)
        pal.paste(255, mask=mask)
        pal.info["transparency"] = 255
        dest.parent.mkdir(parents=True, exist_ok=True)
        pal.save(dest, "GIF", transparency=255, optimize=True)


def _synthetic_crest(row: dict[str, Any], dest: Path) -> None:
    name = str(row.get("name") or "OTROS").replace("Otros-", "")
    letters = "".join(part[:1] for part in re.split(r"[\s-]+", name) if part)[:2].upper() or "OT"
    canvas = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    shield = [(7, 4), (33, 4), (35, 23), (29, 33), (20, 38), (11, 33), (5, 23)]
    draw.polygon(shield, fill=(42, 55, 54, 255), outline=(198, 173, 105, 255))
    draw.line([(8, 11), (32, 11)], fill=(198, 173, 105, 255), width=1)
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letters, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((40-tw)//2, 19-th//2), letters, font=font, fill=(245, 241, 225, 255))
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    _normalize_crest(buf.getvalue(), dest)


def _runtime_dest(row: dict[str, Any]) -> Path:
    rel = str(row["runtime_path"]).lstrip("/")
    # runtime path starts with historical9394; PUBLIC points to that directory.
    prefix = "historical9394/"
    if rel.startswith(prefix):
        rel = rel[len(prefix):]
    return PUBLIC / rel


def _normalize(content: bytes, row: dict[str, Any], dest: Path) -> None:
    if row["asset_type"] in {"player", "manager"}:
        _normalize_portrait(content, dest)
    elif row["asset_type"] == "club_crest":
        _normalize_crest(content, dest)
    else:
        _normalize_stadium(content, dest)


def _write_raw(content: bytes, row: dict[str, Any], source: str) -> Path:
    suffix = ".bin"
    try:
        with Image.open(io.BytesIO(content)) as im:
            suffix = "." + (im.format or "img").lower().replace("jpeg", "jpg")
    except Exception:
        pass
    path = RAW_DIR / row["asset_type"] / f"{row['source_id']}_{_norm(source).replace(' ', '_')}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def recover(manifest_path: Path, *, limit: int | None = None, types: set[str] | None = None, source_ids: set[int] | None = None, skip_commons: bool = False, delay: float = 0.4, dry_run: bool = False) -> dict[str, Any]:
    manifest = _load(manifest_path)
    section_map = {"player": "players", "manager": "managers", "club_crest": "club_crests", "stadium": "stadiums"}
    rows: list[dict[str, Any]] = []
    for asset_type, section in section_map.items():
        if types and asset_type not in types:
            continue
        rows.extend(row for row in manifest.get(section, []) if not source_ids or int(row.get("source_id") or 0) in source_ids)

    report_rows: list[dict[str, Any]] = []
    processed = 0
    downloaded = 0
    generated = 0
    skipped_existing = 0
    failed = 0

    for row in rows:
        dest = _runtime_dest(row)
        if dest.exists():
            skipped_existing += 1
            continue
        if limit is not None and processed >= limit:
            break
        processed += 1
        entry: dict[str, Any] = {"asset_type": row["asset_type"], "source_id": row["source_id"], "name": row.get("name"), "destination": str(dest.relative_to(ROOT))}

        if row["asset_type"] == "club_crest" and row.get("synthetic_container"):
            if not dry_run:
                _synthetic_crest(row, dest)
            generated += 1
            entry.update({"status": "generated", "source": "game_synthetic_crest"})
            report_rows.append(entry)
            continue

        content: bytes | None = None
        source_meta: dict[str, Any] = {}
        source_name: str | None = None
        errors: list[dict[str, str]] = []

        for candidate in row.get("source_candidates", []):
            if not candidate.get("automatic"):
                continue
            source = candidate.get("source") or "unknown"
            if source == "Wikimedia Commons" and skip_commons:
                continue
            try:
                if candidate.get("mode") == "profile_scrape" and candidate.get("profile_url"):
                    content, source_meta = _bdfutbol_profile_image(candidate["profile_url"])
                elif candidate.get("mode") == "direct_image" and candidate.get("download_url"):
                    content, _ = _fetch(candidate["download_url"])
                    source_meta = {"download_url": candidate["download_url"]}
                elif source == "Wikimedia Commons":
                    content, source_meta = _commons_image(row)
                if content:
                    source_name = source
                    break
                errors.append({"source": source, "error": str(source_meta.get("reason") or "no_image")})
            except Exception as exc:
                errors.append({"source": source, "error": str(exc)})
            if delay:
                time.sleep(delay)

        if content and source_name:
            try:
                raw_path = _write_raw(content, row, source_name)
                if not dry_run:
                    _normalize(content, row, dest)
                downloaded += 1
                entry.update({"status": "downloaded", "source": source_name, "source_meta": source_meta, "raw_file": str(raw_path.relative_to(ROOT))})
            except Exception as exc:
                failed += 1
                entry.update({"status": "failed", "errors": errors + [{"source": source_name, "error": f"normalize: {exc}"}]})
        else:
            failed += 1
            entry.update({"status": "failed", "errors": errors})
        report_rows.append(entry)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path),
        "network_policy": "best_effort_resumable",
        "processed": processed,
        "downloaded": downloaded,
        "generated": generated,
        "skipped_existing": skipped_existing,
        "failed": failed,
        "rows": report_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recover and normalize missing Míster 93/94 images")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--type", action="append", dest="types", choices=["player", "manager", "club_crest", "stadium"])
    parser.add_argument("--id", action="append", dest="source_ids", type=int, help="only process a specific runtime/source ID; repeatable")
    parser.add_argument("--skip-commons", action="store_true")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--timeout", type=float, default=20.0, help="network timeout per request in seconds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    global NETWORK_TIMEOUT
    NETWORK_TIMEOUT = max(1.0, float(args.timeout))
    report = recover(args.manifest, limit=args.limit, types=set(args.types) if args.types else None, source_ids=set(args.source_ids) if args.source_ids else None, skip_commons=args.skip_commons, delay=max(0.0, args.delay), dry_run=args.dry_run)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("processed", "downloaded", "generated", "skipped_existing", "failed")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
