from __future__ import annotations

"""Apply single-candidate (surname-unique, DOB-unverifiable) squad matches.

Companion to apply_bdfutbol_squad_matches.py: that script only applies rows
whose BDFutbol birth date matched ours exactly. Some of our registry rows
have no birth_date recorded at all, so DOB verification is impossible even
though the surname uniquely identifies exactly one player on the club's
1993-94 squad. This script applies those -- explicitly reviewed and approved
by a human -- and tags them with a distinct provenance string so they stay
auditable/greppable as a lower-confidence tier than the DOB-verified ones.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "data" / "football9394" / "created_players_registry.json"
DEFAULT_REGISTRY_CSV = REPO_ROOT / "data" / "football9394" / "created_players_registry.csv"
PROVENANCE = "BDFutbol club squad roster cross-check, unique surname match, no birth date on file to verify (v0.47, human-reviewed)"


def apply_single_candidate_matches(
    match_reports: list[Path],
    registry_json: Path = DEFAULT_REGISTRY_JSON,
    registry_csv: Path = DEFAULT_REGISTRY_CSV,
) -> dict[str, Any]:
    registry = json.loads(registry_json.read_text(encoding="utf-8"))
    players = registry["players"]
    by_sid = {int(p["source_id"]): p for p in players}

    applied: list[dict[str, Any]] = []
    seen_sids: set[int] = set()

    for report_path in match_reports:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for club_result in report.get("results", []):
            for entry in club_result.get("needs_review", []):
                if len(entry["candidates"]) != 1:
                    continue
                sid = int(entry["source_id"])
                if sid in seen_sids:
                    continue
                row = by_sid.get(sid)
                if row is None or row.get("bdfutbol_id"):
                    continue
                cand = entry["candidates"][0]
                row["bdfutbol_id"] = cand["bdfutbol_id"]
                row["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{cand['bdfutbol_id']}.html"
                if not row.get("bdfutbol_search_name"):
                    row["bdfutbol_search_name"] = cand["full_name"]
                row["photo_status"] = "ready_for_download"
                row["individual_profile_source"] = PROVENANCE
                row["individual_profile_source_url"] = row["bdfutbol_url"]
                seen_sids.add(sid)
                applied.append({"source_id": sid, "our_name": row.get("display_name"), "matched_name": cand["full_name"], "bdfutbol_id": cand["bdfutbol_id"]})

    registry_json.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with registry_csv.open(encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle))
    with registry_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for p in players:
            writer.writerow(p)

    return {"applied": len(applied), "rows": applied}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("match_reports", type=Path, nargs="+")
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--registry-csv", type=Path, default=DEFAULT_REGISTRY_CSV)
    args = parser.parse_args()
    result = apply_single_candidate_matches(args.match_reports, args.registry_json, args.registry_csv)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
