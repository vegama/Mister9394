from __future__ import annotations

"""Add real 1993-94-era players to near-functional national-team pools.

The import is deliberately small and evidence-driven. Every candidate is first
reconciled against the entire current player database; ambiguous candidates stop
the import. Missing players are stored under a non-playable Otros-País owner if
their historical club is not part of an active competition.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.app.football9394.snapshot_runtime import PRESENTATION_COUNTRIES
from backend.tools.enrich_world_cup_1994 import (
    build_identity_candidate_index,
    clean_text,
    derived_attributes,
    identity_candidate_pool,
    make_container,
    position_fields,
    write_creation_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_ADDITIONS = REPO_ROOT / "data" / "football9394" / "national_pool_1993_94_additions.json"
DEFAULT_REPORT = REPO_ROOT / "data" / "football9394" / "national_pool_1993_94_enrichment_report.json"


def build_player(row: dict[str, Any], *, team_id: int) -> dict[str, Any]:
    overall = int(row["overall"])
    pos = str(row["position_code"]).upper()
    primary, broad, role_ratings = position_fields(pos)
    return {
        "source_id": int(row["source_id"]),
        "team_id": int(team_id),
        "display_name": row["display_name"],
        "first_name": row.get("first_name") or row["display_name"],
        "surname1": row.get("surname1"),
        "surname2": None,
        "birth_date": f"{row['birth_date']}T00:00:00",
        "birth_country_id": int(row["country_id"]),
        "international_country_id": int(row["country_id"]),
        "preferred_foot": 1,
        "shirt_number": None,
        "primary_role": primary,
        "broad_position": broad,
        "overall": overall,
        "category": min(99, overall + 1),
        "height_cm": None,
        "weight_kg": None,
        "salary": 0,
        "release_clause": 0,
        "contract_start_year": None,
        "contract_end_year": None,
        "loan": False,
        "initially_reserve": False,
        "retired": False,
        "attributes": derived_attributes(overall, pos, f"national-pool-{row['source_id']}"),
        "birth_city_id": 0,
        "naturalized_country_id": None,
        "basque_origin": False,
        "favorite_shirt_number": 0,
        "injury_proneness": 0,
        "progression_mean": 0,
        "fan_affection": 5,
        "academy_team_id": 0,
        "previous_team_id": 0,
        "previous_team_years": 0,
        "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False, "long_shots": False, "cuts_inside": False, "first_time_play": False, "dives": False},
        "identity_source": row.get("identity_source"),
        "identity_source_url": row.get("identity_source_url"),
        "historical_data_source": row.get("identity_source"),
        "attribute_source": "provisional_pending_profile_review",
        "profile_review_required": True,
        "role_detail_source": "verified_historical_broad_position",
        "historical_club_1994": row.get("historical_club_1994"),
        "historical_position_1993_94": row.get("historical_position"),
        "market_container_origin": row.get("country_name"),
        "external_origin": "national_pool_1993_94",
        "creation_batch": row.get("creation_batch") or "national_team_pool_expansion_0.22",
        "verified_national_pool_year": row.get("verified_national_pool_year"),
        "verified_national_pool_1993_94": bool(row.get("verified_national_pool_year") == 1993),
        "verified_era_pool_1993_94": True,
        "source_confidence": row.get("source_confidence"),
        "historical_context": row.get("historical_context"),
    }


def enrich(snapshot_path: Path = DEFAULT_SNAPSHOT, additions_path: Path = DEFAULT_ADDITIONS, report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    additions = json.loads(additions_path.read_text(encoding="utf-8"))

    # Idempotent rerun: remove only players derived by this batch. Containers are
    # stable shared ownership records and can be reused safely.
    snapshot["players"] = [p for p in snapshot.get("players", []) if p.get("external_origin") != "national_pool_1993_94"]
    index = build_identity_candidate_index(snapshot.get("players", []))
    teams_by_id = {int(t["source_id"]): t for t in snapshot.get("teams", [])}
    containers_by_country = {int(t.get("country_id") or 0): t for t in snapshot.get("teams", []) if t.get("market_container")}

    resolutions: list[dict[str, Any]] = []
    created = 0
    reused = 0
    for row in additions.get("players", []):
        country_id = int(row["country_id"])
        candidates = identity_candidate_pool(
            index,
            display=row["display_name"],
            given=row.get("first_name") or "",
            family=row.get("surname1") or "",
            dob=row.get("birth_date"),
            expected_team=None,
            override=None,
        )
        result = reconcile_player_identity(
            candidates,
            target_display=row["display_name"],
            target_given=row.get("first_name") or "",
            target_family=row.get("surname1") or "",
            target_birth_date=row.get("birth_date"),
            target_country_id=country_id,
        )
        audit = {
            "candidate_source_id": int(row["source_id"]),
            "display_name": row["display_name"],
            "country_id": country_id,
            "compared_against_existing_players": len(snapshot.get("players", [])),
            "resolution": result.resolution,
            "confidence": result.confidence,
            "matched_existing_id": int(result.player["source_id"]) if result.player else None,
            "candidate_matches": [
                {"source_id": c.source_id, "display_name": c.display_name, "score": c.score, "same_dob": c.same_dob, "same_team": c.same_team, "same_country": c.same_country}
                for c in result.candidates
            ],
        }
        if result.resolution == "ambiguous_existing_candidates":
            raise RuntimeError(f"ambiguous historical identity: {row['display_name']}")
        if result.player is not None:
            player = result.player
            player["international_country_id"] = country_id
            player["verified_era_pool_1993_94"] = True
            era_sources = player.setdefault("verified_era_pool_sources", [])
            era_source = {"year": row.get("verified_national_pool_year"), "source": row.get("identity_source"), "url": row.get("identity_source_url")}
            if era_source not in era_sources:
                era_sources.append(era_source)
            if row.get("verified_national_pool_year") == 1993:
                player["verified_national_pool_1993_94"] = True
                sources = player.setdefault("verified_national_pool_sources", [])
                source_row = {"year": 1993, "source": row.get("identity_source"), "url": row.get("identity_source_url")}
                if source_row not in sources:
                    sources.append(source_row)
            audit["action"] = "reused_existing"
            reused += 1
            resolutions.append(audit)
            continue

        container = containers_by_country.get(country_id)
        if container is None:
            container = make_container({"country_id": country_id, "name": row["country_name"], "team_code": f"C{country_id}"})
            snapshot["teams"].append(container)
            teams_by_id[int(container["source_id"])] = container
            containers_by_country[country_id] = container
        player = build_player(row, team_id=int(container["source_id"]))
        snapshot["players"].append(player)
        audit.update({"action": "created", "created_source_id": int(player["source_id"]), "team_id": int(container["source_id"]), "team_name": container["name"]})
        created += 1
        resolutions.append(audit)

    snapshot["players"].sort(key=lambda p: int(p["source_id"]))
    snapshot["teams"].sort(key=lambda t: int(t["source_id"]))
    snapshot["national_pool_1993_94_enrichment"] = {
        "status": "complete",
        "batch": additions.get("batch"),
        "candidates": len(additions.get("players", [])),
        "created": created,
        "reused_existing": reused,
        "identity_policy": "global existing-player comparison; ambiguity blocks creation",
    }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = write_creation_registry(snapshot)
    report = {
        **snapshot["national_pool_1993_94_enrichment"],
        "created_player_registry_rows": len(registry),
        "resolutions": resolutions,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--additions", type=Path, default=DEFAULT_ADDITIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    print(json.dumps(enrich(args.snapshot, args.additions, args.report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
