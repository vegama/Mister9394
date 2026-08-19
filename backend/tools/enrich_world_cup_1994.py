from __future__ import annotations

"""Idempotently enrich the 1993-94 snapshot with the complete USA 1994 squads.

Identity and tournament membership come from the bundled Fjelstul World Cup
Database extract.  Players already present in the historical snapshot are
reused.  Missing players are added with conservative, deterministic 1993-94
ratings.  If their 1993-94 club is not part of an admitted league in this game,
they are owned by a non-playable ``Otros-<país>`` market container rather than
being exposed as free agents.

The container is deliberately *not* a transfer lock: active clubs may buy from
it and normal historical foreign-player rules still apply to the buyer.
"""

import argparse
from copy import deepcopy
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import unicodedata
from typing import Any
import csv

from backend.app.football9394.identity_reconciliation import reconcile_player_identity, full_name_variants
from backend.app.football9394.snapshot_runtime import PRESENTATION_COUNTRIES

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_SQUADS = REPO_ROOT / "data" / "football9394" / "world_cup_1994_squads.json"
DEFAULT_REPORT = REPO_ROOT / "data" / "football9394" / "world_cup_1994_enrichment_report.json"
DEFAULT_RECONCILIATION = REPO_ROOT / "data" / "football9394" / "player_identity_reconciliation_report.json"
DEFAULT_CREATION_REGISTRY_JSON = REPO_ROOT / "data" / "football9394" / "created_players_registry.json"
DEFAULT_CREATION_REGISTRY_CSV = REPO_ROOT / "data" / "football9394" / "created_players_registry.csv"

# Verified corrections to legacy source identities.  They are applied to the
# existing player rather than creating a replacement identity.
SOURCE_PLAYER_CORRECTIONS: dict[int, dict[str, Any]] = {
    515: {
        "birth_date": "1967-02-27T00:00:00",
        "correction_source": "BDFutbol · Dmitri Lvovich Popov",
        "correction_reason": "legacy snapshot DOB was 1969-02-27; verified historical DOB is 1967-02-27",
    },
}

# Snapshot ids for players whose source spelling is known to differ from the
# international data.  These are identities, not rating overrides.
IDENTITY_OVERRIDES: dict[tuple[str, str], int] = {
    ("BGR", "petar hubchev"): 2609,
    ("ESP", "albert ferrer"): 2,
    ("ESP", "abelardo"): 288,
    ("BRA", "jorginho"): 2364,
    ("BRA", "zetti"): 7784,
    ("BRA", "mazinho"): 7710,
    ("NLD", "peter van vossen"): 6499,
    ("ITA", "antonio conte"): 1061,
    ("RUS", "igor korneev"): 545,
    ("RUS", "dmitri kharine"): 2039,
    ("BGR", "ivaylo yordanov"): 4867,
    ("BGR", "velko yotov"): 542,
    ("NGA", "mutiu adepoju"): 516,
    # Confirmed source identities retained from the 0.21 reconciler.
    ("COL", "victor aristizabal"): 99,
    ("BRA", "claudio taffarel"): 1460,
    ("BRA", "gilmar rinaldi"): 7823,
    ("RUS", "aleksandr mostovoi"): 6380,
    ("SWE", "stefan schwarz"): 4834,
    ("ESP", "paco camarasa"): 83,
    ("ESP", "fernando hierro"): 26,
    ("ESP", "txiki begiristain"): 15,
    ("ESP", "jose luis caminero"): 138,
    ("ARG", "ramon medina bello"): 7070,
    ("BGR", "iliyan kiryakov"): 750,
    ("BGR", "petar mihtarski"): 4825,
    ("IRL", "ronnie whelan"): 1861,
    ("MEX", "luis garcia postigo"): 140,
}

# A real 1993-94 club is used only when that club is in an admitted competition
# in the current universe.  Everything else is intentionally represented by the
# country's market container.  Club provenance for these exceptions was checked
# against the published USA 1994 squad lists (clubs as of 16 June 1994).
PLAYABLE_CLUB_OVERRIDES: dict[tuple[str, str], int] = {
    ("USA", "hugo perez"): 734,              # Los Angeles Salsa
    ("CMR", "thomas n kono"): 793,           # CE L'Hospitalet
    ("RUS", "sergei yuran"): 303,            # SL Benfica
    ("RUS", "dmitri popov"): 17,              # Racing Santander
    ("IRL", "terry phelan"): 253,            # Manchester City
    ("IRL", "paul mcgrath"): 249,            # Aston Villa
    ("IRL", "alan kernaghan"): 253,          # Manchester City
    ("IRL", "phil babb"): 323,               # Coventry City
    ("IRL", "tony cascarino"): 80,           # Chelsea
    ("IRL", "eddie mcgoldrick"): 79,         # Arsenal
    ("IRL", "john sheridan"): 337,            # Sheffield Wednesday
    ("IRL", "alan kelly"): 336,               # Sheffield United
}

# Fjelstul contains a few transposed/incorrect DOB values.  Only corrections we
# explicitly verified against the tournament squad source are applied here.
DOB_CORRECTIONS: dict[tuple[str, str], str] = {
    ("USA", "thomas dooley"): "1961-05-12",
    ("BOL", "carlos trucco"): "1957-08-11",
    ("BEL", "dirk medved"): "1968-09-15",
    ("IRL", "phil babb"): "1970-11-30",
}

# Conservative national baselines for source-missing players.  Existing source
# players always keep their original detailed ratings.
COUNTRY_BASELINES = {
    "ITA": 82, "DEU": 81, "ESP": 81, "BRA": 81, "NLD": 79, "ARG": 79,
    "BEL": 77, "SWE": 77, "RUS": 76, "ROU": 76, "IRL": 75, "CHE": 75,
    "NGA": 75, "BGR": 74, "NOR": 74, "COL": 74, "CMR": 73, "USA": 72,
    "MAR": 71, "GRC": 70, "BOL": 70, "KOR": 69, "SAU": 67,
}

# A small set of 1994-status overrides prevents well-established stars who are
# absent from the club snapshot from being flattened to their national baseline.
OVERALL_OVERRIDES: dict[tuple[str, str], int] = {
    ("BEL", "michel preud homme"): 86,
    ("BEL", "franky van der elst"): 83,
    ("BEL", "enzo scifo"): 84,
    ("IRL", "paul mcgrath"): 83,
    ("RUS", "valeri karpin"): 81,
    ("RUS", "viktor onopko"): 80,
    ("RUS", "ilya tsymbalar"): 79,
    ("RUS", "yuri nikiforov"): 79,
    ("SWE", "thomas ravelli"): 80,
    ("SWE", "joachim bjorklund"): 78,
    ("SWE", "hakan mild"): 78,
    ("BOL", "marco etcheverry"): 79,
    ("CMR", "roger milla"): 74,
    ("CMR", "rigobert song"): 73,
    ("USA", "john harkes"): 76,
    ("USA", "eric wynalda"): 76,
    ("USA", "thomas dooley"): 75,
    ("USA", "brad friedel"): 73,
    ("USA", "claudio reyna"): 73,
}

ATTR_NAMES = (
    "pace", "acceleration", "jumping", "stamina", "strength", "tackling",
    "work_rate", "aggression", "anticipation", "marking", "discipline",
    "positioning", "leadership", "consistency", "vision", "short_pass",
    "long_pass", "dribbling", "finishing", "heading", "off_ball",
    "shot_power", "free_kicks", "penalties", "technique",
)


def clean_text(value: Any) -> str:
    text = str(value or "").replace("not applicable", " ")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def clean_display(player: dict[str, Any], team_code: str) -> str:
    given = str(player.get("given_name") or "").strip()
    family = str(player.get("family_name") or "").strip()
    if given.lower() == "not applicable":
        given = ""
    if family.lower() == "not applicable":
        family = ""
    if team_code == "KOR" and family and given:
        return f"{family} {given}".strip()
    return " ".join(x for x in (given, family) if x).strip() or str(player.get("display_name") or "").replace("not applicable", "").strip()


def player_country_id(player: dict[str, Any]) -> int | None:
    value = player.get("international_country_id") or player.get("birth_country_id")
    return int(value) if isinstance(value, int) and value > 0 else None


def name_variants(player: dict[str, Any]) -> set[str]:
    values = {
        clean_text(player.get("display_name")),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1", "surname2"))),
        clean_text(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1"))),
        clean_text(player.get("surname1")),
        clean_text(" ".join(str(player.get(k) or "") for k in ("surname1", "surname2"))),
    }
    return {v for v in values if v}


def build_identity_candidate_index(players: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[int, dict[str, Any]] = {}
    by_surname: dict[str, list[dict[str, Any]]] = {}
    by_dob: dict[str, list[dict[str, Any]]] = {}
    by_team: dict[int, list[dict[str, Any]]] = {}
    by_prefix: dict[str, list[dict[str, Any]]] = {}
    for player in players:
        pid = int(player.get("source_id") or 0)
        if pid <= 0:
            continue
        by_id[pid] = player
        surname = clean_text(player.get("surname1"))
        if surname:
            by_surname.setdefault(surname, []).append(player)
        dob = str(player.get("birth_date") or "")[:10]
        if dob:
            by_dob.setdefault(dob, []).append(player)
        team_id = int(player.get("team_id") or 0)
        if team_id:
            by_team.setdefault(team_id, []).append(player)
        prefixes: set[str] = set()
        for variant in full_name_variants(player):
            for token in variant.split():
                if len(token) >= 4:
                    prefixes.add(token[:4])
        for prefix in prefixes:
            by_prefix.setdefault(prefix, []).append(player)
    return {"by_id": by_id, "by_surname": by_surname, "by_dob": by_dob, "by_team": by_team, "by_prefix": by_prefix}


def identity_candidate_pool(index: dict[str, Any], *, display: str, given: str, family: str, dob: Any, expected_team: int | None, override: int | None) -> list[dict[str, Any]]:
    pool: dict[int, dict[str, Any]] = {}
    family_key = clean_text(family)
    for player in index["by_surname"].get(family_key, []):
        pool[int(player["source_id"])] = player
    dob_key = str(dob or "")[:10]
    for player in index["by_dob"].get(dob_key, []):
        pool[int(player["source_id"])] = player
    if expected_team:
        for player in index["by_team"].get(int(expected_team), []):
            pool[int(player["source_id"])] = player
    for token in clean_text(f"{display} {given} {family}").split():
        if len(token) >= 4:
            for player in index["by_prefix"].get(token[:4], []):
                pool[int(player["source_id"])] = player
    if override and int(override) in index["by_id"]:
        pool[int(override)] = index["by_id"][int(override)]
    return list(pool.values())


def match_existing(snapshot: dict[str, Any], team_code: str, country_id: int, row: dict[str, Any], identity_index: dict[str, Any]) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    target = clean_text(row["display_name"])
    override = IDENTITY_OVERRIDES.get((team_code, target))
    expected_team = PLAYABLE_CLUB_OVERRIDES.get((team_code, target))
    target_dob = DOB_CORRECTIONS.get((team_code, target), row.get("birth_date"))
    candidates = identity_candidate_pool(
        identity_index,
        display=str(row.get("display_name") or ""),
        given=str(row.get("given_name") or ""),
        family=str(row.get("family_name") or ""),
        dob=target_dob,
        expected_team=expected_team,
        override=override,
    )
    result = reconcile_player_identity(
        candidates,
        target_display=str(row.get("display_name") or ""),
        target_given=str(row.get("given_name") or ""),
        target_family=str(row.get("family_name") or ""),
        target_birth_date=target_dob,
        target_country_id=country_id,
        expected_team_id=expected_team,
        identity_override_id=override,
    )
    audit = {
        "team_code": team_code,
        "display_name": row.get("display_name"),
        "external_player_id": row.get("external_player_id"),
        "target_birth_date": DOB_CORRECTIONS.get((team_code, target), row.get("birth_date")),
        "target_country_id": country_id,
        "expected_team_id": expected_team,
        "resolution": result.resolution,
        "confidence": result.confidence,
        "score": result.score,
        "matched_existing_id": int(result.player["source_id"]) if result.player is not None else None,
        "candidates": [
            {
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
            }
            for c in result.candidates
        ],
    }
    return result.player, result.resolution, audit


def active_league_ids(snapshot: dict[str, Any]) -> set[int]:
    return {int(row["source_id"]) for row in snapshot.get("leagues", []) if bool(row.get("admitted", True))}


def make_container(team: dict[str, Any]) -> dict[str, Any]:
    country_id = int(team["country_id"])
    return {
        "source_id": 9_400_000 + country_id,
        "name": f"Otros-{team['name']}",
        "long_name": f"Otros clubes · {team['name']}",
        "short_name": f"Otros-{team['name']}",
        "initials": f"O{team['team_code']}",
        "league_id": None,
        "league_position": None,
        "stadium_id": None,
        "manager_id": None,
        "members": 0,
        "budget": 0,
        "debt": 0,
        "reserve_of": None,
        "reserve_step": 0,
        "academy_level": 0,
        "squad_building_style": 0,
        "sporting_director_level": 0,
        "women_flag": False,
        "activation_reason": "international_pool_container",
        "familiar_name": f"Otros-{team['name']}",
        "very_short_name": f"Otros-{team['name']}",
        "president": None,
        "secondary_stadium_id": None,
        "training_ground": None,
        "youth_residence": None,
        "main_rival_id": None,
        "regional_rival_id": None,
        "honours": {},
        "academy_style": 0,
        "special_academy_pattern_id": None,
        "initial_points_sanction": None,
        "fifa_registration_ban_until": None,
        "country_id": country_id,
        "playable": False,
        "market_container": True,
        "can_buy_players": False,
        "players_transferable": True,
        "historical_scope": "nonplayable_clubs_1993_94",
    }


def clamp(value: int, lo: int = 20, hi: int = 99) -> int:
    return max(lo, min(hi, int(value)))


def derived_attributes(overall: int, pos: str, external_id: str) -> dict[str, int]:
    seed = sum(ord(c) for c in external_id) % 7 - 3
    base = {name: clamp(overall + ((i * 3 + seed) % 7) - 3) for i, name in enumerate(ATTR_NAMES)}
    if pos == "GK":
        # The legacy match engine has no separate goalkeeper attribute family,
        # so keep physical/mental numbers solid and de-emphasise outfield skills.
        for key in ("tackling", "dribbling", "finishing", "off_ball", "free_kicks"):
            base[key] = clamp(overall - 20)
        for key in ("anticipation", "positioning", "consistency", "jumping", "strength"):
            base[key] = clamp(overall + 4)
    elif pos == "DF":
        for key in ("tackling", "marking", "positioning", "heading", "strength"):
            base[key] = clamp(overall + 5)
        base["finishing"] = clamp(overall - 15)
    elif pos == "MF":
        for key in ("vision", "short_pass", "long_pass", "technique", "work_rate"):
            base[key] = clamp(overall + 4)
    else:
        for key in ("finishing", "off_ball", "shot_power", "pace", "acceleration"):
            base[key] = clamp(overall + 5)
        base["marking"] = clamp(overall - 20)
        base["tackling"] = clamp(overall - 18)
    return base


def position_fields(pos: str) -> tuple[int, str, dict[str, int]]:
    ratings = {str(i): 0 for i in range(18)}
    if pos == "GK":
        primary, broad = 0, "POR"; ratings["0"] = 100
    elif pos == "DF":
        primary, broad = 3, "DEF"; ratings.update({"1": 55, "2": 55, "3": 100, "4": 90, "5": 70})
    elif pos == "MF":
        primary, broad = 7, "MED"; ratings.update({"6": 80, "7": 100, "8": 80, "9": 55, "13": 55})
    else:
        primary, broad = 17, "DEL"; ratings.update({"10": 50, "14": 50, "17": 100})
    return primary, broad, ratings


def inferred_overall(team_code: str, display_name: str, shirt_number: int, external_id: str) -> int:
    key = (team_code, clean_text(display_name))
    if key in OVERALL_OVERRIDES:
        return OVERALL_OVERRIDES[key]
    base = COUNTRY_BASELINES.get(team_code, 71)
    # First-choice shirt numbers get a tiny bump only; shirt number is not used
    # as a proxy for stardom beyond this conservative distinction.
    bump = 1 if 1 <= int(shirt_number or 99) <= 11 else 0
    noise = (sum(ord(c) for c in external_id) % 3) - 1
    return clamp(base + bump + noise, 60, 88)


def build_player(team: dict[str, Any], row: dict[str, Any], *, source_id: int, team_id: int) -> dict[str, Any]:
    team_code = str(team["team_code"])
    display = clean_display(row, team_code)
    normalized = clean_text(display)
    pos = str(row.get("position_code") or "MF").upper()
    overall = inferred_overall(team_code, display, int(row.get("shirt_number") or 0), str(row.get("external_player_id") or ""))
    primary, broad, role_ratings = position_fields(pos)
    birth_date = DOB_CORRECTIONS.get((team_code, normalized), str(row.get("birth_date") or "")[:10])
    given = str(row.get("given_name") or "").strip()
    family = str(row.get("family_name") or "").strip()
    if given.lower() == "not applicable": given = ""
    if family.lower() == "not applicable": family = ""
    return {
        "source_id": source_id,
        "team_id": int(team_id),
        "display_name": display,
        "first_name": given or display,
        "surname1": family or None,
        "surname2": None,
        "birth_date": f"{birth_date}T00:00:00" if birth_date else None,
        "birth_country_id": int(team["country_id"]),
        "international_country_id": int(team["country_id"]),
        "preferred_foot": 1,
        "shirt_number": int(row.get("shirt_number") or 0) or None,
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
        "initially_reserve": int(row.get("shirt_number") or 99) > 11,
        "retired": False,
        "attributes": derived_attributes(overall, pos, str(row.get("external_player_id") or "")),
        "birth_city_id": 0,
        "naturalized_country_id": None,
        "basque_origin": False,
        "favorite_shirt_number": int(row.get("shirt_number") or 0),
        "injury_proneness": 0,
        "progression_mean": 0,
        "fan_affection": 6,
        "academy_team_id": 0,
        "previous_team_id": 0,
        "previous_team_years": 0,
        "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False, "long_shots": False, "cuts_inside": False, "first_time_play": False, "dives": False},
        "historical_squad_1994": True,
        "world_cup_1994": {
            "team_code": team_code,
            "country_id": int(team["country_id"]),
            "group": team.get("group"),
            "shirt_number": int(row.get("shirt_number") or 0),
            "position": pos,
            "external_player_id": row.get("external_player_id"),
        },
        "identity_source": "Fjelstul World Cup Database",
        "historical_data_source": "Fjelstul World Cup Database",
        "attribute_source": "provisional_pending_profile_review",
        "profile_review_required": True,
        "role_detail_source": "derived_from_broad_world_cup_position",
        "historical_club_1994": None,
        "market_container_origin": team["name"] if int(team_id) >= 9_400_000 else None,
        "external_origin": "world_cup_1994",
    }


def apply_verified_source_corrections(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    by_id = {int(p.get("source_id") or 0): p for p in snapshot.get("players", [])}
    for source_id, patch in SOURCE_PLAYER_CORRECTIONS.items():
        player = by_id.get(int(source_id))
        if player is None:
            continue
        before = {key: player.get(key) for key in patch if key not in {"correction_source", "correction_reason"}}
        for key, value in patch.items():
            if key.startswith("correction_"):
                continue
            player[key] = value
        correction = {
            "batch": "identity_reconciliation_0.22",
            "source": patch.get("correction_source"),
            "reason": patch.get("correction_reason"),
            "before": before,
            "after": {key: player.get(key) for key in before},
        }
        history = player.setdefault("verified_data_corrections", [])
        # Older 0.22 development runs could append this same correction on
        # every import. Collapse identical provenance keys before deciding
        # whether the correction needs a history row, preserving the earliest
        # (and therefore most informative) pre-correction value.
        deduped_history = []
        seen_history = set()
        for row in history:
            key = (row.get("batch"), row.get("source"), row.get("reason"))
            if key in seen_history:
                continue
            seen_history.add(key)
            deduped_history.append(row)
        history[:] = deduped_history
        if not any(
            row.get("batch") == correction["batch"]
            and row.get("source") == correction["source"]
            and row.get("reason") == correction["reason"]
            for row in history
        ):
            history.append(correction)
        applied.append({"source_id": source_id, "display_name": player.get("display_name"), "before": before, "after": {key: player.get(key) for key in before}, "source": patch.get("correction_source")})
    return applied


# Campos que este importador rellena con un valor por defecto pero que las
# tandas de perfiles afinan después: la foto que ya se bajó y normalizó, y la
# puerta de identidad concreta por la que pasó cada ficha. Rehacer el registro no
# puede devolverlos a su valor genérico —se perdería el trabajo y volveríamos a
# descargar retratos ya guardados—, así que si el registro anterior traía algo
# más específico, ese valor manda.
CARRIED_OVER = {
    "bdfutbol_id": "",
    "bdfutbol_url": "",
    "photo_status": "pending",
    "duplicate_check": "created_after_global_existing_player_comparison",
}


def write_creation_registry(snapshot: dict[str, Any], *, json_path: Path = DEFAULT_CREATION_REGISTRY_JSON, csv_path: Path = DEFAULT_CREATION_REGISTRY_CSV) -> list[dict[str, Any]]:
    teams = {int(t.get("source_id") or 0): t for t in snapshot.get("teams", [])}
    rows: list[dict[str, Any]] = []
    for p in snapshot.get("players", []):
        if not p.get("external_origin"):
            continue
        if p.get("external_origin") not in {"world_cup_1994", "national_pool_1993_94"}:
            continue
        team = teams.get(int(p.get("team_id") or 0), {})
        wc = p.get("world_cup_1994") or {}
        rows.append({
            "source_id": int(p["source_id"]),
            "display_name": p.get("display_name"),
            "first_name": p.get("first_name"),
            "surname1": p.get("surname1"),
            "surname2": p.get("surname2"),
            "birth_date": str(p.get("birth_date") or "")[:10],
            "country_id": int(p.get("international_country_id") or p.get("birth_country_id") or 0),
            "country_name": PRESENTATION_COUNTRIES.get(int(p.get("international_country_id") or p.get("birth_country_id") or 0), ""),
            "broad_position": p.get("broad_position"),
            "team_id": int(p.get("team_id") or 0),
            "team_name": team.get("name"),
            "creation_batch": p.get("creation_batch") or p.get("external_origin"),
            "identity_source": p.get("identity_source"),
            "identity_source_url": p.get("identity_source_url"),
            "verified_national_pool_year": p.get("verified_national_pool_year"),
            "historical_position_1993_94": p.get("historical_position_1993_94"),
            "historical_club_1994": p.get("historical_club_1994"),
            "overall": int(p.get("overall") or 0),
            "attribute_source": p.get("attribute_source"),
            "profile_review_required": bool(p.get("profile_review_required", False)),
            "profile_review_batch": (p.get("profile_review_0_23") or {}).get("batch"),
            "profile_confidence": (p.get("profile_review_0_23") or {}).get("profile_confidence"),
            "duplicate_check": "created_after_global_existing_player_comparison",
            "matched_existing_id": None,
            "world_cup_1994_team_code": wc.get("team_code"),
            "world_cup_1994_shirt_number": wc.get("shirt_number"),
            "bdfutbol_search_name": p.get("display_name"),
            "bdfutbol_id": "",
            "bdfutbol_url": "",
            "photo_filename": f"{int(p['source_id'])}.jpg",
            "photo_status": "pending",
        })
    # El registro es compartido: las tandas de perfiles turcos, belgas y rusos
    # también escriben en él, y sus fichas no llevan ``external_origin``. Si aquí
    # se reescribiera la lista entera con lo que este importador conoce, esas
    # 1.685 filas desaparecerían aunque el futbolista siga vivo en el universo,
    # y con ellas el rastro de qué foto y qué fuente tiene cada uno. Esta
    # herramienta manda sobre sus dos orígenes y respeta el resto.
    owned = {"world_cup_1994", "national_pool_1993_94"}
    alive = {int(p["source_id"]): p for p in snapshot.get("players", [])}
    fresh = {int(r["source_id"]): r for r in rows}
    if json_path.exists():
        previous = json.loads(json_path.read_text(encoding="utf-8")).get("players", [])
        for row in previous:
            source_id = int(row["source_id"])
            if source_id in fresh:
                # La foto es trabajo de otra tubería y de otra fuente. Rehacer el
                # registro no puede devolver a "pendiente" un retrato que ya está
                # descargado y normalizado: se perdería el rastro y volveríamos a
                # bajarlo.
                current = fresh[source_id]
                for key, default in CARRIED_OVER.items():
                    if row.get(key) and current.get(key) in (None, "", default):
                        current[key] = row[key]
                continue
            player = alive.get(source_id)
            if player is None or player.get("external_origin") in owned:
                continue  # se ha ido del universo, o era nuestro y ya no es un alta
            rows.append(row)
    rows.sort(key=lambda r: int(r["source_id"]))
    payload = {"schema_version": 1, "purpose": "stable registry for historical-player photo acquisition and provenance", "players": rows}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Las filas conservadas de otras tandas no traen exactamente las mismas
    # columnas, así que la cabecera es la unión de todas y no la de la primera.
    fields: list[str] = []
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    fields = fields or ["source_id", "display_name"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def enrich(snapshot_path: Path, squads_path: Path, report_path: Path) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    squads = json.loads(squads_path.read_text(encoding="utf-8"))

    # Remove a previous derived run first.  Existing source records only lose the
    # enrichment metadata, never original source fields.
    derived_ids = {int(p["source_id"]) for p in snapshot.get("players", []) if p.get("external_origin") == "world_cup_1994"}
    if derived_ids:
        snapshot["players"] = [p for p in snapshot["players"] if int(p["source_id"]) not in derived_ids]
    snapshot["teams"] = [t for t in snapshot.get("teams", []) if not t.get("market_container")]
    source_corrections = apply_verified_source_corrections(snapshot)
    identity_index = build_identity_candidate_index(snapshot.get("players", []))
    reconciliation_rows: list[dict[str, Any]] = []

    for p in snapshot.get("players", []):
        for key in ("historical_squad_1994", "world_cup_1994", "historical_data_source"):
            if key in p and p.get("external_origin") != "world_cup_1994":
                p.pop(key, None)

    active_leagues = active_league_ids(snapshot)
    active_team_ids = {int(t["source_id"]) for t in snapshot.get("teams", []) if int(t.get("league_id") or 0) in active_leagues}
    next_player_id = 9_494_000
    existing_ids = {int(p["source_id"]) for p in snapshot["players"]}
    while next_player_id in existing_ids:
        next_player_id += 1

    containers: dict[int, dict[str, Any]] = {}
    resolution_counts = {"existing": 0, "added": 0, "playable_club": 0, "market_container": 0}
    country_report: dict[str, dict[str, Any]] = {}
    seen_resolution_ids: set[int] = set()

    for team in squads["teams"]:
        code = str(team["team_code"])
        cid = int(team["country_id"])
        country_report[code] = {"country_id": cid, "name": team["name"], "existing": 0, "added": 0, "container": 0, "playable_club": 0}
        team["historical_head_coach"] = team.get("head_coach")
        for row in team["players"]:
            row["display_name"] = clean_display(row, code)
            key = (code, clean_text(row["display_name"]))
            player, resolution, identity_audit = match_existing(snapshot, code, cid, row, identity_index)
            reconciliation_rows.append(identity_audit)
            if resolution == "ambiguous_existing_candidates":
                raise RuntimeError(f"ambiguous identity for {code}/{row['display_name']}; review player_identity_reconciliation_report.json")
            if player is not None and int(player["source_id"]) not in seen_resolution_ids:
                pid = int(player["source_id"])
                seen_resolution_ids.add(pid)
                player["historical_squad_1994"] = True
                player["historical_data_source"] = "Fjelstul World Cup Database"
                player["international_country_id"] = cid
                player["world_cup_1994"] = {
                    "team_code": code, "country_id": cid, "group": team.get("group"),
                    "shirt_number": int(row.get("shirt_number") or 0),
                    "position": row.get("position_code"), "external_player_id": row.get("external_player_id"),
                }
                row.update({"resolved_source_id": pid, "resolution": resolution, "game_team_id": int(player.get("team_id") or 0), "game_team_name": next((t.get("name") for t in snapshot["teams"] if int(t["source_id"]) == int(player.get("team_id") or 0)), None)})
                reconciliation_rows[-1].update({"action": "reused_existing", "matched_existing_id": pid})
                resolution_counts["existing"] += 1
                country_report[code]["existing"] += 1
                continue

            # A duplicate resolution or no confident match is treated as missing:
            # each of the 528 historical squad slots must map to one unique player.
            target_team = PLAYABLE_CLUB_OVERRIDES.get(key)
            if target_team is not None and target_team not in active_team_ids:
                raise RuntimeError(f"playable club override {target_team} for {code}/{row['display_name']} is not active")
            if target_team is None:
                container = containers.setdefault(cid, make_container(team))
                target_team = int(container["source_id"])
                resolution_counts["market_container"] += 1
                country_report[code]["container"] += 1
            else:
                resolution_counts["playable_club"] += 1
                country_report[code]["playable_club"] += 1

            player = build_player(team, row, source_id=next_player_id, team_id=target_team)
            if key in PLAYABLE_CLUB_OVERRIDES:
                player["historical_club_1994"] = next((t.get("name") for t in snapshot["teams"] if int(t["source_id"]) == target_team), None)
                player["club_assignment_source"] = "1994 FIFA World Cup squad club listing"
            else:
                player["club_assignment_source"] = "nonplayable_1993_94_club_container"
            snapshot["players"].append(player)
            pid = next_player_id
            next_player_id += 1
            seen_resolution_ids.add(pid)
            row.update({"resolved_source_id": pid, "resolution": "added_world_cup_1994", "game_team_id": int(target_team), "game_team_name": (containers[cid]["name"] if cid in containers and int(containers[cid]["source_id"]) == target_team else player.get("historical_club_1994"))})
            reconciliation_rows[-1].update({"action": "created", "created_source_id": pid, "resolution": "created_after_global_check"})
            resolution_counts["added"] += 1
            country_report[code]["added"] += 1

    snapshot["teams"].extend(sorted(containers.values(), key=lambda t: int(t["source_id"])))
    snapshot["players"].sort(key=lambda p: int(p["source_id"]))
    snapshot["teams"].sort(key=lambda t: int(t["source_id"]))

    all_roster_ids = [int(r["resolved_source_id"]) for t in squads["teams"] for r in t["players"]]
    if len(all_roster_ids) != 528 or len(set(all_roster_ids)) != 528:
        raise RuntimeError("USA 1994 enrichment did not resolve 528 unique squad players")
    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    if any(pid not in by_id for pid in all_roster_ids):
        raise RuntimeError("USA 1994 roster points at a missing runtime player")
    for team in squads["teams"]:
        ids = [int(r["resolved_source_id"]) for r in team["players"]]
        if len(ids) != 22 or len(set(ids)) != 22:
            raise RuntimeError(f"{team['team_code']} does not have 22 unique USA 1994 players")

    snapshot["world_cup_1994_enrichment"] = {
        "status": "complete",
        "squads": 24,
        "players": 528,
        "source_existing_players": resolution_counts["existing"],
        "added_players": resolution_counts["added"],
        "market_container_players": resolution_counts["market_container"],
        "playable_club_assignments": resolution_counts["playable_club"],
        "market_container_teams": len(containers),
        "identity_source": "Fjelstul World Cup Database",
        "detailed_attribute_policy": "source players unchanged; missing-player attributes derived conservatively from 1993-94 tournament context",
        "foreign_rule_policy": "normal_historical_rules_apply",
    }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    squads_path.write_text(json.dumps(squads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        **snapshot["world_cup_1994_enrichment"],
        "countries": country_report,
        "containers": [{"source_id": int(t["source_id"]), "name": t["name"], "country_id": int(t["country_id"])} for t in sorted(containers.values(), key=lambda x: int(x["country_id"]))],
        "playable_club_overrides": [
            {"team_code": code, "player": name, "team_id": team_id, "team_name": next((t.get("name") for t in snapshot["teams"] if int(t["source_id"]) == team_id), None)}
            for (code, name), team_id in sorted(PLAYABLE_CLUB_OVERRIDES.items())
        ],
    }
    report["verified_source_corrections"] = source_corrections
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DEFAULT_RECONCILIATION.write_text(json.dumps({"schema_version": 1, "compared_against_existing_players": len([p for p in snapshot.get("players", []) if p.get("external_origin") != "world_cup_1994"]), "rows": reconciliation_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = write_creation_registry(snapshot)
    report["created_player_registry_rows"] = len(registry)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--squads", type=Path, default=DEFAULT_SQUADS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = enrich(args.snapshot, args.squads, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
