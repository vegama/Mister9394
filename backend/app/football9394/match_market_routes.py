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

@router.get("/api/football9394/careers/{career_id}/market")
def manager_career_market(career_id: str, query: str = "", limit: int = 20, position: str = "", free_agents: bool = False, watched: bool = False) -> list[dict]:
    career = _load_manager_career(career_id)
    return career.search_market(query, limit=limit, position=position, free_agents=free_agents, watched=watched)

@router.get("/api/football9394/careers/{career_id}/market-flow")
def manager_market_flow(career_id: str) -> dict:
    return _load_manager_career(career_id).market_snapshot()

@router.post("/api/football9394/careers/{career_id}/watchlist/{player_id}")
def manager_watchlist(career_id: str, player_id: int, payload: WatchlistPayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.toggle_watchlist(player_id,payload.watched)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/market-inquiry/{player_id}")
def manager_market_inquiry(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: inquiry=career.inquire_player_availability(player_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"inquiry":inquiry,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/incoming-offers/{offer_id}/accept")
def manager_accept_incoming_offer(career_id: str, offer_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: transfer=career.accept_incoming_transfer_offer(offer_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"transfer":transfer,"career":career.snapshot()}

