from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .laws import LAWS_1993_94
from .match_engine import (
    FootballMatchEngine9394,
    FootballTactics9394,
    Footballer9394,
    SPAIN_PRIMERA_SIMULATION_1993_94,
    TeamSheet9394,
)
from .registry import UnresolvedHistoricalRulesError, default_registry_9394
from .rules import SPAIN_PRIMERA_1993_94
from .snapshot_runtime import default_runtime_snapshot
from .team_builder import build_snapshot_team_sheet
from .standings import LeagueMatch9394, build_league_table
from .source_rules import audit_snapshot_competitions
from .pyramid_activation import audit_competition_activation
from .pyramid_floor import active_pyramid_floors, is_floor_league
from .world_career import simulate_world_season_1993_94
from .product_meta import product_version
from .app_paths import default_app_paths
from .webapp_contracts import TacticsPayload, SimulatePayload, WorldSeasonPayload
from .manager_routes import router as manager_router, _load_manager_career, _career_store

CAREER_SAVE_ROOT = default_app_paths().saves

app = FastAPI(title="Míster 93/94 API", version=product_version())
app.include_router(manager_router)




















































def _player(team: str, index: int, position: str, level: int) -> Footballer9394:
    goalkeeper = level if position == "GK" else 8
    return Footballer9394(
        id=f"{team}-{index}", name=f"{team} {index+1}", position=position, overall=level,
        pace=level, stamina=level, technique=level, short_pass=level, long_pass=level,
        creativity=level, finishing=level, heading=level, tackling=level, marking=level,
        positioning=level, discipline=72, leadership=70, goalkeeping=goalkeeper,
    )


def _sheet(name: str, level: int, tactics: TacticsPayload) -> TeamSheet9394:
    safe = "-".join(name.casefold().split())
    positions = ("GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST")
    bench_positions = ("GK", "DF", "DF", "MF", "ST")
    starters = tuple(_player(safe, i, pos, level) for i, pos in enumerate(positions))
    bench = tuple(_player(f"{safe}-b", i, pos, max(45, level - 3)) for i, pos in enumerate(bench_positions))
    return TeamSheet9394(
        team_id=safe,
        team_name=name,
        starters=starters,
        bench=bench,
        tactics=FootballTactics9394(**tactics.model_dump()),
    )


@app.get("/api/football9394/health")
def health() -> dict:
    return {
        "ok": True,
        "version": product_version(),
        "season": "1993-94",
        "players_per_team": LAWS_1993_94.players_per_team,
        "max_used_substitutes": LAWS_1993_94.max_used_substitutes,
        "domain": "football-native",
        "historical_data": {
            "loaded": True,
            "counts": default_runtime_snapshot().counts,
        },
    }


@app.get("/api/football9394/universe")
def universe() -> dict:
    return default_runtime_snapshot().universe_summary()


@app.get("/api/football9394/competitions")
def competitions(include_blocked: bool = False, include_non_admitted: bool = False) -> list[dict]:
    rows = default_runtime_snapshot().competitions()
    audit_rows = audit_snapshot_competitions(rows)
    audits = {(entry.ref.kind, entry.ref.source_id): entry for entry in audit_rows}
    activation_rows, _ = audit_competition_activation(rows, audit_rows)
    activation = {(entry.kind, entry.source_id): entry for entry in activation_rows}
    floors = active_pyramid_floors(rows)
    output = []
    for row in rows:
        key = (row["kind"], row["source_id"])
        audit = audits[key]
        active = activation[key]
        if not include_non_admitted and not row.get("admitted", True):
            continue
        if not include_blocked and not active.active:
            continue
        floor = is_floor_league(row, floors)
        output.append({**row, "rule_status": audit.status, "simulation_ready": audit.simulation_ready,
                       "pyramid_eligible": active.pyramid_eligible, "active": active.active,
                       "activation_reason": active.reason, "ruleset_id": audit.ruleset_id,
                       "format_id": audit.format_id, "rule_notes": list(audit.notes),
                       "pyramid_floor": floor, "sporting_relegation_enabled": not floor})
    return output


@app.get("/api/football9394/rule-audit")
def rule_audit() -> dict:
    rows = default_runtime_snapshot().competitions()
    entries = audit_snapshot_competitions(rows)
    activation, pyramids = audit_competition_activation(rows, entries)
    floors = active_pyramid_floors(rows)
    terminal_excluded = [entry for entry in activation if not entry.active and entry.reason == "source_not_admitted"]
    unresolved = [entry for entry in activation if not entry.active and entry.reason != "source_not_admitted"]
    return {
        "season": "1993-94",
        "total": len(entries),
        "simulation_ready": sum(entry.simulation_ready for entry in entries),
        "active": sum(entry.active for entry in activation),
        "excluded": len(terminal_excluded),
        "non_admitted": len(terminal_excluded),
        "unresolved": len(unresolved),
        "all_source_rows_closed": len(terminal_excluded) + sum(entry.active for entry in activation) == len(entries) and not unresolved,
        "pyramid_floors": {country: {
            "lowest_level": floor.lowest_level, "league_source_ids": list(floor.league_source_ids),
            "sporting_relegation_enabled": False,
        } for country, floor in sorted(floors.items())},
        "pyramids": {country: {
            "levels": list(state.league_levels), "active": state.active, "reason": state.reason
        } for country, state in sorted(pyramids.items())},
        "competitions": [
            {**audit.to_dict(), "pyramid_eligible": active.pyramid_eligible,
             "active": active.active, "activation_reason": active.reason}
            for audit, active in zip(entries, activation, strict=True)
        ],
    }


@app.get("/api/football9394/teams")
def teams(league_id: int | None = None) -> list[dict]:
    return default_runtime_snapshot().teams(league_id=league_id)


@app.get("/api/football9394/teams/{team_id}")
def team(team_id: int) -> dict:
    row = default_runtime_snapshot().team(team_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Equipo MDB {team_id} no encontrado en el snapshot 1993-94")
    return row


@app.get("/api/football9394/teams/{team_id}/squad")
def team_squad(team_id: int) -> list[dict]:
    universe = default_runtime_snapshot()
    if universe.team(team_id) is None:
        raise HTTPException(status_code=404, detail=f"Equipo MDB {team_id} no encontrado en el snapshot 1993-94")
    return universe.squad(team_id)


@app.get("/api/football9394/players")
def players(query: str = "", limit: int = 20, exclude_team_id: int | None = None) -> list[dict]:
    return default_runtime_snapshot().search_players(query, limit=limit, exclude_team_id=exclude_team_id)


@app.get("/api/football9394/teams/{team_id}/calendar")
def team_calendar(team_id: int) -> list[dict]:
    universe = default_runtime_snapshot()
    if universe.team(team_id) is None:
        raise HTTPException(status_code=404, detail=f"Equipo MDB {team_id} no encontrado en el snapshot 1993-94")
    return universe.team_calendar(team_id)


@app.get("/api/football9394/players/{player_id}")
def player(player_id: int) -> dict:
    row = default_runtime_snapshot().player(player_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Jugador MDB {player_id} no encontrado en el snapshot 1993-94")
    return row


@app.get("/api/football9394/leagues/{league_id}/calendar")
def league_calendar(league_id: int) -> list[dict]:
    universe = default_runtime_snapshot()
    if league_id not in universe.leagues_by_id:
        raise HTTPException(status_code=404, detail=f"Liga MDB {league_id} no encontrada en el snapshot 1993-94")
    return universe.league_calendar(league_id)


def _historical_team_level(team_id: int) -> int:
    universe = default_runtime_snapshot()
    values = sorted((int(p.get("overall") or 0) for p in universe.squad(team_id) if p.get("overall")), reverse=True)
    if not values:
        return 62
    core = values[:11]
    return max(45, min(95, round(sum(core) / len(core))))



































































































































@app.get("/api/football9394/career/bootstrap")
def career_bootstrap(team_id: int = 16, through_matchday: int = 7) -> dict:
    universe = default_runtime_snapshot()
    team = universe.team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Equipo MDB {team_id} no encontrado")
    league = team.get("league")
    if not league or int(league["source_id"]) != 1:
        raise HTTPException(status_code=409, detail="El bootstrap jugable actual está certificado para Primera División española")
    calendar = universe.league_calendar(1)
    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    results: list[LeagueMatch9394] = []
    sheet_cache: dict[int, TeamSheet9394] = {}
    for fixture in calendar:
        matchday = int(fixture["matchday"])
        if matchday > through_matchday:
            continue
        home_id, away_id = int(fixture["home_team_id"]), int(fixture["away_team_id"])
        home_team, away_team = universe.team(home_id), universe.team(away_id)
        if home_team is None or away_team is None:
            continue
        home_sheet = sheet_cache.setdefault(home_id, build_snapshot_team_sheet(universe, home_id))
        away_sheet = sheet_cache.setdefault(away_id, build_snapshot_team_sheet(universe, away_id))
        simulated = engine.simulate(
            home_sheet,
            away_sheet,
            seed=9394000 + matchday * 100 + int(fixture["id"]),
        )
        results.append(LeagueMatch9394(str(home_id), str(away_id), simulated.home.goals, simulated.away.goals))
    team_ids = [str(row["source_id"]) for row in universe.teams(league_id=1)]
    table = build_league_table(team_ids, results, SPAIN_PRIMERA_1993_94)
    standings = []
    for row in table:
        club = universe.team(int(row.team_id))
        standings.append({
            "team_id": int(row.team_id), "team_name": club["name"] if club else row.team_id,
            "position": row.position, "played": row.played, "wins": row.wins, "draws": row.draws,
            "losses": row.losses, "goals_for": row.goals_for, "goals_against": row.goals_against,
            "goal_difference": row.goal_difference, "points": row.points,
        })
    next_fixture = next((r for r in calendar if int(r["matchday"]) == through_matchday + 1 and team_id in (int(r["home_team_id"]), int(r["away_team_id"]))), None)
    next_match = None
    if next_fixture:
        home_id, away_id = int(next_fixture["home_team_id"]), int(next_fixture["away_team_id"])
        home, away = universe.team(home_id), universe.team(away_id)
        next_match = {
            **next_fixture, "home_team": home["name"], "away_team": away["name"],
            "home_level": _historical_team_level(home_id), "away_level": _historical_team_level(away_id),
        }
    return {
        "season": "1993-94", "game_date": "1993-10-23", "team": team, "squad": universe.squad(team_id),
        "competition": {**league, "points_win": 2}, "through_matchday": through_matchday,
        "standings": standings, "next_match": next_match,
        "data_origin": "normalized_mdb_snapshot",
    }


@app.get("/api/football9394/rules/{competition}")
def competition_rules(competition: str) -> dict:
    registry = default_registry_9394()
    try:
        rules = registry.resolve(competition)
    except UnresolvedHistoricalRulesError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return asdict(rules)


@app.post("/api/football9394/matches/simulate")
def simulate_match(payload: SimulatePayload) -> dict:
    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    if payload.home_team_id is not None or payload.away_team_id is not None:
        if payload.home_team_id is None or payload.away_team_id is None:
            raise HTTPException(status_code=422, detail="Deben indicarse ambos IDs de equipo MDB")
        universe = default_runtime_snapshot()
        try:
            home_sheet = build_snapshot_team_sheet(
                universe, payload.home_team_id, tactics=FootballTactics9394(**payload.home_tactics.model_dump())
            )
            away_sheet = build_snapshot_team_sheet(
                universe, payload.away_team_id, tactics=FootballTactics9394(**payload.away_tactics.model_dump())
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    else:
        # Compatibility route for isolated simulator/calibration tests. The
        # playable career always sends source IDs and therefore real players.
        home_sheet = _sheet(payload.home_name, payload.home_level, payload.home_tactics)
        away_sheet = _sheet(payload.away_name, payload.away_level, payload.away_tactics)
    result = engine.simulate(home_sheet, away_sheet, seed=payload.seed)
    return asdict(result)


@app.post("/api/football9394/world/seasons/simulate")
def simulate_world_season(payload: WorldSeasonPayload) -> dict:
    season = simulate_world_season_1993_94(seed=payload.seed)
    # Web API returns the complete durable payload. Desktop packaging can point
    # WorldCareerStore9394 at the user-data directory; the development API is
    # intentionally stateless unless a caller explicitly persists it.
    return season


# Production shell: the release launcher serves the built Vue app and the API
# from the same origin. API routes are registered first, so the SPA fallback
# cannot shadow /api/football9394/* endpoints.
_FRONTEND_DIST = Path(os.environ.get(
    "MISTER9394_FRONTEND_DIST",
    Path(__file__).resolve().parents[3] / "frontend" / "dist",
))
if _FRONTEND_DIST.is_dir():
    _ASSETS_DIR = _FRONTEND_DIST / "assets"
    if _ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="frontend-assets")

    @app.get("/{spa_path:path}", include_in_schema=False)
    def frontend_spa(spa_path: str):
        if spa_path == "api" or spa_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        requested = (_FRONTEND_DIST / spa_path).resolve()
        try:
            requested.relative_to(_FRONTEND_DIST.resolve())
        except ValueError:
            requested = _FRONTEND_DIST / "index.html"
        if spa_path and requested.is_file():
            return FileResponse(requested)
        return FileResponse(_FRONTEND_DIST / "index.html")
