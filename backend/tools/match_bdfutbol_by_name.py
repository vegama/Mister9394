from __future__ import annotations

"""Identify pending-identity players by searching BDFutbol's player search
directly by full name and verifying against our recorded birth date.

This is the sibling of match_bdfutbol_squad_rosters.py for players who have
no discoverable club-squad page to anchor on (World Cup 1994 national-team
players from countries BDFutbol covers thinly, e.g. non-European squads).
BDFutbol's search does loose OR-token matching, so results are noisy; only
rows whose birth date matches ours exactly are treated as confirmed.
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394PhotoTool/1.0)"}

RESULT_ROW_RE = re.compile(
    r"<tr class='tipus1'><td class='text-left'>Player</td>"
    r"<td class='text-nowrap text-left'><a href='j/j(\d+)\.html'>(.+?)</a></td>"
    r".*?<span class='sortval(\d{8})'>"
)
_TAG_RE = re.compile(r"<[^>]+>")


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def search_player(client: httpx.Client, name: str) -> list[dict[str, str]]:
    resp = client.get(
        "https://www.bdfutbol.com/en/buscar.php",
        params={"d": name, "bj": "on"},
        headers=HEADERS,
        timeout=20,
        follow_redirects=True,
    )
    resp.raise_for_status()
    out = []
    for m in RESULT_ROW_RE.finditer(resp.text):
        bdfutbol_id, full_name, sortval = m.groups()
        full_name = _TAG_RE.sub("", full_name)
        dob = f"{sortval[:4]}-{sortval[4:6]}-{sortval[6:8]}"
        out.append({"bdfutbol_id": bdfutbol_id, "full_name": full_name, "dob": dob})
    return out


def run(
    queue_path: Path = DEFAULT_QUEUE,
    *,
    countries: set[str] | None = None,
    delay: float = 0.6,
    limit: int | None = None,
) -> dict[str, Any]:
    rows = _load_queue(queue_path)
    pending = [r for r in rows if r.get("photo_status") == "pending" and r.get("display_name")]
    if countries:
        pending = [r for r in pending if r.get("country_name") in countries]
    if limit:
        pending = pending[:limit]

    confirmed: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    no_results: list[dict[str, Any]] = []

    with httpx.Client() as client:
        for row in pending:
            expected_dob = (row.get("birth_date") or "")[:10]
            candidates = search_player(client, row["display_name"])
            time.sleep(delay)
            if not candidates:
                no_results.append({"source_id": row["source_id"], "display_name": row.get("display_name")})
                continue
            match = next((c for c in candidates if expected_dob and c["dob"] == expected_dob), None)
            entry = {
                "source_id": row["source_id"],
                "display_name": row.get("display_name"),
                "country_name": row.get("country_name"),
                "expected_birth_date": expected_dob,
                "candidates": candidates[:20],
            }
            if match:
                entry["matched"] = match
                confirmed.append(entry)
            else:
                needs_review.append(entry)

    return {
        "processed": len(pending),
        "confirmed": confirmed,
        "needs_review": needs_review,
        "no_results": no_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--country", action="append", dest="countries")
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    countries = set(args.countries) if args.countries else None
    report = run(args.queue, countries=countries, delay=args.delay, limit=args.limit)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "processed": report["processed"],
        "confirmed": len(report["confirmed"]),
        "needs_review": len(report["needs_review"]),
        "no_results": len(report["no_results"]),
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
