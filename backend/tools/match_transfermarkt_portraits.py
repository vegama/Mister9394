from __future__ import annotations

"""Best-effort alternative portrait source for players BDFutbol has no photo for.

Sibling of match_bdfutbol_by_name.py / download_bdfutbol_photos.py, but for
Transfermarkt. Transfermarkt's quick search already exposes a small portrait
thumbnail per candidate and marks players with no real photo via a
placeholder URL (``portrait/*/default.jpg``), so a candidate can be screened
for "has a real photo" without an extra request.

Identity is NOT taken on faith from a name match alone: Transfermarkt's
search is fuzzy and common surnames return several different people. A
candidate is only auto-confirmed when our recorded birth date lets us check
their reported current age (tolerance +-1 year, since Transfermarkt shows
age as of today rather than the exact birth date) AND their shown
nationality matches our recorded country. Anything else -- no birth date on
our side, no age match, more than one plausible candidate, or a mismatched
nationality -- is written to ``needs_review`` with full candidate detail
instead of being downloaded, mirroring the BDFutbol matcher's policy of
never guessing identity.

Only rows confirmed this way get a raw download; normalization into the
game's 40x55 RGB JPEG format reuses normalize_bdfutbol_photos.normalize_image
so the output is byte-for-byte the same policy as the BDFutbol pipeline.
"""

import argparse
from datetime import date, datetime, timezone
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.tools.normalize_bdfutbol_photos import normalize_image  # noqa: E402

DEFAULT_QUEUE = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "football9394" / "transfermarkt_photos_raw"
DEFAULT_GAME_DIR = REPO_ROOT / "frontend" / "public" / "historical9394" / "players"

SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36 Mister9394PhotoTool/1.0"}

PLAYER_GRID_RE = re.compile(r'id="player-grid".*?<tbody>(.*?)</tbody>', re.DOTALL)
ROW_SPLIT_RE = re.compile(r'<tr class="(?:odd|even)">(.*?)(?=<tr class="(?:odd|even)">|\Z)', re.DOTALL)
THUMB_RE = re.compile(r'<img src="([^"]+)"[^>]*title="([^"]*)"[^>]*/></a></td>')
SPIELER_ID_RE = re.compile(r'href="/[^"]+/profil/spieler/(\d+)"')
POSITION_RE = re.compile(r'<td class="zentriert">([^<]*)</td>')
AGE_RE = re.compile(r'<td class="zentriert">(\d+|N/A)</td>')
NAT_TITLE_RE = re.compile(r'<img src="[^"]*flagge[^"]*"[^>]*title="([^"]*)"')
PROFILE_IMG_RE = re.compile(r'<img src="([^"]+)"[^>]*class="data-header__profile-image"')

NATIONALITY_ALIASES: dict[str, set[str]] = {
    "Turquía": {"türkiye", "turkey"},
    "Bélgica": {"belgium"},
    "Albania": {"albania"},
    "Brasil": {"brazil"},
    "Burundi": {"burundi"},
    "Finlandia": {"finland"},
    "Ghana": {"ghana"},
    "Zaire": {"dr congo", "congo dr", "zaire", "democratic republic of congo"},
}


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def _is_placeholder(thumb_url: str) -> bool:
    return "default.jpg" in thumb_url


def _clean_club(raw_club_cell: str) -> str:
    m = re.search(r'title="([^"]*)"', raw_club_cell)
    if m:
        return m.group(1)
    return re.sub(r"<[^>]+>", "", raw_club_cell).strip()


def _parse_row(row_html: str) -> dict[str, Any] | None:
    thumb_m = THUMB_RE.search(row_html)
    id_m = SPIELER_ID_RE.search(row_html)
    if not thumb_m or not id_m:
        return None
    thumb_url, name = thumb_m.groups()
    spieler_id = id_m.group(1)
    club_m = re.search(r'</td></tr>\s*<tr><td>(.*?)</td></tr></table>', row_html, re.DOTALL)
    club = _clean_club(club_m.group(1)) if club_m else ""
    text_cells = POSITION_RE.findall(row_html)
    position = text_cells[0].strip() if len(text_cells) >= 1 else "N/A"
    age = text_cells[1].strip() if len(text_cells) >= 2 else "N/A"
    nat_m = NAT_TITLE_RE.search(row_html)
    nationality = nat_m.group(1) if nat_m else "N/A"
    return {
        "spieler_id": spieler_id,
        "name": name,
        "position": position,
        "club": club,
        "age": age,
        "nationality": nationality,
        "thumb_url": thumb_url,
        "has_photo": not _is_placeholder(thumb_url),
        "profile_url": f"https://www.transfermarkt.com/x/profil/spieler/{spieler_id}",
    }


def search_candidates(client: httpx.Client, name: str) -> list[dict[str, Any]]:
    resp = client.get(SEARCH_URL, params={"query": name}, headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    grid_m = PLAYER_GRID_RE.search(resp.text)
    if not grid_m:
        return []
    out = []
    for row_m in ROW_SPLIT_RE.finditer(grid_m.group(1)):
        parsed = _parse_row(row_m.group(1))
        if parsed:
            out.append(parsed)
    return out


def _expected_age(birth_date: str, today: date) -> int | None:
    try:
        y, mo, d = (int(p) for p in birth_date[:10].split("-"))
    except (ValueError, AttributeError):
        return None
    age = today.year - y
    if (today.month, today.day) < (mo, d):
        age -= 1
    return age


def evaluate_row(row: dict[str, Any], candidates: list[dict[str, Any]], today: date) -> dict[str, Any]:
    photo_candidates = [c for c in candidates if c["has_photo"]]
    expected_age = _expected_age(row.get("birth_date") or "", today)
    aliases = NATIONALITY_ALIASES.get(row.get("country_name") or "")

    plausible = []
    for c in photo_candidates:
        if expected_age is None:
            continue
        try:
            age_ok = abs(int(c["age"]) - expected_age) <= 1
        except ValueError:
            age_ok = False
        nat_ok = bool(aliases) and c["nationality"].strip().lower() in aliases
        if age_ok and nat_ok:
            plausible.append(c)

    entry = {
        "source_id": row["source_id"],
        "display_name": row.get("display_name"),
        "country_name": row.get("country_name"),
        "expected_age": expected_age,
        "candidates": candidates,
    }
    if len(plausible) == 1:
        entry["matched"] = plausible[0]
        entry["decision"] = "confirmed"
    elif not candidates:
        entry["decision"] = "no_candidates"
    elif not photo_candidates:
        entry["decision"] = "candidates_no_real_photo"
    else:
        entry["decision"] = "needs_review"
    return entry


def download_matched_photo(client: httpx.Client, entry: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    spieler_id = entry["matched"]["spieler_id"]
    resp = client.get(f"https://www.transfermarkt.com/x/profil/spieler/{spieler_id}", headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    m = PROFILE_IMG_RE.search(resp.text)
    if not m or "default.jpg" in m.group(1):
        return {"source_id": entry["source_id"], "spieler_id": spieler_id, "status": "no_profile_image"}
    img_resp = client.get(m.group(1), headers=HEADERS, timeout=20, follow_redirects=True)
    img_resp.raise_for_status()
    dest = raw_dir / f"{entry['source_id']}.jpg"
    dest.write_bytes(img_resp.content)
    return {"source_id": entry["source_id"], "spieler_id": spieler_id, "status": "downloaded", "file": str(dest.relative_to(REPO_ROOT))}


def run(
    source_ids: list[int],
    *,
    queue_path: Path = DEFAULT_QUEUE,
    raw_dir: Path = DEFAULT_RAW_DIR,
    game_dir: Path = DEFAULT_GAME_DIR,
    delay: float = 1.2,
    limit: int | None = None,
) -> dict[str, Any]:
    rows = _load_queue(queue_path)
    by_id = {int(r["source_id"]): r for r in rows if r.get("source_id") is not None}
    targets = [by_id[sid] for sid in source_ids if sid in by_id and not (game_dir / f"{sid}.jpg").exists()]
    if limit:
        targets = targets[:limit]

    today = datetime.now(timezone.utc).date()
    confirmed: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    no_candidates: list[dict[str, Any]] = []
    candidates_no_real_photo: list[dict[str, Any]] = []

    with httpx.Client() as client:
        for row in targets:
            candidates = search_candidates(client, row.get("display_name") or "")
            time.sleep(delay)
            entry = evaluate_row(row, candidates, today)
            if entry["decision"] == "confirmed":
                confirmed.append(entry)
            elif entry["decision"] == "no_candidates":
                no_candidates.append(entry)
            elif entry["decision"] == "candidates_no_real_photo":
                candidates_no_real_photo.append(entry)
            else:
                needs_review.append(entry)

        raw_dir.mkdir(parents=True, exist_ok=True)
        downloads = []
        for entry in confirmed:
            downloads.append(download_matched_photo(client, entry, raw_dir))
            time.sleep(delay)

    normalize_report = None
    downloaded_files = [d for d in downloads if d["status"] == "downloaded"]
    if downloaded_files:
        from backend.tools.normalize_bdfutbol_photos import normalize_directory
        normalize_report = normalize_directory(raw_dir, game_dir, queue_path=queue_path)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "transfermarkt_quicksearch",
        "processed": len(targets),
        "confirmed": len(confirmed),
        "downloaded": len(downloaded_files),
        "needs_review": len(needs_review),
        "no_candidates": len(no_candidates),
        "candidates_no_real_photo": len(candidates_no_real_photo),
        "confirmed_rows": confirmed,
        "download_results": downloads,
        "needs_review_rows": needs_review,
        "no_candidates_rows": no_candidates,
        "candidates_no_real_photo_rows": candidates_no_real_photo,
        "normalize_report": normalize_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Try to match+download portraits from Transfermarkt for players BDFutbol has no photo for")
    parser.add_argument("--source-ids", type=Path, required=True, help="JSON file: a list of int source_ids to attempt")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--delay", type=float, default=1.2)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    source_ids = json.loads(args.source_ids.read_text(encoding="utf-8"))
    report = run(source_ids, queue_path=args.queue, raw_dir=args.raw_dir, game_dir=args.game_dir, delay=args.delay, limit=args.limit)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {k: v for k, v in report.items() if not k.endswith("_rows") and k != "normalize_report"}
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
