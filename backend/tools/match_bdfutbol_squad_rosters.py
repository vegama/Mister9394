from __future__ import annotations

"""Cross-check pending-identity players against BDFutbol club squad rosters.

For clubs where the photo queue already has at least one confirmed
``bdfutbol_id``, this fetches that player's BDFutbol page to discover the
club's internal id (``data-idclub`` on their 1993-94 career-history row),
then fetches the club's 1993-94 squad page and lists every player on it.

Queue rows still marked ``pending_identity_profile`` for that club are then
matched against the squad by surname. Matches are cross-checked against the
squad member's own BDFutbol birth date before being reported as
``confirmed`` -- nothing is written back to the registry/queue here. This is
a research aid; a human still approves before any bdfutbol_id is assigned.
"""

import argparse
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394PhotoTool/1.0)"}

CAREER_ROW_RE = re.compile(
    r'data-temporada="1993-94"[^>]*data-idclub="(\d+)"[^>]*>\s*<a href="\.\./t/t1993-\d+\.html">1993-94</a>'
)
SQUAD_ROW_RE = re.compile(
    r"href='\.\./j/j(\d+)\.html'><span class='font-weight-bold mr-2 float-left'>([^<]*)</span>"
    r"<span class='d-none d-md-block float-left'>([^<]*)</span>"
)
DOB_RE = re.compile(r"Date of birth</[^>]+>\s*<[^>]+>\s*([0-3]?\d/[01]?\d/\d{4})")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", text.lower())


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def discover_idclub(client: httpx.Client, bootstrap_bdfutbol_id: str) -> str | None:
    resp = client.get(f"https://www.bdfutbol.com/en/j/j{bootstrap_bdfutbol_id}.html", headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    m = CAREER_ROW_RE.search(resp.text)
    return m.group(1) if m else None


def fetch_squad(client: httpx.Client, idclub: str) -> list[dict[str, str]]:
    resp = client.get(f"https://www.bdfutbol.com/en/t/t1993-94{idclub}.html", headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    return [
        {"bdfutbol_id": bid, "surname": surname, "full_name": full_name}
        for bid, surname, full_name in SQUAD_ROW_RE.findall(resp.text)
    ]


def fetch_dob(client: httpx.Client, bdfutbol_id: str) -> str | None:
    resp = client.get(f"https://www.bdfutbol.com/en/j/j{bdfutbol_id}.html", headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    m = DOB_RE.search(resp.text)
    if not m:
        return None
    d, mo, y = m.group(1).split("/")
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def match_club(
    client: httpx.Client,
    team_name: str,
    pending_rows: list[dict[str, Any]],
    bootstrap_bdfutbol_id: str,
    *,
    verify_dob: bool = True,
    delay: float = 0.6,
) -> dict[str, Any]:
    if bootstrap_bdfutbol_id.startswith("idclub:"):
        idclub = bootstrap_bdfutbol_id.split(":", 1)[1]
    else:
        idclub = discover_idclub(client, bootstrap_bdfutbol_id)
    if not idclub:
        return {"team": team_name, "status": "idclub_not_found"}
    time.sleep(delay)
    squad = fetch_squad(client, idclub)
    time.sleep(delay)

    squad_by_norm = {}
    for member in squad:
        squad_by_norm.setdefault(_norm(member["surname"]), []).append(member)

    confirmed: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for row in pending_rows:
        tokens = [t for t in re.split(r"\s+", row.get("display_name") or "") if t]
        candidates: list[dict[str, str]] = []
        for token in tokens:
            candidates.extend(squad_by_norm.get(_norm(token), []))
        if not candidates:
            unmatched.append({"source_id": row["source_id"], "display_name": row.get("display_name")})
            continue
        # de-dupe candidates by bdfutbol_id
        seen_ids = set()
        uniq = []
        for c in candidates:
            if c["bdfutbol_id"] not in seen_ids:
                seen_ids.add(c["bdfutbol_id"])
                uniq.append(c)

        picked = None
        expected_dob = (row.get("birth_date") or "")[:10]
        if verify_dob and expected_dob:
            for c in uniq:
                dob = fetch_dob(client, c["bdfutbol_id"])
                time.sleep(delay)
                if dob == expected_dob:
                    picked = {**c, "dob": dob}
                    break
        entry = {
            "source_id": row["source_id"],
            "display_name": row.get("display_name"),
            "expected_birth_date": expected_dob,
            "candidates": uniq,
        }
        if picked:
            entry["matched"] = picked
            confirmed.append(entry)
        else:
            needs_review.append(entry)

    return {
        "team": team_name,
        "status": "complete",
        "idclub": idclub,
        "squad_size": len(squad),
        "confirmed": confirmed,
        "needs_review": needs_review,
        "unmatched": unmatched,
    }


def run(
    queue_path: Path = DEFAULT_QUEUE,
    *,
    countries: set[str] | None = None,
    verify_dob: bool = True,
    delay: float = 0.6,
    extra_bootstrap: dict[str, str] | None = None,
) -> dict[str, Any]:
    rows = _load_queue(queue_path)
    pending = [r for r in rows if r.get("photo_status") == "pending_identity_profile"]
    if countries:
        pending = [r for r in pending if r.get("country_name") in countries]

    # Bootstrap is keyed by club name only: BDFutbol's per-club id is the same
    # regardless of which nationality of player we happen to already have
    # confirmed there.
    bootstrap: dict[str, str] = {}
    for r in rows:
        team = r.get("team_name")
        if r.get("bdfutbol_id") and team and team not in bootstrap:
            bootstrap[team] = str(r["bdfutbol_id"])
    if extra_bootstrap:
        bootstrap.update(extra_bootstrap)

    by_club: dict[str, list[dict[str, Any]]] = {}
    for r in pending:
        by_club.setdefault(r.get("team_name"), []).append(r)

    results = []
    unresolved_clubs = []
    with httpx.Client() as client:
        for team, club_rows in by_club.items():
            boot_id = bootstrap.get(team)
            if not boot_id:
                unresolved_clubs.append({"team": team, "pending": len(club_rows)})
                continue
            results.append(match_club(client, team, club_rows, boot_id, verify_dob=verify_dob, delay=delay))

    return {
        "clubs_processed": len(results),
        "clubs_unresolved": len(unresolved_clubs),
        "unresolved_clubs": unresolved_clubs,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--country", action="append", dest="countries")
    parser.add_argument("--no-verify-dob", action="store_true")
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--extra-bootstrap", type=Path, help="JSON file mapping team_name -> a known bdfutbol_id for that club")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    countries = set(args.countries) if args.countries else None
    extra_bootstrap = json.loads(args.extra_bootstrap.read_text(encoding="utf-8")) if args.extra_bootstrap else None
    report = run(args.queue, countries=countries, verify_dob=not args.no_verify_dob, delay=args.delay, extra_bootstrap=extra_bootstrap)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "clubs_processed": report["clubs_processed"],
        "clubs_unresolved": report["clubs_unresolved"],
        "confirmed_total": sum(len(r.get("confirmed", [])) for r in report["results"]),
        "needs_review_total": sum(len(r.get("needs_review", [])) for r in report["results"]),
        "unmatched_total": sum(len(r.get("unmatched", [])) for r in report["results"]),
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
