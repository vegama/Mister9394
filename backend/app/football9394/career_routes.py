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

@router.get("/api/football9394/career-options")
def manager_career_options() -> dict:
    return {"season": "1993-94", "leagues": career_selectable_leagues(default_runtime_snapshot())}

@router.post("/api/football9394/careers")
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

@router.get("/api/football9394/careers/{career_id}")
def get_manager_career(career_id: str) -> dict:
    return _load_manager_career(career_id).snapshot()

@router.post("/api/football9394/careers/{career_id}/advance")
def advance_manager_career(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.advance_day()
    _career_store().save(career.state)
    return {**result, "career": career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/play-next")
def play_next_manager_matchday(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        snapshot = career.play_next_matchday()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return snapshot

@router.put("/api/football9394/careers/{career_id}/tactics")
def update_manager_tactics(career_id: str, payload: CareerTacticsPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        career.set_tactics(payload.model_dump())
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return career.snapshot()

@router.put("/api/football9394/careers/{career_id}/selection")
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

@router.post("/api/football9394/careers/{career_id}/jobs/{offer_id}/accept")
def manager_accept_job_offer(career_id: str, offer_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        snapshot = career.accept_job_offer(offer_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return snapshot

@router.get("/api/football9394/careers/{career_id}/professional-career")
def manager_professional_career(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.professional_career_snapshot()
    _career_store().save(career.state)
    return result

@router.post("/api/football9394/careers/{career_id}/jobs/{opportunity_id}/apply")
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

@router.post("/api/football9394/careers/{career_id}/job/resign")
def manager_resign_club_job(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.resign_club_job()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return result

@router.get("/api/football9394/careers/{career_id}/dashboard")
def manager_career_dashboard(career_id: str) -> dict:
    return _load_manager_career(career_id).manager_dashboard()

@router.get("/api/football9394/careers/{career_id}/calendar")
def manager_career_calendar(career_id: str) -> list[dict]:
    return _load_manager_career(career_id).career_calendar()

@router.get("/api/football9394/careers/{career_id}/board")
def manager_career_board(career_id: str) -> dict:
    return _load_manager_career(career_id).board_snapshot(persist=False)

@router.get("/api/football9394/careers/{career_id}/board-project")
def manager_board_project(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    result = career.board_project_snapshot()
    _career_store().save(career.state)
    return result

@router.post("/api/football9394/careers/{career_id}/board-project/requests/{request_type}")
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

@router.get("/api/football9394/careers/{career_id}/match-briefing")
def manager_match_briefing(career_id: str) -> dict | None:
    return _load_manager_career(career_id).match_briefing_snapshot()

@router.post("/api/football9394/careers/{career_id}/advance-until-event")
def advance_manager_career_until_event(career_id: str, max_days: int = 14) -> dict:
    career=_load_manager_career(career_id);result=career.advance_until_event(max_days=max_days);_career_store().save(career.state);return {**result,"career":career.snapshot()}

@router.get("/api/football9394/careers/{career_id}/leagues/{source_id}/standings")
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

@router.post("/api/football9394/careers/{career_id}/transfers/{player_id}")
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

@router.post("/api/football9394/careers/{career_id}/contracts/{player_id}/renew")
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

@router.post("/api/football9394/careers/{career_id}/players/{player_id}/role-promise")
def manager_set_role_promise(career_id: str, player_id: int, payload: RolePromisePayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.set_role_promise(player_id, payload.role)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"result": result, "career": career.snapshot(), "player": result.get("player")}

@router.get("/api/football9394/careers/{career_id}/players/{player_id}")
def manager_career_player(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: return career.player_detail(player_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/api/football9394/careers/{career_id}/live")
def manager_live_match(career_id: str) -> dict | None:
    return _load_manager_career(career_id).live_match_snapshot()

@router.post("/api/football9394/careers/{career_id}/live/start")
def start_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.start_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}

@router.delete("/api/football9394/careers/{career_id}/live/preview")
def cancel_manager_live_preview(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: state=career.cancel_live_preview()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"career":state}

@router.post("/api/football9394/careers/{career_id}/live/advance")
def advance_manager_live_match(career_id: str, payload: LiveAdvancePayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.advance_live_match(payload.minutes)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/live/result")
def simulate_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.simulate_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return result

@router.put("/api/football9394/careers/{career_id}/live/tactics")
def update_manager_live_tactics(career_id: str, payload: CareerTacticsPayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.set_live_tactics(payload.model_dump())
    except (ValueError,TypeError) as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/live/substitution")
def substitute_manager_live_match(career_id: str, payload: LiveSubstitutionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: match=career.substitute_live_match(payload.outgoing_id,payload.incoming_id)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return {"match":match,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/live/finish")
def finish_manager_live_match(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.finish_live_match()
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state);return result

@router.post("/api/football9394/careers/{career_id}/negotiations")
def manager_open_negotiation(career_id: str, payload: MarketNegotiationPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.open_transfer_negotiation(payload.player_id,fee_offer=payload.fee_offer,salary_offer=payload.salary_offer,contract_years=payload.contract_years,squad_role=payload.squad_role,signing_bonus=payload.signing_bonus,release_clause=payload.release_clause,deal_type=payload.deal_type,loan_wage_share=payload.loan_wage_share)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/negotiations/{negotiation_id}")
def manager_counter_negotiation(career_id: str, negotiation_id: str, payload: MarketCounterPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.resubmit_transfer_negotiation(negotiation_id,fee_offer=payload.fee_offer,salary_offer=payload.salary_offer,contract_years=payload.contract_years,loan_wage_share=payload.loan_wage_share)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}

@router.delete("/api/football9394/careers/{career_id}/negotiations/{negotiation_id}")
def manager_withdraw_negotiation(career_id: str, negotiation_id: str) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.withdraw_transfer_negotiation(negotiation_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"negotiation":row,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/transfer-list/{player_id}")
def manager_list_player(career_id: str, player_id: int, payload: TransferListingPayload) -> dict:
    career=_load_manager_career(career_id)
    try: row=career.list_player_for_transfer(player_id,asking_price=payload.asking_price)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"listing":row,"career":career.snapshot()}

@router.delete("/api/football9394/careers/{career_id}/transfer-list/{player_id}")
def manager_unlist_player(career_id: str, player_id: int) -> dict:
    career=_load_manager_career(career_id);career.unlist_player(player_id);_career_store().save(career.state);return {"career":career.snapshot()}

