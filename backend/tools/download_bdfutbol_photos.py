from __future__ import annotations

"""Download historical player portraits from BDFutbol player pages.

For each queue row this fetches the public player page
(``https://www.bdfutbol.com/en/j/j{bdfutbol_id}.html``), reads the photo
carousel embedded in the HTML (``i/j/<file>.jpg``) and saves the best
candidate locally. A player page can carry more than one carousel photo; when
that happens the color one is preferred over black-and-white/sepia scans, and
ties are broken by resolution/file size as a quality proxy.

This is a plain scrape of the public site, not the paid BDFutbol Photos API.
Downloaded files are raw (un-normalized) and must still be run through
``normalize_bdfutbol_photos.py`` to become the game's 40x55 assets.

Players whose normalized photo already exists under the game's asset
directory are skipped up front so re-runs only fetch what is actually
missing.
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx
from PIL import Image
import io

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "football9394" / "bdfutbol_photos_raw"
DEFAULT_GAME_DIR = REPO_ROOT / "frontend" / "public" / "historical9394" / "players"

PLAYER_PAGE = "https://www.bdfutbol.com/en/j/j{bdfutbol_id}.html"
PHOTO_BASE = "https://www.bdfutbol.com/i/j/"
# BDFutbol has used both the old carousel markup and standalone profile images.
# Keep the path capture deliberately narrow: only /i/j/ assets are portraits;
# /i/eg/, /i/t/ and site chrome must never be assigned to a player.
PLAYER_IMG_RE = re.compile(
    r'(?:src|data-src)="(?:https?://www\.bdfutbol\.com/)?(?:\.\./\.\./)?i/j/([^"?]+\.(?:jpg|jpeg|png))',
    re.IGNORECASE,
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394PhotoTool/1.0)"}


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def _is_color(im: Image.Image, sample: int = 900) -> bool:
    rgb = im.convert("RGB")
    rgb.thumbnail((sample, sample))
    pixels = list(rgb.getdata())
    if not pixels:
        return False
    diffs = [max(r, g, b) - min(r, g, b) for r, g, b in pixels]
    return (sum(diffs) / len(diffs)) > 8.0


def _score_candidate(content: bytes) -> tuple[int, int, int]:
    with Image.open(io.BytesIO(content)) as im:
        color_bonus = 1 if _is_color(im) else 0
        pixels = im.size[0] * im.size[1]
    return (color_bonus, pixels, len(content))


def fetch_candidate_filenames(client: httpx.Client, bdfutbol_id: str) -> list[str]:
    resp = client.get(PLAYER_PAGE.format(bdfutbol_id=bdfutbol_id), headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    seen: list[str] = []
    for match in PLAYER_IMG_RE.finditer(resp.text):
        name = match.group(1)
        # Prefer the requested profile's own photo names. BDFutbol commonly
        # exposes a colour and a suffix variant (e.g. 90652.jpg / 90652b.jpg).
        if name.lower().startswith(str(bdfutbol_id).lower()) and name not in seen:
            seen.append(name)
    return seen


def download_best_photo(client: httpx.Client, filenames: list[str]) -> bytes | None:
    best: tuple[tuple[int, int, int], bytes] | None = None
    for name in filenames:
        resp = client.get(PHOTO_BASE + name, headers=HEADERS, timeout=20, follow_redirects=True)
        if resp.status_code != 200 or not resp.content:
            continue
        try:
            score = _score_candidate(resp.content)
        except Exception:
            continue
        if best is None or score > best[0]:
            best = (score, resp.content)
    return best[1] if best else None


def download_queue(
    queue_path: Path = DEFAULT_QUEUE,
    raw_dir: Path = DEFAULT_RAW_DIR,
    game_dir: Path = DEFAULT_GAME_DIR,
    *,
    statuses: set[str] | None = None,
    limit: int | None = None,
    delay: float = 1.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    statuses = statuses or {"ready_for_download"}
    raw_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[dict[str, Any]] = []
    already_in_game: list[int] = []
    already_downloaded: list[str] = []
    no_photo_available: list[str] = []
    failed: list[dict[str, str]] = []

    rows = [
        row
        for row in _load_queue(queue_path)
        if row.get("bdfutbol_id") and str(row.get("photo_status") or "") in statuses
    ]

    processed = 0
    with httpx.Client() as client:
        for row in rows:
            if limit is not None and processed >= limit:
                break
            source_id = int(row["source_id"])
            bdfutbol_id = str(row["bdfutbol_id"])

            if (game_dir / f"{source_id}.jpg").exists():
                already_in_game.append(source_id)
                continue

            dest = raw_dir / f"{bdfutbol_id}.jpg"
            if dest.exists() and not overwrite:
                already_downloaded.append(bdfutbol_id)
                continue

            processed += 1
            try:
                filenames = fetch_candidate_filenames(client, bdfutbol_id)
                if not filenames:
                    no_photo_available.append(bdfutbol_id)
                    continue
                content = download_best_photo(client, filenames)
                if content is None:
                    failed.append({"bdfutbol_id": bdfutbol_id, "error": "no_valid_candidate"})
                    continue
                dest.write_bytes(content)
                downloaded.append({
                    "source_id": source_id,
                    "bdfutbol_id": bdfutbol_id,
                    "display_name": row.get("display_name"),
                    "candidates": len(filenames),
                    "bytes": len(content),
                    "file": str(dest.relative_to(REPO_ROOT)),
                })
            except Exception as exc:  # pragma: no cover - defensive batch reporting
                failed.append({"bdfutbol_id": bdfutbol_id, "error": str(exc)})
            time.sleep(delay)

    return {
        "status": "complete" if not failed else "complete_with_errors",
        "processed": processed,
        "downloaded": len(downloaded),
        "already_in_game": len(already_in_game),
        "already_downloaded": len(already_downloaded),
        "no_photo_available": len(no_photo_available),
        "failed": len(failed),
        "raw_dir": str(raw_dir.relative_to(REPO_ROOT)),
        "downloaded_rows": downloaded,
        "no_photo_available_ids": no_photo_available,
        "failed_rows": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--status", action="append", dest="statuses")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    statuses = set(args.statuses) if args.statuses else None
    report = download_queue(
        args.queue,
        args.raw_dir,
        args.game_dir,
        statuses=statuses,
        limit=args.limit,
        delay=args.delay,
        overwrite=args.overwrite,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
