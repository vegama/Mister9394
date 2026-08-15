from __future__ import annotations

"""Persistent 1993-94 world-season orchestration.

Competition engines remain independent and historically specialised.  This
module is the layer that turns them into one career season: one seed, one list
of admitted competitions, honours, movement links and a durable save artifact.
It deliberately refuses to invent missing promotion feeders or continental
slots; unresolved links are recorded so a later rollover cannot silently use a
modern/default rule.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .snapshot_runtime import FootballUniverseSnapshot9394, default_runtime_snapshot
from .world_competitions import simulate_runtime_competitions

WORLD_SAVE_SCHEMA = 1


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ids(row: dict[str, Any], *names: str) -> tuple[int, ...]:
    out: list[int] = []
    for name in names:
        value = row.get(name)
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            values = value
        else:
            values = (value,)
        for item in values:
            parsed = _as_int(item)
            if parsed is not None and parsed not in out:
                out.append(parsed)
    return tuple(out)


def _team_label(universe: FootballUniverseSnapshot9394, team_id: int | None) -> str | None:
    if team_id is None:
        return None
    team = universe.team(team_id)
    return team.get("name") if team else f"Equipo MDB {team_id}"


def _honours_for(row: dict[str, Any], universe: FootballUniverseSnapshot9394) -> list[dict[str, Any]]:
    honours: list[dict[str, Any]] = []
    source_key = str(row["source_key"])
    name = str(row["name"])

    def add(team_id: Any, label: str) -> None:
        parsed = _as_int(team_id)
        if parsed is None:
            return
        honours.append({
            "team_id": parsed,
            "team_name": _team_label(universe, parsed),
            "competition": source_key,
            "competition_name": name,
            "honour": label,
        })

    add(row.get("champion_team_id"), "Campeón")
    add(row.get("group_champion_team_id"), "Campeón de grupo")
    add(row.get("apertura_champion_team_id"), "Campeón Apertura")
    add(row.get("clausura_champion_team_id"), "Campeón Clausura")
    return honours


# Connections for which both sides are present and the 1993-94 movement rule is
# already modelled by a dedicated runtime. Lower boundary exits remain explicit
# because their feeder competition is not an admitted MDB competition.
KNOWN_MOVEMENT_LINKS = (
    ("league:1", "league:2", "relegated_team_ids", "Primera → Segunda"),
    ("league:2", "league:1", "promoted_to_primera", "Segunda → Primera"),
    ("league:2", "segundab", "relegated_team_ids", "Segunda → Segunda B"),
    ("league:2", "segundab", "promoted_from_segundab", "Segunda B → Segunda"),
    ("league:4", "league:102", "relegated_team_ids", "Serie A → Serie B"),
    ("league:102", "league:4", "promoted_team_ids", "Serie B → Serie A"),
    ("league:31", "league:54", "relegated_team_ids", "Eredivisie → Eerste Divisie"),
    ("league:54", "league:31", "promoted_team_ids", "Eerste Divisie → Eredivisie"),
)


def _movement_report(rows: dict[str, dict[str, Any]], universe: FootballUniverseSnapshot9394) -> dict[str, Any]:
    links: list[dict[str, Any]] = []
    consumed: set[tuple[str, str]] = set()
    for source, target, field, label in KNOWN_MOVEMENT_LINKS:
        row = rows.get(source)
        if not row:
            continue
        ids = _ids(row, field)
        if not ids:
            continue
        consumed.add((source, field))
        links.append({
            "source": source,
            "target": target,
            "rule": field,
            "label": label,
            "team_ids": list(ids),
            "teams": [_team_label(universe, team_id) for team_id in ids],
            "resolved": True,
        })

    # Some specialised outputs repeat movement on both sides of the same link.
    # Consume those aliases so they do not become fake rollover blockers.
    consumed.add(("league:1", "promoted_team_ids"))
    for source_id in (3, 9, 10, 11):
        consumed.add((f"league:{source_id}", "promoted_team_ids"))
    consumed.add(("tournament:88", "promoted_team_ids"))

    unresolved: list[dict[str, Any]] = []
    for key, row in sorted(rows.items()):
        fields = ["promoted_team_ids", "relegated_team_ids", "relegated_team_id"]
        if key in {"league:3", "league:9", "league:10", "league:11"}:
            fields.append("direct_or_forced_relegated")
        for field in fields:
            ids = _ids(row, field)
            if not ids or (key, field) in consumed:
                continue
            unresolved.append({
                "source": key,
                "rule": field,
                "team_ids": list(ids),
                "teams": [_team_label(universe, team_id) for team_id in ids],
                "resolved": False,
                "reason": "destination_or_feeder_not_present_as_certified_1993_94_runtime",
            })
    return {"resolved_links": links, "unresolved_links": unresolved}


def _continental_seed_report(rows: dict[str, dict[str, Any]], universe: FootballUniverseSnapshot9394) -> dict[str, Any]:
    """Return only continental entries that can be derived without guessing.

    National champions are safe candidates for the next European Cup. Spain's
    Copa del Rey winner is a safe Cup Winners' Cup candidate. UEFA Cup places
    are intentionally not guessed until country-by-country allocation and cup
    interactions are modelled.
    """
    european_league_keys = (
        "league:14", "league:31", "league:13", "league:4", "league:5",
        "league:32", "league:1", "league:38",
    )
    european_cup: list[dict[str, Any]] = []
    for key in european_league_keys:
        row = rows.get(key)
        if not row:
            continue
        team_id = _as_int(row.get("champion_team_id"))
        if team_id is not None:
            european_cup.append({"source": key, "team_id": team_id, "team_name": _team_label(universe, team_id)})
    cup_winners: list[dict[str, Any]] = []
    copa = rows.get("tournament:3")
    if copa:
        team_id = _as_int(copa.get("champion_team_id"))
        if team_id is not None:
            cup_winners.append({"source": "tournament:3", "team_id": team_id, "team_name": _team_label(universe, team_id)})
    return {
        "next_season": "1994-95",
        "european_cup_known_candidates": european_cup,
        "cup_winners_cup_known_candidates": cup_winners,
        "uefa_cup_status": "pending_country_slot_allocation",
        "complete": False,
        "note": "No se inventan plazas continentales no derivables de las competiciones activas.",
    }



def _project_pool(initial: list[int], *, outgoing: tuple[int, ...], incoming: tuple[int, ...], expected: int) -> dict[str, Any]:
    pool = [team_id for team_id in initial if team_id not in set(outgoing)]
    for team_id in incoming:
        if team_id not in pool:
            pool.append(team_id)
    return {
        "team_ids": pool,
        "expected": expected,
        "actual": len(pool),
        "unique": len(pool) == len(set(pool)),
        "ready": len(pool) == expected and len(pool) == len(set(pool)),
    }


def _rollover_projection(rows: dict[str, dict[str, Any]], universe: FootballUniverseSnapshot9394) -> dict[str, Any]:
    initial = {league_id: [int(team["source_id"]) for team in universe.teams(league_id=league_id)]
               for league_id in (1, 2, 3, 9, 10, 11, 4, 102, 31, 54)}
    pools: dict[str, dict[str, Any]] = {}

    # Spain: Primera and Segunda exchange clubs normally. Segunda B is the
    # represented floor: promoted clubs leave and the four relegated Segunda
    # clubs fill those vacancies. There are no sporting exits to an invented
    # Tercera. Regional placement is deliberately slot-preserving until richer
    # geographical source data is imported.
    primera = rows["league:1"]; segunda = rows["league:2"]
    pools["league:1"] = _project_pool(initial[1], outgoing=_ids(primera, "relegated_team_ids"),
                                      incoming=_ids(segunda, "promoted_to_primera"), expected=20)
    pools["league:2"] = _project_pool(
        initial[2],
        outgoing=_ids(segunda, "promoted_to_primera", "relegated_team_ids"),
        incoming=_ids(primera, "relegated_team_ids") + _ids(segunda, "promoted_from_segundab"),
        expected=20,
    )

    promoted_from_b = set(_ids(segunda, "promoted_from_segundab"))
    incoming_to_b = list(_ids(segunda, "relegated_team_ids"))
    group_ids = (3, 9, 10, 11)
    group_remaining: dict[int, list[int]] = {}
    group_vacancies: dict[int, int] = {}
    structural_exits: dict[int, tuple[int, ...]] = {}
    for source_id in group_ids:
        row = rows[f"league:{source_id}"]
        structural = _ids(row, "structural_exit_team_ids")
        structural_exits[source_id] = structural
        outgoing = promoted_from_b | set(structural)
        remaining = [team_id for team_id in initial[source_id] if team_id not in outgoing]
        group_remaining[source_id] = remaining
        group_vacancies[source_id] = 20 - len(remaining)

    incoming_cursor = 0
    for source_id in group_ids:
        vacancies = group_vacancies[source_id]
        additions = incoming_to_b[incoming_cursor:incoming_cursor + vacancies]
        incoming_cursor += len(additions)
        team_ids = group_remaining[source_id] + additions
        structural = structural_exits[source_id]
        ready = len(team_ids) == 20 and len(set(team_ids)) == 20 and not structural
        pools[f"league:{source_id}"] = {
            "team_ids": team_ids, "expected": 20, "actual": len(team_ids),
            "unique": len(team_ids) == len(set(team_ids)), "ready": ready,
            "pyramid_floor": True, "sporting_relegation": False,
            "regrouping_method": "vacancy_preserving_data_limited",
        }
        if structural:
            pools[f"league:{source_id}"]["blocker"] = "forced_reserve_exit_needs_external_lower_tier_replacement"
            pools[f"league:{source_id}"]["structural_exit_team_ids"] = list(structural)
    if incoming_cursor != len(incoming_to_b):
        for source_id in group_ids:
            pools[f"league:{source_id}"]["ready"] = False
            pools[f"league:{source_id}"]["blocker"] = "segundab_vacancy_balance_mismatch"

    # Italy: Serie B is now the represented floor. Four clubs can go up and the
    # four relegated Serie-A clubs replace them; no Serie-C feeder is required.
    serie_a = rows["league:4"]; serie_b = rows["league:102"]
    pools["league:4"] = _project_pool(initial[4], outgoing=_ids(serie_a, "relegated_team_ids"),
                                      incoming=_ids(serie_b, "promoted_team_ids"), expected=18)
    pools["league:102"] = _project_pool(initial[102], outgoing=_ids(serie_b, "promoted_team_ids"),
                                        incoming=_ids(serie_a, "relegated_team_ids"), expected=20)
    pools["league:102"]["pyramid_floor"] = True
    pools["league:102"]["sporting_relegation"] = False

    # Netherlands: the admitted two-level system is self-contained. Eerste is
    # the represented floor and has no downward movement.
    ered = rows["league:31"]; eerste = rows["league:54"]
    pools["league:31"] = _project_pool(initial[31], outgoing=_ids(ered, "relegated_team_ids"),
                                       incoming=_ids(eerste, "promoted_team_ids"), expected=18)
    pools["league:54"] = _project_pool(initial[54], outgoing=_ids(eerste, "promoted_team_ids"),
                                       incoming=_ids(ered, "relegated_team_ids"), expected=18)
    pools["league:54"]["pyramid_floor"] = True
    pools["league:54"]["sporting_relegation"] = False

    # Every other admitted national league is currently the lowest represented
    # level in its country. Keep its runtime participant pool stable into the
    # next season instead of fabricating clubs from an absent lower division.
    # Brazil is sourced from the 32-club historical runtime rather than the
    # contaminated 20-club MDB league row.
    for comp in universe.career_competitions():
        if comp.get("kind") != "league":
            continue
        source_id = int(comp["source_id"])
        key = f"league:{source_id}"
        if key in pools:
            continue
        runtime = rows.get(key)
        if runtime is None:
            continue
        explicit = runtime.get("participant_team_ids")
        if explicit:
            team_ids = [int(team_id) if str(team_id).isdigit() else str(team_id) for team_id in explicit]
        else:
            team_ids = [int(team["source_id"]) for team in universe.teams(league_id=source_id)]
        expected = int(runtime.get("clubs") or comp.get("team_count") or len(team_ids))
        pools[key] = {
            "team_ids": team_ids, "expected": expected, "actual": len(team_ids),
            "unique": len(team_ids) == len(set(team_ids)),
            "ready": len(team_ids) == expected and len(team_ids) == len(set(team_ids)),
            "pyramid_floor": True, "sporting_relegation": False,
            "rollover_method": "carry_forward_represented_pool",
        }

    return {
        "target_season": "1994-95",
        "competition_pools": pools,
        "ready_source_keys": sorted(key for key, value in pools.items() if value.get("ready")),
        "blocked_source_keys": sorted(key for key, value in pools.items() if not value.get("ready")),
        "floor_policy": "lowest_represented_division_has_no_sporting_relegation",
        "admitted_league_count": sum(1 for comp in universe.career_competitions() if comp.get("kind") == "league"),
        "projected_league_count": len(pools),
        "all_admitted_leagues_ready": not any(not value.get("ready") for value in pools.values())
            and len(pools) == sum(1 for comp in universe.career_competitions() if comp.get("kind") == "league"),
    }

def simulate_world_season_1993_94(*, seed: int = 9394, universe: FootballUniverseSnapshot9394 | None = None) -> dict[str, Any]:
    universe = universe or default_runtime_snapshot()
    gate = simulate_runtime_competitions(seed_offset=int(seed))
    active_keys = set(gate["active_source_keys"])
    competition_rows = [row for row in gate["competitions"] if row["source_key"] in active_keys]
    by_key = {str(row["source_key"]): row for row in competition_rows}
    honours = [honour for row in competition_rows for honour in _honours_for(row, universe)]
    club_honours: dict[str, list[dict[str, Any]]] = {}
    for honour in honours:
        club_honours.setdefault(str(honour["team_id"]), []).append(honour)

    movement = _movement_report(by_key, universe)
    continental = _continental_seed_report(by_key, universe)
    rollover_projection = _rollover_projection(by_key, universe)
    created = datetime.now(timezone.utc).isoformat()
    return {
        "schema": WORLD_SAVE_SCHEMA,
        "career_id": str(uuid4()),
        "season": "1993-94",
        "seed": int(seed),
        "created_at": created,
        "status": "complete" if gate["all_active_pass"] else "failed",
        "source": "normalized_mdb_snapshot",
        "competition_count": len(competition_rows),
        "all_competitions_complete": len(competition_rows) == 26 and all(bool(row.get("ok")) for row in competition_rows),
        "competitions": competition_rows,
        "honours": honours,
        "club_honours": club_honours,
        "movement": movement,
        "continental_qualification": continental,
        "rollover": {
            "target_season": "1994-95",
            "ready": not movement["unresolved_links"] and rollover_projection["all_admitted_leagues_ready"] and continental["complete"],
            "domestic_ready": not movement["unresolved_links"] and rollover_projection["all_admitted_leagues_ready"],
            "unresolved_movement_links": len(movement["unresolved_links"]),
            "continental_complete": continental["complete"],
            "participant_projection": rollover_projection,
        },
        "gate": {
            "active_declared": gate["active_declared"],
            "active_executed": gate["active_executed"],
            "technical_certified": gate["technical_certified"],
            "all_active_pass": gate["all_active_pass"],
            "seconds": gate["seconds"],
        },
    }


@dataclass(slots=True)
class WorldCareerStore9394:
    root: Path

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, career_id: str) -> Path:
        safe = "".join(ch for ch in str(career_id) if ch.isalnum() or ch in "-_")
        if not safe:
            raise ValueError("career_id inválido")
        return self.root / f"{safe}.json"

    def save(self, payload: dict[str, Any]) -> Path:
        career_id = str(payload.get("career_id") or "")
        path = self.path_for(career_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return path

    def load(self, career_id: str) -> dict[str, Any]:
        path = self.path_for(career_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if int(payload.get("schema", 0)) != WORLD_SAVE_SCHEMA:
            raise ValueError(f"schema de carrera no soportado: {payload.get('schema')}")
        return payload
