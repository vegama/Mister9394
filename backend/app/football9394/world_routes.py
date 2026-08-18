from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .manager_career import ManagerCareerRuntime9394, career_selectable_leagues
from .national_teams import national_team_catalog, national_team_snapshot
from .snapshot_runtime import default_runtime_snapshot
from .manager_route_support import _career_store, _load_manager_career
from .webapp_contracts import (
    CreateManagerCareerPayload, CareerTacticsPayload, CareerSelectionPayload, TransferOfferPayload,
    ContractRenewalPayload, LiveAdvancePayload, LiveSubstitutionPayload, MarketNegotiationPayload,
    MarketCounterPayload, WatchlistPayload, TransferListingPayload, RolePromisePayload,
    StaffResponsibilityPayload, TrainingPlanPayload, TrainingFocusPayload, TrainingRecoveryPayload,
    MatchPreparationPayload, TacticalPhasePayload, TacticalPlayerInstructionPayload,
    OppositionInstructionPayload, SetPieceTakerPayload, DressingConcernPayload, DisciplinePayload,
    NationalSelectionPayload,
)

router = APIRouter()

@router.get("/api/football9394/careers/{career_id}/world")
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

@router.post("/api/football9394/careers/{career_id}/national-job/{offer_id}/accept")
def manager_accept_national_job(career_id: str, offer_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: event=career.accept_national_job(offer_id)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"event":event,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/national-job/resign")
def manager_resign_national_job(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: event=career.resign_national_job()
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"event":event,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/national-selection/auto")
def manager_auto_national_selection(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: ids=career.auto_national_selection()
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"player_ids":ids,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/national-selection")
def manager_set_national_selection(career_id: str, payload: NationalSelectionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: ids=career.set_national_selection(payload.player_ids)
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"player_ids":ids,"career":career.snapshot()}

@router.get("/api/football9394/national-teams")
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

@router.get("/api/football9394/national-teams/{country_id}")
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

