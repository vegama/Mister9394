from __future__ import annotations

"""v1.1.3 historical database hygiene and identity reconciliation.

This pass is deliberately conservative:
- duplicated identities are retired as aliases instead of deleted;
- historical club spells and full source names are preserved;
- current 1993-94 club is corrected only where the transfer chronology has
  already been verified;
- patronymics remain available in ``historical_full_name`` but routine UI uses
  the same short name convention as the rest of the game.
"""

from copy import deepcopy
from difflib import SequenceMatcher
import csv
import shutil
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from backend.app.football9394.player_names import preserve_full_name_and_shorten, short_historical_display_name

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REGISTRY = DATA / "created_players_registry.json"
REGISTRY_CSV = DATA / "created_players_registry.csv"
PHOTO_QUEUE = DATA / "bdfutbol_photo_queue.json"
PHOTO_QUEUE_CSV = DATA / "bdfutbol_photo_queue.csv"
REPORT = DATA / "database_hygiene_v113.json"

# Strong, source-backed non-exact identity matches.  The duplicated row is kept
# as a retired alias so old saves/audits can still resolve the historical ID.
MANUAL_MERGES: dict[int, int] = {
    9494151: 9501277,  # Daniel Borimirov: same final club/date; keep BDFutbol identity
    9495356: 503,       # Rashid Rahimov -> Rashid Rakhimov
    9495151: 2428,      # Ned Zelic -> Nedjeljko Zelic
    9495143: 5556,      # Mixu Paatelainen -> Mika/Mixu Paatelainen
    9496362: 2727,      # Andreas Wagenhaus
    7798: 464,          # Gustavo Matosas
    9051: 1247,         # Marco Ambrosio
    9083: 1250,         # Nicola Boselli
    5512: 2021,         # Dale Gordon
    5862: 2057,         # Andy/Andrew Dow
    5612: 2216,         # Stuart Slater
    9451: 8531,         # Fabio Bellotti
    7385: 7130,         # Fernando Quiroz
    9016: 7211,         # Antonio Mohamed
    9018: 7409,         # Ramon Angel Bernuncio
    7259: 7113,         # Fabian Fernandez
    7589: 7173,         # Raul Peralta
    7425: 7204,         # Raul Cascini
    8898: 7239,         # Hernan Cristante
    9596: 7614,         # Nelson Alcides Cabrera
    8186: 7747,         # Luciano Nunes de Souza
    9863: 6885,         # Erik/Eric ten Voorde
    7295: 7086,         # Leonardo Ramos
    9497252: 9496045,   # Ovidiu Hanganu
    9497242: 9496498,   # Sergiy/Sergei Gusev
    9497237: 9496502,   # Yuriy Shelepnytskyi
    9497262: 9496494,   # Seyhmus Suna
    38272: 2609,        # Petar Houbtchev/Hubchev -> Petar Hubchev
    8266: 7424,         # Claudio Borghi (same identity; 1993 Platense)
    9782: 9718,         # Corrupted Eduardo Jaume/Favaro row -> Eduardo Jaume
}

# Same-DOB/same-display pairs which are known to be different people.  These
# are never auto-merged; display disambiguation handles the UI instead.
VERIFIED_DISTINCT: set[frozenset[int]] = {
    frozenset((1759, 1774)),      # Rodney / Raymond Wallace
    frozenset((6729, 6749)),      # Gerard / Dennis de Nooijer
    frozenset((2539, 2735)),      # Michael / Andreas Zeyer
    frozenset((3312, 3867)),      # two different Manolo identities (BDFutbol profiles differ)
    frozenset((4817, 7976)),      # Paulo Antonio Pereira / Paulo Silas (twins)
    frozenset((2833, 2836)),      # Frank / Ronald de Boer
    frozenset((6533, 6534)),      # Bjarki / Arnar Gunnlaugsson
    frozenset((7248, 7249)),      # Guillermo / Gustavo Barros Schelotto
    frozenset((9496380, 9496385)),# Shota / Archil Arveladze
    frozenset((4552, 4562)),      # Jorge / Jose Lorenzo
    frozenset((4200, 4203)),      # Suso / Joaquin Lopez
    frozenset((8238, 8911)),      # Jose Jaime / Mario Ordiales
    frozenset((1021, 3074)),      # Pedro / Juan Diaz
    frozenset((9500793, 9503540)),# Kent Nielsen: 1961 international vs 1972 youth player
}

# Current-club corrections use the game's 1993-94 snapshot convention: summer
# 1993 moves are applied, while later in-season moves remain club spells.
CURRENT_TEAM_OVERRIDES: dict[int, int] = {
    515: 17,          # Dmitri Popov -> Racing Santander (12 Aug 1993)
    517: 17,          # Dmitri Radchenko -> Racing Santander (15 Aug 1993)
    2705: 871,        # Stanislav Cherchesov -> SG Dynamo Dresden (13 Jul 1993)
    9497352: 9315002, # Andrey Chernyshov -> Dynamo Moskva (31 Jul 1993)
    2727: 9357001,    # Wagenhaus -> Fenerbahce (Aug 1993)
    9495109: 9347003, # Fabian Estay -> Olympiakos
    9496045: 9357003, # Hanganu -> Samsunspor (Jun 1993)
    9496498: 9357002, # Gusev -> Trabzonspor (Jul 1993; Altay only from Nov)
    9496502: 9357002, # Shelepnytskyi -> Trabzonspor (Altay only from Nov)
    9496494: 9357004, # Suna -> Kocaelispor after summer move; Altay loan from Nov
    9496036: 9357003, # Cheregi -> Samsunspor for 1993-94
    9496515: 9357010, # Cafer Aydin opens 93-94 at Kayserispor; Ankaragucu from Nov 1993
    9494159: 9347013, # Kolitsidakis: Apollon -> Panathinaikos during season
    9497169: 9347004, # Katsiaounis: Aris -> Panachaiki
    9497066: 9347011, # Kyrillidis: Levadiakos -> Larisa
    9497067: 9347004, # Mouratidis: Aris -> Larisa
    9497065: 9347004, # Kolomitrousis: Aris -> Larisa
    9496990: 9347013, # Karasavvidis: Apollon -> PAOK
    9718: 404,         # Eduardo Jaume -> Racing de Montevideo (Racing 1993 source)
    9715: 2341,        # Claudio Morena -> Tecos U.A.G. (signed Aug 1992; still there in 1993)
    9735: 997,         # Jacinto Cabrera -> Liverpool Montevideo (documented Apr/Oct 1993)
    9741: 1411,        # Luis Barbat -> Independiente Medellin (1 Jul 1993)
}

# Explicit Greek/Turkey/Belgium duplicate rows which exact-name detection also
# catches.  Keeping them here documents the transfer chronology and guarantees
# the rule survives name-format changes.
MANUAL_MERGES.update({
    9497628: 9494159,
    9497531: 9495109,
    9496414: 9496036,
    9497539: 9497169,
    9497608: 9497066,
    9497542: 9497067,
    9497541: 9497065,
    9497639: 9496990,
})

VERIFIED_PHOTO_ID_REMAP = {9497314: 9496515}  # Cafer Aydin: verified v0.34 BDFutbol portrait

PROFILE_CORRECTIONS = {
    9741: {
        "historical_profile_source_url": "https://www.auf.org.uy/historico-jugadores/1/b/or_mam/",
        "snapshot_club_source_url": "https://www.transfermarkt.co/spielbericht/index/spielbericht/4787485",
        "snapshot_club_source_note": "Transfer Liverpool -> Independiente Medellin dated 1 Jul 1993; Colombian press already reports the loan in Feb 1993.",
    },
    9751: {
        "display_name": "Armando Dely Valdés",
        "first_name": "Armando Javier",
        "surname1": "Dely",
        "surname2": "Valdés",
        "historical_full_name": "Armando Javier Dely Valdés",
        "birth_date": "1964-01-05T00:00:00",
        "primary_role": 17,
        "broad_position": "DEL",
        "role_ratings": {**{str(i): 0 for i in range(18)}, "11": 80, "17": 100},
        "height_cm": 183,
        "weight_kg": 85,
        "historical_position_1993_94": "Forward",
        "historical_profile_source_url": "https://www.national-football-teams.com/player/43640/Armando_Dely_Valdes.html",
        "profile_review_required": False,
        "identity_field_resolution_v113": "normalized_accent_full_name_and_forward_role; club retained because 1993 sources conflict",
    },
    9703: {
        "display_name": "Roberto Suárez",
        "first_name": "Roberto Óscar",
        "surname1": "Suárez",
        "surname2": None,
        "historical_full_name": "Roberto Óscar Suárez",
        "historical_profile_source_url": "https://www.transfermarkt.com/roberto-oscar-suarez/profil/spieler/1015227",
        "identity_field_resolution_v113": "middle_given_name_was_misparsed_as_surname",
    },
    9718: {
        "display_name": "Eduardo Jaume",
        "first_name": "Eduardo",
        "surname1": "Jaume",
        "surname2": None,
        "historical_full_name": "Eduardo Jaume",
        "identity_field_resolution_v113": "removed_cross-contaminated_Favaro_surname",
    },
    9746: {
        "display_name": "Cono Aguiar",
        "first_name": "Jesús Cono",
        "surname1": "Aguiar",
        "surname2": "Moreira",
        "historical_full_name": "Jesús Cono Aguiar Moreira",
        "birth_date": "1968-07-19T00:00:00",
        "height_cm": 187,
        "historical_profile_source_url": "https://www.transfermarkt.com/cono-aguiar/profil/spieler/296437",
    },
    9749: {
        "display_name": "Washington Rodríguez",
        "first_name": "Washington Óscar",
        "surname1": "Rodríguez",
        "surname2": "Secco",
        "historical_full_name": "Washington Óscar Rodríguez Secco",
        "birth_date": "1970-01-12T00:00:00",
        "historical_profile_source_url": "https://atilio.uy/jugador:1631",
    },
    9754: {
        "display_name": "Claudio Ciccia",
        "first_name": "Claudio Fabián",
        "surname1": "Ciccia",
        "surname2": "Bourdin",
        "historical_full_name": "Claudio Fabián Ciccia Bourdin",
        "birth_date": "1972-04-11T00:00:00",
        "historical_profile_source_url": "https://www.transfermarkt.com/claudio-ciccia/profil/spieler/903876",
        "identity_field_resolution_v113": "corrected_day_month_transposition",
    },
    9496672: {
        "primary_role": 2,
        "broad_position": "DEF",
        "historical_position_1993_94": "Left Back",
        "birth_date": "1968-03-08T00:00:00",
        "international_country_id": 40,
        "historical_birth_place_text": "Moscow (USSR)",
        "profile_position_precision": "exact",
        "profile_review_required": False,
        "height_cm": 179,
        "weight_kg": 74,
        "historical_profile_source_note": "BDFutbol j69694 / specialist cross-check: primary role left-back",
        "historical_profile_source_url": "https://www.bdfutbol.com/en/j/j69694.html",
    },
    9496780: {
        "display_name": "Murad Magomedov",
        "historical_birth_place_text": "Makhachkala (USSR)",
        "display_name_resolution": "birthplace_removed_from_display_name_v113",
    },
    9500872: {
        "primary_role": 12,
        "broad_position": "DEL",
        "historical_position_1993_94": "Right Winger",
        "profile_position_precision": "exact",
        "profile_review_required": False,
        "historical_position_source": "Austria Salzburg archive + Transfermarkt season profile",
        "historical_position_source_url": "https://wiki.austria-salzburg.at/wiki/Nikola_Jurcevic",
        "historical_profile_source_note": "Verified as right winger/forward; previous centre-back role was erroneous.",
        "identity_field_resolution_v113": "corrected_source_position_conflict_v113",
    },
}

STAGING_ID_REMAP = {
    9496680: 9496512,  # Mukhsin Mukhamadiev: active 93-94 identity is Ankaragucu
    9497314: 9496515,  # Cafer Aydin duplicated across Kayserispor/Ankaragucu
    9496345: 9496672,  # Ravil Sabitov duplicated across Waregem/Lokomotiv Moskva
}

ROLE_TO_BROAD_FALLBACK = {
    0: "POR", 1: "DEF", 2: "DEF", 3: "DEF", 4: "DEF", 5: "DEF",
    6: "MED", 7: "MED", 8: "MED", 9: "MED", 10: "MED", 11: "DEL",
    12: "DEL", 13: "MED", 14: "MED", 15: "DEL", 16: "DEL", 17: "DEL",
}


def clean(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def clean_ws(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return " ".join(value.split())


def full_name(player: dict[str, Any]) -> str:
    return clean(" ".join(str(player.get(k) or "") for k in ("first_name", "surname1", "surname2")))


def team_name(team_by_id: dict[int, dict[str, Any]], team_id: int | None) -> str | None:
    row = team_by_id.get(int(team_id or 0))
    return str(row.get("name")) if row else None


def add_spell(player: dict[str, Any], *, team_id: int, club: str, source: str) -> None:
    spells = list(player.get("historical_club_spells_1993_94") or [])
    key = (int(team_id), clean(club))
    if not any((int(s.get("team_id") or 0), clean(s.get("club"))) == key for s in spells):
        spells.append({"club": club, "team_id": int(team_id), "source": source})
    player["historical_club_spells_1993_94"] = spells


def merge_player(canonical: dict[str, Any], duplicate: dict[str, Any], *, team_by_id: dict[int, dict[str, Any]]) -> None:
    old_id = int(duplicate["source_id"])
    new_id = int(canonical["source_id"])
    dup_team = int(duplicate.get("team_id") or 0)
    if dup_team and team_name(team_by_id, dup_team):
        add_spell(canonical, team_id=dup_team, club=team_name(team_by_id, dup_team) or "", source="identity_merge_v113")
    can_team = int(canonical.get("team_id") or 0)
    if can_team and team_name(team_by_id, can_team):
        add_spell(canonical, team_id=can_team, club=team_name(team_by_id, can_team) or "", source="identity_merge_v113")

    # Preserve richer source-backed metadata without replacing established core data.
    for key in (
        "bdfutbol_id", "bdfutbol_url", "historical_profile_source", "historical_profile_source_url",
        "historical_position_1993_94", "historical_position_source", "historical_position_source_url",
        "historical_birth_place_text", "historical_birth_state", "birth_territory_country_id",
        "height_cm", "weight_kg",
        "historical_biography_1993_94", "historical_biography_status",
        "historical_biography_source_url", "historical_biography_source_label",
    ):
        if canonical.get(key) in (None, "", [], {}) and duplicate.get(key) not in (None, "", [], {}):
            canonical[key] = deepcopy(duplicate[key])
    for key in ("historical_biographies_1993_94", "represented_selection_history"):
        merged = list(canonical.get(key) or [])
        for item in list(duplicate.get(key) or []):
            if item not in merged:
                merged.append(deepcopy(item))
        if merged:
            canonical[key] = merged

    history = list(canonical.get("identity_merge_history") or [])
    if not any(int(x.get("merged_source_id") or -1) == old_id for x in history):
        history.append({
            "checkpoint": "1.1.3",
            "merged_source_id": old_id,
            "reason": "verified_same_historical_identity_database_hygiene",
            "duplicate_display_name": duplicate.get("display_name"),
            "duplicate_team_id": duplicate.get("team_id"),
        })
    canonical["identity_merge_history"] = history

    duplicate["retired"] = True
    duplicate["historical_exclusion_reason"] = "duplicate_identity_reconciled_v113"
    duplicate["merged_into_source_id"] = new_id
    duplicate["identity_resolution"] = "retired_alias_to_canonical_v113"


def repair_metadata_from_retired_aliases(players: list[dict[str, Any]]) -> int:
    """Backfill source-backed metadata lost before v1.1.3 aliases became canonical-safe."""
    by_id = {int(p["source_id"]): p for p in players}
    fields = (
        "historical_biography_1993_94", "historical_biography_status",
        "historical_biography_source_url", "historical_biography_source_label",
        "historical_profile_source", "historical_profile_source_url",
        "historical_position_source", "historical_position_source_url",
    )
    changed = 0
    for alias in players:
        target_id = alias.get("merged_into_source_id") if alias.get("retired") else None
        if target_id is None:
            continue
        canonical = by_id.get(int(target_id))
        if not canonical or canonical.get("retired"):
            continue
        for key in fields:
            if canonical.get(key) in (None, "", [], {}) and alias.get(key) not in (None, "", [], {}):
                canonical[key] = deepcopy(alias[key])
                changed += 1
    return changed


def auto_exact_merges(players: list[dict[str, Any]]) -> dict[int, int]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for player in players:
        if player.get("retired"):
            continue
        key = (clean(player.get("display_name")), str(player.get("birth_date") or "")[:10])
        if key[0] and key[1]:
            grouped.setdefault(key, []).append(player)
    result: dict[int, int] = {}
    for rows in grouped.values():
        if len(rows) != 2:
            continue
        a, b = rows
        pair = frozenset((int(a["source_id"]), int(b["source_id"])))
        if pair in VERIFIED_DISTINCT:
            continue
        similarity = SequenceMatcher(None, full_name(a), full_name(b)).ratio()
        if similarity < 0.74:
            continue
        # Prefer an established (non-generated) identity, otherwise the lower ID.
        def rank(p: dict[str, Any]) -> tuple[int, int]:
            generated = bool(p.get("external_origin"))
            return (1 if generated else 0, int(p["source_id"]))
        canonical, duplicate = sorted(rows, key=rank)
        result[int(duplicate["source_id"])] = int(canonical["source_id"])
    return result


def ensure_ecuador_container(snapshot: dict[str, Any]) -> int:
    for team in snapshot.get("teams", []):
        if int(team.get("country_id") or 0) == 34 and bool(team.get("market_container")):
            return int(team["source_id"])
    source_id = 9_400_034
    template = next(t for t in snapshot["teams"] if t.get("name") == "Otros-Argentina")
    team = deepcopy(template)
    team.update({
        "source_id": source_id,
        "name": "Otros-Ecuador",
        "long_name": "Otros clubes · Ecuador",
        "short_name": "Otros-Ecuador",
        "familiar_name": "Otros-Ecuador",
        "very_short_name": "Otros-Ecuador",
        "initials": "OC34",
        "country_id": 34,
        "league_id": None,
        "league_position": None,
        "activation_reason": "historical_identity_container_v113",
        "historical_scope": "nonplayable_clubs_1993_94",
        "playable": False,
        "market_container": True,
        "can_buy_players": False,
    })
    snapshot["teams"].append(team)
    return source_id


def restore_branko_milosevic(snapshot: dict[str, Any]) -> int:
    # 9495160 was reused by a later Belgium import for Cvijan Milosevic.  Keep
    # Cvijan on that established ID and restore Branko to a new stable ID.
    target_id = 9_499_000
    if any(int(p.get("source_id") or 0) == target_id for p in snapshot["players"]):
        return target_id
    template = deepcopy(next(p for p in snapshot["players"] if int(p.get("source_id") or 0) == 9495154))
    reviews = json.loads((DATA / "created_player_profile_reviews.json").read_text(encoding="utf-8"))
    review = None
    def find_review(value: Any) -> None:
        nonlocal review
        if review is not None:
            return
        if isinstance(value, dict):
            if int(value.get("source_id") or 0) == 9495160 and value.get("display_name") == "Branko Milošević":
                review = deepcopy(value)
                return
            for v in value.values():
                find_review(v)
        elif isinstance(value, list):
            for v in value:
                find_review(v)
    find_review(reviews)
    attrs = deepcopy((review or {}).get("attributes_after") or template.get("attributes") or {})
    template.update({
        "source_id": target_id,
        "team_id": 9_400_015,
        "display_name": "Branko Milošević",
        "first_name": "Branko",
        "surname1": "Milošević",
        "surname2": None,
        "birth_date": "1964-08-21T00:00:00",
        "birth_country_id": None,
        "international_country_id": 15,
        "shirt_number": None,
        "primary_role": 7,
        "broad_position": "MED",
        "overall": 69,
        "category": 70,
        "attributes": attrs,
        "retired": False,
        "identity_source": "National-Football-Teams · players used by the senior national team in 1993",
        "identity_source_url": "https://www.national-football-teams.com/country/12/1993/Australia.html",
        "historical_data_source": "National-Football-Teams · players used by the senior national team in 1993",
        "attribute_source": "fixed_source_comparable_review_0.23",
        "profile_review_required": False,
        "role_detail_source": "verified_historical_broad_position",
        "historical_club_1994": "Sydney Olympic",
        "historical_position_1993_94": "Midfielder",
        "market_container_origin": "Australia",
        "external_origin": "national_pool_1993_94",
        "creation_batch": "verified_1993_national_pools_0.22",
        "verified_national_pool_year": 1993,
        "verified_national_pool_1993_94": True,
        "verified_era_pool_1993_94": True,
        "source_confidence": "high",
        "historical_context": "Senior Australian international recorded in 1993; ID restored after Belgium import collision v1.1.3",
    })
    if review:
        review.pop("attributes_before", None)
        review.pop("attributes_after", None)
        review["source_id"] = target_id
        template["profile_review_0_23"] = review
    snapshot["players"].append(template)
    return target_id


def normalise_identity_whitespace(players: list[dict[str, Any]]) -> int:
    changed = 0
    for player in players:
        for key in ("display_name", "first_name", "surname1", "surname2"):
            old = player.get(key)
            new = clean_ws(old)
            if new != old:
                player[key] = new
                changed += 1
    return changed


def shorten_russian_names(players: list[dict[str, Any]], team_by_id: dict[int, dict[str, Any]]) -> int:
    """Keep patronymics as historical metadata, never as routine UI names.

    The original cleanup scoped this to players currently in Russia or created by
    the Russian importer.  That missed ex-USSR players already transferred to
    Turkey/Western Europe.  We therefore also shorten any *display* that is the
    exact ``first_name + surname`` form and whose second given-name token is a
    patronymic.  Surname-only legacy displays are intentionally left alone.
    """
    russian_team_ids = {
        tid for tid, team in team_by_id.items()
        if int(team.get("league_id") or 0) == 930015 or int(team.get("country_id") or 0) == 40
    }
    changed = 0
    for player in players:
        text = " ".join(str(player.get(k) or "") for k in (
            "historical_data_source", "historical_profile_source", "creation_batch", "market_container_origin"
        )).lower()
        in_russian_scope = int(player.get("team_id") or 0) in russian_team_ids or "russia" in text or "rusia" in text
        first = clean_ws(player.get("first_name")) or ""
        family = clean_ws(player.get("surname1")) or ""
        display = clean_ws(player.get("display_name")) or ""
        expected_short = short_historical_display_name(player)
        exposes_patronymic = bool(
            first and family and display == f"{first} {family}" and expected_short and expected_short != display
        )
        if (in_russian_scope or exposes_patronymic) and preserve_full_name_and_shorten(player):
            changed += 1
    return changed


def disambiguate_same_team_display(players: list[dict[str, Any]]) -> int:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for player in players:
        if player.get("retired"):
            continue
        key = (int(player.get("team_id") or 0), clean(player.get("display_name")))
        if key[0] and key[1]:
            groups.setdefault(key, []).append(player)
    changed = 0
    for rows in groups.values():
        if len(rows) < 2:
            continue
        proposed: list[str] = []
        for player in rows:
            first = clean_ws(player.get("first_name")) or ""
            surname = clean_ws(player.get("surname1")) or ""
            first_token = first.split()[0] if first else ""
            proposed.append(" ".join(x for x in (first_token, surname) if x).strip())
        if len(set(clean(x) for x in proposed if x)) != len(rows):
            proposed = [" ".join(x for x in (clean_ws(p.get("first_name")) or "", clean_ws(p.get("surname1")) or "", clean_ws(p.get("surname2")) or "") if x).strip() for p in rows]
        for player, new_name in zip(rows, proposed):
            if new_name and clean(new_name) != clean(player.get("display_name")):
                player.setdefault("historical_display_name", player.get("display_name"))
                player["display_name"] = new_name
                player["display_name_resolution"] = "same_team_identity_disambiguation_v113"
                changed += 1
    return changed


def patch_staging(path: Path, aliases: dict[int, int], display_by_id: dict[int, str]) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    def walk(value: Any) -> None:
        nonlocal changed
        if isinstance(value, dict):
            sid = value.get("resolved_source_id")
            if isinstance(sid, int) and sid in aliases:
                new = aliases[sid]
                value["duplicate_source_id_retired"] = sid
                value["resolved_source_id"] = new
                if new in display_by_id:
                    value["resolved_display_name"] = display_by_id[new]
                value["identity_resolution"] = "reconciled_database_hygiene_v113"
                changed += 1
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(payload)
    if changed:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def patch_world_cup_references() -> int:
    path = DATA / "world_cup_1994_squads.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = {9494181: 9496364, 9494201: 9496480, 9494151: 9501277}
    changed = 0
    def walk(value: Any) -> None:
        nonlocal changed
        if isinstance(value, dict):
            sid = value.get("resolved_source_id")
            if isinstance(sid, int) and sid in mapping:
                value["resolved_source_id"] = mapping[sid]
                value["resolution"] = "reconciled_existing_1993_94_identity_v113"
                changed += 1
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def sync_world_cup_metadata_to_snapshot(snapshot_by_id: dict[int, dict[str, Any]]) -> int:
    """Apply World Cup squad metadata to the surviving canonical player IDs."""
    path = DATA / "world_cup_1994_squads.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for team in payload.get("teams", []):
        for row in team.get("players", []):
            sid = int(row.get("resolved_source_id") or 0)
            player = snapshot_by_id.get(sid)
            if not player or player.get("retired"):
                continue
            wc = {
                "team_code": team.get("team_code"),
                "country_id": int(team.get("country_id") or 0),
                "group": team.get("group"),
                "shirt_number": row.get("shirt_number"),
                "position": row.get("position_code"),
                "external_player_id": row.get("external_player_id"),
            }
            if player.get("historical_squad_1994") is not True:
                player["historical_squad_1994"] = True
                changed += 1
            if player.get("world_cup_1994") != wc:
                player["world_cup_1994"] = wc
                changed += 1
    return changed


def retire_empty_market_containers(snapshot: dict[str, Any]) -> list[int]:
    """Hide obsolete Otros-* containers left empty by identity reconciliation."""
    occupied = {int(p.get("team_id") or 0) for p in snapshot.get("players", []) if not p.get("retired")}
    retired = []
    for team in snapshot.get("teams", []):
        tid = int(team.get("source_id") or 0)
        if team.get("market_container") and tid not in occupied:
            team["market_container"] = False
            team["players_transferable"] = False
            team["retired_market_container_v113"] = True
            team["retired_market_container_reason"] = "empty_after_identity_reconciliation"
            retired.append(tid)
    return retired


def patch_branko_source_files(new_id: int) -> int:
    changed = 0
    for path in (DATA / "national_pool_1993_94_additions.json", DATA / "created_player_profile_reviews.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        def walk(value: Any) -> None:
            nonlocal changed
            if isinstance(value, dict):
                if int(value.get("source_id") or 0) == 9495160 and value.get("display_name") == "Branko Milošević":
                    value["source_id"] = new_id
                    value["id_collision_repaired_v113"] = True
                    changed += 1
                for v in value.values():
                    walk(v)
            elif isinstance(value, list):
                for v in value:
                    walk(v)
        walk(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def patch_registry(aliases: dict[int, int], branko_id: int, snapshot_by_id: dict[int, dict[str, Any]]) -> int:
    if not REGISTRY.exists():
        return 0
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = payload.get("players", payload if isinstance(payload, list) else [])
    changed = 0
    for row in rows:
        sid = int(row.get("source_id") or 0)
        if sid in aliases:
            target = aliases[sid]
            if row.get("merged_into_source_id") != target or row.get("retired_alias_v113") is not True:
                row["merged_into_source_id"] = target
                row["retired_alias_v113"] = True
                changed += 1
    if not any(int(r.get("source_id") or 0) == branko_id for r in rows):
        p = snapshot_by_id[branko_id]
        rows.append({
            "source_id": branko_id,
            "display_name": p["display_name"], "first_name": p["first_name"], "surname1": p["surname1"], "surname2": None,
            "birth_date": "1964-08-21", "country_id": 15, "country_name": "Australia", "broad_position": "MED",
            "team_id": 9400015, "team_name": "Otros-Australia", "creation_batch": "verified_1993_national_pools_0.22",
            "identity_source": p["identity_source"], "identity_source_url": p["identity_source_url"],
            "verified_national_pool_year": 1993, "historical_position_1993_94": "Midfielder",
            "historical_club_1994": "Sydney Olympic", "overall": 69, "attribute_source": p["attribute_source"],
            "profile_review_required": False, "duplicate_check": "id_collision_restored_v113", "photo_filename": f"{branko_id}.jpg",
            "photo_status": "pending_identity_profile",
        })
        changed += 1
    REGISTRY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Rebuild the CSV from JSON when possible so IDs cannot diverge.
    if rows:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys and not isinstance(row.get(key), (dict, list)):
                    keys.append(key)
        with REGISTRY_CSV.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k) for k in keys})
    return changed


def reconcile_verified_photo_aliases() -> int:
    """Move verified normalized portraits from retired staging IDs to canonical IDs.

    Historical audit files keep their original source_id for traceability, but the
    active registry/queue and runtime asset must follow the canonical identity.
    """
    changed = 0
    players_dir = ROOT / "frontend" / "public" / "historical9394" / "players"
    for old_id, canonical_id in VERIFIED_PHOTO_ID_REMAP.items():
        old_asset = players_dir / f"{old_id}.jpg"
        canonical_asset = players_dir / f"{canonical_id}.jpg"
        if old_asset.exists():
            if not canonical_asset.exists() or old_asset.read_bytes() != canonical_asset.read_bytes():
                shutil.copy2(old_asset, canonical_asset)
                changed += 1
        for path in (REGISTRY, PHOTO_QUEUE):
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload.get("players", payload if isinstance(payload, list) else [])
            row = next((r for r in rows if int(r.get("source_id") or 0) == canonical_id), None)
            if row is None:
                continue
            if row.get("photo_filename") != f"{canonical_id}.jpg":
                row["photo_filename"] = f"{canonical_id}.jpg"
                changed += 1
            if canonical_asset.exists() and row.get("photo_status") != "bundled_normalized_bdfutbol":
                row["photo_status"] = "bundled_normalized_bdfutbol"
                changed += 1
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def sync_active_identity_fields(snapshot_by_id: dict[int, dict[str, Any]]) -> int:
    """Keep registry/photo queue presentation aligned with canonical active identities."""
    changed = 0
    for path in (REGISTRY,):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("players", payload if isinstance(payload, list) else [])
        for row in rows:
            sid = int(row.get("source_id") or 0)
            player = snapshot_by_id.get(sid)
            if not player or player.get("retired"):
                continue
            keys = ["display_name", "historical_full_name"]
            if sid in PROFILE_CORRECTIONS:
                keys.extend(["historical_position_1993_94", "broad_position", "height_cm", "weight_kg"])
            for key in keys:
                value = player.get(key)
                if value not in (None, "") and row.get(key) != value:
                    row[key] = value
                    changed += 1
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def patch_profile_comparables(aliases: dict[int, int]) -> int:
    path = DATA / "created_player_profile_reviews.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    def walk(value: Any, key: str | None = None) -> None:
        nonlocal changed
        if isinstance(value, dict):
            for k, v in list(value.items()):
                if k in {"source_id", "created_source_id", "matched_existing_id"} and isinstance(v, int) and v in aliases:
                    # Do not rewrite the subject's own retired source_id; registry/audits retain history.
                    if k != "source_id":
                        value[k] = aliases[v]
                        changed += 1
                elif k in {"attribute_comparable_source_ids"} and isinstance(v, list):
                    nv = [aliases.get(int(x), int(x)) if isinstance(x, int) else x for x in v]
                    if nv != v:
                        value[k] = nv; changed += 1
                elif k in {"primary_comparable", "secondary_comparable"} and isinstance(v, dict):
                    sid = v.get("source_id")
                    if isinstance(sid, int) and sid in aliases:
                        v["source_id"] = aliases[sid]; changed += 1
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
    walk(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    players: list[dict[str, Any]] = snapshot["players"]
    before_active = sum(not p.get("retired") for p in players)
    before_total = len(players)
    whitespace_fixed = normalise_identity_whitespace(players)

    ecuador_id = ensure_ecuador_container(snapshot)
    branko_id = restore_branko_milosevic(snapshot)
    team_by_id = {int(t["source_id"]): t for t in snapshot["teams"]}
    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    alias_metadata_repairs = repair_metadata_from_retired_aliases(players)

    merge_map = dict(auto_exact_merges(players))
    merge_map.update(MANUAL_MERGES)
    # Drop rules already reconciled by older checkpoints or missing in a partial dataset.
    merge_map = {old: new for old, new in merge_map.items() if old in by_id and new in by_id and old != new}
    merge_events = []
    for old, new in sorted(merge_map.items()):
        duplicate, canonical = by_id[old], by_id[new]
        if duplicate.get("retired") and int(duplicate.get("merged_into_source_id") or 0) == new:
            continue
        merge_player(canonical, duplicate, team_by_id=team_by_id)
        merge_events.append({"retired_source_id": old, "canonical_source_id": new, "name": canonical.get("display_name")})

    # Eduardo Jaume's old Huracán Buceo assignment belongs to a much later
    # stage of his career, not to 1993-94.  The duplicate row 9782 was a
    # cross-contamination with Eduardo Favaro, a different player.
    if 9718 in by_id:
        by_id[9718]["historical_club_spells_1993_94"] = [
            spell for spell in list(by_id[9718].get("historical_club_spells_1993_94") or [])
            if int(spell.get("team_id") or 0) != 2360
        ]
        by_id[9718]["identity_resolution_note_v113"] = "Racing 1993 identity; Huracán Buceo assignment was from later career and is not an opening-snapshot club."

    # Roberto Oste is one person and his 1993-94 club is Emelec, a non-playable
    # country in this database.  Put him in a truthful market container rather
    # than leaving one of the Argentine duplicate clubs as the active identity.
    if 7283 in by_id:
        CURRENT_TEAM_OVERRIDES[7283] = ecuador_id
        by_id[7283]["historical_club_1994"] = "Emelec"
        by_id[7283]["market_container_origin"] = "Ecuador"
        by_id[7283]["historical_context_v113"] = "1993-94 club Emelec; stored in non-playable Otros-Ecuador container"

    # Same-season duplicate staging rows are one person with multiple club spells.
    if 9496515 in by_id:
        add_spell(by_id[9496515], team_id=9357010, club="Kayserispor", source="opening_club_v113")
        add_spell(by_id[9496515], team_id=9357009, club="Ankaragücü", source="in_season_transfer_nov_1993_v113")
        by_id[9496515]["in_season_transfer_note_v113"] = "Kayserispor -> Ankaragücü, November 1993"
    if 9496672 in by_id:
        add_spell(by_id[9496672], team_id=9315004, club="Lokomotiv Moskva", source="opening_club_v113")
        add_spell(by_id[9496672], team_id=466, club="KSV Waregem", source="in_season_transfer_dec_1993_v113")
        by_id[9496672]["in_season_transfer_note_v113"] = "Lokomotiv Moskva -> KSV Waregem, December 1993"

    club_corrections = []
    for sid, tid in CURRENT_TEAM_OVERRIDES.items():
        player = by_id.get(sid)
        if not player:
            continue
        old_team = int(player.get("team_id") or 0)
        if old_team and team_name(team_by_id, old_team) and sid != 9718:
            add_spell(player, team_id=old_team, club=team_name(team_by_id, old_team) or "", source="pre_v113_snapshot")
        elif old_team and sid == 9718:
            later = list(player.get("historical_club_spells_later") or [])
            row = {"club": team_name(team_by_id, old_team) or "Huracán Buceo", "team_id": old_team, "season": "later_career", "source": "identity_reconciliation_v113"}
            if row not in later:
                later.append(row)
            player["historical_club_spells_later"] = later
        player["team_id"] = tid
        club = team_name(team_by_id, tid)
        if club and sid != 7283:
            player["historical_club_1994"] = club
        player["snapshot_club_resolution"] = "verified_1993_94_chronology_v113"
        add_spell(player, team_id=tid, club=club or player.get("historical_club_1994") or "", source="snapshot_club_v113")
        if old_team != tid:
            club_corrections.append({"source_id": sid, "display_name": player.get("display_name"), "from_team_id": old_team, "to_team_id": tid, "to_team": club})

    profile_corrections = []
    for sid, fields in PROFILE_CORRECTIONS.items():
        player = by_id.get(sid)
        if not player:
            continue
        changed_fields = {}
        for key, value in fields.items():
            if player.get(key) != value:
                changed_fields[key] = {"before": player.get(key), "after": value}
                player[key] = value
        if changed_fields:
            profile_corrections.append({"source_id": sid, "display_name": player.get("display_name"), "fields": changed_fields})

    # A few legacy rows carried a valid tactical role but no broad category.
    # Fill only the missing field; never overwrite a sourced category here.
    missing_broad_repairs = []
    for player in players:
        if player.get("retired") or player.get("broad_position"):
            continue
        role = int(player.get("primary_role") or -1)
        broad = ROLE_TO_BROAD_FALLBACK.get(role)
        if broad:
            player["broad_position"] = broad
            player["position_resolution_v113"] = "derived_from_existing_primary_role_missing_broad_position"
            missing_broad_repairs.append({"source_id": int(player["source_id"]), "display_name": player.get("display_name"), "primary_role": role, "broad_position": broad})

    russian_shortened = shorten_russian_names(players, team_by_id)
    same_team_disambiguated = disambiguate_same_team_display(players)

    # Staging must resolve to the surviving identities, otherwise re-running an
    # importer would recreate the same duplicate.
    aliases = dict(merge_map)
    aliases.update(STAGING_ID_REMAP)
    display_by_id = {int(p["source_id"]): str(p.get("display_name") or "") for p in players}
    staging_changed = 0
    for name in ("russia_1993_roster_staging.json", "turkey_1993_94_roster_staging.json", "greece_1993_94_roster_staging.json", "belgium_1993_94_roster_staging.json"):
        staging_changed += patch_staging(DATA / name, aliases, display_by_id)

    wc_refs = patch_world_cup_references()
    wc_metadata_sync = sync_world_cup_metadata_to_snapshot(by_id)
    retired_empty_containers = retire_empty_market_containers(snapshot)
    branko_refs = patch_branko_source_files(branko_id)
    profile_refs = patch_profile_comparables(aliases)

    # Snapshot source counts are descriptive rather than a fixed contract; keep
    # a direct v1.1.3 audit block instead of rewriting historical checkpoint counts.
    after_active = sum(not p.get("retired") for p in players)
    snapshot.setdefault("database_hygiene", {})["v1.1.3"] = {
        "active_players_before": before_active,
        "active_players_after": after_active,
        "total_rows_before": before_total,
        "total_rows_after": len(players),
        "retired_aliases_added": len(merge_events),
        "russian_display_names_shortened": russian_shortened,
        "identity_whitespace_fields_cleaned": whitespace_fixed,
        "alias_metadata_repairs": alias_metadata_repairs,
        "same_team_display_names_disambiguated": same_team_disambiguated,
        "branko_milosevic_restored_source_id": branko_id,
        "otros_ecuador_team_id": ecuador_id,
        "world_cup_references_reconciled": wc_refs,
        "world_cup_metadata_synced": wc_metadata_sync,
        "empty_market_containers_retired": retired_empty_containers,
    }
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    registry_changes = patch_registry(aliases, branko_id, by_id)
    photo_alias_changes = reconcile_verified_photo_aliases()
    registry_identity_sync_changes = sync_active_identity_fields(by_id)

    report = {
        "checkpoint": "1.1.3",
        "status": "applied",
        "active_players_before": before_active,
        "active_players_after": after_active,
        "total_player_rows": len(players),
        "verified_identity_merges": merge_events,
        "verified_identity_merge_count": len(merge_events),
        "retired_aliases_total": sum(bool(p.get("retired")) and p.get("merged_into_source_id") is not None for p in players),
        "retired_market_containers_total": [int(t["source_id"]) for t in snapshot.get("teams", []) if t.get("retired_market_container_v113")],
        "verified_distinct_pairs": [sorted(x) for x in sorted(VERIFIED_DISTINCT, key=lambda s: min(s))],
        "club_corrections": club_corrections,
        "russian_display_names_shortened": russian_shortened,
        "identity_whitespace_fields_cleaned": whitespace_fixed,
        "alias_metadata_repairs": alias_metadata_repairs,
        "same_team_display_names_disambiguated": same_team_disambiguated,
        "staging_references_reconciled": staging_changed,
        "world_cup_references_reconciled": wc_refs,
        "world_cup_metadata_synced": wc_metadata_sync,
        "empty_market_containers_retired": retired_empty_containers,
        "branko_source_references_repaired": branko_refs,
        "profile_comparable_references_repaired": profile_refs,
        "registry_rows_touched": registry_changes,
        "verified_photo_alias_changes": photo_alias_changes,
        "registry_identity_sync_changes": registry_identity_sync_changes,
        "profile_corrections": profile_corrections,
        "missing_broad_position_repairs": missing_broad_repairs,
        "notes": [
            "retired aliases remain in historical_snapshot for save/reference safety but are excluded from runtime squads/market",
            "Russian patronymics are preserved in historical_full_name and no longer used as routine display_name",
            "Russia 1993 participation does not overwrite the post-summer European 1993-94 starting club",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"verified_identity_merges", "club_corrections", "verified_distinct_pairs"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
