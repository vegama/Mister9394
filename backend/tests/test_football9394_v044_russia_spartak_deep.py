from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SPARTAK_ID = 617
RUSSIA_LEAGUE_ID = 930015
PRE_V044_RUSSIA_SHA = "f73e73c7dee70fd00d82f9679d189677161a662bc72b71a5a723584fb5715cfa"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def players_by_id():
    return {int(p["source_id"]): p for p in load("historical_snapshot.json")["players"]}


def test_v044_spartak_is_first_intentional_russian_deepening_and_other_clubs_are_frozen():
    audit = load("historical_profiles_metadata_audit_v044.json")
    assert audit["status"] == "pass"
    assert audit["target_club"] == "Spartak Moskva"
    assert audit["profiles_curated"] == 33
    assert audit["profiles"]["bdfutbol_profiles_resolved"] == 33
    assert audit["profiles"]["historical_state_births"] == {
        "USSR": 32,
        "German Democratic Republic": 1,
    }

    integrity = audit["russia_integrity"]
    assert integrity["previous_checkpoint_sha256"] == PRE_V044_RUSSIA_SHA
    assert integrity["before_sha256"] == PRE_V044_RUSSIA_SHA
    assert integrity["after_sha256"] != PRE_V044_RUSSIA_SHA
    assert integrity["changed_intentionally"] is True
    assert integrity["non_target_clubs_unchanged"] is True
    assert integrity["non_target_clubs_before_sha256"] == integrity["non_target_clubs_after_sha256"]

    stage = load("russia_1993_roster_staging.json")
    spartak = next(c for c in stage["clubs"] if c["name"] == "Spartak Moskva")
    assert len(spartak["players"]) == 33
    assert all(p.get("bdfutbol_id") for p in spartak["players"])
    assert all(p.get("resolved_birth_date") for p in spartak["players"])
    assert all(p.get("resolved_birth_state") in {"USSR", "German Democratic Republic"} for p in spartak["players"])
    assert all(p.get("resolved_birth_country_id") is None for p in spartak["players"])


def test_v044_birth_state_territory_citizenship_selection_and_transliteration_are_distinct_fields():
    p = players_by_id()

    stauce = p[9496613]
    assert stauce.get("birth_country_id") is None
    assert stauce["historical_birth_state"] == "USSR"
    assert stauce["birth_territory_country_id"] == 52
    assert stauce["international_country_id"] == 52
    assert stauce["represented_selection_country_ids"] == [52]
    assert stauce["represented_selection_country_ids_1993"] == [52]

    onopko = p[9494088]
    assert onopko.get("birth_country_id") is None
    assert onopko["historical_birth_state"] == "USSR"
    assert onopko["birth_territory_country_id"] == 85
    assert onopko["profile_nationality_country_ids"] == [40, 85]
    assert onopko["international_country_id"] == 40

    karpin = p[9494084]
    assert karpin["historical_birth_state"] == "USSR"
    assert karpin["birth_territory_country_id"] == 39
    assert karpin["profile_nationality_country_ids"] == [40, 39]
    assert karpin["international_country_id"] == 40

    pyatnitsky = p[9494083]
    assert pyatnitsky["birth_territory_country_id"] == 209
    assert pyatnitsky["profile_nationality_country_ids"] == [40, 209]
    assert pyatnitsky["represented_selection_country_ids"] == [209, 40]
    assert pyatnitsky["represented_selection_country_ids_1993"] == [40]

    tsymbalar = p[9494087]
    assert tsymbalar["birth_territory_country_id"] == 85
    assert tsymbalar["represented_selection_country_ids"] == [85, 40]
    assert tsymbalar["represented_selection_country_ids_1993"] == []

    kechinov = p[9497357]
    assert kechinov["birth_territory_country_id"] == 209
    assert kechinov["represented_selection_country_ids"] == [209, 40]
    assert kechinov["represented_selection_country_ids_1993"] == []

    pohodin = p[9497354]
    assert pohodin["display_name"] == "Serhiy Anatoliyovych Pohodin"
    assert pohodin["birth_territory_country_id"] == 85
    assert pohodin["represented_selection_country_ids"] == [85]
    assert pohodin["name_transliterations"]["bdfutbol_squad"] == "Pogodin"
    assert pohodin["name_transliterations"]["bdfutbol_profile"] == "Serhiy Anatoliyovych Pohodin"

    bondar = p[9497353]
    assert bondar.get("birth_country_id") is None
    assert bondar["historical_birth_state"] == "German Democratic Republic"
    assert bondar["birth_territory_country_id"] == 4

    # No 1993 citizenship is manufactured from birthplace, a later profile nationality,
    # a gameplay nationality, or the selection represented.
    spartak = [x for x in p.values() if int(x.get("team_id") or 0) == SPARTAK_ID]
    assert len(spartak) == 33
    assert all(x["citizenship_country_ids_1993"] == [] for x in spartak)
    assert all(x["citizenship_1993_resolution"] == "unresolved_not_inferred_from_birth_or_later_profile_v044" for x in spartak)


def test_v044_corrects_source_conflict_and_bad_position_inferences_without_overclaiming_exact_roles():
    p = players_by_id()
    assert p[9495357]["birth_date"] == "1972-08-21T00:00:00"  # Ramiz Mamedov
    conflicts = load("russia_source_conflicts_v044.json")
    assert conflicts["conflicts"] == [{
        "source_id": 9495357,
        "player": "Ramiz Mehman oğlu Mamedov",
        "field": "birth_date",
        "prior": "1972-05-21",
        "resolved": "1972-08-21",
        "decision": "individual profile + independent corroboration wins",
        "source_urls": [
            "https://www.bdfutbol.com/en/j/j705104.html",
            "https://www.transfermarkt.com/ramiz-mamedov/profil/spieler/67117",
        ],
    }]

    expected_roles = {
        9497353: 3,   # Bondar: defender, not forward
        9497357: 7,   # Kechinov: midfielder, not centre-forward
        9497359: 3,   # Gradilenko: defender, not forward
        9497360: 7,   # Baksheev: broad midfielder, not inferred left winger
        9497362: 17,  # Krestov: forward, not left-back
        9497363: 3,   # Rekuts: broad defender, not inferred defensive midfielder
    }
    for sid, role in expected_roles.items():
        assert p[sid]["primary_role"] == role

    # BDFutbol leaves Sergeev's position blank; retain the staged centre-back only as
    # a reviewed inference, never relabel it as a source-exact BDF position.
    assert p[9497361]["primary_role"] == 3
    assert p[9497361]["profile_position_precision"] == "profile_position_blank"
    assert p[9497361]["profile_review_required"] is True


def test_v044_registry_photo_queue_source_drift_and_next_front_are_deterministic():
    audit = load("historical_profiles_metadata_audit_v044.json")
    reg = load("created_players_registry.json")["players"]
    queue = load("bdfutbol_photo_queue.json")["players"]
    rb = {int(x["source_id"]): x for x in reg}
    qb = {int(x["source_id"]): x for x in queue}
    assert len(rb) == len(reg) and len(qb) == len(queue)
    assert set(rb) == set(qb)

    target_ids = {int(x["source_id"]) for x in audit["profiles"]["changes"]}
    assert len(target_ids) == 33
    canonical_preexisting = {2705, 515, 517}  # Cherchesov, Popov, Radchenko
    assert audit["identity_registry"]["created_profiles_updated"] == 30
    assert set(audit["identity_registry"]["canonical_preexisting_enriched_not_registered"]) == canonical_preexisting
    assert audit["identity_registry"]["registry_photo_queue_synchronised"] is True
    assert canonical_preexisting.isdisjoint(rb)
    assert canonical_preexisting.isdisjoint(qb)
    created_target_ids = target_ids - canonical_preexisting
    assert len(created_target_ids) == 30
    for sid in created_target_ids:
        assert rb[sid].get("bdfutbol_id") and rb[sid].get("bdfutbol_url")
        assert qb[sid].get("bdfutbol_id") and qb[sid].get("bdfutbol_url")
        assert qb[sid]["photo_status"] in {"ready_for_download", "bundled_normalized_bdfutbol"}

    drift = audit["source_drift"]
    assert drift["pinned_staging_rows"] == 33
    assert drift["current_page_additional_names"] == ["Shmykov", "Masalitin", "Ternavskiy", "Alenichev"]
    assert drift["decision"] == "do_not_auto_add_in_v044"

    deep_queue = load("russia_deepening_queue_v044.json")
    assert deep_queue["completed_clubs"] == ["Spartak Moskva"]
    assert deep_queue["queue"][0] == "Rotor Volgograd"
    assert audit["next_front"][0] == "Rotor Volgograd"


def test_v044_global_1993_context_freezes_historical_birth_and_transliteration_policy():
    ctx = load("country_context_1993.json")
    birth_policy = ctx["historical_birth_state_policy"]
    assert "birth_country_id is not backfilled to the successor state" in birth_policy["ussr"]
    assert "German Democratic Republic" in birth_policy["other_historical_states"]
    assert "must never auto-assign 1993 citizenship" in birth_policy["no_default"]
    translit = ctx["transliteration_policy"]
    assert "Keep source spellings/romanizations as aliases" in translit["rule"]
    assert "Never merge identities on transliteration similarity alone" in translit["identity_gate"]
