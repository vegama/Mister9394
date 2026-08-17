from __future__ import annotations

"""Gate for historical players created by enrichment batches.

Every generated player is compared against the pre-existing database.  Strong
or ambiguous collisions fail the gate.  The report is deliberately machine
readable so future data passes and the photo pipeline can inspect it.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.tools.enrich_world_cup_1994 import build_identity_candidate_index, identity_candidate_pool, clean_text

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_REPORT = REPO_ROOT / "data" / "football9394" / "created_players_duplicate_audit.json"


def audit(snapshot_path: Path = DEFAULT_SNAPSHOT, report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    created = [p for p in snapshot.get("players", []) if p.get("external_origin") in {"world_cup_1994", "national_pool_1993_94"}]
    base = [p for p in snapshot.get("players", []) if p.get("external_origin") not in {"world_cup_1994", "national_pool_1993_94"}]
    index = build_identity_candidate_index(base)
    collisions: list[dict[str, Any]] = []
    checked: list[dict[str, Any]] = []
    for player in created:
        country_id = int(player.get("international_country_id") or player.get("birth_country_id") or 0) or None
        team_id = int(player.get("team_id") or 0)
        expected_team = team_id if 0 < team_id < 9_400_000 else None
        candidates = identity_candidate_pool(
            index,
            display=str(player.get("display_name") or ""),
            given=str(player.get("first_name") or ""),
            family=str(player.get("surname1") or ""),
            dob=player.get("birth_date"),
            expected_team=expected_team,
            override=None,
        )
        result = reconcile_player_identity(
            candidates,
            target_display=str(player.get("display_name") or ""),
            target_given=str(player.get("first_name") or ""),
            target_family=str(player.get("surname1") or ""),
            target_birth_date=player.get("birth_date"),
            target_country_id=country_id,
            expected_team_id=expected_team,
        )
        row = {
            "created_source_id": int(player["source_id"]),
            "display_name": player.get("display_name"),
            "country_id": country_id,
            "team_id": team_id,
            "resolution": result.resolution,
            "candidate_count": len(result.candidates),
            "matched_existing_id": int(result.player["source_id"]) if result.player is not None else None,
            "candidates": [c.__dict__ if hasattr(c, "__dict__") else {
                "source_id": c.source_id,
                "display_name": c.display_name,
                "score": c.score,
                "full_similarity": c.full_similarity,
                "given_similarity": c.given_similarity,
                "same_surname": c.same_surname,
                "same_country": c.same_country,
                "same_team": c.same_team,
                "same_dob": c.same_dob,
                "same_day_month": c.same_day_month,
                "year_delta": c.year_delta,
            } for c in result.candidates],
        }
        checked.append(row)
        if result.player is not None or result.resolution == "ambiguous_existing_candidates":
            collisions.append(row)

    # Generated-to-generated exact identity duplication is independently banned.
    seen: dict[tuple[str, str], int] = {}
    generated_duplicates: list[dict[str, Any]] = []
    for player in created:
        key = (clean_text(player.get("display_name")), str(player.get("birth_date") or "")[:10])
        if key in seen:
            generated_duplicates.append({"key": key, "source_ids": [seen[key], int(player["source_id"])]})
        else:
            seen[key] = int(player["source_id"])

    report = {
        "status": "pass" if not collisions and not generated_duplicates else "fail",
        "created_players_checked": len(created),
        "existing_players_compared": len(base),
        "strong_or_ambiguous_collisions": collisions,
        "generated_exact_duplicates": generated_duplicates,
        "checked": checked,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = audit(args.snapshot, args.report)
    print(json.dumps({k: v for k, v in report.items() if k != "checked"}, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
