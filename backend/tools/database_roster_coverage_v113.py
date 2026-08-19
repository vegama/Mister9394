from __future__ import annotations

"""Source-backed 1993-94 roster coverage fixes for the v1.1.3 data pass.

This tool is intentionally small and idempotent.  It only applies additions or
exclusions backed by named historical sources.  Ratings are fixed, conservative
1993-94 estimates cloned from role/level comparables already present in the
historical database; there is no runtime formula and no synthetic filler.
"""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "database_roster_coverage_v113.json"

VVV_TEAM_ID = 412
VVV_SEASON_SOURCE = "https://historie.vvv-venlo.nl/nl/seizoenen/1993-1994"

# Jos Rutten's official VVV page gives 26-08-1992 as his final league match.
# Keep the historical row resolvable but do not count it in the 1993-94 squad.
VVV_INACTIVE_ROWS = {
    6993: {
        "reason": "not_in_vvv_first_team_1993_94_official_season_record",
        "source": "https://historie.vvv-venlo.nl/nl/spelers/Rutten/Jos/11-11-1962",
    }
}

# New IDs are in a dedicated, stable v1.1.3 manual-source range.
# comparable_source_id supplies only the fixed attribute shape.  Identity,
# role, season participation and the target overall below are independently
# curated from the historical sources listed here.
VVV_ADDITIONS: tuple[dict[str, Any], ...] = (
    {
        "source_id": 9499100, "display_name": "Eugène Hanssen", "first_name": "Eugène", "surname1": "Hanssen",
        "birth_date": "1959-01-09T00:00:00", "primary_role": 2, "broad_position": "DEF", "overall": 72,
        "preferred_foot": 2, "appearances_total": 34, "goals_total": 1, "comparable_source_id": 6668,
        "source_profile_url": "https://historie.vvv-venlo.nl/nl/spelers/Hanssen/Eug%C3%A8ne/09-01-1959",
        "historical_position_1993_94": "Left Back",
    },
    {
        "source_id": 9499101, "display_name": "Saeed Janfada", "first_name": "Saeed", "surname1": "Janfada",
        "birth_date": "1964-03-21T00:00:00", "primary_role": 2, "broad_position": "DEF", "overall": 71,
        "preferred_foot": 2, "appearances_total": 39, "goals_total": 1, "comparable_source_id": 6668,
        "source_profile_url": "https://historie.vvv-venlo.nl/en/spelers/Janfada/Saeed/21-03-1964",
        "historical_position_1993_94": "Left Back",
    },
    {
        "source_id": 9499102, "display_name": "Pieter van Leenders", "first_name": "Pieter", "surname1": "van Leenders",
        "birth_date": "1966-12-10T00:00:00", "primary_role": 7, "broad_position": "MED", "overall": 70,
        "preferred_foot": 1, "appearances_total": 30, "goals_total": 5, "comparable_source_id": 6998,
        "source_profile_url": "https://historie.vvv-venlo.nl/spelers/Leenders/Pieter/10-12-1966",
        "historical_position_1993_94": "Central Midfielder",
    },
    {
        "source_id": 9499103, "display_name": "Bert Spee", "first_name": "Bert", "surname1": "Spee",
        "birth_date": "1966-09-14T00:00:00", "primary_role": 7, "broad_position": "MED", "overall": 69,
        "preferred_foot": 1, "appearances_total": 32, "goals_total": 0, "comparable_source_id": 6998,
        "source_profile_url": "https://historie.vvv-venlo.nl/nl/spelers/Spee/Bert/14-09-1966",
        "historical_position_1993_94": "Central Midfielder",
    },
    {
        "source_id": 9499104, "display_name": "Eric Teeuwen", "first_name": "Eric", "surname1": "Teeuwen",
        "birth_date": "1972-04-06T00:00:00", "primary_role": 3, "broad_position": "DEF", "overall": 66,
        "preferred_foot": 1, "appearances_total": 7, "goals_total": 0, "comparable_source_id": 6992,
        "source_profile_url": "https://historie.vvv-venlo.nl/nl/spelers/Teeuwen/Eric/06-04-1972",
        "historical_position_1993_94": "Defender",
    },
    {
        "source_id": 9499105, "display_name": "Jaap Geurtjens", "first_name": "Jaap", "surname1": "Geurtjens",
        "birth_date": "1974-08-09T00:00:00", "primary_role": 3, "broad_position": "DEF", "overall": 63,
        "preferred_foot": 1, "appearances_total": 2, "goals_total": 0, "comparable_source_id": 6849,
        "source_profile_url": VVV_SEASON_SOURCE,
        "historical_position_1993_94": "Defender",
    },
    {
        "source_id": 9499106, "display_name": "Micky Oestreich", "first_name": "Micky", "surname1": "Oestreich",
        "birth_date": "1969-08-21T00:00:00", "primary_role": 17, "broad_position": "DEL", "overall": 65,
        "preferred_foot": 1, "appearances_total": 5, "goals_total": 0, "comparable_source_id": 7005,
        "source_profile_url": "https://historie.vvv-venlo.nl/spelers/Oestreich/Micky/21-08-1969",
        "historical_position_1993_94": "Striker",
    },
    {
        "source_id": 9499107, "display_name": "Erwin Wolter", "first_name": "Erwin", "surname1": "Wolter",
        "birth_date": "1973-04-12T00:00:00", "primary_role": 7, "broad_position": "MED", "overall": 66,
        "preferred_foot": 1, "appearances_total": 7, "goals_total": 0, "comparable_source_id": 6848,
        "source_profile_url": "https://www.bdfutbol.com/es/j/j63136.html",
        "historical_position_1993_94": "Central Midfielder",
    },
)


def _scaled_attributes(source: dict[str, Any], target_overall: int) -> dict[str, int]:
    delta = int(target_overall) - int(source.get("overall") or target_overall)
    attrs = deepcopy(source.get("attributes") or {})
    return {key: max(35, min(92, int(value) + delta)) for key, value in attrs.items()}


def _role_ratings(role: int) -> dict[str, int]:
    ratings = {str(i): 0 for i in range(18)}
    ratings[str(role)] = 100
    # Closely adjacent historical specialist roles count as secondary cover.
    secondary = {2: (4,), 3: (4,), 7: (6, 8), 17: ()}.get(role, ())
    for item in secondary:
        ratings[str(item)] = 80
    return ratings


def _new_player(spec: dict[str, Any], comparable: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(comparable)
    row.update({
        "source_id": int(spec["source_id"]),
        "team_id": VVV_TEAM_ID,
        "display_name": spec["display_name"],
        "first_name": spec["first_name"],
        "surname1": spec["surname1"],
        "surname2": None,
        "birth_date": spec["birth_date"],
        "birth_country_id": 3,
        "birth_city_id": 0,
        "international_country_id": None,
        "naturalized_country_id": None,
        "primary_role": int(spec["primary_role"]),
        "broad_position": spec["broad_position"],
        "overall": int(spec["overall"]),
        "category": int(spec["overall"]),
        "attributes": _scaled_attributes(comparable, int(spec["overall"])),
        "role_ratings": _role_ratings(int(spec["primary_role"])),
        "preferred_foot": int(spec["preferred_foot"]),
        "shirt_number": None,
        "height_cm": None,
        "weight_kg": None,
        "retired": False,
        "external_origin": "verified_vvv_1993_94_roster_v113",
        "creation_batch": "roster_coverage_v113_vvv",
        "identity_source": "Historie VVV-Venlo · season 1993-1994",
        "identity_source_url": VVV_SEASON_SOURCE,
        "historical_data_source": "Historie VVV-Venlo · season 1993-1994",
        "historical_profile_source_url": spec["source_profile_url"],
        "historical_position_1993_94": spec["historical_position_1993_94"],
        "historical_position_source_url": "https://www.transfermarkt.com/vvvtm/kader/verein/1426/saison_id/1993",
        "historical_club_1994": "VVV Venlo",
        "historical_1993_94_appearances_total": int(spec["appearances_total"]),
        "historical_1993_94_goals_total": int(spec["goals_total"]),
        "attribute_source": "fixed_same_era_role_level_comparable_v113",
        "attribute_comparable_source_id": int(spec["comparable_source_id"]),
        "attribute_comparable_source_ids": [int(spec["comparable_source_id"])],
        "attribute_method_note": "Fixed one-time estimate from same-era role/league-level comparable; not a runtime formula.",
        "profile_review_required": False,
        "source_confidence": "high_identity_roster_medium_attributes",
    })
    # Do not pretend the comparable's biographical/contract information belongs
    # to the new player.
    for key in (
        "bdfutbol_id", "bdfutbol_url", "source_profile_url", "historical_full_name",
        "identity_merge_history", "merged_into_source_id", "historical_exclusion_reason",
        "snapshot_inactive_reason", "contract_start_year", "contract_end_year",
        "previous_team_id", "previous_team_years", "loan", "buyback_option", "release_clause",
    ):
        row.pop(key, None)
    row["contract_start_year"] = None
    row["contract_end_year"] = None
    row["previous_team_id"] = 0
    row["previous_team_years"] = 0
    row["loan"] = False
    row["buyback_option"] = 0
    row["release_clause"] = 0
    return row


def apply() -> dict[str, Any]:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    players: list[dict[str, Any]] = snapshot["players"]
    by_id = {int(p["source_id"]): p for p in players}
    # Reconstruct the pre-pass active count on reruns: rows created by this
    # tool are excluded and historical rows this pass intentionally inactivated
    # are counted back in.  This keeps the report meaningful and idempotent.
    before_vvv = sum(
        1 for p in players
        if int(p.get("team_id") or 0) == VVV_TEAM_ID
        and not p.get("retired")
        and p.get("creation_batch") != "roster_coverage_v113_vvv"
    ) + sum(
        1 for source_id in VVV_INACTIVE_ROWS
        if source_id in by_id and int(by_id[source_id].get("team_id") or 0) == VVV_TEAM_ID
    )

    inactive = []
    for source_id, meta in VVV_INACTIVE_ROWS.items():
        player = by_id.get(source_id)
        if not player:
            continue
        player["retired"] = True  # technical inactive flag used by runtime roster/market filters
        player["snapshot_inactive_reason"] = meta["reason"]
        player["snapshot_inactive_source_url"] = meta["source"]
        player["snapshot_inactive_semantics"] = "historical_row_retained_but_not_active_1993_94_squad"
        inactive.append({"source_id": source_id, "display_name": player.get("display_name")})

    additions = []
    for spec in VVV_ADDITIONS:
        source_id = int(spec["source_id"])
        comparable = by_id[int(spec["comparable_source_id"])]
        if source_id in by_id:
            # Re-running the tool repairs the row rather than duplicating it.
            existing = by_id[source_id]
            if existing.get("creation_batch") != "roster_coverage_v113_vvv":
                raise RuntimeError(f"Refusing to overwrite unrelated source_id {source_id}")
            rebuilt = _new_player(spec, comparable)
            existing.clear(); existing.update(rebuilt)
            row = existing
        else:
            row = _new_player(spec, comparable)
            players.append(row)
            by_id[source_id] = row
        additions.append({
            "source_id": source_id,
            "display_name": row["display_name"],
            "overall": row["overall"],
            "primary_role": row["primary_role"],
            "appearances_total": row["historical_1993_94_appearances_total"],
        })

    after_vvv = sum(1 for p in players if int(p.get("team_id") or 0) == VVV_TEAM_ID and not p.get("retired"))
    snapshot.setdefault("database_hygiene", {}).setdefault("v1.1.3", {})["vvv_1993_94_roster_coverage"] = {
        "active_before": before_vvv,
        "active_after": after_vvv,
        "inactive_historical_rows": [row["source_id"] for row in inactive],
        "source_backed_additions": [int(spec["source_id"]) for spec in VVV_ADDITIONS],
        "source": VVV_SEASON_SOURCE,
    }
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "checkpoint": "1.1.3-data",
        "status": "pass",
        "team_id": VVV_TEAM_ID,
        "team": "VVV Venlo",
        "active_before": before_vvv,
        "active_after": after_vvv,
        "inactive_historical_rows": inactive,
        "additions": additions,
        "expected_source_backed_addition_ids": [int(spec["source_id"]) for spec in VVV_ADDITIONS],
        "season_source": VVV_SEASON_SOURCE,
        "policy": "Real source-backed players only; fixed conservative attributes; no synthetic filler.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
