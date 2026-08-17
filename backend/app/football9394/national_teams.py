from __future__ import annotations

"""National-team layer for the frozen 1993-94 universe.

Most selections are built from the source player's explicit international
association, falling back to birth country.  USA 1994 is special: the project
bundles the complete 24 x 22 historical squads and maps every squad slot to one
unique runtime player.  This gives the 1994 World Championship exact historical
participants and exact historical player pools while later career tournaments
remain alternate history.
"""

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from .snapshot_runtime import FootballUniverseSnapshot9394, PRESENTATION_COUNTRIES, REPO_ROOT

SQUAD_SIZE_9394 = 22
WORLD_CUP_1994_DATA = REPO_ROOT / "data" / "football9394" / "world_cup_1994_squads.json"


@lru_cache(maxsize=1)
def _world_cup_1994_data() -> dict[str, Any]:
    try:
        return json.loads(Path(WORLD_CUP_1994_DATA).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"teams": []}


def world_cup_1994_team_info(country_id: int) -> dict[str, Any] | None:
    for team in _world_cup_1994_data().get("teams", []):
        if int(team.get("country_id") or 0) == int(country_id):
            players = list(team.get("players") or [])
            ids = [int(row["resolved_source_id"]) for row in players if row.get("resolved_source_id") is not None]
            return {
                "country_id": int(country_id),
                "team_code": team.get("team_code"),
                "name": team.get("name") or PRESENTATION_COUNTRIES.get(int(country_id)),
                "group": team.get("group"),
                "head_coach": team.get("historical_head_coach") or team.get("head_coach"),
                "squad_size": len(players),
                "resolved_players": len(ids),
                "complete": len(players) == SQUAD_SIZE_9394 and len(ids) == SQUAD_SIZE_9394 and len(set(ids)) == SQUAD_SIZE_9394,
                "player_ids": ids,
            }
    return None


def world_cup_1994_country_ids() -> list[int]:
    return [int(team["country_id"]) for team in _world_cup_1994_data().get("teams", [])]


def world_cup_1994_player_ids(universe: FootballUniverseSnapshot9394, country_id: int) -> list[int]:
    info = world_cup_1994_team_info(country_id)
    if not info or not info["complete"]:
        return []
    ids = [int(pid) for pid in info["player_ids"]]
    if any(pid not in universe.players_by_id for pid in ids):
        return []
    return ids


@dataclass(frozen=True, slots=True)
class NationalTeamSummary9394:
    country_id: int
    name: str
    eligible_players: int
    average_top_22: float
    depth_ready_40: bool = False
    depth_gap_to_40: int = 0
    qualified_1994: bool = False
    world_cup_1994_group: str | None = None
    world_cup_1994_squad_complete: bool = False
    historical_head_coach: str | None = None


def _country_id(player: dict[str, Any]) -> int | None:
    value = player.get("international_country_id") or player.get("birth_country_id")
    return int(value) if isinstance(value, int) and value > 0 else None


def eligible_national_players(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    players = [p for p in universe.payload.get("players", []) if not p.get("retired") and _country_id(p) == int(country_id)]
    players.sort(key=lambda p: (-_rating(p, development), str(p.get("display_name") or ""), int(p.get("source_id") or 0)))
    return players


def _functional_pool(players: list[dict[str, Any]]) -> bool:
    """A selectable national team must be able to name a credible 22-man squad.

    The thresholds deliberately leave some tactical freedom while preventing a
    country from being labelled "functional" just because it has 18 names in
    the mixed source catalogue. USA 94 squads satisfy this by construction.
    """
    if len(players) < SQUAD_SIZE_9394:
        return False
    counts = {pos: 0 for pos in ("POR", "DEF", "MED", "DEL")}
    for player in players:
        pos = str(player.get("broad_position") or "MED").upper()
        if pos in counts:
            counts[pos] += 1
    return counts["POR"] >= 2 and counts["DEF"] >= 5 and counts["MED"] >= 5 and counts["DEL"] >= 3


def national_team_catalog(universe: FootballUniverseSnapshot9394) -> list[NationalTeamSummary9394]:
    by_country: dict[int, list[dict[str, Any]]] = {}
    for player in universe.payload.get("players", []):
        if player.get("retired"):
            continue
        cid = _country_id(player)
        if cid is None or cid not in PRESENTATION_COUNTRIES:
            continue
        by_country.setdefault(cid, []).append(player)
    output: list[NationalTeamSummary9394] = []
    for cid, players in by_country.items():
        if not _functional_pool(players):
            continue
        ratings = sorted((int(p.get("overall") or p.get("category") or 60) for p in players), reverse=True)
        top = ratings[:SQUAD_SIZE_9394]
        wc = world_cup_1994_team_info(cid)
        output.append(NationalTeamSummary9394(
            country_id=cid,
            name=PRESENTATION_COUNTRIES[cid],
            eligible_players=len(players),
            average_top_22=round(sum(top) / len(top), 1),
            depth_ready_40=len(players) >= 38,
            depth_gap_to_40=max(0, 40 - len(players)),
            qualified_1994=wc is not None,
            world_cup_1994_group=(wc or {}).get("group"),
            world_cup_1994_squad_complete=bool((wc or {}).get("complete")),
            historical_head_coach=(wc or {}).get("head_coach"),
        ))
    return sorted(output, key=lambda row: (-row.average_top_22, row.name))


def _rating(player: dict[str, Any], development: dict[str, dict[str, Any]] | None) -> int:
    if development:
        state = development.get(str(player["source_id"]))
        if state and state.get("overall") is not None:
            return int(state["overall"])
    return int(player.get("overall") or player.get("category") or 60)


def _api_with_development(universe: FootballUniverseSnapshot9394, player: dict[str, Any], development: dict[str, dict[str, Any]] | None) -> dict[str, Any]:
    api = universe.player_api(player)
    if development:
        state = development.get(str(player["source_id"]), {})
        api["overall"] = state.get("overall", api.get("overall"))
        api["form"] = state.get("form")
        api["morale"] = state.get("morale")
        api["condition"] = state.get("condition")
        if int(state.get("injury_days") or 0) > 0:
            api["status"] = f"Lesionado · {state['injury_days']} d"
    return api


def select_national_squad(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
    size: int = SQUAD_SIZE_9394,
) -> list[dict[str, Any]]:
    if country_id not in PRESENTATION_COUNTRIES:
        raise KeyError(f"país {country_id} sin nombre fiable en el snapshot")
    eligible = eligible_national_players(universe, country_id, development=development)
    if len(eligible) < min(size, 11):
        raise ValueError(f"{PRESENTATION_COUNTRIES[country_id]} sólo tiene {len(eligible)} jugadores elegibles")

    by_pos = {pos: [] for pos in ("POR", "DEF", "MED", "DEL")}
    for player in eligible:
        pos = str(player.get("broad_position") or "MED").upper()
        if pos not in by_pos:
            pos = "MED"
        by_pos[pos].append(player)
    for rows in by_pos.values():
        rows.sort(key=lambda p: (-_rating(p, development), str(p.get("display_name") or "")))

    quotas = {"POR": 3, "DEF": 7, "MED": 7, "DEL": 5}
    selected: list[dict[str, Any]] = []
    for pos, quota in quotas.items():
        selected.extend(by_pos[pos][:quota])
    if len(selected) < size:
        remaining = [p for p in eligible if p not in selected]
        remaining.sort(key=lambda p: (-_rating(p, development), str(p.get("display_name") or "")))
        selected.extend(remaining[: size - len(selected)])
    return [_api_with_development(universe, player, development) for player in selected[:size]]


def national_squad_from_player_ids(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    player_ids: list[int],
    *,
    development: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    eligible={int(row["source_id"]):row for row in eligible_national_players(universe,country_id,development=development)}
    output=[]
    for player_id in player_ids:
        row=eligible.get(int(player_id))
        if row is not None:
            output.append(_api_with_development(universe,row,development))
    return output


def historical_world_cup_1994_squad(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return national_squad_from_player_ids(universe,country_id,world_cup_1994_player_ids(universe,country_id),development=development)


def national_team_snapshot(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
    selected_player_ids: list[int] | None = None,
) -> dict[str, Any]:
    squad = (national_squad_from_player_ids(universe,country_id,selected_player_ids,development=development) if selected_player_ids else select_national_squad(universe, country_id, development=development))
    wc = world_cup_1994_team_info(country_id)
    historical_squad = historical_world_cup_1994_squad(universe, country_id, development=development) if wc and wc.get("complete") else []
    return {
        "country_id": int(country_id),
        "name": PRESENTATION_COUNTRIES[int(country_id)],
        "squad_size": len(squad),
        "squad": squad,
        "selection_policy": "PaisInternacional; fallback PaisNacimiento",
        "source_backed": True,
        "qualified_1994": wc is not None,
        "world_cup_1994": ({**wc, "squad": historical_squad} if wc else None),
    }
