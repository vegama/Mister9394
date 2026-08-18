from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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
from .manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394, career_selectable_leagues
from .national_teams import national_team_catalog, national_team_snapshot

app = FastAPI(title="Míster 93/94 API", version="0.8.0")


class TacticsPayload(BaseModel):
    formation: str = "4-4-2"
    mentality: str = "balanced"
    tempo: str = "normal"
    pressing: str = "medium"
    directness: str = "mixed"
    defensive_line: str = "medium"
    width: str = "normal"
    offside_trap: bool = False
    marking: str = "zonal"
    build_up: str = "balanced"
    final_third: str = "mixed"
    transition: str = "balanced"


class SimulatePayload(BaseModel):
    home_team_id: int | None = None
    away_team_id: int | None = None
    home_name: str = "Racing de Santander"
    away_name: str = "Real Sociedad"
    home_level: int = Field(72, ge=45, le=95)
    away_level: int = Field(76, ge=45, le=95)
    seed: int = 9394
    home_tactics: TacticsPayload = Field(default_factory=TacticsPayload)
    away_tactics: TacticsPayload = Field(default_factory=TacticsPayload)



class WorldSeasonPayload(BaseModel):
    seed: int = 9394


class CreateManagerCareerPayload(BaseModel):
    team_id: int = 16
    league_id: int | None = None
    seed: int = 9394
    through_matchday: int = Field(0, ge=0, le=44)
    age_policy: str = "frozen_attributes_dynamic"


class CareerTacticsPayload(TacticsPayload):
    pass


class CareerSelectionPayload(BaseModel):
    starter_ids: list[int] | None = None
    bench_ids: list[int] | None = None
    auto_select: bool = False


class TransferOfferPayload(BaseModel):
    fee_offer: int = Field(ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)


class ContractRenewalPayload(BaseModel):
    years: int = Field(default=3, ge=1, le=6)
    salary_offer: int | None = Field(default=None, ge=0)


class LiveAdvancePayload(BaseModel):
    minutes: int = Field(default=5, ge=1, le=45)


class LiveSubstitutionPayload(BaseModel):
    outgoing_id: int
    incoming_id: int


class MarketNegotiationPayload(BaseModel):
    player_id: int
    fee_offer: int = Field(default=0, ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)
    squad_role: str = "rotation"
    signing_bonus: int = Field(default=0, ge=0)
    release_clause: int | None = Field(default=None, ge=1)
    deal_type: str = "transfer"
    loan_wage_share: int = Field(default=100, ge=0, le=100)


class MarketCounterPayload(BaseModel):
    fee_offer: int = Field(default=0, ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)
    loan_wage_share: int | None = Field(default=None, ge=0, le=100)


class WatchlistPayload(BaseModel):
    watched: bool = True


class TransferListingPayload(BaseModel):
    asking_price: int | None = Field(default=None, ge=0)


class RolePromisePayload(BaseModel):
    role: str


class StaffResponsibilityPayload(BaseModel):
    assignee: str

class TrainingPlanPayload(BaseModel):
    intensity: str | None = None
    weekly_plan: list[str] | None = None

class TrainingFocusPayload(BaseModel):
    focus: str

class TrainingRecoveryPayload(BaseModel):
    recovery: str

class MatchPreparationPayload(BaseModel):
    focus: str

class TacticalPhasePayload(BaseModel):
    build_up: str | None = None
    final_third: str | None = None
    transition: str | None = None

class TacticalPlayerInstructionPayload(BaseModel):
    duty: str = "support"
    freedom: str = "balanced"
    pressing: str = "normal"
    clear: bool = False

class OppositionInstructionPayload(BaseModel):
    tight_mark: bool = False
    press: bool = False
    show_foot: str = "none"

class SetPieceTakerPayload(BaseModel):
    player_id: int | None = None

class DressingConcernPayload(BaseModel):
    response: str

class DisciplinePayload(BaseModel):
    action: str

class NationalSelectionPayload(BaseModel):
    player_ids: list[int]


CAREER_SAVE_ROOT = Path(os.environ.get(
    "MISTER9394_SAVE_DIR",
    Path(__file__).resolve().parents[3] / "data" / "football9394" / "careers",
))


def _career_store() -> ManagerCareerStore9394:
    return ManagerCareerStore9394(CAREER_SAVE_ROOT)


def _load_manager_career(career_id: str) -> ManagerCareerRuntime9394:
    try:
        return ManagerCareerRuntime9394(_career_store().load(career_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Carrera Míster 93/94 no encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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


@app.get("/api/football9394/career-options")
def manager_career_options() -> dict:
    return {"season": "1993-94", "leagues": career_selectable_leagues(default_runtime_snapshot())}


@app.post("/api/football9394/careers")
def create_manager_career(payload: CreateManagerCareerPayload) -> dict:
    try:
        career = ManagerCareerRuntime9394.create(
            team_id=payload.team_id, league_id=payload.league_id, seed=payload.seed, through_matchday=payload.through_matchday,
            age_policy=payload.age_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return career.snapshot()


@app.get("/api/football9394/careers/{career_id}")
def get_manager_career(career_id: str) -> dict:
    return _load_manager_career(career_id).snapshot()


@app.post("/api/football9394/careers/{career_id}/advance")
def advance_manager_career(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.advance_day()
    _career_store().save(career.state)
    return {**result, "career": career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/play-next")
def play_next_manager_matchday(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        snapshot = career.play_next_matchday()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return snapshot


@app.put("/api/football9394/careers/{career_id}/tactics")
def update_manager_tactics(career_id: str, payload: CareerTacticsPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        career.set_tactics(payload.model_dump())
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return career.snapshot()


@app.put("/api/football9394/careers/{career_id}/selection")
def update_manager_selection(career_id: str, payload: CareerSelectionPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        if payload.auto_select:
            auto = career._auto_selection()
            selection = career.set_selection(auto["starter_ids"], auto["bench_ids"])
        else:
            if payload.starter_ids is None:
                raise ValueError("Debes enviar el once titular o activar la selección automática.")
            selection = career.set_selection(payload.starter_ids, payload.bench_ids)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"selection": selection, "career": career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/jobs/{offer_id}/accept")
def manager_accept_job_offer(career_id: str, offer_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        snapshot = career.accept_job_offer(offer_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return snapshot


@app.get("/api/football9394/careers/{career_id}/professional-career")
def manager_professional_career(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.professional_career_snapshot()
    _career_store().save(career.state)
    return result


@app.post("/api/football9394/careers/{career_id}/jobs/{opportunity_id}/apply")
def manager_apply_for_job(career_id: str, opportunity_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.apply_for_job(opportunity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return result


@app.post("/api/football9394/careers/{career_id}/job/resign")
def manager_resign_club_job(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.resign_club_job()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return result



@app.post("/api/football9394/careers/{career_id}/captain/{player_id}")
def manager_set_captain(career_id: str, player_id: int) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.set_captain(player_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"result": result, "career": career.snapshot()}

@app.get("/api/football9394/careers/{career_id}/dashboard")
def manager_career_dashboard(career_id: str) -> dict:
    return _load_manager_career(career_id).manager_dashboard()


@app.get("/api/football9394/careers/{career_id}/calendar")
def manager_career_calendar(career_id: str) -> list[dict]:
    return _load_manager_career(career_id).career_calendar()


@app.get("/api/football9394/careers/{career_id}/board")
def manager_career_board(career_id: str) -> dict:
    return _load_manager_career(career_id).board_snapshot(persist=False)


@app.get("/api/football9394/careers/{career_id}/board-project")
def manager_board_project(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.board_project_snapshot()
    _career_store().save(career.state)
    return result


@app.post("/api/football9394/careers/{career_id}/board-project/requests/{request_type}")
def manager_board_request(career_id: str, request_type: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.submit_board_request(request_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return result


@app.get("/api/football9394/careers/{career_id}/staff")
def manager_career_staff(career_id: str) -> dict:
    return _load_manager_career(career_id).staff_snapshot()


@app.put("/api/football9394/careers/{career_id}/staff/responsibilities/{responsibility_key}")
def manager_assign_staff_responsibility(career_id: str, responsibility_key: str, payload: StaffResponsibilityPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        staff = career.set_staff_responsibility(responsibility_key, payload.assignee)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"staff": staff, "career": career.snapshot()}


@app.get("/api/football9394/careers/{career_id}/training")
def manager_career_training(career_id: str) -> dict:
    return _load_manager_career(career_id).training_snapshot()


@app.put("/api/football9394/careers/{career_id}/training")
def manager_update_training(career_id: str, payload: TrainingPlanPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        training = career.set_training_plan(intensity=payload.intensity, weekly_plan=payload.weekly_plan)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"training": training, "career": career.snapshot()}


@app.put("/api/football9394/careers/{career_id}/training/players/{player_id}")
def manager_update_training_focus(career_id: str, player_id: int, payload: TrainingFocusPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        training = career.set_player_training_focus(player_id, payload.focus)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"training": training, "career": career.snapshot()}


@app.put("/api/football9394/careers/{career_id}/training/recovery/{player_id}")
def manager_update_training_recovery(career_id: str, player_id: int, payload: TrainingRecoveryPayload) -> dict:
    career=_load_manager_career(career_id)
    try: training=career.set_player_recovery_plan(player_id,payload.recovery)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"training":training,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/training/match-preparation")
def manager_update_match_preparation(career_id: str, payload: MatchPreparationPayload) -> dict:
    career=_load_manager_career(career_id)
    try: training=career.set_match_preparation_focus(payload.focus)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"training":training,"career":career.snapshot()}

@app.get("/api/football9394/careers/{career_id}/tactical-plan")
def manager_tactical_plan(career_id: str) -> dict:
    return _load_manager_career(career_id).tactical_plan_snapshot()

@app.put("/api/football9394/careers/{career_id}/tactical-plan")
def manager_update_tactical_plan(career_id: str, payload: TacticalPhasePayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_phase_plan(build_up=payload.build_up,final_third=payload.final_third,transition=payload.transition)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/tactical-plan/players/{player_id}")
def manager_update_player_instruction(career_id: str, player_id: int, payload: TacticalPlayerInstructionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_individual_instruction(player_id,payload.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/tactical-plan/opposition/{player_id}")
def manager_update_opposition_instruction(career_id: str, player_id: int, payload: OppositionInstructionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_opposition_instruction(player_id,tight_mark=payload.tight_mark,press=payload.press,show_foot=payload.show_foot)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/tactical-plan/set-pieces/{kind}")
def manager_update_set_piece_taker(career_id: str, kind: str, payload: SetPieceTakerPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_set_piece_taker(kind,payload.player_id)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@app.get("/api/football9394/careers/{career_id}/staff-reports")
def manager_staff_reports(career_id: str) -> dict:
    return _load_manager_career(career_id).staff_reports_snapshot()

@app.get("/api/football9394/careers/{career_id}/match-briefing")
def manager_match_briefing(career_id: str) -> dict | None:
    return _load_manager_career(career_id).match_briefing_snapshot()

@app.get("/api/football9394/careers/{career_id}/scouting")
def manager_career_scouting(career_id: str) -> dict:
    return _load_manager_career(career_id).scouting_snapshot()


@app.post("/api/football9394/careers/{career_id}/scouting/{player_id}")
def manager_start_scouting(career_id: str, player_id: int) -> dict:
    career = _load_manager_career(career_id)
    try:
        assignment = career.start_scouting_player(player_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"assignment": assignment, "career": career.snapshot()}


@app.get("/api/football9394/careers/{career_id}/squad-plan")
def manager_squad_plan(career_id: str) -> dict:
    return _load_manager_career(career_id).squad_plan_snapshot()


@app.get("/api/football9394/careers/{career_id}/news")
def manager_career_news(career_id: str, category: str = "", limit: int = 80) -> list[dict]:
    return _load_manager_career(career_id).news_snapshot(category=category,limit=limit)


@app.get("/api/football9394/careers/{career_id}/information-world")
def manager_information_world(career_id: str, limit: int = 80) -> dict:
    return _load_manager_career(career_id).information_world_snapshot(limit=limit)


@app.get("/api/football9394/careers/{career_id}/competitions")
def manager_career_competitions(career_id: str) -> list[dict]:
    return _load_manager_career(career_id).competition_directory()


@app.get("/api/football9394/careers/{career_id}/competitions/{kind}/{source_id}")
def manager_career_competition(career_id: str, kind: str, source_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: return career.competition_detail(kind,source_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc


@app.get("/api/football9394/careers/{career_id}/history")
def manager_career_history(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    return {"season_recaps":list(career.state.get("season_recaps") or []),"season_archive":list(career.state.get("season_archive") or []),"season_dossiers":list(career.state.get("season_dossiers") or []),"honours":list(career.state.get("honours") or []),"club_honours":list((career.state.get("club_honours") or {}).get(str(int(career.state["team_id"])),[])),"board_history":list(career.state.get("board_history") or []),"ai_squad_audits":list(career.state.get("ai_squad_audits") or []),"summer_briefing":dict(career.state.get("summer_briefing") or {}),"longitudinal_health":list(career.state.get("longitudinal_health") or [])}


@app.post("/api/football9394/careers/{career_id}/advance-until-event")
def advance_manager_career_until_event(career_id: str, max_days: int = 14) -> dict:
    career=_load_manager_career(career_id);result=career.advance_until_event(max_days=max_days);_career_store().save(career.state);return {**result,"career":career.snapshot()}


@app.get("/api/football9394/careers/{career_id}/leagues/{source_id}/standings")
def manager_career_league_standings(career_id: str, source_id: int) -> dict:
    career = _load_manager_career(career_id)
    rows = career.league_standings(source_id)
    controlled = int(career.state.get("league_id") or 0)
    progress = (career.state.get("world_leagues") or {}).get(str(source_id)) if source_id != controlled else None
    if source_id != controlled and progress is None:
        raise HTTPException(status_code=409, detail="competición con runtime especializado aún no incremental")
    return {
        "source_id": int(source_id), "rows": rows,
        "completed_round": int(progress.get("completed_round") or 0) if progress else int(career.state.get("completed_matchday") or 0),
        "result_count": len(progress.get("results") or []) if progress else len(career.state.get("results") or []),
    }


@app.get("/api/football9394/careers/{career_id}/market")
def manager_career_market(career_id: str, query: str = "", limit: int = 20, position: str = "", free_agents: bool = False, watched: bool = False) -> list[dict]:
    career = _load_manager_career(career_id)
    return career.search_market(query, limit=limit, position=position, free_agents=free_agents, watched=watched)


@app.post("/api/football9394/careers/{career_id}/transfers/{player_id}")
def manager_career_transfer(career_id: str, player_id: int, payload: TransferOfferPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        decision = career.negotiate_player(
            player_id, fee_offer=payload.fee_offer, salary_offer=payload.salary_offer,
            contract_years=payload.contract_years,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"decision": decision, "career": career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/contracts/{player_id}/renew")
def manager_career_renew_contract(career_id: str, player_id: int, payload: ContractRenewalPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        decision = career.renew_player_contract(player_id, years=payload.years, salary_offer=payload.salary_offer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"decision": decision, "career": career.snapshot()}


@app.get("/api/football9394/careers/{career_id}/economy")
def manager_career_economy(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    return {
        "finances": dict(career.state.get("finances") or {}),
        "summary": career.economy_snapshot(),
        "ledger": list(career.state.get("economy_ledger") or [])[-100:],
        "ai_transfers": list(career.state.get("ai_transfer_history") or [])[-100:],
        "contracts": list(career.state.get("contract_history") or [])[-100:],
    }



@app.post("/api/football9394/careers/{career_id}/players/{player_id}/role-promise")
def manager_set_role_promise(career_id: str, player_id: int, payload: RolePromisePayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.set_role_promise(player_id, payload.role)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"result": result, "career": career.snapshot(), "player": result.get("player")}

@app.post("/api/football9394/careers/{career_id}/dressing-room/concerns/{concern_id}")
def manager_respond_concern(career_id: str, concern_id: str, payload: DressingConcernPayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.respond_dressing_room_concern(concern_id,payload.response)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}

@app.post("/api/football9394/careers/{career_id}/players/{player_id}/discipline")
def manager_discipline_player(career_id: str, player_id: int, payload: DisciplinePayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.discipline_player(player_id,payload.action)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}

@app.get("/api/football9394/careers/{career_id}/players/{player_id}")
def manager_career_player(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: return career.player_detail(player_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/football9394/careers/{career_id}/live")
def manager_live_match(career_id: str) -> dict | None:
    return _load_manager_career(career_id).live_match_snapshot()


@app.post("/api/football9394/careers/{career_id}/live/start")
def start_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.start_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}


@app.delete("/api/football9394/careers/{career_id}/live/preview")
def cancel_manager_live_preview(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: state=career.cancel_live_preview()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"career":state}


@app.post("/api/football9394/careers/{career_id}/live/advance")
def advance_manager_live_match(career_id: str, payload: LiveAdvancePayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.advance_live_match(payload.minutes)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/live/result")
def simulate_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.simulate_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return result


@app.put("/api/football9394/careers/{career_id}/live/tactics")
def update_manager_live_tactics(career_id: str, payload: CareerTacticsPayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.set_live_tactics(payload.model_dump())
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/live/substitution")
def substitute_manager_live_match(career_id: str, payload: LiveSubstitutionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.substitute_live_match(payload.outgoing_id,payload.incoming_id)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/live/finish")
def finish_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.finish_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return result


@app.get("/api/football9394/careers/{career_id}/market-flow")
def manager_market_flow(career_id: str) -> dict:
    return _load_manager_career(career_id).market_snapshot()


@app.post("/api/football9394/careers/{career_id}/watchlist/{player_id}")
def manager_watchlist(career_id: str, player_id: int, payload: WatchlistPayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.toggle_watchlist(player_id,payload.watched)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/market-inquiry/{player_id}")
def manager_market_inquiry(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: inquiry=career.inquire_player_availability(player_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"inquiry":inquiry,"career":career.snapshot()}

@app.post("/api/football9394/careers/{career_id}/negotiations")
def manager_open_negotiation(career_id: str, payload: MarketNegotiationPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.open_transfer_negotiation(payload.player_id,fee_offer=payload.fee_offer,salary_offer=payload.salary_offer,contract_years=payload.contract_years,squad_role=payload.squad_role,signing_bonus=payload.signing_bonus,release_clause=payload.release_clause,deal_type=payload.deal_type,loan_wage_share=payload.loan_wage_share)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}


@app.put("/api/football9394/careers/{career_id}/negotiations/{negotiation_id}")
def manager_counter_negotiation(career_id: str, negotiation_id: str, payload: MarketCounterPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.resubmit_transfer_negotiation(negotiation_id,fee_offer=payload.fee_offer,salary_offer=payload.salary_offer,contract_years=payload.contract_years,loan_wage_share=payload.loan_wage_share)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}


@app.delete("/api/football9394/careers/{career_id}/negotiations/{negotiation_id}")
def manager_withdraw_negotiation(career_id: str, negotiation_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.withdraw_transfer_negotiation(negotiation_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}

@app.post("/api/football9394/careers/{career_id}/transfer-list/{player_id}")
def manager_list_player(career_id: str, player_id: int, payload: TransferListingPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.list_player_for_transfer(player_id,asking_price=payload.asking_price)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"listing":row,"career":career.snapshot()}


@app.delete("/api/football9394/careers/{career_id}/transfer-list/{player_id}")
def manager_unlist_player(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id);career.unlist_player(player_id);_career_store().save(career.state);return {"career":career.snapshot()}


@app.post("/api/football9394/careers/{career_id}/incoming-offers/{offer_id}/accept")
def manager_accept_incoming_offer(career_id: str, offer_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: transfer=career.accept_incoming_transfer_offer(offer_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"transfer":transfer,"career":career.snapshot()}


@app.get("/api/football9394/careers/{career_id}/world")
def manager_career_world(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    snap = career.snapshot()
    return {
        "game_date": snap["game_date"],
        "world_progress": snap["world_progress"],
        "special_progress": snap["special_progress"],
        "tournament_progress": snap["tournament_progress"],
        "international_history": snap["international_history"],
        "international_manager": snap.get("international_manager"),
        "international_tournaments": snap.get("international_tournaments", []),
        "recent_world_events": snap["recent_world_events"],
    }


@app.post("/api/football9394/careers/{career_id}/national-job/{offer_id}/accept")
def manager_accept_national_job(career_id: str, offer_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: event=career.accept_national_job(offer_id)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"event":event,"career":career.snapshot()}

@app.post("/api/football9394/careers/{career_id}/national-job/resign")
def manager_resign_national_job(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: event=career.resign_national_job()
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"event":event,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/national-selection/auto")
def manager_auto_national_selection(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: ids=career.auto_national_selection()
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"player_ids":ids,"career":career.snapshot()}

@app.put("/api/football9394/careers/{career_id}/national-selection")
def manager_set_national_selection(career_id: str, payload: NationalSelectionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: ids=career.set_national_selection(payload.player_ids)
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"player_ids":ids,"career":career.snapshot()}

@app.get("/api/football9394/national-teams")
def national_teams() -> list[dict]:
    universe = default_runtime_snapshot()
    return [
        {"country_id": row.country_id, "name": row.name, "eligible_players": row.eligible_players,
         "average_top_22": row.average_top_22, "depth_ready_40": row.depth_ready_40,
         "depth_gap_to_40": row.depth_gap_to_40, "qualified_1994": row.qualified_1994,
         "world_cup_1994_group": row.world_cup_1994_group,
         "world_cup_1994_squad_complete": row.world_cup_1994_squad_complete,
         "historical_head_coach": row.historical_head_coach}
        for row in national_team_catalog(universe)
    ]


@app.get("/api/football9394/national-teams/{country_id}")
def national_team(country_id: int, career_id: str | None = None) -> dict:
    universe = default_runtime_snapshot()
    development = None
    selected_player_ids = None
    if career_id:
        career = _load_manager_career(career_id)
        development = career.state.get("player_development")
        international = career.state.get("international_manager") or {}
        if int(international.get("country_id") or 0) == int(country_id):
            selected_player_ids = [int(pid) for pid in international.get("selected_player_ids") or []]
    try:
        return national_team_snapshot(universe, country_id, development=development, selected_player_ids=selected_player_ids)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
