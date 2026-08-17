from __future__ import annotations

"""Apply DOB-verified squad-roster matches from match_bdfutbol_squad_rosters.py
onto the created-players registry.

Only rows in the match report's ``confirmed`` lists are touched -- those are
the ones whose BDFutbol birth date matched our recorded birth date exactly.
``needs_review``/``unmatched`` entries and unresolved clubs are left alone
for manual follow-up.

Two distinct situations get merged here:
  * rows that already carried the same bdfutbol_id (a stale photo_status
    left over from an earlier batch) -- only photo_status is corrected;
  * rows with no prior bdfutbol_id -- the id/url/search name are written for
    the first time, with provenance recorded so it is auditable later.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "data" / "football9394" / "created_players_registry.json"
DEFAULT_REGISTRY_CSV = REPO_ROOT / "data" / "football9394" / "created_players_registry.csv"
DEFAULT_MATCH_REPORT = REPO_ROOT / "data" / "football9394" / "bdfutbol_squad_match_report.json"
PROVENANCE_TAG = "bdfutbol_squad_roster_dob_verified_v047"


def apply_matches(
    registry_json: Path = DEFAULT_REGISTRY_JSON,
    registry_csv: Path = DEFAULT_REGISTRY_CSV,
    match_report: Path = DEFAULT_MATCH_REPORT,
) -> dict[str, Any]:
    registry = json.loads(registry_json.read_text(encoding="utf-8"))
    players = registry["players"]
    by_sid = {int(p["source_id"]): p for p in players}

    report = json.loads(match_report.read_text(encoding="utf-8"))

    status_fixed = 0
    newly_identified = 0
    skipped_missing_row = []

    for club_result in report.get("results", []):
        for entry in club_result.get("confirmed", []):
            sid = int(entry["source_id"])
            row = by_sid.get(sid)
            if row is None:
                skipped_missing_row.append(sid)
                continue
            matched = entry["matched"]
            existing_id = str(row.get("bdfutbol_id") or "")
            if existing_id == matched["bdfutbol_id"]:
                if row.get("photo_status") == "pending_identity_profile":
                    row["photo_status"] = "ready_for_download"
                    status_fixed += 1
                continue
            row["bdfutbol_id"] = matched["bdfutbol_id"]
            row["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{matched['bdfutbol_id']}.html"
            if not row.get("bdfutbol_search_name"):
                row["bdfutbol_search_name"] = matched["full_name"]
            row["photo_status"] = "ready_for_download"
            row["individual_profile_source"] = "BDFutbol club squad roster cross-check, name + birth date verified (v0.47)"
            row["individual_profile_source_url"] = row["bdfutbol_url"]
            newly_identified += 1

    registry_json.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with registry_csv.open(encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle))
    with registry_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for p in players:
            writer.writerow(p)

    return {
        "status_fixed": status_fixed,
        "newly_identified": newly_identified,
        "skipped_missing_row": skipped_missing_row,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--registry-csv", type=Path, default=DEFAULT_REGISTRY_CSV)
    parser.add_argument("--match-report", type=Path, default=DEFAULT_MATCH_REPORT)
    args = parser.parse_args()
    result = apply_matches(args.registry_json, args.registry_csv, args.match_report)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
