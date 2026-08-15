from __future__ import annotations

"""Source-backed national-team layer for Míster 93/94.

The MDB exposes `PaisInternacional` on players even though it does not contain a
physical national-team table. We therefore build selections from that explicit
international association, falling back to birth country only when no
international association exists. No club player is duplicated or invented.
"""

from dataclasses import dataclass
from typing import Any

from .snapshot_runtime import FootballUniverseSnapshot9394, PRESENTATION_COUNTRIES

SQUAD_SIZE_9394 = 22


@dataclass(frozen=True, slots=True)
class NationalTeamSummary9394:
    country_id: int
    name: str
    eligible_players: int
    average_top_22: float


def _country_id(player: dict[str, Any]) -> int | None:
    value = player.get("international_country_id") or player.get("birth_country_id")
    return int(value) if isinstance(value, int) and value > 0 else None


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
        if len(players) < 18:
            continue
        ratings = sorted((int(p.get("overall") or p.get("category") or 60) for p in players), reverse=True)
        top = ratings[:SQUAD_SIZE_9394]
        output.append(NationalTeamSummary9394(
            country_id=cid,
            name=PRESENTATION_COUNTRIES[cid],
            eligible_players=len(players),
            average_top_22=round(sum(top) / len(top), 1),
        ))
    return sorted(output, key=lambda row: (-row.average_top_22, row.name))


def _rating(player: dict[str, Any], development: dict[str, dict[str, Any]] | None) -> int:
    if development:
        state = development.get(str(player["source_id"]))
        if state and state.get("overall") is not None:
            return int(state["overall"])
    return int(player.get("overall") or player.get("category") or 60)


def select_national_squad(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
    size: int = SQUAD_SIZE_9394,
) -> list[dict[str, Any]]:
    if country_id not in PRESENTATION_COUNTRIES:
        raise KeyError(f"país {country_id} sin nombre fiable en el snapshot")
    eligible = [p for p in universe.payload.get("players", []) if not p.get("retired") and _country_id(p) == country_id]
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

    # 22-man balanced pool: 3 GK, 7 DEF, 7 MID, 5 FWD. If a source country is
    # position-poor, fill the remainder with the best eligible real players.
    quotas = {"POR": 3, "DEF": 7, "MED": 7, "DEL": 5}
    selected: list[dict[str, Any]] = []
    for pos, quota in quotas.items():
        selected.extend(by_pos[pos][:quota])
    if len(selected) < size:
        remaining = [p for p in eligible if p not in selected]
        remaining.sort(key=lambda p: (-_rating(p, development), str(p.get("display_name") or "")))
        selected.extend(remaining[: size - len(selected)])
    selected = selected[:size]

    output = []
    for player in selected:
        api = universe.player_api(player)
        if development:
            state = development.get(str(player["source_id"]), {})
            api["overall"] = state.get("overall", api.get("overall"))
            api["form"] = state.get("form")
            api["morale"] = state.get("morale")
            api["condition"] = state.get("condition")
            if int(state.get("injury_days") or 0) > 0:
                api["status"] = f"Lesionado · {state['injury_days']} d"
        output.append(api)
    return output


def national_team_snapshot(
    universe: FootballUniverseSnapshot9394,
    country_id: int,
    *,
    development: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    squad = select_national_squad(universe, country_id, development=development)
    return {
        "country_id": int(country_id),
        "name": PRESENTATION_COUNTRIES[int(country_id)],
        "squad_size": len(squad),
        "squad": squad,
        "selection_policy": "PaisInternacional; fallback PaisNacimiento",
        "source_backed": True,
    }
