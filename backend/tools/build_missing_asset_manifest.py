from __future__ import annotations

"""Build the canonical missing-asset manifest for Míster 93/94.

The manifest is intentionally source-agnostic.  It inventories what the runtime
actually needs, annotates known BDFutbol mappings, and adds safe discovery URLs
for Wikimedia Commons / image search.  Downloading is handled by
``recover_missing_assets.py`` so the same JSON can be used both in CI-like
passes and from a Windows PC with normal Internet access.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
PUBLIC = ROOT / "frontend" / "public" / "historical9394"
SNAPSHOT = DATA / "historical_snapshot.json"
CATALOG = DATA / "historical_source_catalog.json"
BDF_QUEUE = DATA / "bdfutbol_photo_queue.json"
BELGIUM_CLUBS = DATA / "belgium_1993_94_club_assets.json"
MONDEFOOTBALL_MAPPING = DATA / "mondefootball_club_mapping.json"
BDF_MANAGER_OVERRIDES = DATA / "bdfutbol_manager_profile_overrides.json"
DEFAULT_OUTPUT = DATA / "missing_assets_1993_94.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_ids(directory: Path, suffix: str) -> set[int]:
    out: set[int] = set()
    if not directory.exists():
        return out
    for path in directory.glob(f"*{suffix}"):
        if path.stem.isdigit():
            out.add(int(path.stem))
    return out


def _search_urls(query: str) -> dict[str, str]:
    q = quote_plus(query)
    return {
        "wikimedia_commons": f"https://commons.wikimedia.org/w/index.php?search={q}&title=Special:MediaSearch&type=image",
        "google_images": f"https://www.google.com/search?tbm=isch&q={q}",
        "bing_images": f"https://www.bing.com/images/search?q={q}",
    }


def _country_maps(catalog: dict[str, Any]) -> tuple[dict[int, str], dict[int, str]]:
    countries = {int(row["source_id"]): row.get("name") or row.get("display_name") or str(row["source_id"]) for row in catalog.get("countries", [])}
    cities = {int(row["source_id"]): row.get("name") or str(row["source_id"]) for row in catalog.get("cities", [])}
    return countries, cities


def _bdf_player_map() -> dict[int, dict[str, Any]]:
    if not BDF_QUEUE.exists():
        return {}
    payload = _load(BDF_QUEUE)
    rows = payload.get("players", payload) if isinstance(payload, dict) else payload
    return {int(row["source_id"]): row for row in rows if row.get("source_id") is not None}


def _bdf_club_map() -> dict[int, dict[str, Any]]:
    if not BELGIUM_CLUBS.exists():
        return {}
    return {int(row["team_id"]): row for row in _load(BELGIUM_CLUBS).get("clubs", [])}


def _mondefootball_club_map() -> dict[int, dict[str, Any]]:
    """Return only the manually validated Mondefootball↔MDB mappings."""
    if not MONDEFOOTBALL_MAPPING.exists():
        return {}
    payload = _load(MONDEFOOTBALL_MAPPING)
    rows = list(payload.get("seguros") or [])
    manual = payload.get("a_mano") or {}
    if isinstance(manual, dict):
        rows.extend(dict(value, mf=key) for key, value in manual.items())
    return {int(row["mdb"]): row for row in rows if row.get("mdb") and row.get("mf")}


def _bdf_manager_map() -> dict[int, dict[str, Any]]:
    if not BDF_MANAGER_OVERRIDES.exists():
        return {}
    payload = _load(BDF_MANAGER_OVERRIDES)
    return {int(row["source_id"]): row for row in payload.get("managers", []) if row.get("source_id") is not None}


def _bdf_manual_lookup_url(name: str, role: str) -> str:
    # Google is only used as a discovery index; recover_missing_assets never
    # auto-downloads from search-result pages.  site: narrows the result to BDF.
    return "https://www.google.com/search?q=" + quote_plus(f'site:bdfutbol.com {name} {role}')


def _date10(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    return text[:10] if text else None


def _candidate_common(query: str) -> list[dict[str, Any]]:
    urls = _search_urls(query)
    return [
        {
            "source": "Wikimedia Commons",
            "mode": "api_search_then_download",
            "lookup_url": urls["wikimedia_commons"],
            "automatic": True,
            "license_policy": "only_download_when_commons_returns_a_file_and_license_metadata",
        },
        {"source": "Google Images", "mode": "manual_discovery", "lookup_url": urls["google_images"], "automatic": False},
        {"source": "Bing Images", "mode": "manual_discovery", "lookup_url": urls["bing_images"], "automatic": False},
    ]


def build_manifest() -> dict[str, Any]:
    snapshot = _load(SNAPSHOT)
    catalog = _load(CATALOG)
    countries, cities = _country_maps(catalog)
    bdf_players = _bdf_player_map()
    bdf_clubs = _bdf_club_map()
    monde_clubs = _mondefootball_club_map()
    bdf_managers = _bdf_manager_map()

    player_assets = _file_ids(PUBLIC / "players", ".jpg")
    club_assets = _file_ids(PUBLIC / "clubs", ".gif")
    stadium_assets = _file_ids(PUBLIC / "stadiums", ".jpg")
    manager_assets = _file_ids(PUBLIC / "managers", ".jpg")

    teams = {int(row["source_id"]): row for row in snapshot.get("teams", [])}
    stadiums = {int(row["source_id"]): row for row in catalog.get("stadiums", [])}
    managers = {int(row["source_id"]): row for row in catalog.get("managers", [])}

    players: list[dict[str, Any]] = []
    for row in snapshot.get("players", []):
        sid = int(row["source_id"])
        if sid in player_assets:
            continue
        team = teams.get(int(row.get("team_id") or 0), {})
        country_id = int(row.get("international_country_id") or row.get("birth_country_id") or 0)
        country = countries.get(country_id)
        display = row.get("display_name") or " ".join(filter(None, [row.get("first_name"), row.get("surname1")]))
        query = " ".join(filter(None, [display, team.get("name"), country, "football 1993 1994"]))
        candidates: list[dict[str, Any]] = []
        bdf = bdf_players.get(sid)
        if bdf and bdf.get("bdfutbol_id"):
            bid = str(bdf["bdfutbol_id"])
            candidates.append({
                "source": "BDFutbol",
                "mode": "profile_scrape",
                "profile_url": bdf.get("bdfutbol_url") or f"https://www.bdfutbol.com/en/j/j{bid}.html",
                "bdfutbol_id": bid,
                "automatic": True,
            })
        else:
            candidates.append({
                "source": "BDFutbol",
                "mode": "manual_profile_discovery",
                "lookup_url": _bdf_manual_lookup_url(display, "jugador futbolista"),
                "automatic": False,
            })
        candidates.extend(_candidate_common(query))
        players.append({
            "asset_type": "player",
            "source_id": sid,
            "name": display,
            "team_id": row.get("team_id"),
            "team": team.get("name"),
            "country": country,
            "birth_date": _date10(row.get("birth_date")),
            "position": row.get("broad_position"),
            "runtime_path": f"/historical9394/players/{sid}.jpg",
            "target": {"format": "JPEG", "width": 40, "height": 55, "mode": "RGB"},
            "source_candidates": candidates,
        })

    used_manager_ids = sorted({int(row["manager_id"]) for row in snapshot.get("teams", []) if row.get("manager_id")})
    managers_missing: list[dict[str, Any]] = []
    teams_by_manager: dict[int, list[dict[str, Any]]] = {}
    for team in snapshot.get("teams", []):
        mid = int(team.get("manager_id") or 0)
        if mid:
            teams_by_manager.setdefault(mid, []).append(team)
    for mid in used_manager_ids:
        m = managers.get(mid)
        if not m or mid == 1 or str(m.get("display_name") or "").startswith("(VACIO") or mid in manager_assets:
            continue
        club_names = [t.get("name") for t in teams_by_manager.get(mid, []) if t.get("name")]
        country = countries.get(int(m.get("birth_country_id") or 0))
        display = m.get("display_name") or " ".join(filter(None, [m.get("first_name"), m.get("surname1")]))
        query = " ".join(filter(None, [display, club_names[0] if club_names else None, "football manager 1993 1994"]))
        candidates: list[dict[str, Any]] = []
        bdf = bdf_managers.get(mid)
        if bdf and bdf.get("bdfutbol_url"):
            candidates.append({
                "source": "BDFutbol",
                "mode": "profile_scrape",
                "profile_url": bdf["bdfutbol_url"],
                "bdfutbol_id": str(bdf.get("bdfutbol_id") or ""),
                "automatic": True,
                "identity_verification": bdf.get("verification"),
            })
        else:
            candidates.append({
                "source": "BDFutbol",
                "mode": "manual_profile_discovery",
                "lookup_url": _bdf_manual_lookup_url(display, "entrenador"),
                "automatic": False,
            })
        candidates.extend(_candidate_common(query))
        managers_missing.append({
            "asset_type": "manager",
            "source_id": mid,
            "name": display,
            "clubs": club_names,
            "country": country,
            "birth_date": _date10(m.get("birth_date")),
            "runtime_path": f"/historical9394/managers/{mid}.jpg",
            "target": {"format": "JPEG", "width": 40, "height": 55, "mode": "RGB"},
            "source_candidates": candidates,
        })

    clubs_missing: list[dict[str, Any]] = []
    league_by_id = {int(row["source_id"]): row for row in snapshot.get("leagues", [])}
    for team in snapshot.get("teams", []):
        tid = int(team["source_id"])
        if tid in club_assets:
            continue
        synthetic = str(team.get("name") or "").startswith("Otros-")
        league = league_by_id.get(int(team.get("league_id") or 0), {})
        query = " ".join(filter(None, [team.get("name"), league.get("country"), "football club crest logo"])).strip()
        candidates: list[dict[str, Any]] = []
        bdf = bdf_clubs.get(tid)
        if bdf and bdf.get("bdfutbol_crest_url"):
            candidates.append({"source": "BDFutbol", "mode": "direct_image", "download_url": bdf["bdfutbol_crest_url"], "automatic": True})
        monde = monde_clubs.get(tid)
        if monde:
            candidates.append({
                "source": "Mondefootball",
                "mode": "direct_image",
                "download_url": f"https://s.hs-data.com/gfx/emblem/common/150x150/{monde['mf']}.png",
                "profile_url": f"https://www.mondefootball.fr/teams/te{monde['mf']}/x/",
                "automatic": True,
                "identity_verification": {"mdb_team_id": tid, "mondefootball_id": str(monde["mf"]), "name": monde.get("nombre")},
            })
        if not synthetic:
            candidates.extend(_candidate_common(query))
        clubs_missing.append({
            "asset_type": "club_crest",
            "source_id": tid,
            "name": team.get("name"),
            "country": league.get("country"),
            "synthetic_container": synthetic,
            "runtime_path": f"/historical9394/clubs/{tid}.gif",
            "target": {"format": "GIF", "width": 40, "height": 40, "mode": "P", "transparent": True},
            "source_candidates": candidates,
            "fallback": "generate_neutral_game_crest" if synthetic else None,
        })

    used_stadium_ids = sorted({int(row["stadium_id"]) for row in snapshot.get("teams", []) if row.get("stadium_id")})
    teams_by_stadium: dict[int, list[str]] = {}
    for team in snapshot.get("teams", []):
        sid = int(team.get("stadium_id") or 0)
        if sid:
            teams_by_stadium.setdefault(sid, []).append(team.get("name"))
    stadiums_missing: list[dict[str, Any]] = []
    for sid in used_stadium_ids:
        if sid in stadium_assets:
            continue
        row = stadiums.get(sid, {})
        city = cities.get(int(row.get("city_id") or 0))
        name = row.get("name") or row.get("short_name") or f"Estadio {sid}"
        clubs = [x for x in teams_by_stadium.get(sid, []) if x]
        query = " ".join(filter(None, [name, city, clubs[0] if clubs else None, "stadium football"])).strip()
        stadiums_missing.append({
            "asset_type": "stadium",
            "source_id": sid,
            "name": name,
            "short_name": row.get("short_name"),
            "city": city,
            "clubs": clubs,
            "capacity": row.get("capacity"),
            "runtime_path": f"/historical9394/stadiums/{sid}.jpg",
            "target": {"format": "JPEG", "width": 100, "height": 75, "mode": "RGB"},
            "source_candidates": _candidate_common(query),
        })

    categories = {
        "players": players,
        "managers": managers_missing,
        "club_crests": clubs_missing,
        "stadiums": stadiums_missing,
    }
    counts = {key: len(value) for key, value in categories.items()}
    counts["total"] = sum(counts.values())
    counts["synthetic_club_crests"] = sum(1 for row in clubs_missing if row.get("synthetic_container"))
    return {
        "schema_version": 1,
        "season": snapshot.get("season", "1993-94"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "only_missing_runtime_assets": True,
            "remote_sources_are_candidates_not_identity_truth": True,
            "historical_identity_must_not_be_overwritten_by_modern_metadata": True,
            "automatic_download_order": ["BDFutbol when exact identity mapping exists", "Wikimedia Commons"],
            "manual_fallback_sources": ["BDFutbol profile discovery", "Google Images", "Bing Images"],
        },
        "counts": counts,
        **categories,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_manifest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
