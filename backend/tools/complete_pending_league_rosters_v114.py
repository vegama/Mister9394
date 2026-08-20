from __future__ import annotations

"""Completa clubes 1993-94 pendientes con plantillas históricas verificables.

La primera fuente es Transfermarkt temporada 1993-94. Solo se usa 1994-95 como
reserva de continuidad juvenil y queda marcado como tal en cada ficha.
"""

import html
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.tools.enrich_world_cup_1994 import derived_attributes, position_fields

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "pending_league_rosters_tm_audit.json"
TM = "https://www.transfermarkt.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; historical-football-research/1.0)"}
ROLE = {"Goalkeeper": (0, "POR", "POR"), "Defender": (3, "DEF", "DEF"),
        "Midfielder": (7, "MED", "MED"), "Midfield": (7, "MED", "MED"),
        "Attack": (17, "DEL", "DEL"), "Forward": (17, "DEL", "DEL")}


def get(url: str) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=8) as response:
        return response.read().decode("utf-8", "replace")


def fold(value: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(value or "")).lower()
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", raw).split())


def tm_club_id(name: str) -> tuple[int | None, str | None]:
    aliases = {"FK Bodø/Glimt": "Bodo Glimt", "Widzew Lodz": "Widzew Łódź"}
    text = get(f"{TM}/schnellsuche/ergebnis/schnellsuche?query={quote(aliases.get(name, name))}")
    candidates = re.findall(r'href="/([^"/]+)/(?:startseite|profil)/verein/(\d+)"', text)
    wanted = fold(name)
    for slug, sid in candidates:
        if fold(slug.replace("-", " ")) == wanted:
            return int(sid), slug
    for slug, sid in candidates:
        if wanted and (wanted in fold(slug.replace("-", " ")) or fold(slug.replace("-", " ")) in wanted):
            return int(sid), slug
    return (int(candidates[0][1]), candidates[0][0]) if candidates else (None, None)


def squad_rows(club_id: int, slug: str, season: int) -> list[dict[str, Any]]:
    url = f"{TM}/{slug}/kader/verein/{club_id}/saison_id/{season}"
    text = get(url)
    rows = []
    for body in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.I | re.S):
        link = re.search(r'href="(/[^"/]+/profil/spieler/(\d+))"[^>]*>\s*([^<]+?)\s*</a>', body, re.I | re.S)
        position = re.search(r'title="([^"]+)"', body, re.I)
        if not link or not position:
            continue
        pos = html.unescape(position.group(1)).strip()
        if pos not in ROLE:
            continue
        rows.append({"name": html.unescape(re.sub(r"\s+", " ", link.group(3))).strip(),
                     "tm_id": link.group(2), "profile_url": TM + link.group(1), "position": pos})
    unique = {}
    for row in rows:
        unique[row["tm_id"]] = row
    return list(unique.values())


def dob(profile_url: str) -> str | None:
    text = get(profile_url)
    match = re.search(r'itemprop="birthDate"[^>]*>\s*(\d{2})/(\d{2})/(\d{4})', text, re.I)
    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}" if match else None


def split_name(name: str) -> tuple[str, str]:
    bits = name.split()
    return (bits[0], bits[-1]) if len(bits) > 1 else (name, name)


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    teams = {int(t["source_id"]): t for t in snapshot["teams"]}
    players = snapshot["players"]
    report = {"status": "complete", "source": "Transfermarkt historical squads", "clubs": [], "created": 0, "moved": 0, "fallback_1994_95": 0}
    next_id = max(int(p["source_id"]) for p in players) + 1
    # Recompute pending from current runtime state, not from a stale report.
    league_names = {"Divizia A", "A Grupa", "Ekstraklasa", "Allsvenskan", "Tippeligaen", "Superligaen", "Bundesliga", "Nationalliga A", "Vyshcha Liha"}
    for team in list(teams.values()):
        lid = int(team.get("league_id") or 0)
        pending_league = (team.get("pending_activation") or {}).get("league")
        if lid not in {56, 66, 89, 91, 88, 69, 62, 55, 12} and pending_league not in league_names:
            continue
        current = [p for p in players if not p.get("retired") and int(p.get("team_id") or 0) == int(team["source_id"])]
        if len(current) >= 18:
            continue
        try:
            club_id, slug = tm_club_id(team.get("name") or "")
            if not club_id:
                raise RuntimeError("Transfermarkt club not found")
            rows = squad_rows(club_id, slug or "", 1993)
            season_used = "1993-94"
            if len(rows) < 18:
                rows = squad_rows(club_id, slug or "", 1994)
                season_used = "1994-95 fallback youth continuity"
            if not rows:
                raise RuntimeError("no squad rows")
            team_added = 0
            for row in rows:
                if len([p for p in players if not p.get("retired") and int(p.get("team_id") or 0) == int(team["source_id"])]) >= 18:
                    break
                birth = dob(row["profile_url"])
                if not birth:
                    continue
                existing = next((p for p in players if not p.get("retired") and str(p.get("birth_date") or "")[:10] == birth and (fold(p.get("display_name")) == fold(row["name"]) or fold(p.get("surname1")) == fold(row["name"]))), None)
                role, broad, code = ROLE[row["position"]]
                if existing:
                    old_team = int(existing.get("team_id") or 0)
                    if old_team != int(team["source_id"]):
                        existing["team_id"] = int(team["source_id"])
                        existing["historical_club_1994"] = team.get("name")
                        existing["snapshot_club_resolution"] = "verified_transfermarkt_end_of_season_v114"
                        report["moved"] += 1
                        team_added += 1
                    continue
                given, family = split_name(row["name"])
                player = {
                    "source_id": next_id, "team_id": int(team["source_id"]), "display_name": row["name"],
                    "first_name": given, "surname1": family, "surname2": None, "birth_date": birth + "T00:00:00",
                    "birth_country_id": team.get("country_id") or 0, "international_country_id": team.get("country_id") or 0,
                    "preferred_foot": 1, "shirt_number": None, "primary_role": role, "broad_position": broad,
                    "overall": 60, "category": 61, "height_cm": None, "weight_kg": None, "salary": 0,
                    "release_clause": 0, "contract_start_year": None, "contract_end_year": None, "loan": False,
                    "initially_reserve": False, "retired": False, "attributes": derived_attributes(60, code, f"tm-v114-{next_id}"),
                    "birth_city_id": 0, "naturalized_country_id": None, "basque_origin": False,
                    "favorite_shirt_number": 0, "injury_proneness": 0, "progression_mean": 0, "fan_affection": 5,
                    "academy_team_id": 0, "previous_team_id": 0, "previous_team_years": 0,
                    "buyback_option": 0, "role_ratings": position_fields(code)[2],
                    "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False, "long_shots": False, "cuts_inside": False, "first_time_play": False, "dives": False},
                    "identity_source": f"Transfermarkt {season_used} squad - {team.get('name')}", "identity_source_url": row["profile_url"],
                    "historical_data_source": f"Transfermarkt {season_used} squad - {team.get('name')}",
                    "attribute_source": "provisional_historical_roster_v114", "profile_review_required": season_used != "1993-94",
                    "role_detail_source": "transfermarkt_historical_squad_position", "historical_club_1994": team.get("name"),
                    "historical_position_1993_94": {"POR":"Goalkeeper","DEF":"Defender","MED":"Midfielder","DEL":"Forward"}[broad],
                    "external_origin": "league_club_1993_94", "creation_batch": "transfermarkt_roster_completion_v114",
                    "transfermarkt_id": row["tm_id"], "historical_roster_role": "youth_debut_following_season_fallback" if season_used != "1993-94" else "senior_season_roster",
                }
                players.append(player); next_id += 1; report["created"] += 1; team_added += 1
                if season_used != "1993-94": report["fallback_1994_95"] += 1
            report["clubs"].append({"team_id": int(team["source_id"]), "team": team.get("name"), "transfermarkt_id": club_id, "slug": slug, "season": season_used, "added_or_moved": team_added, "final_squad": len([p for p in players if not p.get("retired") and int(p.get("team_id") or 0) == int(team["source_id"])] )})
        except Exception as exc:
            report["clubs"].append({"team_id": int(team["source_id"]), "team": team.get("name"), "status": "blocked", "error": str(exc)})
        # Guardado incremental: un club sin ficha no debe hacer perder los anteriores.
        SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        time.sleep(0.03)
    players.sort(key=lambda p: int(p["source_id"]))
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("created", "moved", "fallback_1994_95")}, ensure_ascii=False))
    for row in report["clubs"]: print(row)


if __name__ == "__main__":
    main()
