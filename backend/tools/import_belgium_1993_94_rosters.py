from __future__ import annotations

"""Close the historical Belgium 1993-94 roster gate and activate league 930052.

This is an offline curation/import step. It does not invent runtime rating rules:
all added attributes and specialist roles are materialised into the snapshot.
"""

from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import hashlib
import json
import re
import sys
import unicodedata
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.football9394.mdb_jet4 import Jet4MDB
from tools.review_created_player_profiles import ATTRS, materialise_attributes

DATA = ROOT / "data" / "football9394"
SNAP_PATH = DATA / "historical_snapshot.json"
STAGE_PATH = DATA / "belgium_1993_94_roster_staging.json"
FOUNDATION_PATH = DATA / "bel_tur_rus_1993_94_league_foundations.json"
ASSETS_PATH = DATA / "belgium_1993_94_club_assets.json"
REGISTRY_PATH = DATA / "created_players_registry.json"
AUDIT_PATH = DATA / "belgium_1993_94_roster_gate_audit.json"
MDB_PATH = Path("/mnt/data/m9394_source/basedatos(1).mdb")

LEAGUE_ID = 930052
BELGIUM_ID = 17
OTHER_BELGIUM_ID = 9400017
CREATION_BATCH = "belgium_league_rosters_0.25"


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().lower()
    return re.sub(r"\s+", " ", text)


def birth_year(value: Any) -> int | None:
    if isinstance(value, datetime):
        return value.year
    try:
        return int(str(value or "")[:4])
    except (ValueError, TypeError):
        return None


def age_ok(age: int | None, year: int | None) -> bool:
    if age is None or year is None:
        return False
    # BDF age is season-row age, so either calendar side of 1993-94 is valid.
    return year in {1993 - age, 1994 - age}


# Seven genuine same-season two-club rows. One person is kept; the opening club
# is used as the initial 1993-94 membership and both spells remain in provenance.
TRANSFER_GROUPS = {
    "nwanu": {"opening": "Beveren", "clubs": ("Beveren", "Anderlecht")},
    "schepens": {"opening": "Gent", "clubs": ("Gent", "Standard Liège")},
    "pister": {"opening": "Standard Liège", "clubs": ("Standard Liège", "Gent")},
    "urban": {"opening": "Waregem", "clubs": ("Waregem", "KV Mechelen")},
    "abeels": {"opening": "Waregem", "clubs": ("Waregem", "Germinal Ekeren")},
    "ballenghien": {"opening": "Waregem", "clubs": ("Waregem", "Germinal Ekeren")},
    "ernes": {"opening": "RFC Liège", "clubs": ("RFC Liège", "Molenbeek")},
}

# Only raw-MDB identities explicitly verified against the 1993-94 player are
# eligible for reuse. Generic matching is deliberately limited to the curated
# historical/imported pool (source ids >= 9490000) to prevent homonym reuse.
SAFE_RAW_MDB_IDS = {2830, 2565, 6792, 2777, 4929, 6387}
EXISTING_OVERRIDES = {
    "preud homme": 2830,
    "molby": 2565,
    "berghuis": 6792,
    "jakobsen": 2777,
    "edmilson": 4929,
    "remy": 6387,
}

# Profiles for which the exact specialist role is source-backed or historically
# well established. All other starters are inferred from BDF's position-ordered
# first XI and explicitly labelled as inference in the audit.
ROLE_OVERRIDES = {
    # Anderlecht
    "de wilde": 0, "crasson": 1, "de wolf": 2, "albert@anderlecht": 3,
    "rutjes": 4, "boffin": 13, "versavel@anderlecht": 13, "walem": 7,
    "zetterberg": 8, "bosman": 17, "nilis": 17, "maes@anderlecht": 0,
    "haagdoren": 13, "degryse": 8, "emmers": 7, "kooiman": 3,
    "nwanu": 3, "suray": 3, "preko": 17, "marchoul": 1,
    "musonda": 7, "asare": 6, "peiremans": 7,
    # Club Brugge / internationals
    "verlinden": 0, "medved": 1, "borkelmans": 2, "renier": 3,
    "plovie": 4, "staelens": 6, "van der heyden": 13, "verheyen": 12,
    "okon": 7, "amokachi": 17, "eijkelkamp": 17, "van der elst": 7,
    # Other source-backed internationals
    "van meir": 3, "smidts": 3, "severeyns": 17, "bodart": 0,
    "genaux": 1, "wilmots": 8, "goossens@standard liege": 17,
    "stelea": 0, "bettagno": 9, "preud homme": 0, "de boeck": 3,
    "czerniatynski": 17, "molby": 6, "hofmans": 17, "selymes": 2,
    "munteanu": 13, "weber": 17, "oliseh": 7, "arnold": 17,
    "rekdal": 7, "jakobsen": 16, "de nil": 13, "dauwen": 3,
    "keshi": 3, "vidmar": 17, "berghuis": 16, "remy": 17, "edmilson": 17,
}

FULL_NAMES = {
    "maes@anderlecht": "Peter Maes", "rutjes": "Graeme Rutjes",
    "zetterberg": "Pär Zetterberg", "haagdoren": "Philip Haagdoren",
    "kooiman": "Wim Kooiman", "suray": "Olivier Suray", "preko": "Yaw Preko",
    "marchoul": "Guy Marchoul", "musonda": "Charly Musonda",
    "peiremans": "Frédéric Peiremans", "molby": "Johnny Mølby",
    "nwanu": "Chidi Nwanu", "schepens": "Gunther Schepens",
    "pister": "Thierry Pister", "urban": "Flórián Urbán",
    "abeels": "Jean-Marie Abeels", "ernes": "Luc Ernès",
    "peeters@lierse": "Bob Peeters", "peeters@lommel@19": "Bart Peeters",
    "berghuis": "Frank Berghuis", "jakobsen": "Jahn Ivar Jakobsen",
    "remy": "Jacques Remy",
}

# BDF ids confirmed through individual historical player pages. These are used
# for traceable portrait download/normalisation after the data import.
BDF_IDS = {
    "de wilde@anderlecht": 89371, "crasson": 99629, "rutjes": 46192, "versavel@anderlecht": 46191,
    "nilis": 93902, "maes@anderlecht": 98416, "haagdoren": 99667,
    "degryse": 99316, "emmers": 46194, "kooiman": 97393, "suray": 99670,
    "marchoul": 42447, "musonda": 42448, "asare": 99947, "peiremans": 2857,
    "nwanu": 99668, "schepens": 98424, "pister": 65661, "urban": 68620,
    "peeters@lierse": 85779, "peeters@lommel@19": 68582,
}

# Conservative nationality curation for obvious/verified foreign players. Unknown
# nationalities are left unset instead of silently being asserted as Belgian.
NATIONALITY = {
    "rutjes": 3, "zetterberg": 79, "bosman": 3, "kooiman": 3, "nwanu": 59,
    "preko": 42, "asare": 42,
    "okon": 15, "amokachi": 59, "eijkelkamp": 3, "disztl": 93, "dziubinski": 70,
    "edmilson": 62, "wamberto": 62, "karagiannis": 47, "varga": 93,
    "janevski": 75, "balog": 93, "misse misse": 66, "malbasa": 75,
    "gulyas": 93, "silvagni": 63,
    "svilar": 75, "lehnhoff": 4, "bursac": 75, "kulcsar": 93,
    "aloisi": 15, "jakovljevic": 75,
    "rednic": 72, "andre cruz": 62, "rytchkov": 40, "stelea": 72, "van rooy": 3,
    "swietek": 70, "eszenyi": 93, "molby": 33, "urban": 93, "arambasic": 31,
    "tahamata": 3, "halmai": 93, "buia": 72, "jussila": 41,
    "berghuis": 3, "gorter": 3,
    "selymes": 72, "munteanu": 72, "cheregi": 72, "hanganu": 72,
    "weber": 31, "longo": 15,
    "oliseh": 59, "arnold": 15, "milosevic": 75,
    "rekdal": 60, "lankhaar": 3, "jakobsen": 60,
    "verkuyl": 3, "viscaal": 3, "booy": 3, "karacic": 31, "ramcic": 75,
    "rubenilson": 62, "lorincz": 93, "keshi": 59,
    "kruzen": 3, "vidmar": 15, "atteveld": 3,
    "sarpong": 42, "nwachukwu": 59,
}

# Existing players whose role detail was previously broad or wrong.
HISTORICAL_POSITION_TO_ROLE = {
    "goalkeeper": 0, "right back": 1, "left back": 2, "centre back": 3,
    "central defender": 3, "defensive midfielder": 6, "centre midfielder": 7,
    "central midfielder": 7, "attacking midfielder": 8, "right midfielder": 9,
    "right winger": 12, "left midfielder": 13, "left winger": 16,
    "centre forward": 17, "center forward": 17, "forward": 17,
}

ROLE_TO_BROAD = {0: "POR", 1: "DEF", 2: "DEF", 3: "DEF", 4: "DEF", 5: "DEF",
                 6: "MED", 7: "MED", 8: "MED", 9: "MED", 10: "MED", 11: "DEL",
                 12: "DEL", 13: "MED", 14: "MED", 15: "DEL", 16: "DEL", 17: "DEL"}
ROLE_TO_LABEL = {0:"Goalkeeper",1:"Right Back",2:"Left Back",3:"Centre Back",4:"Centre Back",
                 5:"Sweeper",6:"Defensive Midfielder",7:"Centre Midfielder",8:"Attacking Midfielder",
                 9:"Right Midfielder",10:"Right Inside",11:"Right Attacking Midfielder",12:"Right Winger",
                 13:"Left Midfielder",14:"Left Inside",15:"Left Attacking Midfielder",16:"Left Winger",17:"Centre Forward"}

# First eleven on BDF is position-grouped and is a better fallback than a generic
# DEF/MED/DEL label. It is explicitly tagged as inference, never as a verified fact.
XI_ROLE_FALLBACK = (0, 1, 3, 4, 2, 9, 7, 7, 13, 17, 17)

CLUB_BASE = {1:74,2:73,3:72,4:71,5:71,6:71,7:69,8:70,9:69,10:69,11:69,12:68,13:68,14:68,15:68,16:67,17:66,18:66}


def identity_lookup_key(club: str, row: dict[str, Any]) -> str:
    name = norm(row["bdfutbol_name"])
    if name == "preud homme":
        return name
    if name == "de wilde" and club == "Anderlecht":
        return "de wilde@anderlecht"
    if name == "albert" and club == "Anderlecht":
        return "albert@anderlecht"
    if name == "versavel" and club == "Anderlecht":
        return "versavel@anderlecht"
    if name == "goossens" and club == "Standard Liège":
        return "goossens@standard liege"
    if name == "maes" and club == "Anderlecht":
        return "maes@anderlecht"
    if name == "peeters" and club == "Lierse":
        return "peeters@lierse"
    if name == "peeters" and club == "Lommel" and int(row.get("age_1993_94") or -1) == 19:
        return "peeters@lommel@19"
    return name


def exact_role_ratings(role: int) -> dict[str, int]:
    out = {str(i): 0 for i in range(18)}
    out[str(role)] = 100
    adjacent = {
        0:{}, 1:{3:60,9:55}, 2:{4:60,13:55}, 3:{4:75,5:60,6:45},
        4:{3:75,5:60,6:45}, 5:{3:75,4:75,6:60}, 6:{7:75,3:50,4:50},
        7:{6:70,8:65,9:45,13:45}, 8:{7:65,11:55,15:55,17:45},
        9:{12:75,7:55,8:50,1:45}, 10:{9:80,12:65,7:55},
        11:{12:80,9:65,8:65,17:50}, 12:{9:75,11:65,17:50},
        13:{16:75,7:55,8:50,2:45}, 14:{13:80,16:65,7:55},
        15:{16:80,13:65,8:65,17:50}, 16:{13:75,15:65,17:50},
        17:{11:45,15:45,12:35,16:35,8:30},
    }
    for rid, val in adjacent.get(role, {}).items():
        out[str(rid)] = val
    return out


def safe_existing_match(players: list[dict[str, Any]], club: str, row: dict[str, Any]) -> dict[str, Any] | None:
    key = identity_lookup_key(club, row)
    override = EXISTING_OVERRIDES.get(key)
    if override:
        hit = next((p for p in players if int(p.get("source_id") or 0) == override), None)
        if hit:
            return hit
    n = norm(row["bdfutbol_name"])
    age = int(row.get("age_1993_94")) if row.get("age_1993_94") is not None else None
    hits = []
    for p in players:
        source_id = int(p.get("source_id") or 0)
        if source_id < 9490000 and source_id not in SAFE_RAW_MDB_IDS:
            continue
        year = birth_year(p.get("birth_date"))
        if not age_ok(age, year):
            continue
        variants = {norm(p.get("surname1")), norm(p.get("surname2")), norm(p.get("display_name"))}
        # Surname must be exact. A substring/display-name only match is not safe.
        if n and n in variants:
            hits.append(p)
    uniq = {int(p["source_id"]): p for p in hits}
    return next(iter(uniq.values())) if len(uniq) == 1 else None


def split_display(display: str) -> tuple[str | None, str | None]:
    parts = display.strip().split()
    if len(parts) <= 1:
        return None, display.strip() or None
    return " ".join(parts[:-1]), parts[-1]


def target_overall(position: int, row: dict[str, Any]) -> int:
    base = CLUB_BASE[position]
    starts = int(row.get("starts") or 0); apps = int(row.get("appearances") or 0); goals = int(row.get("goals") or 0)
    if starts >= 24: base += 2
    elif starts >= 15: base += 1
    elif apps < 8: base -= 2
    elif apps < 15: base -= 1
    if goals > 0:
        if goals >= 15: base += 2
        elif goals >= 7: base += 1
    return max(61, min(79, base))


def choose_attrs(originals: list[dict[str, Any]], player: dict[str, Any], overall: int, serial: int) -> tuple[dict[str, int], list[int]]:
    broad = player["broad_position"]
    pool = [p for p in originals if p.get("broad_position") == broad and p.get("attributes") and abs(int(p.get("overall") or 0)-overall) <= 5]
    pool.sort(key=lambda p:(abs(int(p.get("overall") or 0)-overall), int(p.get("source_id") or 0)))
    if len(pool) < 2:
        pool = [p for p in originals if p.get("broad_position") == broad and p.get("attributes")]
        pool.sort(key=lambda p:(abs(int(p.get("overall") or 0)-overall), int(p.get("source_id") or 0)))
    if len(pool) < 2:
        raise RuntimeError(f"No source-backed comparables for {player['display_name']} / {broad}")
    # Deterministic variety while staying close to the historical source scale.
    a = pool[(serial * 7) % min(len(pool), 24)]
    b = pool[(serial * 13 + 5) % min(len(pool), 24)]
    if int(a["source_id"]) == int(b["source_id"]):
        b = pool[(pool.index(a) + 1) % min(len(pool), 24)]
    attrs = materialise_attributes(overall, a, b)
    digest = hashlib.sha256(player["display_name"].encode("utf-8")).digest()
    # Tiny individual deviations avoid cloned vectors without changing tier.
    for i, attr in enumerate(("consistency", "work_rate", "anticipation", "technique")):
        delta = (-1, 0, 1)[digest[i] % 3]
        attrs[attr] = max(20, min(99, int(attrs[attr]) + delta))
    return attrs, [int(a["source_id"]), int(b["source_id"])]


def make_team_from_mdb(raw: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    def i(v):
        try:return int(v) if v is not None else None
        except:return None
    return {
        "source_id": int(asset["team_id"]),
        "name": str(raw.get("Nombre") or asset["name"]),
        "long_name": str(raw.get("NombreLargo") or raw.get("Nombre") or asset["name"]),
        "short_name": str(raw.get("NombreCorto") or asset["name"]),
        "initials": str(raw.get("Siglas")) if raw.get("Siglas") else None,
        "league_id": LEAGUE_ID, "league_position": int(asset["historical_position"]),
        "stadium_id": i(raw.get("Estadio")), "manager_id": None,
        "members": i(raw.get("Socios")) or 0, "budget": i(raw.get("Presupuesto")) or 0,
        "debt": None, "reserve_of": None, "reserve_step": 0,
        "academy_level": i(raw.get("Nivel_cantera")) or 1,
        "squad_building_style": i(raw.get("Confeccion_plantilla")) or 2,
        "sporting_director_level": i(raw.get("Secretario_tecnico_estrella")) or 0,
        "women_flag": False, "activation_reason": "historical_belgium_1993_94_roster_gate",
        "familiar_name": str(raw.get("NombreFamiliar")) if raw.get("NombreFamiliar") else asset["name"],
        "very_short_name": str(raw.get("NombreMuyCorto")) if raw.get("NombreMuyCorto") else asset["name"],
        "president": None, "secondary_stadium_id": i(raw.get("EstadioSecundario")),
        "training_ground": None, "youth_residence": None,
        "main_rival_id": i(raw.get("MaximoRival")), "regional_rival_id": i(raw.get("MaximoRivalRegional")),
        "honours": {
            "intercontinental": i(raw.get("PalmaresIntercontinentales")) or 0,
            "continental": i(raw.get("PalmaresContinentales")) or 0,
            "continental_2": i(raw.get("PalmaresContinentales2")) or 0,
            "continental_3": i(raw.get("PalmaresContinentales3")) or 0,
            "continental_4": i(raw.get("PalmaresContinentales4")),
            "continental_supercups": i(raw.get("PalmaresSuperCopasContinentales")) or 0,
            "national_leagues": i(raw.get("PalmaresLigasNacionales")) or 0,
            "national_cups": i(raw.get("PalmaresCopasNacionales")) or 0,
            "national_cups_2": i(raw.get("PalmaresCopasNacionales2")),
            "national_supercups": i(raw.get("PalmaresSuperCopasNacionales")) or 0,
        },
        "academy_style": i(raw.get("Estilo_cantera")) or 2,
        "special_academy_pattern_id": None, "initial_points_sanction": None,
        "fifa_registration_ban_until": None, "country_id": BELGIUM_ID,
        "historical_season": "1993-94", "historical_position": int(asset["historical_position"]),
        "historical_identity_source": "BDFutbol 1993-94 squad and supplied MDB same-club identity",
    }


def make_historical_team(asset: dict[str, Any]) -> dict[str, Any]:
    pos = int(asset["historical_position"])
    budgets = {1:45000000,2:40000000,3:18000000,4:20000000,5:22000000,6:34000000,7:12000000,8:26000000}
    name = asset["name"]
    initials = "".join(word[0] for word in name.replace("-"," ").split()[:3]).upper()
    return {
        "source_id": int(asset["team_id"]), "name": name, "long_name": name,
        "short_name": name, "initials": initials or name[:3].upper(),
        "league_id": LEAGUE_ID, "league_position": pos, "stadium_id": None,
        "manager_id": None, "members": 0, "budget": budgets.get(pos, 9000000), "debt": None,
        "reserve_of": None, "reserve_step": 0, "academy_level": 1, "squad_building_style": 2,
        "sporting_director_level": 0, "women_flag": False,
        "activation_reason": "historical_belgium_1993_94_roster_gate",
        "familiar_name": name, "very_short_name": name, "president": None,
        "secondary_stadium_id": None, "training_ground": None, "youth_residence": None,
        "main_rival_id": None, "regional_rival_id": None, "honours": {}, "academy_style": 2,
        "special_academy_pattern_id": None, "initial_points_sanction": None,
        "fifa_registration_ban_until": None, "country_id": BELGIUM_ID,
        "historical_season": "1993-94", "historical_position": pos,
        "historical_identity_source": "historical-only club id; BDFutbol 1993-94 squad/crest source",
    }


def main() -> None:
    snapshot = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    stage = json.loads(STAGE_PATH.read_text(encoding="utf-8"))
    foundation = json.loads(FOUNDATION_PATH.read_text(encoding="utf-8"))
    assets = json.loads(ASSETS_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    mdb = Jet4MDB(MDB_PATH)
    raw_teams = {int(r["Id"]): r for r in mdb.rows("Equipo") if isinstance(r.get("Id"), int)}

    players = snapshot["players"]
    by_id = {int(p["source_id"]): p for p in players}
    asset_by_name = {a["name"]: a for a in assets["clubs"]}
    team_by_name = {a["name"]: int(a["team_id"]) for a in assets["clubs"]}
    belgian_team_ids = set(team_by_name.values())

    # Replace old/mixed-era memberships, but preserve records for other historical uses.
    mixed_era_excluded = 0
    for p in players:
        if int(p.get("team_id") or 0) in belgian_team_ids:
            p["retired"] = True
            p["historical_exclusion_reason"] = "mixed_era_mdb_not_1993_94"
            mixed_era_excluded += 1

    # Build one identity object for each genuine person.
    identities: dict[str, dict[str, Any]] = {}
    row_to_identity: dict[tuple[str, str, int], str] = {}
    for club in stage["clubs"]:
        cname = club["name"]
        for index, row in enumerate(club["players"]):
            n = norm(row["bdfutbol_name"])
            age = int(row.get("age_1993_94") or -1)
            if n in TRANSFER_GROUPS and cname in TRANSFER_GROUPS[n]["clubs"]:
                ikey = f"transfer:{n}"
            else:
                ikey = f"{norm(cname)}:{n}:{age}"
            row_to_identity[(cname, n, age)] = ikey
            entry = identities.setdefault(ikey, {"rows": [], "name": n})
            entry["rows"].append((cname, index, row))

    originals = [p for p in players if not p.get("external_origin") and not p.get("creation_batch")]
    next_id = max(max(by_id), 9495999) + 1
    used_vectors = {tuple(int((p.get("attributes") or {}).get(k, -1)) for k in ATTRS) for p in players if p.get("attributes")}
    reused = 0; created = 0; role_sources = Counter(); photo_ready = 0
    registry_by_id = {int(r["source_id"]): r for r in registry["players"] if r.get("source_id") is not None}
    identity_records = []

    # Process higher-usage identity representative first for stable role/overall choice.
    for serial, (ikey, ident) in enumerate(sorted(identities.items())):
        rows = ident["rows"]
        representative = max(rows, key=lambda item:(int(item[2].get("starts") or 0), int(item[2].get("appearances") or 0), int(item[2].get("minutes") or 0)))
        rep_club, rep_index, rep_row = representative
        n = ident["name"]
        lookup = identity_lookup_key(rep_club, rep_row)
        if ikey.startswith("transfer:"):
            opening_club = TRANSFER_GROUPS[n]["opening"]
            # use that club's row for the initial profile when present
            opening_rows = [x for x in rows if x[0] == opening_club]
            if opening_rows:
                rep_club, rep_index, rep_row = opening_rows[0]
                lookup = identity_lookup_key(rep_club, rep_row)
        else:
            opening_club = rep_club

        player = safe_existing_match(players, rep_club, rep_row)
        # Transfer groups can be found through either club's row.
        if player is None and ikey.startswith("transfer:"):
            for c, _, r in rows:
                player = safe_existing_match(players, c, r)
                if player is not None:
                    break

        role = ROLE_OVERRIDES.get(lookup)
        role_source = None
        if player is not None:
            hist = norm(player.get("historical_position_1993_94"))
            if hist in HISTORICAL_POSITION_TO_ROLE:
                role = HISTORICAL_POSITION_TO_ROLE[hist]
                role_source = "existing_historical_position"
        if role is not None and role_source is None:
            role_source = "curated_historical_role"
        if role is None:
            if int(rep_row.get("goals") or 0) < 0:
                role = 0; role_source = "bdfutbol_goalkeeper_stat"
            elif rep_index < 11:
                role = XI_ROLE_FALLBACK[rep_index]; role_source = "bdfutbol_lineup_order_inference"
            else:
                # Conservative deterministic role fill for non-starting squad players.
                goals = int(rep_row.get("goals") or 0)
                apps = int(rep_row.get("appearances") or 0)
                if goals >= max(5, int(apps * .25)):
                    role = 17
                else:
                    cycle = (3,4,1,2,7,6,9,13,8,17,12,16)
                    role = cycle[(rep_index - 11 + serial) % len(cycle)]
                role_source = "squad_balance_inference"
        role_sources[role_source] += 1
        broad = ROLE_TO_BROAD[role]

        if player is None:
            source_id = next_id; next_id += 1
            display = FULL_NAMES.get(lookup) or str(rep_row["bdfutbol_name"])
            first, surname = split_display(display)
            nationality = NATIONALITY.get(lookup, NATIONALITY.get(n))
            overall = target_overall(int(asset_by_name[opening_club]["historical_position"]), rep_row)
            player = {
                "source_id": source_id, "team_id": team_by_name[opening_club], "display_name": display,
                "first_name": first, "surname1": surname, "surname2": None, "birth_date": None,
                "birth_country_id": nationality, "international_country_id": nationality,
                "preferred_foot": None, "shirt_number": None, "primary_role": role,
                "broad_position": broad, "overall": overall, "category": overall,
                "height_cm": None, "weight_kg": None, "salary": 0, "release_clause": 0,
                "contract_start_year": 1993, "contract_end_year": None, "loan": False,
                "initially_reserve": int(rep_row.get("starts") or 0) < 8, "retired": False,
                "attributes": {}, "role_ratings": exact_role_ratings(role),
                "hidden_traits": {"individualist":False,"killer_pass":False,"holds_ball":False,"long_shots":False,"cuts_inside":False,"first_time_play":False,"dives":False},
                "external_origin": "historical_belgium_1993_94", "creation_batch": CREATION_BATCH,
                "profile_review_required": False,
            }
            attrs, comps = choose_attrs(originals, player, overall, serial)
            vector = tuple(attrs[k] for k in ATTRS)
            bump = 0
            while vector in used_vectors:
                key = ATTRS[(serial + bump) % len(ATTRS)]
                attrs[key] = min(99, attrs[key] + 1)
                vector = tuple(attrs[k] for k in ATTRS); bump += 1
            used_vectors.add(vector)
            player["attributes"] = attrs
            player["attribute_source"] = "fixed_source_comparable_belgium_1993_94"
            player["attribute_comparable_source_ids"] = comps
            players.append(player); by_id[source_id] = player; created += 1
        else:
            source_id = int(player["source_id"]); reused += 1
            # Correct role specialisation when the historical evidence is finer than prior pool data.
            player["primary_role"] = role; player["broad_position"] = broad
            player["role_ratings"] = exact_role_ratings(role)
            player["retired"] = False
            player.pop("historical_exclusion_reason", None)

        # Apply 1993-94 club and auditable identity data to both reused and created players.
        player["team_id"] = team_by_name[opening_club]
        player["historical_club_1994"] = opening_club
        player["historical_position_1993_94"] = ROLE_TO_LABEL[role]
        player["historical_position_source"] = role_source
        player["bdfutbol_name_1993_94"] = rep_row["bdfutbol_name"]
        player["historical_age_1993_94"] = int(rep_row.get("age_1993_94") or -1)
        player["historical_club_spells_1993_94"] = [
            {"club": c, "team_id": team_by_name[c], "appearances": int(r.get("appearances") or 0),
             "starts": int(r.get("starts") or 0), "minutes": int(r.get("minutes") or 0), "goals": int(r.get("goals") or 0)}
            for c, _, r in rows
        ]
        player["historical_data_source"] = "BDFutbol 1993-94 squad page; identity/position audit v0.25"
        player["bdfutbol_squad_url"] = asset_by_name[rep_club]["bdfutbol_squad_url"]
        bdf_id = BDF_IDS.get(lookup, BDF_IDS.get(n))
        if bdf_id:
            player["bdfutbol_id"] = int(bdf_id)
            player["bdfutbol_url"] = f"https://www.bdfutbol.com/en/j/j{bdf_id}.html"
            photo_ready += 1

        # Persist per-stage-row resolution; transfer rows point to same source id.
        for c, _, r in rows:
            r["identity_resolution"] = "reused_snapshot_safe" if source_id < 9496000 else "created_historical_identity"
            r["resolved_source_id"] = source_id
            r["resolved_display_name"] = player["display_name"]
            r["resolved_primary_role"] = role
            r["resolved_exact_position"] = ROLE_TO_LABEL[role]
            r["position_source"] = role_source
            r["opening_club_1993_94"] = opening_club
            if bdf_id: r["bdfutbol_id"] = int(bdf_id)

        reg = registry_by_id.get(source_id)
        if not (player.get("external_origin") or player.get("creation_batch")):
            if reg is not None:
                registry["players"].remove(reg); registry_by_id.pop(source_id, None)
            reg = None
        elif reg is None:
            reg = {"source_id":source_id}; registry["players"].append(reg); registry_by_id[source_id] = reg
        if reg is not None:
            reg.update({
            "display_name": player["display_name"], "first_name": player.get("first_name"),
            "surname1": player.get("surname1"), "surname2": player.get("surname2"),
            "birth_date": player.get("birth_date"), "country_id": player.get("international_country_id") or player.get("birth_country_id"),
            "country_name": "Bélgica" if (player.get("international_country_id") or player.get("birth_country_id")) == BELGIUM_ID else None,
            "broad_position": broad, "team_id": player["team_id"], "team_name": opening_club,
            "creation_batch": player.get("creation_batch"), "identity_source": player["historical_data_source"],
            "identity_source_url": player["bdfutbol_squad_url"], "verified_national_pool_year": 1994,
            "historical_position_1993_94": player["historical_position_1993_94"], "historical_club_1994": opening_club,
            "overall": player.get("overall"), "attribute_source": player.get("attribute_source"),
            "profile_review_required": False, "duplicate_check": "belgium_1993_94_identity_gate",
            "matched_existing_id": source_id if source_id < 9496000 else None,
            "bdfutbol_search_name": player["display_name"],
            "bdfutbol_id": str(bdf_id or ""), "bdfutbol_url": player.get("bdfutbol_url", ""),
            "photo_filename": f"{source_id}.jpg", "photo_status": "ready_for_download" if bdf_id else "pending_identity_profile",
        })
        identity_records.append({
            "identity_key": ikey, "source_id": source_id, "display_name": player["display_name"],
            "opening_club": opening_club, "role": role, "position": ROLE_TO_LABEL[role],
            "position_source": role_source, "bdfutbol_id": bdf_id,
            "spells": player["historical_club_spells_1993_94"],
        })

    # Insert/update the 18 teams.
    team_index = {int(t["source_id"]): i for i, t in enumerate(snapshot["teams"])}
    for asset in assets["clubs"]:
        tid = int(asset["team_id"])
        raw = raw_teams.get(tid)
        row = make_team_from_mdb(raw, asset) if raw is not None else make_historical_team(asset)
        if tid in team_index:
            snapshot["teams"][team_index[tid]] = row
        else:
            snapshot["teams"].append(row)

    # Activate dedicated historical league id; the modern source id 52 remains absent.
    snapshot["leagues"] = [l for l in snapshot["leagues"] if int(l.get("source_id") or 0) not in {52, LEAGUE_ID}]
    snapshot["leagues"].append({
        "source_id": LEAGUE_ID, "country_id": BELGIUM_ID, "country": "Bélgica",
        "name": "Eerste Klasse / Division 1", "short_name": "Division 1", "level": 1,
        "team_count": 18, "turns": 2, "yellow_card_cycle": 5,
        "max_foreigners_starting": None, "max_foreigners_squad": None,
        "prefer_nationals": False, "source_start": "1993-08-01T00:00:00",
        "source_end": "1994-05-31T00:00:00", "source_edition": "1993-94",
        "admitted": True, "signable": True,
        "source_rule_hints": {
            "historical_runtime_id": True, "points_win": 2,
            "direct_relegation_places": [17,18],
            "modern_mdb_source_id_blocked": 52,
            "foreign_rule_status": "kept separate from roster activation; do not infer modern MDB limits",
        },
    })
    snapshot["leagues"].sort(key=lambda l:int(l.get("source_id") or 0))

    # Foundation is now active for Belgium only; Turkey and Russia remain gated.
    bel = next(l for l in foundation["leagues"] if l["key"] == "bel_1993_94")
    bel["activation_status"] = "active_historical_roster_gate_passed"
    bel["activated_runtime_league_id"] = LEAGUE_ID
    for c in bel["clubs"]:
        c["team_id"] = team_by_name[c["name"]]
        c["roster_status"] = "complete_historical_1993_94"

    # Gate metrics from active opening-day squads.
    roster_counts = {}
    role_counts = {}
    for name, tid in team_by_name.items():
        rows = [p for p in players if int(p.get("team_id") or 0) == tid and not p.get("retired")]
        roster_counts[name] = len(rows)
        role_counts[name] = dict(Counter(ROLE_TO_LABEL.get(int(p.get("primary_role") or 0), "?") for p in rows))
        if len(rows) < 18:
            raise RuntimeError(f"Belgium gate failed: {name} has only {len(rows)} active historical players")

    # Any Belgian international with a recognised active historical club must no longer sit in Otros-Bélgica.
    stranded = [p for p in players if int(p.get("team_id") or 0) == OTHER_BELGIUM_ID and not p.get("retired")
                and norm(p.get("historical_club_1994")) in {norm(n) for n in team_by_name}]
    if stranded:
        raise RuntimeError("Historical Belgian internationals remain stranded: " + ", ".join(p["display_name"] for p in stranded))

    audit = {
        "schema_version": 1, "season": "1993-94", "league_id": LEAGUE_ID,
        "status": "pass_belgium_1993_94_active", "staged_rows": sum(len(c["players"]) for c in stage["clubs"]),
        "unique_identities": len(identities), "same_season_transfer_duplicate_rows": 7,
        "clubs": 18, "minimum_required": 18, "minimum_active_roster": min(roster_counts.values()),
        "roster_counts": roster_counts, "role_counts": role_counts,
        "reused_existing_players": reused, "created_players": created,
        "mixed_era_memberships_excluded": mixed_era_excluded,
        "position_provenance": dict(role_sources), "bdfutbol_ids_ready_for_portraits": photo_ready,
        "otros_belgica_stranded_recognised_club": len(stranded),
        "modern_mdb_league_id_52_active": False,
        "transfer_identity_groups": TRANSFER_GROUPS,
        "identities": identity_records,
    }
    if audit["staged_rows"] != 413 or audit["unique_identities"] != 406:
        raise RuntimeError(f"Unexpected Belgium identity cardinality: {audit['staged_rows']} / {audit['unique_identities']}")

    SNAP_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    STAGE_PATH.write_text(json.dumps(stage, ensure_ascii=False, indent=2), encoding="utf-8")
    FOUNDATION_PATH.write_text(json.dumps(foundation, ensure_ascii=False, indent=2), encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:audit[k] for k in ("status","staged_rows","unique_identities","minimum_active_roster","reused_existing_players","created_players","mixed_era_memberships_excluded","bdfutbol_ids_ready_for_portraits","position_provenance")}, ensure_ascii=False, indent=2))
    print(json.dumps(roster_counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
