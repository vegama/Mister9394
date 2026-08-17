from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_all_four_added_leagues_use_source_exhaustive_rosters_with_18_only_as_floor():
    audit = load("bel_tur_rus_gre_full_roster_depth_audit.json")
    assert audit["status"] == "expanded_source_rosters"
    assert "18 is a minimum safety floor" in audit["policy"]
    assert audit["totals"] == {"Belgium": 413, "Turkey": 414, "Russia": 492, "Greece": 496}
    assert audit["minimums"] == {"Belgium": 19, "Turkey": 23, "Russia": 22, "Greece": 22}
    assert all(v >= 18 for country in audit["counts"].values() for v in country.values())
    assert max(audit["counts"]["Turkey"].values()) == 30
    assert max(audit["counts"]["Russia"].values()) == 33
    assert max(audit["counts"]["Greece"].values()) == 32


def test_expanded_stagings_have_unique_resolved_identities_and_are_reproducible():
    expected = {
        "turkey_1993_94_roster_staging.json": (419, 419),
        # Russia now preserves 492 historical roster rows while proven cross-club duplicates
        # resolve to 481 identities. A spell is not a second person.
        "russia_1993_roster_staging.json": (492, 481),
        "greece_1993_94_roster_staging.json": (496, 496),
    }
    for name, (row_count, identity_count) in expected.items():
        stage = load(name)
        rows = [p for c in stage["clubs"] for p in c["players"]]
        ids = [int(p["resolved_source_id"]) for p in rows]
        assert len(rows) == row_count
        assert len(set(ids)) == identity_count
        assert min(len(c["players"]) for c in stage["clubs"]) >= 18
        if name.startswith("russia_"):
            # Every repeated resolved identity is backed by the same stable individual-profile ID.
            by_sid = {}
            for row in rows:
                by_sid.setdefault(int(row["resolved_source_id"]), set()).add(str(row.get("bdfutbol_id") or ""))
            assert all(len(bids) == 1 and "" not in bids for sid, bids in by_sid.items() if ids.count(sid) > 1)


def test_turkish_name_normalisation_and_russian_reconciliation_reuse_existing_people():
    snap = {int(p["source_id"]): p for p in load("historical_snapshot.json")["players"]}
    tur = load("turkey_1993_94_roster_staging.json")
    rus = load("russia_1993_roster_staging.json")
    trows = {p["bdfutbol_name"]: p for c in tur["clubs"] for p in c["players"] if p["bdfutbol_name"] in {"Mandıralı", "Çalımbay"}}
    assert int(trows["Mandıralı"]["resolved_source_id"]) == 9495349
    assert int(trows["Çalımbay"]["resolved_source_id"]) == 9495338
    rakh = next(p for c in rus["clubs"] if c["name"] == "Lokomotiv Moskva" for p in c["players"] if p["bdfutbol_name"] == "Rachimov")
    assert int(rakh["resolved_source_id"]) == 503
    for merged in (9496361, 9496363, 9496379, 9496389, 9496395, 9496426, 9496484, 9497392):
        assert merged not in snap


def test_profiles_use_1993_valid_country_context_and_keep_birth_vs_internationality_distinct():
    p = {int(x["source_id"]): x for x in load("historical_snapshot.json")["players"]}
    assert (int(p[9496380]["birth_country_id"]), int(p[9496380]["international_country_id"])) == (104, 104)
    assert (int(p[9496385]["birth_country_id"]), int(p[9496385]["international_country_id"])) == (104, 104)
    assert int(p[9496390]["international_country_id"]) == 78
    assert int(p[9496629]["international_country_id"]) == 132
    assert (int(p[503]["birth_country_id"]), int(p[503]["international_country_id"])) == (202, 40)
    # Soviet birthplace is historical state + successor territory context, never retro-backfilled
    # into birth_country_id. Represented selection remains an independent fact.
    assert p[9494086].get("birth_country_id") is None
    assert p[9494086]["historical_birth_state"] == "USSR"
    assert int(p[9494086]["birth_territory_country_id"]) == 104
    assert int(p[9494086]["international_country_id"]) == 40
    assert p[9496942]["birth_date"] == "1969-10-29T00:00:00"
    assert (int(p[9496942]["birth_country_id"]), int(p[9496942]["international_country_id"])) == (4, 47)
    assert int(p[9496627]["primary_role"]) == 17
    assert p[9496627]["role_ratings"]["17"] == 100
    assert p[9496627]["role_ratings"]["11"] == 45


def test_country_catalog_uses_1993_map_without_creating_modern_only_states():
    catalog = {int(c["source_id"]): c for c in load("historical_source_catalog.json")["countries"]}
    assert catalog[104]["valid_as_state_1993"] is True
    assert catalog[132]["valid_as_state_1993"] is True
    assert catalog[78]["valid_as_state_1993"] is True
    assert catalog[202]["valid_as_state_1993"] is True
    assert catalog[75]["historical_name_1993"] == "República Federal de Yugoslavia"
    assert catalog[88]["historical_name_1993"] == "Zaire"
    assert catalog[76]["valid_as_state_1993"] is False
    assert catalog[129]["valid_as_state_1993"] is False
    norm = load("country_normalization_1993_audit.json")
    assert norm["created_country_ids"] == []
    assert set(norm["reused_existing_1993_country_ids"]) == {4, 63, 78, 104, 132, 202}


def test_photo_registry_queue_are_still_exactly_synchronised_after_roster_expansion():
    registry = load("created_players_registry.json")["players"]
    queue = load("bdfutbol_photo_queue.json")["players"]
    reg_ids = [int(r["source_id"]) for r in registry]
    queue_ids = [int(r["source_id"]) for r in queue]
    assert len(reg_ids) == len(set(reg_ids)) >= 2107
    assert len(queue_ids) == len(set(queue_ids)) >= 2107
    assert set(reg_ids) == set(queue_ids)


def test_greek_numeric_foreign_limit_remains_uninvented_while_cyprus_equivalence_survives():
    snapshot = load("historical_snapshot.json")
    league = next(x for x in snapshot["leagues"] if int(x.get("source_id") or 0) == 930047)
    evidence = load("greece_1993_94_foreign_rule_evidence.json")
    assert league["max_foreigners_starting"] is None
    assert league["max_foreigners_squad"] is None
    assert evidence["decision"] == "do_not_encode_numeric_limit_yet"
    assert league["source_rule_hints"]["foreign_domestic_equivalent_country_ids"] == [25]
