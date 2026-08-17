from __future__ import annotations

import json
from pathlib import Path

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.app.football9394.national_teams import national_team_catalog
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.tools.export_bdfutbol_photo_queue import build_queue


def test_popov_style_legacy_dob_error_reuses_existing_player_when_club_and_identity_agree():
    existing = {
        "source_id": 515,
        "display_name": "Popov",
        "first_name": "Dmitry Lvovich",
        "surname1": "Popov",
        "birth_date": "1969-02-27T00:00:00",
        "birth_country_id": 40,
        "international_country_id": None,
        "team_id": 17,
    }
    result = reconcile_player_identity(
        [existing],
        target_display="Dmitri Popov",
        target_given="Dmitri",
        target_family="Popov",
        target_birth_date="1967-02-27",
        target_country_id=40,
        expected_team_id=17,
    )
    assert result.player is existing
    assert result.resolution == "global_team_name"


def test_missing_international_country_does_not_hide_existing_irish_player():
    existing = {
        "source_id": 1912,
        "display_name": "Paul McGrath",
        "first_name": "Paul",
        "surname1": "McGrath",
        "birth_date": "1959-12-04T00:00:00",
        "birth_country_id": 2,  # birthplace can differ from international team
        "international_country_id": None,
        "team_id": 249,
    }
    result = reconcile_player_identity(
        [existing],
        target_display="Paul McGrath",
        target_given="Paul",
        target_family="McGrath",
        target_birth_date="1959-12-04",
        target_country_id=46,
        expected_team_id=249,
    )
    assert result.player is existing
    assert result.confidence == "high"


def test_ambiguous_global_identity_blocks_automatic_creation():
    rows = [
        {"source_id": 1, "display_name": "Juan Perez", "first_name": "Juan", "surname1": "Perez", "birth_date": "1970-01-01", "team_id": 10, "birth_country_id": 11},
        {"source_id": 2, "display_name": "Juan Perez", "first_name": "Juan", "surname1": "Perez", "birth_date": "1970-01-01", "team_id": 10, "birth_country_id": 11},
    ]
    result = reconcile_player_identity(
        rows,
        target_display="Juan Perez",
        target_given="Juan",
        target_family="Perez",
        target_birth_date="1970-01-01",
        target_country_id=11,
        expected_team_id=10,
    )
    assert result.player is None
    assert result.resolution == "ambiguous_existing_candidates"


def test_new_near_functional_batch_raises_catalog_to_44():
    universe = default_runtime_snapshot()
    catalog = {row.country_id: row for row in national_team_catalog(universe)}
    assert len(catalog) >= 49
    for country_id in (75, 68, 44, 93, 36):
        assert country_id in catalog
        assert catalog[country_id].eligible_players >= 22


def test_creation_registry_and_bdfutbol_queue_contain_only_true_new_players():
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root / "data/football9394/created_players_registry.json").read_text(encoding="utf-8"))
    rows = registry.get("players", registry)
    assert len(rows) >= 367
    allowed={
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
    }
    assert all(row["duplicate_check"] in allowed for row in rows)
    original_new=[row for row in rows if row["duplicate_check"]=="created_after_global_existing_player_comparison"]
    assert all(row.get("matched_existing_id") is None for row in original_new)
    assert not any(int(row["source_id"]) == 515 for row in rows)

    queue = build_queue(root / "data/football9394/created_players_registry.json")
    assert len(queue) == len(rows)
    assert all(row.get("photo_filename") for row in queue)
    assert all(row.get("bdfutbol_search_name") for row in queue)
    assert all(row.get("photo_status") in {"pending","pending_identity_profile","ready_for_download","bundled_normalized_bdfutbol"} for row in queue)
