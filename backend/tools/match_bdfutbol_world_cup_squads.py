from __future__ import annotations

"""Cross-check pending World Cup 1994 players against BDFutbol's own
World Cup 1994 squad pages (a "manager" tool section, not the regular club
pages): https://www.bdfutbol.com/es/c/plantilla.html?temporada=<code>&club=<Country>

BDFutbol groups the 24 finalists under six `temporada` codes (one per
1994 group). GROUP_CODES below was discovered by probing every country
against a range of codes and keeping the one whose page title read
"<country> 1994 Mundial".

Each squad row is one of two kinds:
  * "main" -- the player has a full profile on the main site
    (j/j<id>.html?manager=1); DOB comes from the English "Date of birth"
    field and photos go through the regular /i/j/<id>.jpg pipeline.
  * "manager" -- the player only exists inside this manager tool
    (c/jugador.html?id=<id>); DOB comes from the Spanish
    "Fecha de nacimiento" field and the photo is a direct upload URL
    embedded in the squad row itself (no /i/j/ equivalent).

Matching follows the same discipline as match_bdfutbol_squad_rosters.py:
a candidate is only "confirmed" when their BDFutbol birth date matches ours
exactly.
"""

import argparse
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
DEFAULT_MANAGER_RAW_DIR = REPO_ROOT / "data" / "football9394" / "bdfutbol_photos_raw_manager"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394PhotoTool/1.0)"}
PLANTILLA_URL = "https://www.bdfutbol.com/es/c/plantilla.html"

GROUP_CODES: dict[str, str] = {
    "Estados Unidos": "2805", "Suiza": "2805", "Colombia": "2805", "Rumanía": "2805",
    "Brasil": "2806", "Suecia": "2806", "Rusia": "2806", "Camerún": "2806",
    "Alemania": "2807", "Bolivia": "2807", "España": "2807", "Corea del Sur": "2807",
    "Argentina": "2809", "Grecia": "2809", "Nigeria": "2809", "Bulgaria": "2809",
    "México": "2810", "Irlanda": "2810", "Italia": "2810", "Noruega": "2810",
    "Bélgica": "2811", "Marruecos": "2811", "Países Bajos": "2811", "Arabia Saudí": "2811",
}

ROW_RE = re.compile(
    r'<img class="mini-foto-jugador" src="([^"]+)" alt=""></td>.*?'
    r"href='(\.\./j/j\d+\.html\?manager=1|\.\./c/jugador\.html\?id=\d+)'>"
    r"<span class='font-weight-bold mr-2 float-left'>([^<]*)</span>"
    r"<span class='d-none d-md-block float-left'>([^<]*)</span>"
)
DOB_EN_RE = re.compile(r"Date of birth</[^>]+>\s*<[^>]+>\s*([0-3]?\d/[01]?\d/\d{4})")
DOB_ES_RE = re.compile(r"Fecha de nacimiento</[^>]+>\s*<[^>]+>\s*([0-3]?\d/[01]?\d/\d{4})")


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


def fetch_squad(client: httpx.Client, country: str) -> list[dict[str, str]]:
    code = GROUP_CODES[country]
    resp = client.get(PLANTILLA_URL, params={"temporada": code, "club": country}, headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    squad = []
    for photo_src, href, surname, full_name in ROW_RE.findall(resp.text):
        if "j/j" in href:
            m = re.search(r"j/j(\d+)\.html", href)
            squad.append({"kind": "main", "id": m.group(1), "surname": surname, "full_name": full_name, "photo_url": urljoin("https://www.bdfutbol.com/i/m/", photo_src)})
        else:
            m = re.search(r"id=(\d+)", href)
            squad.append({"kind": "manager", "id": m.group(1), "surname": surname, "full_name": full_name, "photo_url": urljoin(str(resp.url), photo_src.replace(".mini.png", ""))})
    return squad


def fetch_dob(client: httpx.Client, member: dict[str, str]) -> str | None:
    if member["kind"] == "main":
        resp = client.get(f"https://www.bdfutbol.com/en/j/j{member['id']}.html", headers=HEADERS, timeout=20, follow_redirects=True)
        pattern = DOB_EN_RE
    else:
        resp = client.get("https://www.bdfutbol.com/es/c/jugador.html", params={"id": member["id"]}, headers=HEADERS, timeout=20, follow_redirects=True)
        pattern = DOB_ES_RE
    resp.raise_for_status()
    m = pattern.search(resp.text)
    if not m:
        return None
    d, mo, y = m.group(1).split("/")
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def match_country(client: httpx.Client, country: str, pending_rows: list[dict[str, Any]], *, delay: float = 0.6) -> dict[str, Any]:
    squad = fetch_squad(client, country)
    time.sleep(delay)
    squad_by_norm: dict[str, list[dict[str, str]]] = {}
    for member in squad:
        keys = {_norm(member["surname"])}
        keys.update(_norm(t) for t in re.split(r"[\s-]+", member["full_name"]))
        for key in keys:
            if key:
                squad_by_norm.setdefault(key, []).append(member)

    confirmed: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for row in pending_rows:
        tokens = [t for t in re.split(r"\s+", row.get("display_name") or "") if t]
        candidates: list[dict[str, str]] = []
        for token in tokens:
            candidates.extend(squad_by_norm.get(_norm(token), []))
        seen = set()
        uniq = [c for c in candidates if not ((c["kind"], c["id"]) in seen or seen.add((c["kind"], c["id"])))]
        if not uniq:
            unmatched.append({"source_id": row["source_id"], "display_name": row.get("display_name")})
            continue
        expected_dob = (row.get("birth_date") or "")[:10]
        picked = None
        if expected_dob:
            for c in uniq:
                dob = fetch_dob(client, c)
                time.sleep(delay)
                if dob == expected_dob:
                    picked = {**c, "dob": dob}
                    break
        entry = {"source_id": row["source_id"], "display_name": row.get("display_name"), "expected_birth_date": expected_dob, "candidates": uniq}
        if picked:
            entry["matched"] = picked
            confirmed.append(entry)
        else:
            needs_review.append(entry)

    return {"country": country, "squad_size": len(squad), "confirmed": confirmed, "needs_review": needs_review, "unmatched": unmatched}


def run(queue_path: Path = DEFAULT_QUEUE, *, delay: float = 0.6) -> dict[str, Any]:
    rows = _load_queue(queue_path)
    pending = [r for r in rows if r.get("photo_status") == "pending" and r.get("country_name") in GROUP_CODES]
    by_country: dict[str, list[dict[str, Any]]] = {}
    for r in pending:
        by_country.setdefault(r["country_name"], []).append(r)

    results = []
    with httpx.Client() as client:
        for country, country_rows in by_country.items():
            results.append(match_country(client, country, country_rows, delay=delay))

    return {"results": results}


def download_manager_photos(report: dict[str, Any], raw_dir: Path = DEFAULT_MANAGER_RAW_DIR, *, delay: float = 0.6) -> dict[str, Any]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    failed = []
    with httpx.Client() as client:
        for club_result in report.get("results", []):
            for entry in club_result.get("confirmed", []):
                matched = entry["matched"]
                if matched["kind"] != "manager":
                    continue
                dest = raw_dir / f"{entry['source_id']}.jpg"
                try:
                    resp = client.get(matched["photo_url"], headers=HEADERS, timeout=20, follow_redirects=True)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                    downloaded.append({"source_id": entry["source_id"], "file": str(dest)})
                except Exception as exc:  # pragma: no cover
                    failed.append({"source_id": entry["source_id"], "error": str(exc)})
                time.sleep(delay)
    return {"downloaded": len(downloaded), "failed": len(failed), "rows": downloaded, "failed_rows": failed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.queue, delay=args.delay)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "countries_processed": len(report["results"]),
        "confirmed_total": sum(len(r["confirmed"]) for r in report["results"]),
        "needs_review_total": sum(len(r["needs_review"]) for r in report["results"]),
        "unmatched_total": sum(len(r["unmatched"]) for r in report["results"]),
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
