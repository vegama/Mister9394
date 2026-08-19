from __future__ import annotations

"""Export the historical-player creation registry as a BDFutbol photo work queue.

The queue intentionally contains only players that were truly created by the
historical enrichers. Existing/reconciled players are tracked in the identity
reports instead, so a photo downloader can process new records without turning
reused identities into duplicate assets.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "data" / "football9394" / "created_players_registry.json"
DEFAULT_CSV = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.csv"
DEFAULT_JSON = REPO_ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"

QUEUE_FIELDS = [
    "source_id",
    "display_name",
    "first_name",
    "surname1",
    "surname2",
    "birth_date",
    "country_id",
    "country_name",
    "broad_position",
    "team_id",
    "team_name",
    "creation_batch",
    "identity_source",
    "identity_source_url",
    "verified_national_pool_year",
    "historical_position_1993_94",
    "historical_club_1994",
    "duplicate_check",
    "matched_existing_id",
    "bdfutbol_search_name",
    "bdfutbol_id",
    "bdfutbol_url",
    "photo_filename",
    "photo_width",
    "photo_height",
    "photo_format",
    "photo_mode",
    "photo_status",
]


def build_queue(registry_path: Path = DEFAULT_REGISTRY) -> list[dict[str, Any]]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = payload.get("players", payload) if isinstance(payload, dict) else payload
    queue: list[dict[str, Any]] = []
    for row in rows or []:
        if row.get("retired_alias_v113"):
            continue
        if str(row.get("duplicate_check") or "") not in {
            "created_after_global_existing_player_comparison",
            "belgium_1993_94_identity_gate",
            "turkey_1993_94_explicit_identity_gate",
            "russia_1993_explicit_identity_gate",
            "greece_1993_94_explicit_identity_gate",
            "exact_name_birthdate_historical_identity_gate",
            "exact_name_birthdate_bdfutbol_identity_gate",
            "exact_name_birthdate_source_profile_gate_v036",
            "exact_name_birthdate_source_profile_gate_v037",
            "exact_name_birthdate_source_profile_gate_v038",
            "exact_name_birthdate_source_profile_gate_v039",
            "exact_name_birthdate_source_profile_gate_v040",
            "exact_name_birthdate_source_profile_gate_v041",
            "exact_name_birthdate_source_profile_gate_v042",
            "exact_name_birthdate_source_profile_gate_v043",
            "exact_name_birthdate_source_profile_gate_v044",
            "individual_profile_id_identity_gate_v045",
            "individual_profile_id_identity_gate_v046",
            "id_collision_restored_v113",
        }:
            continue
        item = {field: row.get(field) for field in QUEUE_FIELDS}
        item["photo_status"] = item.get("photo_status") or "pending"
        item["photo_filename"] = item.get("photo_filename") or f"{int(row['source_id'])}.jpg"
        item["photo_width"] = 40
        item["photo_height"] = 55
        item["photo_format"] = "JPEG"
        item["photo_mode"] = "RGB"
        item["bdfutbol_search_name"] = item.get("bdfutbol_search_name") or row.get("display_name")
        queue.append(item)
    queue.sort(key=lambda row: (str(row.get("country_name") or ""), str(row.get("display_name") or ""), int(row["source_id"])))
    return queue


def export_queue(
    registry_path: Path = DEFAULT_REGISTRY,
    csv_path: Path = DEFAULT_CSV,
    json_path: Path = DEFAULT_JSON,
) -> dict[str, Any]:
    queue = build_queue(registry_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(queue)
    json_path.write_text(json.dumps({"players": queue}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "complete",
        "players": len(queue),
        "csv": str(csv_path.relative_to(REPO_ROOT)),
        "json": str(json_path.relative_to(REPO_ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()
    print(json.dumps(export_queue(args.registry, args.csv, args.json), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
