from __future__ import annotations

from copy import deepcopy

from backend.app.football9394.longitudinal_health import (
    FULL_HISTORY_SEASONS,
    build_world_health,
    compact_long_career_state,
    ensure_longitudinal_health_state,
)
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _season_label(start: int) -> str:
    return f"{start}-{str(start + 1)[-2:]}"


def test_g_recovers_pre_g_manager_recaps_from_canonical_archive():
    archives=[]
    for start in range(1993,2023):
        season=_season_label(start)
        archives.append({
            "season":season,
            "managed_club":{
                "season":season,"team_id":16,"team_name":"Real Sociedad",
                "position":1,"points":76,"titles":[],
            },
        })
    state={"season_archive":archives,"season_recaps":[deepcopy(row["managed_club"]) for row in archives[-20:]]}
    ensure_longitudinal_health_state(state)
    assert len(state["season_recaps"])==30
    assert state["season_recaps"][0]["season"]=="1993-94"
    assert state["season_recaps"][0]["recovered_from_archive"] is True


def test_g_compacts_old_detail_without_forgetting_seasons():
    archives=[];recaps=[];dossiers=[]
    for start in range(1993,2008):
        season=_season_label(start)
        table=[{"team_id":i,"position":i,"points":80-i} for i in range(1,21)]
        recap={"season":season,"team_id":16,"team_name":"Real Sociedad","position":1,"points":76,"titles":[],"champions":[{"team_id":16}]*10,"league_awards":{"1":{"rows":[1,2,3]}}}
        archives.append({"season":season,"league_tables":{"1":deepcopy(table)},"honours":[],"movements":[],"managed_club":deepcopy(recap)})
        recaps.append(deepcopy(recap))
        dossiers.append({"season":season,"league_tables":{"1":deepcopy(table)},"league_awards":{"1":{"rows":[1,2,3]}},"champions":[],"movements":[],"managed_recap":deepcopy(recap)})
    state={
        "season_archive":archives,"season_recaps":recaps,"season_dossiers":dossiers,
        "ai_contract_history":[],"ai_transfer_history":[],"economy_ledger":[],"contract_history":[],
        "transfer_history":[],"international_history":[],"processed_months":[],
    }
    compact_long_career_state(state,season="2007-08")
    old_count=len(archives)-FULL_HISTORY_SEASONS
    assert len(state["season_recaps"])==15
    assert all(row.get("history_compacted") for row in state["season_archive"][:old_count])
    assert all(row.get("history_compacted") for row in state["season_recaps"][:old_count])
    assert all(row.get("history_compacted") for row in state["season_dossiers"][:old_count])
    assert all(not row.get("history_compacted") for row in state["season_archive"][-FULL_HISTORY_SEASONS:])
    assert state["season_archive"][0]["league_tables"]=={}
    assert state["season_archive"][0]["league_table_summaries"]["1"]["team_count"]==20


def test_g_world_health_surfaces_oversized_squads_instead_of_marking_them_clean():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=9394,through_matchday=0)
    health=build_world_health(
        career,from_season="1992-93",to_season="1993-94",date_text="1993-07-01",transition_ms=1000,
    )
    assert health["active_clubs"]>400
    assert health["oversized_squads"]>0
    assert any(issue["code"]=="oversized_squads" for issue in health["issues"])
    assert health["status"]=="warning"
