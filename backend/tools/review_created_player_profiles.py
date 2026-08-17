from __future__ import annotations

"""One-time data curation for players added outside the historical MDB snapshot.

This is deliberately *not* a gameplay rating formula. It materialises fixed player
profiles after comparing each added player with source-backed 1993-94 players.
The output is stored in the snapshot and in an auditable JSON catalogue.

Policy:
- original/source-backed player records are never rewritten here;
- every externally-created player must receive a fixed reviewed profile;
- broad historical position remains authoritative when no finer source exists;
- source-backed comparable players provide the shape/range of attributes;
- explicit historical exceptions are curated by name and documented;
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import math
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "football9394" / "historical_snapshot.json"
REVIEW_JSON = ROOT / "data" / "football9394" / "created_player_profile_reviews.json"
AUDIT_JSON = ROOT / "docs" / "v024_created_player_profile_audit.json"
WC_USAGE_JSON = ROOT / "data" / "football9394" / "world_cup_1994_player_usage.json"

ATTRS = (
    "pace", "acceleration", "jumping", "stamina", "strength", "tackling",
    "work_rate", "aggression", "anticipation", "marking", "discipline",
    "positioning", "leadership", "consistency", "vision", "short_pass",
    "long_pass", "dribbling", "finishing", "heading", "off_ball",
    "shot_power", "free_kicks", "penalties", "technique",
)


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().lower()
    return re.sub(r"\s+", " ", text)


def clamp(v: float, lo: int = 20, hi: int = 99) -> int:
    return max(lo, min(hi, int(round(v))))


# Fixed curator decisions for players whose old country-baseline number was clearly
# not compatible with their 1993-94 standing. These are data corrections, not a
# function applied to other players.
CURATED_OVERALLS: dict[str, tuple[int, str]] = {
    # Colombia
    "oscar cordoba": (79, "Colombia first-choice goalkeeper at USA 94; source scale comparison with Mondragon and leading keepers"),
    "andres escobar": (81, "established Colombia/Atletico Nacional international central defender; old 74 baseline materially understated him"),
    "leonel alvarez": (80, "established Colombia holding midfielder and USA 94 starter; old 75 baseline understated his senior standing"),
    "luis fernando herrera": (78, "experienced Colombia starting defender; calibrated below the elite Colombian core"),
    "wilson perez": (77, "Colombia starting defender at USA 94; modest upward correction from generic baseline"),
    "alexis mendoza": (77, "senior Colombia central defender; generic baseline compressed him too far"),
    "herman gaviria": (76, "Colombia starter and scorer at USA 94; modest correction"),
    "antony de avila": (77, "established international forward; generic 74 baseline too flat"),
    "gabriel gomez": (76, "experienced Colombia midfielder; modest correction"),
    "mauricio serna": (74, "squad midfielder not used at USA 94; retain below established starters in 1993-94"),
    "ivan valenciano": (75, "prolific domestic forward but reserve at USA 94; placed below Asprilla/Valencia tier"),
    # Romania
    "ilie dumitrescu": (82, "key Steaua attacker and five-start/two-goal USA 94 performer; old 76 baseline clearly low"),
    "daniel prodan": (79, "Romania starting central defender through five USA 94 matches"),
    "dorinel munteanu": (79, "Romania ever-present midfielder at USA 94; established senior international"),
    "gheorghe mihali": (77, "Romania starting defender; retained below Popescu/Belodedici tier"),
    "tibor selymes": (77, "Romania starting left-sided defender; modest correction"),
    "florin prunea": (77, "Romania first-choice goalkeeper for most of USA 94"),
    "bogdan stelea": (77, "Romania international goalkeeper in strong 1993-94 pool"),
    "basarab panduru": (78, "high-level technical Romanian midfielder; old country baseline slightly low"),
    "iulian chirita": (75, "unused USA 94 squad midfielder; old 78 generic result was too generous"),
    # South Korea
    "hong myung bo": (78, "South Korea defensive leader; three starts and two goals at USA 94; old 69 baseline was a major outlier"),
    "kim joo sung": (77, "senior South Korea star and three-start USA 94 midfielder"),
    "hwang sun hong": (76, "South Korea first-choice striker and USA 94 scorer"),
    "seo jung won": (74, "attacking international with a USA 94 goal; above generic domestic baseline"),
    "ko jeong woon": (73, "three-start South Korea attacker; modest upward correction"),
    "ha seok ju": (73, "senior attacking midfielder/wing option; modest correction"),
    "choi in young": (72, "South Korea first-choice USA 94 goalkeeper"),
    # Greece
    "dimitris saravakos": (80, "established Panathinaikos/Greek international attacking midfielder; generic 70 baseline was untenable"),
    "stelios manolas": (79, "long-established AEK and Greece central defender/captain-level player"),
    "tasos mitropoulos": (78, "veteran Greece international midfielder; old 71 baseline compressed senior status"),
    "stratos apostolakis": (76, "experienced Greece defender; corrected above generic baseline"),
    "panagiotis tsalouchidis": (76, "established Greece midfielder and USA 94 starter"),
    "ioannis kalitzakis": (75, "first-choice Greece defender at USA 94"),
    "nikos nioplias": (74, "Greece starting midfielder at USA 94"),
    "savvas kofidis": (74, "Greece starting midfielder at USA 94"),
    "alexis alexandris": (74, "established domestic striker; generic baseline slightly low"),
    "vasilis dimitriadis": (74, "established AEK striker; generic 69 baseline too low"),
    "nikos machlas": (73, "young but starting Greece forward at USA 94"),
    # Nigeria
    "emmanuel amunike": (81, "key Nigeria attacker; four starts/two goals at USA 94 and high-level 1993-94 trajectory"),
    "daniel amokachi": (81, "Club Brugge/Nigeria power forward; four starts/two goals at USA 94"),
    "uche okechukwu": (80, "established Brondby/Fenerbahce-level Nigeria central defender and four-start USA 94 player"),
    "sunday oliseh": (78, "young but already four-start Nigeria central midfielder at USA 94"),
    "augustine eguavoen": (78, "senior Nigeria starting defender"),
    "stephen keshi": (78, "veteran Nigeria defensive leader; balanced for age/role in 1993-94"),
    "chidi nwanu": (77, "Nigeria starting defender at USA 94"),
    "michael emenalo": (75, "Nigeria starting defender at USA 94; modest correction"),
    "alloysius agu": (73, "reserve goalkeeper behind Rufai; old 74 slightly generous"),
    "uche okafor": (73, "unused USA 94 squad defender; kept below first-choice defensive tier"),
    # Bulgaria
    "trifon ivanov": (80, "established Bulgaria central defender and USA 94 core starter"),
    "borislav mihaylov": (79, "Bulgaria captain/first-choice goalkeeper through seven USA 94 matches"),
    "nasko sirakov": (79, "senior Bulgaria striker and USA 94 starter/scorer"),
    "zlatko yankov": (78, "six-start Bulgaria midfielder at USA 94"),
    "daniel borimirov": (77, "Bulgaria midfielder/scorer at USA 94; modest correction"),
    "nikolay iliev": (77, "established Bulgaria defender; old baseline slightly low"),
    "tsanko tsvetanov": (76, "six-start Bulgaria defender"),
    # Belgium
    "marc degryse": (81, "Belgium attacking leader behind Scifo tier; USA 94 starter/scorer"),
    "philippe albert": (80, "Belgium starting defender and two-goal USA 94 performer"),
    "lorenzo staelens": (80, "Belgium four-start midfielder; established Club Brugge player"),
    "luc nilis": (80, "high-level Anderlecht/Belgium forward in 1993-94"),
    "michel de wolf": (79, "experienced Belgium starting defender"),
    "josip weber": (79, "Belgium starting striker at USA 94"),
    # Cameroon
    "thomas n kono": (77, "veteran elite Cameroon goalkeeper; old 74 baseline understated established level despite reserve WC role"),
    "stephen tataw": (76, "Cameroon captain/starting defender at USA 94"),
    "roger milla": (75, "veteran technical forward; age reduces physical level but not finishing/anticipation class"),
    "marc vivien foe": (73, "young Cameroon starter; retain developmental 1993-94 level rather than later reputation"),
    # Saudi Arabia
    "saeed al owairan": (75, "Saudi Arabia attacking reference and four-start USA 94 scorer; generic 67 was too low"),
    "majed abdullah": (75, "historic Saudi striker, still a USA 94 starter but late-career; balanced below prime reputation"),
    "mohamed al deayea": (74, "Saudi Arabia first-choice goalkeeper at USA 94"),
    "fuad anwar": (74, "Saudi Arabia midfield core and two-goal USA 94 player"),
    "fahad al bishi": (72, "four-start Saudi Arabia midfielder"),
    "sami al jaber": (72, "young Saudi Arabia striker and USA 94 scorer"),
    "mohammed al khilaiwi": (72, "four-start Saudi Arabia defender"),
    "mohamed abd al jawad": (72, "experienced Saudi Arabia starting defender"),
    "ahmed jamil madani": (72, "Saudi Arabia starting central defender"),
    # USA
    "john harkes": (78, "established USA/English-league midfielder and USA 94 starter"),
    "eric wynalda": (77, "USA first-choice forward and USA 94 scorer"),
    "thomas dooley": (77, "experienced USA starter with Bundesliga background"),
    "paul caligiuri": (75, "USA four-start defender; modest correction over old 71"),
    "fernando clavijo": (73, "USA starting veteran defender; old 71 slightly low"),
    "cobi jones": (74, "young but important pace option at USA 94"),
    "claudio reyna": (72, "elite prospect but did not play at USA 94; avoid rating later-career reputation into 1993-94"),
    "brad friedel": (72, "young reserve goalkeeper in 1993-94; later reputation intentionally not back-projected"),
    # Morocco
    "tahar el khalej": (77, "senior Morocco midfielder/defensive organiser; generic 72 baseline too low"),
    "rachid daoudi": (76, "Morocco set-piece/creative midfielder and USA 94 starter"),
    "mustapha hadji": (75, "young attacking midfielder already in USA 94 squad; calibrated below later peak"),
    "mohammed chaouch": (75, "Morocco starting forward and USA 94 scorer"),
    "abdelkrim el hadrioui": (74, "Morocco three-start defender"),
    # Bolivia
    "jose milton melgar": (76, "experienced Bolivia midfield organiser and three-start USA 94 player"),
    "carlos trucco": (75, "Bolivia first-choice USA 94 goalkeeper"),
    "carlos borja": (73, "Bolivia veteran midfielder and three-start USA 94 player"),
    "william ramallo": (73, "Bolivia starting striker at USA 94"),
    "julio cesar baldivieso": (73, "young but first-choice attacking midfielder at USA 94"),
    # Norway / Switzerland / Ireland
    "erik mykland": (77, "Norway creative midfield starter; generic 74 baseline too low"),
    "kjetil rekdal": (77, "Norway midfielder and USA 94 scorer"),
    "oyvind leonhardsen": (76, "Norway three-start midfielder"),
    "alain geiger": (79, "Switzerland veteran defensive leader and four-start USA 94 player"),
    "georges bregy": (77, "Switzerland veteran midfielder and USA 94 scorer"),
    "john aldridge": (80, "proven Liverpool/Tranmere-era goalscorer and Ireland USA 94 scorer"),
}

# Style hints are used only to select source-backed comparable profiles. Unknown
# players remain conservative/balanced rather than receiving invented specialties.
ARCHETYPE_OVERRIDES: dict[str, str] = {
    "andres escobar": "ball_playing_defender", "leonel alvarez": "ball_winner",
    "ilie dumitrescu": "attacking_mid", "dorinel munteanu": "runner_mid",
    "hong myung bo": "ball_playing_defender", "kim joo sung": "attacking_mid",
    "hwang sun hong": "mobile_forward", "dimitris saravakos": "creator_mid",
    "stelios manolas": "stopper", "tasos mitropoulos": "ball_winner",
    "emmanuel amunike": "mobile_forward", "daniel amokachi": "power_forward",
    "uche okechukwu": "stopper", "sunday oliseh": "ball_winner",
    "stephen keshi": "ball_playing_defender", "trifon ivanov": "stopper",
    "nasko sirakov": "poacher", "marc degryse": "creator_forward",
    "philippe albert": "ball_playing_defender", "franky van der elst": "ball_winner",
    "luc nilis": "creator_forward", "roger milla": "poacher",
    "marc vivien foe": "runner_mid", "saeed al owairan": "mobile_forward",
    "majed abdullah": "poacher", "fuad anwar": "ball_winner",
    "john harkes": "runner_mid", "eric wynalda": "mobile_forward",
    "thomas dooley": "ball_playing_defender", "cobi jones": "runner_mid",
    "claudio reyna": "creator_mid", "tahar el khalej": "ball_winner",
    "rachid daoudi": "creator_mid", "mustapha hadji": "attacking_mid",
    "jose milton melgar": "creator_mid", "marco etcheverry": "creator_mid",
    "erik mykland": "creator_mid", "kjetil rekdal": "attacking_mid",
    "alain geiger": "balanced_defender", "georges bregy": "creator_mid",
    "john aldridge": "poacher",
    # Existing 0.22 national-pool additions with historically identifiable styles.
    "fabian estay": "creator_mid", "jose luis sierra": "creator_mid",
    "marcelo vega": "attacking_mid", "miguel ramirez": "fullback",
    "javier margas": "stopper", "rodrigo barrera": "mobile_forward",
    "mixu paatelainen": "power_forward", "ari hjelm": "mobile_forward",
    "markku kanerva": "stopper", "ned zelic": "ball_playing_defender",
    "aurelio vidmar": "attacking_mid", "graham arnold": "power_forward",
    "alex tobin": "stopper", "paul wade": "ball_winner",
    "charles akonnor": "creator_mid", "samuel kuffour": "stopper",
    "abdelhafid tasfaout": "poacher", "tahar cherif el ouazzani": "creator_mid",
    "celso ayala": "stopper", "dusan tittel": "ball_playing_defender",
    # 0.24 Belgium / Turkey / Russia national-depth additions.
    "bertrand crasson": "fullback", "regis genaux": "fullback",
    "pascal plovie": "stopper", "johan walem": "creator_mid",
    "gert verheyen": "mobile_forward", "gilles de bilde": "mobile_forward",
    "bulent korkmaz": "stopper", "recep cetin": "fullback",
    "ogun temizkanoglu": "stopper", "gokhan keskin": "ball_playing_defender",
    "emre asik": "stopper", "ergun penbe": "fullback",
    "tugay kerimoglu": "creator_mid", "oguz cetin": "creator_mid",
    "unal karaman": "runner_mid", "mehmet ozdilek": "attacking_mid",
    "suat kaya": "ball_winner", "riza calimbay": "runner_mid",
    "sergen yalcin": "creator_mid", "orhan cikirikci": "mobile_forward",
    "feyyaz ucar": "poacher", "hakan sukur": "power_forward",
    "hami mandirali": "creator_forward", "ertugrul saglam": "mobile_forward",
    "aykut kocaman": "poacher", "saffet sancakli": "power_forward",
    "rashid rahimov": "fullback", "ramiz mamedov": "fullback",
    "yuri kovtun": "stopper", "vladimir tatarchuk": "runner_mid",
    "sergei podpaly": "ball_winner",
}


CURATED_ATTRIBUTE_PATCHES: dict[str, dict[str, int]] = {
    # Explicit clean-up where a source-comparable shape produced a trait that is
    # contradicted by the player's well-established historical profile.
    "dimitris saravakos": {"anticipation": 76, "aggression": 58},
    "fabian estay": {"anticipation": 74, "aggression": 58},
    "tahar cherif el ouazzani": {"anticipation": 72, "aggression": 65, "finishing": 74, "free_kicks": 82, "penalties": 78},
    "philippe albert": {"penalties": 76},
    "alain geiger": {"shot_power": 82, "free_kicks": 72, "penalties": 76},
    "hong myung bo": {"leadership": 84, "consistency": 82},
    # 0.24 fixed curator decisions for distinctive 1993-94 profiles.
    "hakan sukur": {"finishing": 82, "heading": 84, "off_ball": 82, "strength": 80},
    "hami mandirali": {"shot_power": 86, "free_kicks": 84, "finishing": 79, "technique": 80},
    "sergen yalcin": {"vision": 81, "dribbling": 80, "technique": 82, "short_pass": 79},
    "oguz cetin": {"vision": 82, "short_pass": 82, "long_pass": 80, "technique": 80},
    "ridvan dilmen": {"dribbling": 83, "technique": 82, "acceleration": 80},
    "bulent korkmaz": {"marking": 82, "tackling": 82, "leadership": 83, "aggression": 82},
    "tugay kerimoglu": {"vision": 80, "short_pass": 81, "long_pass": 82, "technique": 80},
    "gert verheyen": {"off_ball": 79, "stamina": 79, "heading": 77},
    "johan walem": {"vision": 79, "short_pass": 80, "technique": 79},
}

def world_cup_archetype(player: dict[str, Any]) -> tuple[str, str]:
    name = norm(player.get("display_name"))
    if name in ARCHETYPE_OVERRIDES:
        return ARCHETYPE_OVERRIDES[name], "explicit historical style hint"
    # Fjelstul verifies the broad World Cup position but not a reliable sub-role.
    # Do not turn a shirt number into invented tactical detail. Unknown players stay
    # conservative/balanced until a finer historical source is available.
    pos = player.get("broad_position")
    if pos == "POR": return "goalkeeper", "verified World Cup broad position"
    if pos == "DEF": return "balanced_defender", "verified World Cup broad position; no invented sub-role"
    if pos == "MED": return "balanced_mid", "verified World Cup broad position; no invented sub-role"
    return "balanced_forward", "verified World Cup broad position; no invented sub-role"

def profile_archetype(player: dict[str, Any]) -> tuple[str, str]:
    name = norm(player.get("display_name"))
    if name in ARCHETYPE_OVERRIDES:
        return ARCHETYPE_OVERRIDES[name], "explicit historical style hint"
    if player.get("external_origin") == "world_cup_1994":
        return world_cup_archetype(player)
    pos = player.get("broad_position")
    if pos == "POR": return "goalkeeper", "verified broad position; conservative profile"
    if pos == "DEF": return "balanced_defender", "verified broad position; conservative profile"
    if pos == "MED": return "balanced_mid", "verified broad position; conservative profile"
    return "balanced_forward", "verified broad position; conservative profile"


def avg(a: dict[str, int], keys: tuple[str, ...]) -> float:
    return sum(float(a.get(k, 50)) for k in keys) / len(keys)


def archetype_score(player: dict[str, Any], archetype: str) -> float:
    a = player.get("attributes") or {}
    o = float(player.get("overall") or 70)
    if archetype == "goalkeeper":
        return avg(a, ("acceleration", "jumping", "tackling", "marking", "positioning", "anticipation", "consistency")) - 0.4 * avg(a, ("finishing", "dribbling"))
    if archetype == "fullback":
        return avg(a, ("pace", "acceleration", "stamina", "work_rate", "short_pass", "dribbling", "tackling")) - 0.2 * avg(a, ("strength", "heading"))
    if archetype == "stopper":
        return avg(a, ("tackling", "marking", "strength", "heading", "aggression", "positioning")) - 0.15 * avg(a, ("dribbling", "vision"))
    if archetype == "ball_playing_defender":
        return avg(a, ("positioning", "vision", "short_pass", "long_pass", "technique", "tackling"))
    if archetype == "balanced_defender":
        keys=("pace","stamina","strength","tackling","marking","positioning","heading","short_pass","consistency")
        return 100 - avg({k: abs(float(a.get(k,o))-o) for k in keys}, keys)
    if archetype == "creator_mid":
        return avg(a, ("vision", "short_pass", "long_pass", "dribbling", "technique", "free_kicks")) - 0.15 * avg(a, ("marking", "heading"))
    if archetype == "ball_winner":
        return avg(a, ("tackling", "marking", "work_rate", "aggression", "strength", "stamina", "positioning"))
    if archetype == "runner_mid":
        return avg(a, ("pace", "acceleration", "stamina", "work_rate", "off_ball", "short_pass"))
    if archetype == "attacking_mid":
        return avg(a, ("vision", "dribbling", "finishing", "off_ball", "shot_power", "technique", "short_pass"))
    if archetype == "balanced_mid":
        keys=("stamina","work_rate","vision","short_pass","long_pass","dribbling","technique","positioning","consistency")
        return 100 - avg({k: abs(float(a.get(k,o))-o) for k in keys}, keys)
    if archetype == "poacher":
        return avg(a, ("finishing", "off_ball", "anticipation", "positioning", "acceleration"))
    if archetype == "power_forward":
        return avg(a, ("strength", "heading", "jumping", "finishing", "shot_power", "off_ball"))
    if archetype == "mobile_forward":
        return avg(a, ("pace", "acceleration", "dribbling", "off_ball", "finishing", "technique"))
    if archetype == "creator_forward":
        return avg(a, ("vision", "short_pass", "long_pass", "dribbling", "technique", "finishing"))
    keys=("pace","acceleration","strength","finishing","off_ball","dribbling","heading","technique","consistency")
    return 100 - avg({k: abs(float(a.get(k,o))-o) for k in keys}, keys)


def compatible_archetypes(pos: str) -> tuple[str, ...]:
    return {
        "POR": ("goalkeeper",),
        "DEF": ("fullback", "stopper", "ball_playing_defender", "balanced_defender"),
        "MED": ("creator_mid", "ball_winner", "runner_mid", "attacking_mid", "balanced_mid"),
        "DEL": ("poacher", "power_forward", "mobile_forward", "creator_forward", "balanced_forward"),
    }[pos]



def style_coherent(candidate: dict[str, Any], archetype: str) -> bool:
    """Reject source rows whose broad-position label conflicts with their actual attribute shape.

    The historical MDB contains a few positional oddities (for example midfielders stored
    as defenders). Those records remain untouched, but they must not become profile
    references for newly curated players.
    """
    a=candidate.get("attributes") or {}; o=float(candidate.get("overall") or 70)
    def m(*keys: str) -> float: return sum(float(a.get(k,o)) for k in keys)/len(keys)
    if archetype == "goalkeeper": return candidate.get("broad_position") == "POR"
    if archetype == "fullback":
        return m("pace","acceleration","stamina","work_rate") >= o-1 and m("tackling","marking") >= o-10
    if archetype == "stopper":
        return m("tackling","marking") >= o-5 and m("strength","heading","positioning") >= o-4
    if archetype == "ball_playing_defender":
        return m("tackling","marking") >= o-10 and m("vision","short_pass","long_pass","technique") >= o-2
    if archetype == "balanced_defender":
        return m("tackling","marking","positioning") >= o-10
    if archetype == "creator_mid":
        return m("vision","short_pass","long_pass","technique") >= o+1 and m("anticipation","positioning") >= o-15
    if archetype == "ball_winner":
        return m("tackling","marking") >= o-7 and m("work_rate","stamina","strength") >= o-5
    if archetype == "runner_mid":
        return m("pace","acceleration","stamina","work_rate") >= o-1
    if archetype == "attacking_mid":
        return m("vision","dribbling","finishing","shot_power","technique") >= o-1
    if archetype == "balanced_mid":
        return m("vision","short_pass","long_pass","technique") >= o-5
    if archetype == "poacher":
        return m("finishing","off_ball","anticipation") >= o
    if archetype == "power_forward":
        return m("strength","heading","jumping","finishing") >= o-1
    if archetype == "mobile_forward":
        return m("pace","acceleration","dribbling","off_ball") >= o
    if archetype == "creator_forward":
        return m("vision","short_pass","dribbling","technique") >= o
    if archetype == "balanced_forward":
        return m("finishing","off_ball","dribbling") >= o-5
    return True

def comparable_pool(originals: list[dict[str, Any]], player: dict[str, Any], archetype: str, target_overall: int) -> list[tuple[float, dict[str, Any]]]:
    pos = player.get("broad_position")
    country = int(player.get("international_country_id") or player.get("birth_country_id") or 0)
    rows: list[tuple[float, dict[str, Any]]] = []
    for candidate in originals:
        if candidate.get("broad_position") != pos:
            continue
        co = int(candidate.get("overall") or 0)
        if abs(co - target_overall) > 5:
            continue
        if not style_coherent(candidate, archetype):
            continue
        c_country = int(candidate.get("international_country_id") or candidate.get("birth_country_id") or 0)
        same_country = country > 0 and c_country == country
        # Source scale proximity dominates. Same-country source players are preferred,
        # and style score breaks ties. This only chooses comparable records; it does
        # not calculate the target player's overall.
        score = abs(co - target_overall) * 8.0
        if same_country:
            score -= 10.0
        score -= archetype_score(candidate, archetype) * 0.08
        # Avoid ultra-low source records whose attributes contain placeholders.
        if min((candidate.get("attributes") or {}).values() or [50]) <= 0:
            score += 30
        rows.append((score, candidate))
    rows.sort(key=lambda row: (row[0], abs(int(row[1].get("overall") or 0)-target_overall), int(row[1].get("source_id") or 0)))
    return rows


def choose_comparables(
    pool: list[tuple[float, dict[str, Any]]],
    player: dict[str, Any],
    used_pairs: Counter[tuple[int,int]],
    used_vectors: set[tuple[int, ...]],
    target_overall: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    if len(pool) < 2:
        raise RuntimeError(f"not enough source-backed comparables for {player.get('display_name')}")
    # Select among the best historical-scale fits, while avoiding repeated pairs
    # and exact cloned output profiles. The decision is materialised as fixed data.
    shortlist = [p for _, p in pool[:18]]
    pid = int(player.get("source_id") or 0)
    options=[]
    for i, a in enumerate(shortlist):
        for j, b in enumerate(shortlist):
            if j <= i: continue
            pair=(int(a['source_id']), int(b['source_id']))
            reuse=used_pairs[pair]
            tie=(pid + pair[0]*17 + pair[1]*31) % 997
            options.append(((reuse, i+j, tie),a,b,pair))
    options.sort(key=lambda row:row[0])
    for _,a,b,pair in options:
        attrs=materialise_attributes(target_overall,a,b)
        vector=tuple(attrs[k] for k in ATTRS)
        if vector in used_vectors:
            continue
        used_pairs[pair]+=1
        used_vectors.add(vector)
        return a,b,attrs
    raise RuntimeError(f"could not materialise a unique source-comparable profile for {player.get('display_name')}")


def materialise_attributes(target_overall: int, primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, int]:
    # Preserve the *shape* of two actual source-backed profiles, translated to the
    # target player's already-curated overall. This is a curation operation whose
    # result is written as fixed data; it is never called by match/career runtime.
    oa=float(primary.get("overall") or target_overall)
    ob=float(secondary.get("overall") or target_overall)
    aa=primary.get("attributes") or {}; ab=secondary.get("attributes") or {}
    out={}
    for key in ATTRS:
        da=float(aa.get(key,oa))-oa
        db=float(ab.get(key,ob))-ob
        out[key]=clamp(target_overall + (da*0.62 + db*0.38))
    return out


def materialise_role_ratings(player: dict[str, Any], primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str,int]:
    pos=player.get('broad_position')
    pa=primary.get('role_ratings') or {}; pb=secondary.get('role_ratings') or {}
    out={str(i): clamp(float(pa.get(str(i),0))*0.65 + float(pb.get(str(i),0))*0.35, 0, 100) for i in range(18)}
    allowed={
        'POR': {0}, 'DEF': {1,2,3,4,5,6}, 'MED': {6,7,8,9,10,11,12,13,14,15,16}, 'DEL': {9,10,11,12,13,14,15,16,17}
    }[pos]
    for k in list(out):
        if int(k) not in allowed: out[k]=0
    if max(out.values()) < 70:
        # retain the player's broad canonical role when source role detail is sparse
        fallback={'POR':0,'DEF':3,'MED':7,'DEL':17}[pos]; out[str(fallback)]=100
    return out


def world_cup_usage_by_external_id() -> dict[str, dict[str, Any]]:
    if not WC_USAGE_JSON.exists(): return {}
    data=json.loads(WC_USAGE_JSON.read_text(encoding='utf-8'))
    return {str(r['external_player_id']):r for r in data.get('players',[])}


def review(snapshot: dict[str, Any]) -> tuple[list[dict[str,Any]], dict[str,Any]]:
    originals=[p for p in snapshot.get('players',[]) if not p.get('external_origin')]
    created=[p for p in snapshot.get('players',[]) if p.get('external_origin') in {'world_cup_1994','national_pool_1993_94'}]
    wc_usage=world_cup_usage_by_external_id()
    used_pairs: Counter[tuple[int,int]]=Counter()
    used_vectors: set[tuple[int, ...]] = set()
    records=[]
    old_vectors=Counter(tuple((p.get('attributes') or {}).get(k) for k in ATTRS) for p in created)
    overall_changes=[]

    for player in sorted(created,key=lambda p:int(p.get('source_id') or 0)):
        namekey=norm(player.get('display_name'))
        old_overall=int(player.get('overall') or 70)
        if namekey in CURATED_OVERALLS:
            target_overall, overall_reason=CURATED_OVERALLS[namekey]
            overall_decision='changed'
        else:
            target_overall=old_overall
            overall_reason='retained after source-scale/context review; no evidence strong enough to override the existing individual value'
            overall_decision='retained'
        archetype, archetype_basis=profile_archetype(player)
        pool=comparable_pool(originals, player, archetype, target_overall)
        primary,secondary,attrs=choose_comparables(pool, player, used_pairs, used_vectors, target_overall)
        attribute_patch = CURATED_ATTRIBUTE_PATCHES.get(namekey, {})
        if attribute_patch:
            # Replace only explicit curator decisions; the fixed output remains fully auditable.
            attrs.update({key: clamp(value) for key, value in attribute_patch.items()})
        roles=materialise_role_ratings(player,primary,secondary)
        old_attrs=dict(player.get('attributes') or {})
        player['overall']=target_overall
        player['category']=min(99,max(target_overall,int(player.get('category') or target_overall)))
        player['attributes']=attrs
        player['role_ratings']=roles
        player['attribute_source']='fixed_source_comparable_review_0.23'
        player['profile_review_required']=False
        usage=None
        if player.get('external_origin')=='world_cup_1994':
            eid=str((player.get('world_cup_1994') or {}).get('external_player_id') or '')
            usage=wc_usage.get(eid)
        confidence='high' if namekey in CURATED_OVERALLS or namekey in ARCHETYPE_OVERRIDES else ('medium' if usage and usage.get('starts',0)>0 else 'conservative')
        review_meta={
            'batch':'created_player_profile_audit_0.23',
            'overall_before':old_overall,'overall_after':target_overall,
            'overall_decision':overall_decision,'overall_reason':overall_reason,
            'archetype':archetype,'archetype_basis':archetype_basis,
            'primary_comparable':{'source_id':int(primary['source_id']),'display_name':primary['display_name'],'overall':int(primary['overall']),'broad_position':primary['broad_position']},
            'secondary_comparable':{'source_id':int(secondary['source_id']),'display_name':secondary['display_name'],'overall':int(secondary['overall']),'broad_position':secondary['broad_position']},
            'world_cup_1994_usage':usage,
            'profile_confidence':confidence,
            'explicit_attribute_patch':attribute_patch or None,
            'policy':'fixed data curation against source-backed players; no runtime rating formula',
        }
        player['profile_review_0_23']=review_meta
        if old_overall!=target_overall:
            overall_changes.append({'source_id':int(player['source_id']),'display_name':player['display_name'],'before':old_overall,'after':target_overall,'reason':overall_reason})
        records.append({
            'source_id':int(player['source_id']),'display_name':player['display_name'],
            'external_origin':player.get('external_origin'),'broad_position':player.get('broad_position'),
            **review_meta,'attributes_before':old_attrs,'attributes_after':attrs,
        })

    new_vectors=Counter(tuple((p.get('attributes') or {}).get(k) for k in ATTRS) for p in created)
    pending=[p for p in created if p.get('attribute_source')!='fixed_source_comparable_review_0.23' or p.get('profile_review_required')]
    audit={
        'schema_version':1,
        'checkpoint':'0.24.0-bel-tur-rus-1993-data',
        'profile_method_version':'0.23-source-comparable-fixed-data',
        'policy':{
            'new_universal_rating_rule':False,
            'runtime_formula_added':False,
            'original_players_modified':False,
            'created_players_materialised_as_fixed_data':True,
        },
        'counts':{
            'source_backed_original_players':len(originals),
            'created_players_reviewed':len(records),
            'overall_changes':len(overall_changes),
            'old_unique_attribute_vectors':len(old_vectors),
            'new_unique_attribute_vectors':len(new_vectors),
            'old_duplicate_vector_groups':sum(1 for n in old_vectors.values() if n>1),
            'new_duplicate_vector_groups':sum(1 for n in new_vectors.values() if n>1),
            'max_old_vector_reuse':max(old_vectors.values()) if old_vectors else 0,
            'max_new_vector_reuse':max(new_vectors.values()) if new_vectors else 0,
            'pending_profile_reviews':len(pending),
            'explicit_attribute_patch_players':sum(1 for r in records if r.get('explicit_attribute_patch')),
        },
        'overall_changes':overall_changes,
        'pending_profile_reviews':[{'source_id':p['source_id'],'display_name':p['display_name']} for p in pending],
    }
    return records,audit


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--snapshot',type=Path,default=SNAPSHOT)
    ap.add_argument('--review-json',type=Path,default=REVIEW_JSON)
    ap.add_argument('--audit-json',type=Path,default=AUDIT_JSON)
    args=ap.parse_args()
    snapshot=json.loads(args.snapshot.read_text(encoding='utf-8'))
    # Make it possible to prove original/source-backed players were untouched.
    orig_before={int(p['source_id']):hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for p in snapshot.get('players',[]) if not p.get('external_origin')}
    records,audit=review(snapshot)
    orig_after={int(p['source_id']):hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for p in snapshot.get('players',[]) if not p.get('external_origin')}
    changed_orig=[pid for pid,h in orig_before.items() if orig_after.get(pid)!=h]
    audit['original_player_hash_changes']=changed_orig
    audit['policy']['original_players_modified']=bool(changed_orig)
    if changed_orig: raise RuntimeError(f'original players unexpectedly changed: {changed_orig[:10]}')
    args.snapshot.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    args.review_json.write_text(json.dumps({'schema_version':1,'players':records},ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    args.audit_json.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    print(json.dumps(audit['counts'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
