from __future__ import annotations

"""Cross-check missing portraits against BDFutbol's global player index.

The season queue only contains identities discovered in the 93/94 source
passes.  BDFutbol's global search can find the same person through a different
season or competition, so this tool searches by name + birth year and accepts
only an exact birth date before downloading the profile portrait.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import html
import io
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
PUBLIC = ROOT / "frontend" / "public" / "historical9394" / "players"
SEARCH = "https://www.bdfutbol.com/en/buscar.php"
PROFILE = "https://www.bdfutbol.com/en/j/j{}/{}.html"
PHOTO_BASE = "https://www.bdfutbol.com/i/j/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394GlobalCrosscheck/1.0)"}
IMG_RE = re.compile(r"(?:src|data-src)=[\"'](?:https?://www\.bdfutbol\.com/)?(?:\.\./\.\./)?i/j/([^\"'?]+\.(?:jpg|jpeg|png))[\"']", re.I)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
LINK_RE = re.compile(r"href=['\"](?:\.\./)?j/j(\d+)\.html['\"]", re.I)
DATE_RE = re.compile(r"sortval(\d{8})", re.I)


def norm(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


_CYR = dict(zip("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", ["A", "B", "V", "G", "D", "E", "Yo", "Zh", "Z", "I", "Y", "K", "L", "M", "N", "O", "P", "R", "S", "T", "U", "F", "Kh", "Ts", "Ch", "Sh", "Shch", "", "Y", "", "E", "Yu", "Ya"]))
_CYR.update({key.lower(): value.lower() for key, value in list(_CYR.items())})
CYRILLIC = str.maketrans(_CYR)
_GREEK = dict(zip("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ", ["A", "V", "G", "D", "E", "Z", "I", "Th", "I", "K", "L", "M", "N", "X", "O", "P", "R", "S", "T", "Y", "F", "Ch", "Ps", "O"]))
_GREEK.update({key.lower(): value.lower() for key, value in list(_GREEK.items())})
GREEK = str.maketrans(_GREEK)


def repair_mojibake(value: str) -> str:
    if any(marker in value for marker in ("Ã", "Â", "Ð", "Ñ", "Î", "Ï")):
        try:
            repaired = value.encode("cp1252").decode("utf-8")
            if repaired.count("�") <= value.count("�"):
                return repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return value


def transliterate(value: str) -> str:
    value = repair_mojibake(value).translate(CYRILLIC).translate(GREEK)
    return (value.replace("ß", "ss").replace("ẞ", "SS").replace("ł", "l").replace("Ł", "L")
            .replace("đ", "d").replace("Đ", "D").replace("ð", "d").replace("þ", "th")
            .replace("æ", "ae").replace("Æ", "AE").replace("œ", "oe").replace("Œ", "OE"))


def ascii_fold(value: str) -> str:
    value = repair_mojibake(value).replace("ı", "i").replace("İ", "I")
    value = unicodedata.normalize("NFKD", value)
    return "".join(c for c in value if not unicodedata.combining(c))


def query_variants(name: str) -> list[str]:
    values = [name, repair_mojibake(name), transliterate(name), ascii_fold(name)]
    # BDFutbol's search is surname-friendly; use the final surname as a
    # fallback only for names that actually need transliteration.
    if norm(name) != norm(transliterate(name)) and len(name.split()) >= 2:
        values.append(name.split()[-1])
    out = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


def fetch(url: str, timeout: float = 25) -> bytes:
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def search_candidates(row: dict) -> list[tuple[str, str]]:
    birth = str(row.get("birth_date") or "")[:10]
    year = birth[:4]
    if len(year) != 4:
        return []
    expected = norm(row.get("name"))
    found: list[tuple[str, str]] = []
    for search_name in query_variants(row.get("name", "")):
        query = urlencode({"d": search_name, "bj": "on", "an1": year, "an2": year})
        text = fetch(SEARCH + "?" + query).decode("utf-8", errors="replace")
        for match in ROW_RE.finditer(text):
            fragment = match.group(1)
            link = LINK_RE.search(fragment)
            date = DATE_RE.search(fragment)
            if not link or not date or date.group(1) != birth.replace("-", ""):
                continue
            visible = re.sub(r"<[^>]+>", " ", html.unescape(fragment))
            visible = " ".join(visible.split())
            # Accept the raw or transliterated spelling, but still require all
            # meaningful catalogued tokens to occur in the returned identity.
            visible_tokens = set(norm(visible).split()) | set(norm(transliterate(visible)).split())
            expected_tokens = set(norm(row.get("name")).split()) | set(norm(transliterate(row.get("name", ""))).split())
            if not expected_tokens.issubset(visible_tokens):
                continue
            candidate = (link.group(1), visible)
            if candidate not in found:
                found.append(candidate)
    return found


def score_image(data: bytes) -> tuple[int, int, int]:
    with Image.open(io.BytesIO(data)) as image:
        rgb = image.convert("RGB")
        rgb.thumbnail((500, 500))
        pixels = list(rgb.getdata())
        if not pixels:
            return (-100, 0, 0)
        black = sum(1 for p in pixels if max(p) <= 8) / len(pixels)
        if black >= 0.8:
            return (-100, 0, 0)
        chroma = sum(max(p) - min(p) for p in pixels) / len(pixels)
        return (1 if chroma > 6 else 0, image.width * image.height, len(data))


def profile_photo(bdf_id: str) -> tuple[bytes | None, str | None]:
    # The second URL segment is the language-independent profile slug; the
    # site's current HTML uses the English route but accepts the numeric page.
    page = fetch(f"https://www.bdfutbol.com/en/j/j{bdf_id}.html").decode("utf-8", errors="replace")
    names: list[str] = []
    # Current BDFutbol pages sometimes omit the profile image from the HTML,
    # while the stable direct endpoint still serves it. Try it first; the
    # content validator below rejects missing/black placeholders.
    try:
        direct = fetch(PHOTO_BASE + bdf_id + ".jpg")
        if score_image(direct)[0] >= 0:
            names.append(bdf_id + ".jpg")
    except Exception:
        pass
    for match in IMG_RE.finditer(page):
        name = match.group(1)
        if name.lower().startswith(bdf_id.lower()) and name not in names:
            names.append(name)
    best: tuple[tuple[int, int, int], bytes, str] | None = None
    for name in names:
        try:
            data = fetch(PHOTO_BASE + name)
            score = score_image(data)
            if score[0] >= 0 and (best is None or score > best[0]):
                best = (score, data, PHOTO_BASE + name)
        except Exception:
            continue
    return (best[1], best[2]) if best else (None, None)


def save_portrait(data: bytes, destination: Path) -> None:
    with Image.open(io.BytesIO(data)) as image:
        rgb = image.convert("RGB")
        out = ImageOps.fit(rgb, (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        destination.parent.mkdir(parents=True, exist_ok=True)
        out.save(destination, "JPEG", quality=88, optimize=True)


def process(row: dict) -> dict:
    destination = PUBLIC / f"{row['source_id']}.jpg"
    result = {"source_id": row["source_id"], "name": row["name"], "status": "skipped", "source": "BDFutbol global search"}
    if destination.exists():
        result["reason"] = "already_exists"
        return result
    try:
        candidates = search_candidates(row)
        for bdf_id, label in candidates:
            data, source_url = profile_photo(bdf_id)
            if data is None:
                continue
            save_portrait(data, destination)
            result.update({"status": "downloaded", "bdfutbol_id": bdf_id, "profile_label": label, "source_url": source_url})
            return result
        result["status"] = "no_exact_match"
        result["candidate_count"] = len(candidates)
    except Exception as exc:
        result["status"] = "failed"
        result["reason"] = str(exc)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DATA / "missing_assets_1993_94_alternatives_wikipedia.json")
    parser.add_argument("--report", type=Path, default=DATA / "bdfutbol_global_crosscheck.json")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--candidate-only", action="store_true", help="reprocess only IDs previously found in batch reports")
    parser.add_argument("--transliterated-only", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = payload.get("players", [])
    if args.candidate_only:
        ids: set[int] = set()
        for report_path in DATA.glob("bdfutbol_global_crosscheck_batch_*.json"):
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                ids.update(int(item["source_id"]) for item in report.get("results", []) if item.get("candidate_count", 0) > 0)
            except Exception:
                continue
        rows = [row for row in rows if int(row["source_id"]) in ids]
    if args.transliterated_only:
        rows = [row for row in rows if len(query_variants(row.get("name", ""))) > 1]
    rows = rows[args.offset :]
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
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "BDFutbol global search, exact name + exact birth date",
        "candidates": len(rows),
        "downloaded": sum(r["status"] == "downloaded" for r in results),
        "no_exact_match": sum(r["status"] == "no_exact_match" for r in results),
        "failed": sum(r["status"] == "failed" for r in results),
        "results": results,
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("candidates", "downloaded", "no_exact_match", "failed")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
