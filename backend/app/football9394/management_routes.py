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

@router.post("/api/football9394/careers/{career_id}/captain/{player_id}")
def manager_set_captain(career_id: str, player_id: int) -> dict:
    career = _load_manager_career(career_id)
    try:
        result = career.set_captain(player_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"result": result, "career": career.snapshot()}

@router.get("/api/football9394/careers/{career_id}/staff")
def manager_career_staff(career_id: str) -> dict:
    return _load_manager_career(career_id).staff_snapshot()

@router.put("/api/football9394/careers/{career_id}/staff/responsibilities/{responsibility_key}")
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

@router.get("/api/football9394/careers/{career_id}/training")
def manager_career_training(career_id: str) -> dict:
    return _load_manager_career(career_id).training_snapshot()

@router.put("/api/football9394/careers/{career_id}/training")
def manager_update_training(career_id: str, payload: TrainingPlanPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        training = career.set_training_plan(intensity=payload.intensity, weekly_plan=payload.weekly_plan)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"training": training, "career": career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/training/players/{player_id}")
def manager_update_training_focus(career_id: str, player_id: int, payload: TrainingFocusPayload) -> dict:
    career = _load_manager_career(career_id)
    try:
        training = career.set_player_training_focus(player_id, payload.focus)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _career_store().save(career.state)
    return {"training": training, "career": career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/training/recovery/{player_id}")
def manager_update_training_recovery(career_id: str, player_id: int, payload: TrainingRecoveryPayload) -> dict:
    career=_load_manager_career(career_id)
    try: training=career.set_player_recovery_plan(player_id,payload.recovery)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"training":training,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/training/match-preparation")
def manager_update_match_preparation(career_id: str, payload: MatchPreparationPayload) -> dict:
    career=_load_manager_career(career_id)
    try: training=career.set_match_preparation_focus(payload.focus)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"training":training,"career":career.snapshot()}

@router.get("/api/football9394/careers/{career_id}/tactical-plan")
def manager_tactical_plan(career_id: str) -> dict:
    return _load_manager_career(career_id).tactical_plan_snapshot()

@router.put("/api/football9394/careers/{career_id}/tactical-plan")
def manager_update_tactical_plan(career_id: str, payload: TacticalPhasePayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_phase_plan(build_up=payload.build_up,final_third=payload.final_third,transition=payload.transition)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/tactical-plan/players/{player_id}")
def manager_update_player_instruction(career_id: str, player_id: int, payload: TacticalPlayerInstructionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_individual_instruction(player_id,payload.model_dump())
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/tactical-plan/opposition/{player_id}")
def manager_update_opposition_instruction(career_id: str, player_id: int, payload: OppositionInstructionPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_opposition_instruction(player_id,tight_mark=payload.tight_mark,press=payload.press,show_foot=payload.show_foot)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@router.put("/api/football9394/careers/{career_id}/tactical-plan/set-pieces/{kind}")
def manager_update_set_piece_taker(career_id: str, kind: str, payload: SetPieceTakerPayload) -> dict:
    career=_load_manager_career(career_id)
    try: plan=career.set_tactical_set_piece_taker(kind,payload.player_id)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    _career_store().save(career.state);return {"tactical_plan":plan,"career":career.snapshot()}

@router.get("/api/football9394/careers/{career_id}/staff-reports")
def manager_staff_reports(career_id: str) -> dict:
    return _load_manager_career(career_id).staff_reports_snapshot()

@router.get("/api/football9394/careers/{career_id}/scouting")
def manager_career_scouting(career_id: str) -> dict:
    return _load_manager_career(career_id).scouting_snapshot()

@router.post("/api/football9394/careers/{career_id}/scouting/{player_id}")
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

@router.get("/api/football9394/careers/{career_id}/squad-plan")
def manager_squad_plan(career_id: str) -> dict:
    return _load_manager_career(career_id).squad_plan_snapshot()

@router.get("/api/football9394/careers/{career_id}/teams/{team_id}")
def manager_career_team(career_id: str, team_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: return career.team_detail(team_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc

@router.get("/api/football9394/careers/{career_id}/news")
def manager_career_news(career_id: str, category: str = "", limit: int = 80) -> list[dict]:
    return _load_manager_career(career_id).news_snapshot(category=category,limit=limit)

@router.get("/api/football9394/careers/{career_id}/information-world")
def manager_information_world(career_id: str, limit: int = 80) -> dict:
    return _load_manager_career(career_id).information_world_snapshot(limit=limit)

@router.get("/api/football9394/careers/{career_id}/competitions")
def manager_career_competitions(career_id: str) -> list[dict]:
    return _load_manager_career(career_id).competition_directory()

@router.get("/api/football9394/careers/{career_id}/competitions/{kind}/{source_id}")
def manager_career_competition(career_id: str, kind: str, source_id: int) -> dict:
    career=_load_manager_career(career_id)
    try: return career.competition_detail(kind,source_id)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc

@router.get("/api/football9394/careers/{career_id}/history")
def manager_career_history(career_id: str) -> dict:
    career=_load_manager_career(career_id)
    return {"season_recaps":list(career.state.get("season_recaps") or []),"season_archive":list(career.state.get("season_archive") or []),"season_dossiers":list(career.state.get("season_dossiers") or []),"honours":list(career.state.get("honours") or []),"club_honours":list((career.state.get("club_honours") or {}).get(str(int(career.state["team_id"])),[])),"career_milestones":list(career.state.get("career_milestones") or []),"board_history":list(career.state.get("board_history") or []),"ai_squad_audits":list(career.state.get("ai_squad_audits") or []),"summer_briefing":dict(career.state.get("summer_briefing") or {}),"longitudinal_health":list(career.state.get("longitudinal_health") or [])}

@router.get("/api/football9394/careers/{career_id}/economy")
def manager_career_economy(career_id: str) -> dict:
    career = _load_manager_career(career_id)
    return {
        "finances": dict(career.state.get("finances") or {}),
        "summary": career.economy_snapshot(),
        "ledger": list(career.state.get("economy_ledger") or [])[-100:],
        "ai_transfers": list(career.state.get("ai_transfer_history") or [])[-100:],
        "contracts": list(career.state.get("contract_history") or [])[-100:],
    }

@router.post("/api/football9394/careers/{career_id}/dressing-room/concerns/{concern_id}")
def manager_respond_concern(career_id: str, concern_id: str, payload: DressingConcernPayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.respond_dressing_room_concern(concern_id,payload.response)
    except KeyError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}

@router.post("/api/football9394/careers/{career_id}/players/{player_id}/discipline")
def manager_discipline_player(career_id: str, player_id: int, payload: DisciplinePayload) -> dict:
    career=_load_manager_career(career_id)
    try: result=career.discipline_player(player_id,payload.action)
    except (KeyError,ValueError) as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc
    _career_store().save(career.state);return {"result":result,"career":career.snapshot()}

