from __future__ import annotations

"""Curated v0.29 individual-profile pass for Turkey, Russia and Greece.

This tool only applies source-backed identity/biographical/position corrections and
materialises any required attribute reshaping from existing 1993-94 source-backed
players. It deliberately does not guess missing biographies, photos or Greek
foreign-player limits.
"""

from collections import Counter
from pathlib import Path
from typing import Any
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from tools.review_created_player_profiles import ATTRS, materialise_attributes

DATA = ROOT / "data" / "football9394"
SNAP = DATA / "historical_snapshot.json"
REGISTRY = DATA / "created_players_registry.json"
PROFILE_AUDIT = DATA / "turkey_russia_greece_individual_profile_audit.json"
FOREIGN_EVIDENCE = DATA / "greece_1993_94_foreign_rule_evidence.json"

STAGES = {
    "Turkey": DATA / "turkey_1993_94_roster_staging.json",
    "Russia": DATA / "russia_1993_roster_staging.json",
    "Greece": DATA / "greece_1993_94_roster_staging.json",
}
AUDITS = {
    "Turkey": DATA / "turkey_1993_94_roster_gate_audit.json",
    "Russia": DATA / "russia_1993_roster_gate_audit.json",
    "Greece": DATA / "greece_1993_94_roster_gate_audit.json",
}

ROLE_TO_BROAD = {
    0: "POR", 1: "DEF", 2: "DEF", 3: "DEF", 4: "DEF", 5: "DEF",
    6: "MED", 7: "MED", 8: "MED", 9: "MED", 10: "MED", 11: "DEL",
    12: "DEL", 13: "MED", 14: "MED", 15: "DEL", 16: "DEL", 17: "DEL",
}
ROLE_TO_LABEL = {
    0: "Goalkeeper", 1: "Right Back", 2: "Left Back", 3: "Centre Back",
    4: "Centre Back", 5: "Libero", 6: "Defensive Midfielder",
    7: "Centre Midfielder", 8: "Attacking Midfielder", 9: "Right Midfielder",
    10: "Right Inside", 11: "Right Attacking Midfielder", 12: "Right Winger",
    13: "Left Midfielder", 14: "Left Inside", 15: "Left Attacking Midfielder",
    16: "Left Winger", 17: "Centre Forward",
}
COUNTRY_NAMES = {
    4: "Alemania", 25: "Chipre", 40: "Rusia", 47: "Grecia", 52: "Lituania",
    70: "Polonia", 79: "Suecia", 80: "Suiza", 84: "Turquía", 85: "Ucrania",
}

# portrait_verified means the cited BDFutbol individual page exposes an image.
PATCHES: dict[int, dict[str, Any]] = {
    # Turkey / Galatasaray
    9496352: dict(country="Turkey", display_name="Reinhard Stumpf", first_name="Reinhard", surname1="Stumpf",
                  birth_date="1961-11-26", birth_country_id=4, international_country_id=4,
                  height_cm=190, weight_kg=85, bdfutbol_id="98735", profile_position="Defender", portrait_verified=True),
    9496353: dict(country="Turkey", display_name="Mert Korkmaz", first_name="Mert", surname1="Korkmaz",
                  birth_date="1971-08-16", birth_country_id=84, international_country_id=84,
                  bdfutbol_id="54548", profile_position="Defender", portrait_verified=True),
    9496354: dict(country="Turkey", display_name="Falko Götz", first_name="Falko", surname1="Götz",
                  birth_date="1962-03-26", birth_country_id=4, international_country_id=4,
                  height_cm=181, weight_kg=77, bdfutbol_id="90652", profile_position="Midfielder", portrait_verified=True),
    9496355: dict(country="Turkey", display_name="Nezih Ali Boloğlu", first_name="Nezih Ali", surname1="Boloğlu",
                  birth_date="1964-08-04", birth_country_id=84, international_country_id=84,
                  bdfutbol_id="702614", profile_position="Goalkeeper", role=0, portrait_verified=True),
    9496357: dict(country="Turkey", display_name="Ali Erdal Keser", first_name="Ali Erdal", surname1="Keser",
                  birth_date="1961-06-20", birth_country_id=84, international_country_id=84,
                  height_cm=174, weight_kg=67, bdfutbol_id="91805", profile_position="Midfielder", portrait_verified=True),
    9496358: dict(country="Turkey", display_name="Kubilay Türkyılmaz", first_name="Kubilay", surname1="Türkyılmaz",
                  birth_date="1967-03-04", birth_country_id=80, international_country_id=80,
                  secondary_nationality_country_id=84, height_cm=180, weight_kg=81,
                  bdfutbol_id="95868", profile_position="Forward", role=17, portrait_verified=True),
    9496359: dict(country="Turkey", display_name="Ahmet Bulut", first_name="Ahmet", surname1="Bulut",
                  birth_date="1969-07-04", birth_country_id=84, international_country_id=84,
                  bdfutbol_id="702755", profile_position="Goalkeeper", role=0, portrait_verified=True),
    9496360: dict(country="Turkey", display_name="Mustafa Kocabey", first_name="Mustafa", surname1="Kocabey",
                  birth_date="1974-10-06", birth_country_id=84, international_country_id=84,
                  bdfutbol_id="702754", profile_position="Forward", role=17, portrait_verified=True),
    # Russia / Spartak
    9496613: dict(country="Russia", display_name="Gintaras Staučė", first_name="Gintaras", surname1="Staučė",
                  birth_date="1969-12-24", birth_country_id=52, international_country_id=52,
                  height_cm=188, weight_kg=80, bdfutbol_id="98206", profile_position="Goalkeeper", role=0, portrait_verified=True),
    9494088: dict(country="Russia", display_name="Viktor Onopko", first_name="Viktor", surname1="Onopko",
                  birth_date="1969-10-14", birth_country_id=85, international_country_id=40,
                  height_cm=188, weight_kg=77, bdfutbol_id="2609", profile_position="Central", portrait_verified=True),
    9496615: dict(country="Russia", display_name="Nikolai Pisarev", first_name="Nikolai", surname1="Pisarev",
                  birth_date="1968-11-23", birth_country_id=40, international_country_id=40,
                  height_cm=180, weight_kg=79, bdfutbol_id="2091", profile_position="Forward", role=17, portrait_verified=True),
    9496616: dict(country="Russia", display_name="Fyodor Cherenkov", first_name="Fyodor", surname1="Cherenkov",
                  birth_date="1959-07-25", birth_country_id=40, international_country_id=40,
                  height_cm=178, bdfutbol_id="41922", profile_position="Midfielder", role=7, portrait_verified=True),
    9496617: dict(country="Russia", display_name="Aleksandr Pomazun", first_name="Aleksandr", surname1="Pomazun",
                  birth_date="1971-10-11", birth_country_id=85,
                  height_cm=191, weight_kg=90, bdfutbol_id="590782", profile_position="Goalkeeper", role=0, portrait_verified=True),
    9496618: dict(country="Russia", display_name="Dmitri Ananko", first_name="Dmitri", surname1="Ananko",
                  birth_date="1973-09-29", birth_country_id=40, international_country_id=40,
                  height_cm=180, bdfutbol_id="84989", profile_position="Central", role=3, portrait_verified=True),
    # Greece / key players
    9494163: dict(country="Greece", display_name="Dimitris Saravakos", first_name="Dimitris", surname1="Saravakos",
                  birth_date="1961-07-26", birth_country_id=47, international_country_id=47,
                  height_cm=172, bdfutbol_id="58026", profile_position="Midfielder", portrait_verified=True),
    9496930: dict(country="Greece", display_name="Vassilis Tsartas", first_name="Vassilis", surname1="Tsartas",
                  birth_date="1972-11-12", birth_country_id=47, international_country_id=47,
                  height_cm=185, weight_kg=75, bdfutbol_id="2572", profile_position="Midfielder", portrait_verified=False),
    9494166: dict(country="Greece", display_name="Tasos Mitropoulos", first_name="Tasos", surname1="Mitropoulos",
                  birth_date="1957-08-23", birth_country_id=47, international_country_id=47,
                  height_cm=190, bdfutbol_id="42541", profile_position="Forward", portrait_verified=True,
                  role_note="Stored specialist midfield role retained; broad BDFutbol profile conflicts with verified existing historical role."),
    9496943: dict(country="Greece", display_name="Krzysztof Warzycha", first_name="Krzysztof", surname1="Warzycha",
                  birth_date="1964-11-17", birth_country_id=70, international_country_id=70,
                  bdfutbol_id="59705", profile_position="Forward", role=17, portrait_verified=True),
    9494177: dict(country="Greece", display_name="Alexis Alexandris", first_name="Alexis", surname1="Alexandris",
                  birth_date="1968-10-21", birth_country_id=47, international_country_id=47,
                  height_cm=175, bdfutbol_id="708921", profile_position="Forward", role=17, portrait_verified=True),
}

ROGER_DUPLICATE_ID = 9496356
ROGER_EXISTING_ID = 9494093
ROGER_PATCH = dict(country="Turkey", display_name="Roger Ljung", first_name="Roger", surname1="Ljung",
                   birth_date="1966-01-08", birth_country_id=79, international_country_id=79,
                   height_cm=188, bdfutbol_id="80039", profile_position="Midfielder", portrait_verified=True,
                   role_note="World Cup 1994 source records him as DF; retained as centre-back/defender despite BDFutbol's broad Midfielder label.")


def dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def role_ratings(role: int) -> dict[str, int]:
    out = {str(i): 0 for i in range(18)}
    out[str(role)] = 100
    adj = {
        0: {}, 1: {3: 60, 9: 55}, 2: {4: 60, 13: 55}, 3: {4: 75, 5: 60, 6: 45},
        4: {3: 75, 5: 60, 6: 45}, 5: {3: 75, 4: 75, 6: 60}, 6: {7: 75, 3: 50, 4: 50},
        7: {6: 70, 8: 65, 9: 45, 13: 45}, 8: {7: 65, 11: 55, 15: 55, 17: 45},
        9: {12: 75, 7: 55, 8: 50, 1: 45}, 10: {9: 80, 12: 65, 7: 55},
        11: {12: 80, 9: 65, 8: 65, 17: 50}, 12: {9: 75, 11: 65, 17: 50},
        13: {16: 75, 7: 55, 8: 50, 2: 45}, 14: {13: 80, 16: 65, 7: 55},
        15: {16: 80, 13: 65, 8: 65, 17: 50}, 16: {13: 75, 15: 65, 17: 50},
        17: {11: 45, 15: 45, 12: 35, 16: 35, 8: 30},
    }
    for k, v in adj[role].items():
        out[str(k)] = v
    return out


def source_comparables(originals: list[dict[str, Any]], broad: str, overall: int, sid: int) -> tuple[dict[str, Any], dict[str, Any]]:
    pool = [p for p in originals if p.get("broad_position") == broad and p.get("attributes")]
    pool.sort(key=lambda p: (abs(int(p.get("overall") or 0) - overall), int(p.get("source_id") or 0)))
    pool = pool[:32]
    if len(pool) < 2:
        raise RuntimeError(f"No source-backed comparables for {broad}")
    a = pool[(sid * 7) % len(pool)]
    b = pool[(sid * 13 + 5) % len(pool)]
    if a["source_id"] == b["source_id"]:
        b = pool[(pool.index(a) + 1) % len(pool)]
    return a, b


def apply_patch(player: dict[str, Any], patch: dict[str, Any], originals: list[dict[str, Any]]) -> dict[str, Any]:
    sid = int(player["source_id"])
    before_role = int(player.get("primary_role") or 0)
    before_broad = player.get("broad_position")
    for key in ("display_name", "first_name", "surname1", "birth_country_id", "international_country_id", "height_cm", "weight_kg"):
        if key in patch:
            player[key] = patch[key]
    if patch.get("birth_date"):
        player["birth_date"] = patch["birth_date"] + "T00:00:00"
    if patch.get("secondary_nationality_country_id"):
        player["secondary_nationality_country_id"] = int(patch["secondary_nationality_country_id"])
    if not player.get("historical_position_1993_94") and before_role in ROLE_TO_LABEL:
        player["historical_position_1993_94"] = ROLE_TO_LABEL[before_role]
        player["historical_position_source"] = "retained verified broad/specialist role; profile pass v0.29"
    if "role" in patch and int(patch["role"]) != before_role:
        role = int(patch["role"])
        broad = ROLE_TO_BROAD[role]
        player["primary_role"] = role
        player["broad_position"] = broad
        player["historical_position_1993_94"] = ROLE_TO_LABEL[role]
        player["historical_position_source"] = "BDFutbol individual player profile v0.29"
        player["role_ratings"] = role_ratings(role)
        a, b = source_comparables(originals, broad, int(player.get("overall") or 70), sid)
        player["attributes"] = materialise_attributes(int(player.get("overall") or 70), a, b)
        player["attribute_source"] = "fixed_source_comparable_role_correction_0.29"
        player["profile_role_correction_0_29"] = {
            "from_role": before_role, "from_broad_position": before_broad,
            "to_role": role, "to_broad_position": broad,
            "comparables": [int(a["source_id"]), int(b["source_id"])],
            "policy": "fixed source-comparable materialisation; no football 75/25 rule",
        }
    bdf = str(patch["bdfutbol_id"])
    player["bdfutbol_id"] = bdf
    player["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{bdf}.html"
    player["historical_profile_source"] = "BDFutbol individual player profile v0.29"
    player["historical_profile_source_url"] = player["bdfutbol_url"]
    player["source_profile_position"] = patch.get("profile_position")
    if patch.get("role_note"):
        player["source_profile_position_note"] = patch["role_note"]
    correction = player.get("profile_role_correction_0_29") or {}
    recorded_before = int(correction.get("from_role", before_role))
    return {
        "source_id": sid,
        "display_name": player.get("display_name"),
        "country": patch["country"],
        "bdfutbol_id": bdf,
        "bdfutbol_url": player["bdfutbol_url"],
        "profile_position": patch.get("profile_position"),
        "role_before": recorded_before,
        "role_after": int(player.get("primary_role") or 0),
        "portrait_verified": bool(patch.get("portrait_verified")),
    }


def patch_registry(row: dict[str, Any], player: dict[str, Any], patch: dict[str, Any]) -> None:
    for key in ("display_name", "first_name", "surname1", "team_id", "broad_position", "overall", "attribute_source"):
        row[key] = player.get(key)
    row["birth_date"] = str(player.get("birth_date") or "").split("T")[0] or None
    cid = player.get("international_country_id") or player.get("birth_country_id")
    row["country_id"] = cid
    row["country_name"] = COUNTRY_NAMES.get(int(cid)) if cid else None
    row["historical_position_1993_94"] = player.get("historical_position_1993_94")
    row["historical_club_1994"] = "Galatasaray" if int(player["source_id"]) in {9494093, *range(9496352, 9496361)} else row.get("historical_club_1994")
    row["bdfutbol_search_name"] = player.get("display_name")
    row["bdfutbol_id"] = str(patch["bdfutbol_id"])
    row["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{patch['bdfutbol_id']}.html"
    row["individual_profile_source"] = "BDFutbol individual player profile v0.29"
    row["source_profile_position"] = patch.get("profile_position")
    row["photo_status"] = "ready_for_download" if patch.get("portrait_verified") else row.get("photo_status", "pending_identity_profile")
    if int(player["source_id"]) == ROGER_EXISTING_ID:
        row["team_name"] = "Galatasaray"
        # Roger remains a legitimately created World Cup identity, so keep the
        # queue-compatible creation marker and record reconciliation separately.
        row["duplicate_check"] = "created_after_global_existing_player_comparison"
        row.pop("matched_existing_id", None)
        row["reconciled_duplicate_source_id"] = ROGER_DUPLICATE_ID
        row["duplicate_reconciliation_batch"] = "turkey_individual_profiles_0.29"


def patch_stage(stage: dict[str, Any], old_sid: int, new_sid: int, player: dict[str, Any], patch: dict[str, Any]) -> None:
    for club in stage.get("clubs", []):
        for row in club.get("players", []):
            if int(row.get("resolved_source_id") or -1) != old_sid:
                continue
            row["resolved_source_id"] = new_sid
            row["resolved_display_name"] = player["display_name"]
            row["resolved_primary_role"] = int(player["primary_role"])
            row["resolved_exact_position"] = player["historical_position_1993_94"]
            row["position_source"] = "bdfutbol_individual_profile_v0.29" if "role" in patch else row.get("position_source")
            row["individual_profile_source_url"] = player["bdfutbol_url"]
            row["bdfutbol_id"] = str(patch["bdfutbol_id"])
            row["resolved_birth_date"] = player.get("birth_date")
            row["resolved_country_id"] = player.get("international_country_id") or player.get("birth_country_id")
            if old_sid == ROGER_DUPLICATE_ID:
                row["identity_resolution"] = "reused_verified_world_cup_identity_v0.29"
            return


def patch_audit_identity(audit: dict[str, Any], old_sid: int, new_sid: int, player: dict[str, Any], patch: dict[str, Any]) -> None:
    for row in audit.get("identities", []):
        if int(row.get("source_id") or -1) != old_sid:
            continue
        row["source_id"] = new_sid
        row["display_name"] = player["display_name"]
        row["role"] = int(player["primary_role"])
        row["position"] = player["historical_position_1993_94"]
        if "role" in patch:
            row["position_source"] = "bdfutbol_individual_profile_v0.29"
        row["individual_profile_source_url"] = player["bdfutbol_url"]
        return


def greek_foreign_evidence() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "season": "1993-94",
        "league_id": 930047,
        "status": "candidate_3_strongly_corroborated_primary_domestic_numeric_clause_not_recovered",
        "candidate_limit": 3,
        "primary_domestic_numerical_clause_recovered": False,
        "runtime": {"max_foreigners_starting": None, "max_foreigners_squad": None},
        "decision": "do_not_encode_numeric_limit_yet",
        "reason": "The historical value 3 is strongly corroborated, but the exact Greek domestic rule text governing 1993-94 has not been recovered. Cypriot domestic equivalence is source-supported and is modelled separately, so it is not used as a reason to guess the numeric quota.",
        "sources": [
            {
                "kind": "primary_eu_legal_record_uefa_framework",
                "title": "Bosman, Case C-415/93 - EUR-Lex",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:61993CJ0415",
                "finding": "Records UEFA's 1991 3+2 framework, permitting national associations to limit first-division line-ups to three foreign players plus two assimilated players.",
                "scope": "UEFA framework; not proof of Greece's exact domestic 1993-94 clause.",
            },
            {
                "kind": "primary_greek_statute_regulatory_framework",
                "title": "Greek Law 1958/1991, Government Gazette A 122/5-5-1991",
                "url": "https://minsports.gov.gr/wp-content/uploads/2012/11/1958_%CE%A6%CE%95%CE%9A_122%CE%91_5-5-91%CE%A4%CE%BC%CE%AE%CE%BC%CE%B1%CF%84%CE%B1_%CE%91%CE%BC%CE%B5%CE%B9%CE%B2%CE%BF%CE%BC%CE%AD%CE%BD%CF%89%CE%BD_%CE%91%CE%B8%CE%BB%CE%B7%CF%84%CF%8E%CE%BD_-_%CE%91%CE%B8%CE%BB%CE%B7%CF%84%CE%B9%CE%BA%CE%AD%CF%82_%CE%91%CE%BD%CF%8E%CE%BD%CF%85%CE%BC%CE%B5%CF%82_%CE%95%CF%84%CE%B1%CE%B9%CF%81%CE%B5%CE%AF%CE%B5%CF%82_%CE%BA%CE%B1%CE%B9_%CE%AC%CE%BB%CE%BB%CE%B5%CF%82_%CE%B4%CE%B9%CE%B1%CF%84%CE%AC%CE%BE%CE%B5%CE%B9%CF%82.pdf",
                "finding": "Official statutory framework for paid/professional sport and football bodies; it does not provide the recovered numerical foreign-player clause needed for 1993-94.",
                "scope": "Primary Greek legal framework; numerical league rule still missing.",
            },
            {
                "kind": "historical_first_person_corroboration",
                "title": "Nikos Nioplias interview - AthleteStories",
                "url": "https://www.athletestories.gr/nioplias-nikos-me-mia-ball-sta-podia/",
                "finding": "Nioplias recalls that each Greek club had only three foreign players in that era.",
                "scope": "Strong historical corroboration, not a regulatory text.",
            },
            {
                "kind": "historical_rule_change_corroboration",
                "title": "Novasports historical record - third foreign player, 30 November 1988",
                "url": "https://www.novasports.gr/category/novasportsstorieshd/article/1477326/otan-o-tritos-ksenos-mpike-stin-zwi-mas-video/",
                "finding": "Records that on 30 November 1988 participation of a third foreign player was instituted in the Greek championship.",
                "scope": "Established sports-media chronology; underlying signed federation/league decision or FEK not yet recovered.",
            },
            {
                "kind": "domestic_equivalence_evidence",
                "title": "RSSSF - Foreign Players in Greece since 1959/60",
                "url": "https://www.rsssf.org/players/foreign-players-in-grk6080.html",
                "finding": "Cypriots did not count as foreigners; some Albanian players with Greek roots also technically did not count.",
                "scope": "Shows nationality != Greece cannot be used as the complete domestic eligibility rule.",
            },
        ],
        "domestic_equivalence": {
            "runtime_encoded": True,
            "equivalent_country_ids": [25],
            "equivalent_countries": ["Cyprus"],
            "scope": "Domestic Greek competitions only; continental competition nationality remains association-based.",
        },
        "implementation_blockers": [
            "Recover exact Greek federation/league or Government Gazette text that sets the numerical limit applicable in 1993-94.",
        ],
    }


def main() -> None:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    stages = {k: json.loads(p.read_text(encoding="utf-8")) for k, p in STAGES.items()}
    audits = {k: json.loads(p.read_text(encoding="utf-8")) for k, p in AUDITS.items()}
    players = snap["players"]
    byid = {int(p["source_id"]): p for p in players}
    originals = [p for p in players if not p.get("external_origin") and not p.get("creation_batch")]
    regby = {int(r["source_id"]): r for r in registry["players"] if r.get("source_id") is not None}

    # Explicit duplicate reconciliation: the Turkey import created a second Roger Ljung.
    if ROGER_DUPLICATE_ID in byid:
        if ROGER_EXISTING_ID not in byid:
            raise RuntimeError("Verified Roger Ljung World Cup identity is missing")
        players[:] = [p for p in players if int(p["source_id"]) != ROGER_DUPLICATE_ID]
        registry["players"][:] = [r for r in registry["players"] if int(r.get("source_id") or -1) != ROGER_DUPLICATE_ID]
        byid.pop(ROGER_DUPLICATE_ID)
        regby.pop(ROGER_DUPLICATE_ID, None)
        audits["Turkey"]["created_players"] = max(0, int(audits["Turkey"].get("created_players") or 0) - 1)
        audits["Turkey"]["reused_existing_players"] = int(audits["Turkey"].get("reused_existing_players") or 0) + 1

    roger = byid[ROGER_EXISTING_ID]
    roger["team_id"] = 645
    roger["historical_club_1994"] = "Galatasaray"
    roger["club_assignment_source"] = "BDFutbol Galatasaray 1993-94 explicit identity reconciliation v0.29"
    roger_record = apply_patch(roger, ROGER_PATCH, originals)
    patch_registry(regby[ROGER_EXISTING_ID], roger, ROGER_PATCH)
    # Patch both the pre-reconciliation and already-reconciled identity so the
    # tool remains idempotent if a later curated field is refined.
    patch_stage(stages["Turkey"], ROGER_DUPLICATE_ID, ROGER_EXISTING_ID, roger, ROGER_PATCH)
    patch_stage(stages["Turkey"], ROGER_EXISTING_ID, ROGER_EXISTING_ID, roger, ROGER_PATCH)
    patch_audit_identity(audits["Turkey"], ROGER_DUPLICATE_ID, ROGER_EXISTING_ID, roger, ROGER_PATCH)
    patch_audit_identity(audits["Turkey"], ROGER_EXISTING_ID, ROGER_EXISTING_ID, roger, ROGER_PATCH)

    changes = [roger_record | {"duplicate_reconciliation": {"removed_source_id": ROGER_DUPLICATE_ID, "reused_source_id": ROGER_EXISTING_ID}}]
    for sid, patch in PATCHES.items():
        player = byid.get(sid)
        if player is None:
            raise RuntimeError(f"Missing curated profile source_id {sid}")
        record = apply_patch(player, patch, originals)
        changes.append(record)
        if sid in regby:
            patch_registry(regby[sid], player, patch)
        patch_stage(stages[patch["country"]], sid, sid, player, patch)
        patch_audit_identity(audits[patch["country"]], sid, sid, player, patch)

    # Refresh provenance/counts on each league audit after role corrections.
    for country, audit in audits.items():
        identity_roles = Counter(int(r["role"]) for r in audit.get("identities", []) if r.get("role") is not None)
        audit["role_counts"] = {str(k): v for k, v in sorted(identity_roles.items())}
        audit["position_provenance"] = dict(Counter(str(r.get("position_source") or "unknown") for r in audit.get("identities", [])))
        relevant = [c for c in changes if c["country"] == country]
        audit["individual_profile_enrichment_0_29"] = {
            "profiles_curated": len(relevant),
            "portrait_profiles_ready_for_download": sum(1 for c in relevant if c["portrait_verified"]),
            "role_corrections": sum(1 for c in relevant if c["role_before"] != c["role_after"]),
            "source": "BDFutbol individual player pages; explicit fixed curation only",
        }

    evidence = greek_foreign_evidence()
    dump(FOREIGN_EVIDENCE, evidence)
    greek_audit = audits["Greece"]
    greek_audit["rule_evidence"]["foreigners"] = {
        "evidence_file": "greece_1993_94_foreign_rule_evidence.json",
        "candidate_limit": 3,
        "primary_domestic_numerical_clause_recovered": False,
        "runtime_encoded": False,
        "reason": "No guessed numeric rule: source corroboration is strong but the exact Greek 1993-94 domestic regulatory clause is not yet recovered; Cypriot equivalence must also be represented.",
    }
    for league in snap.get("leagues", []):
        if int(league.get("source_id") or -1) == 930047:
            league["max_foreigners_starting"] = None
            league["max_foreigners_squad"] = None
            hints = league.setdefault("source_rule_hints", {})
            hints["foreign_rule_status"] = "candidate_3_strongly_corroborated_but_not_encoded_without_primary_greek_numeric_clause"
            hints["foreign_rule_evidence_file"] = "greece_1993_94_foreign_rule_evidence.json"
            hints["foreign_domestic_equivalent_country_ids"] = [25]
            hints["foreign_domestic_equivalence_status"] = "Cypriots source-supported as non-foreign and encoded for domestic Greek competitions"
            break

    # Top-level profile audit is deliberately explicit about what remains unresolved.
    profile_audit = {
        "schema_version": 1,
        "checkpoint": "0.29.0-turkey-russia-greece-individual-profiles",
        "policy": "Only source-backed fields are changed. Missing biographies and photo IDs remain unresolved rather than inferred. Role changes re-materialise fixed attributes from original source-backed 1993-94 comparables; football 75/25 is never used.",
        "profiles_curated": len(changes),
        "portrait_profiles_ready_for_download": sum(1 for c in changes if c["portrait_verified"]),
        "by_country": {
            country: {
                "profiles_curated": sum(1 for c in changes if c["country"] == country),
                "portrait_profiles_ready_for_download": sum(1 for c in changes if c["country"] == country and c["portrait_verified"]),
                "role_corrections": sum(1 for c in changes if c["country"] == country and c["role_before"] != c["role_after"]),
            }
            for country in ("Turkey", "Russia", "Greece")
        },
        "role_corrections": [c for c in changes if c["role_before"] != c["role_after"]],
        "duplicate_reconciliations": [c for c in changes if c.get("duplicate_reconciliation")],
        "changes": changes,
        "greece_foreign_rule": {
            "evidence_file": FOREIGN_EVIDENCE.name,
            "candidate_limit": 3,
            "runtime_encoded": False,
            "why": evidence["reason"],
        },
    }

    dump(SNAP, snap)
    dump(REGISTRY, registry)
    for k, path in STAGES.items(): dump(path, stages[k])
    for k, path in AUDITS.items(): dump(path, audits[k])
    dump(PROFILE_AUDIT, profile_audit)
    print(json.dumps({
        "profiles_curated": len(changes),
        "portrait_ready": profile_audit["portrait_profiles_ready_for_download"],
        "role_corrections": len(profile_audit["role_corrections"]),
        "snapshot_players": len(snap["players"]),
        "registry_rows": len(registry["players"]),
        "greece_foreign_runtime_encoded": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
