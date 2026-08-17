from __future__ import annotations

import json
from pathlib import Path

from backend.app.football9394.foreign_rules import ForeignPlayerRule9394, foreign_count, is_foreign_player

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _players_by_id() -> dict[int, dict]:
    return {int(p["source_id"]): p for p in _load("historical_snapshot.json")["players"]}


def test_greek_foreign_limit_is_audited_but_not_guessed_into_runtime():
    snapshot = _load("historical_snapshot.json")
    league = next(row for row in snapshot["leagues"] if int(row.get("source_id") or 0) == 930047)
    evidence = _load("greece_1993_94_foreign_rule_evidence.json")

    assert evidence["candidate_limit"] == 3
    assert evidence["primary_domestic_numerical_clause_recovered"] is False
    assert evidence["decision"] == "do_not_encode_numeric_limit_yet"
    assert evidence["runtime"] == {"max_foreigners_starting": None, "max_foreigners_squad": None}
    assert league["max_foreigners_starting"] is None
    assert league["max_foreigners_squad"] is None
    assert league["source_rule_hints"]["foreign_rule_evidence_file"] == "greece_1993_94_foreign_rule_evidence.json"

    equivalence = next(s for s in evidence["sources"] if s["kind"] == "domestic_equivalence_evidence")
    assert "Cypriots did not count as foreigners" in equivalence["finding"]
    assert evidence["domestic_equivalence"]["runtime_encoded"] is True
    assert evidence["domestic_equivalence"]["equivalent_country_ids"] == [25]
    assert league["source_rule_hints"]["foreign_domestic_equivalent_country_ids"] == [25]


def test_greek_domestic_equivalence_support_treats_cypriots_as_non_foreign_only_domestically():
    cypriot = {"international_country_id": 25}
    german = {"international_country_id": 4}
    assert is_foreign_player(cypriot, home_country_id=47, domestic_equivalent_country_ids={25}) is False
    assert is_foreign_player(german, home_country_id=47, domestic_equivalent_country_ids={25}) is True
    assert is_foreign_player(
        cypriot, home_country_id=47, continental=True, domestic_equivalent_country_ids={25}
    ) is True

    rule = ForeignPlayerRule9394(
        "league", 930047, "Alpha Ethniki", 47, 3, None,
        domestic_equivalent_country_ids=frozenset({25}),
    )
    assert foreign_count([cypriot, german], rule) == 1


def test_turkey_individual_profiles_fix_roles_and_reconcile_roger_ljung():
    players = _players_by_id()
    assert 9496356 not in players

    roger = players[9494093]
    assert roger["display_name"] == "Roger Ljung"
    assert int(roger["team_id"]) == 645
    assert roger["bdfutbol_id"] == "80039"
    assert int(roger["primary_role"]) == 3

    bol = players[9496355]
    assert (bol["display_name"], bol["birth_date"], int(bol["primary_role"]), bol["broad_position"]) == (
        "Nezih Ali Boloğlu", "1964-08-04T00:00:00", 0, "POR"
    )
    assert bol["attribute_source"] in {"fixed_source_comparable_role_correction_0.29", "fixed_source_comparable_profile_coherence_0.30", "fixed_source_comparable_role_correction_0.31"}

    turkyilmaz = players[9496358]
    assert (int(turkyilmaz["birth_country_id"]), int(turkyilmaz["international_country_id"])) == (80, 80)
    assert int(turkyilmaz["primary_role"]) == 17
    assert turkyilmaz["broad_position"] == "DEL"

    bulut = players[9496359]
    assert (int(bulut["primary_role"]), bulut["broad_position"]) == (0, "POR")
    assert int(players[9496360]["primary_role"]) == 17

    stage = _load("turkey_1993_94_roster_staging.json")
    ljung_rows = [r for club in stage["clubs"] for r in club["players"] if r.get("bdfutbol_name") == "Ljung"]
    assert len(ljung_rows) == 1
    assert int(ljung_rows[0]["resolved_source_id"]) == 9494093
    assert ljung_rows[0]["identity_resolution"] in {"reused_verified_world_cup_identity_v0.29", "reused_staged_identity"}


def test_russia_individual_profiles_fix_identity_nationality_and_roles():
    players = _players_by_id()
    stauce = players[9496613]
    assert stauce["display_name"] == "Gintaras Staučė"
    assert (int(stauce["birth_country_id"]), int(stauce["primary_role"])) == (52, 0)

    onopko = players[9494088]
    assert (int(onopko["birth_country_id"]), int(onopko["international_country_id"])) == (85, 40)
    assert (onopko["height_cm"], onopko["weight_kg"]) == (188, 77)

    cherenkov = players[9496616]
    assert (int(cherenkov["primary_role"]), cherenkov["broad_position"]) == (8, "MED")
    assert cherenkov["attribute_source"] in {"fixed_source_comparable_role_correction_0.29", "fixed_source_comparable_profile_coherence_0.30", "fixed_source_comparable_role_correction_0.31"}

    pomazun = players[9496617]
    assert int(pomazun["birth_country_id"]) == 85
    assert int(pomazun["international_country_id"]) == 40
    assert int(pomazun["primary_role"]) == 0

    ananko = players[9496618]
    assert (int(ananko["primary_role"]), ananko["broad_position"]) == (3, "DEF")


def test_greece_individual_profiles_correct_tsartas_and_warzycha_without_flattening_specialists():
    players = _players_by_id()
    tsartas = players[9496930]
    assert tsartas["display_name"] == "Vassilis Tsartas"
    assert tsartas["birth_date"] == "1972-11-12T00:00:00"
    assert tsartas["bdfutbol_id"] == "2572"

    warzycha = players[9496943]
    assert warzycha["display_name"] == "Krzysztof Warzycha"
    assert (int(warzycha["primary_role"]), warzycha["broad_position"]) == (17, "DEL")

    # Existing specialist knowledge wins over a coarser profile category.
    mitropoulos = players[9494166]
    assert (int(mitropoulos["primary_role"]), mitropoulos["broad_position"]) == (8, "MED")
    assert int(players[9494163]["primary_role"]) == 8
    assert int(players[9494177]["primary_role"]) == 17


def test_profile_audit_and_photo_queue_are_traceable_and_synchronised():
    audit = _load("turkey_russia_greece_individual_profile_audit.json")
    registry = _load("created_players_registry.json")["players"]
    queue = _load("bdfutbol_photo_queue.json")["players"]
    reg = {int(row["source_id"]): row for row in registry}
    queued = {int(row["source_id"]): row for row in queue}

    assert audit["profiles_curated"] == 20
    assert audit["portrait_profiles_ready_for_download"] == 19
    assert len(audit["role_corrections"]) == 7
    assert len(audit["duplicate_reconciliations"]) == 1
    assert set(reg) == set(queued)
    assert 9496356 not in reg

    for sid in (9494093, 9496355, 9496943):
        assert reg[sid]["photo_status"] in {"ready_for_download", "bundled_normalized_bdfutbol"}
        assert queued[sid]["photo_status"] == reg[sid]["photo_status"]
        assert reg[sid]["bdfutbol_id"]

    assert reg[9496930]["bdfutbol_id"] == "2572"
    assert reg[9496930]["photo_status"] == "ready_for_download"
    assert queued[9496930]["photo_status"] == "ready_for_download"


def test_snapshot_and_registry_have_unique_source_ids_after_profile_pass():
    snapshot_ids = [int(p["source_id"]) for p in _load("historical_snapshot.json")["players"]]
    registry_ids = [int(p["source_id"]) for p in _load("created_players_registry.json")["players"]]
    assert len(snapshot_ids) == len(set(snapshot_ids)) == 12499
    assert len(registry_ids) == len(set(registry_ids)) == 2107
