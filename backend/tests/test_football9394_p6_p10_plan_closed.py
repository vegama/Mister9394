from __future__ import annotations

from datetime import date

from backend.app.football9394.career_quality_gate import long_horizon_invariant_gate, nomad_gate, profile_playability_gate
from backend.app.football9394.era_policy import enforce_frozen_rules_policy, regulatory_integrity_report
from backend.app.football9394.international_manager import generate_national_job_offers, accept_national_job, international_manager_snapshot, set_national_selection, record_international_player_match
from backend.app.football9394.international_tournaments import simulate_world_championship_24
from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.market_ecosystem import agent_pressure_for_player, player_market_preferences, recruitment_plan, register_replacement_chain
from backend.app.football9394.match_signatures import player_match_boxscore


def test_p6_managed_match_persists_observable_individual_signature():
    career=ManagerCareerRuntime9394.create(team_id=3,league_id=1,seed=6001,through_matchday=0)
    career._simulate_matchday(1)
    histories=career.state.get("player_match_history") or {}
    rows=[entry for history in histories.values() for entry in history]
    assert rows
    assert all("observable" in row and "signature" in row for row in rows)
    assert any((row.get("signature") or {}).get("primary") for row in rows)
    assert any(int((row.get("observable") or {}).get("shots") or 0)>0 for row in rows)


def test_p7_market_preferences_agent_pressure_and_six_month_plan_are_explainable():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=7001,through_matchday=0)
    player=career._career_players_by_team[16][0]
    prefs=player_market_preferences(player,overall=78,current_club_score=55,target_club_score=82,wants_move=True,current_salary=10_000_000,offered_salary=15_000_000,role_shortage=1)
    assert prefs["openness"]>50 and prefs["reasons"]
    agent=agent_pressure_for_player(career.state,player_id=int(player["source_id"]),current_year=1993,contract_end_year=1994,satisfaction=42,rival_interest=True)
    assert agent["pressure"]>=60 and agent["wage_multiplier"]>1
    plan=recruitment_plan(team_id=16,players=career._career_players_by_team[16],development=career.state["player_development"],contracts=career.state["contract_overrides"],cash=career.state["club_finances"]["16"]["cash"],current_date=date(1993,11,1),coach_profile=career._coach_profile(16))
    assert plan["planning_horizon_months"]==6 and "primary_need" in plan and "contract_risk_count" in plan


def test_p7_follow_up_purchase_is_recorded_as_replacement_chain():
    state={}
    first=[{"player_id":10,"from_team_id":2,"to_team_id":3,"fee":10}]
    follow=[{"player_id":20,"from_team_id":4,"to_team_id":2,"fee":12}]
    chains=register_replacement_chain(state,day=date(1993,12,1),first_deals=first,follow_up_deals=follow)
    assert chains and follow[0]["replacement_chain_for_player_id"]==10


def test_p8_rules_policy_repairs_tampered_save_and_holds_thirty_year_probe():
    career=ManagerCareerRuntime9394.create(team_id=3,league_id=1,seed=8001,through_matchday=0)
    career.state["rules_policy"]="bosman_future"
    enforce_frozen_rules_policy(career.state)
    assert career.state["rules_policy"]=="frozen_1993_94"
    report=regulatory_integrity_report(career.universe,season="2023-24",sample_years=(1993,2003,2013,2023))
    assert report["passed"] and report["laws"]["used_substitutes"]==2
    horizons=long_horizon_invariant_gate(career)
    assert horizons["passed"] and [r["seasons"] for r in horizons["horizons"]]==[3,10,20,30]


def test_p9_manager_can_accept_country_keep_22_and_play_frozen_world_championship():
    career=ManagerCareerRuntime9394.create(team_id=3,league_id=1,seed=9001,through_matchday=0)
    offers=generate_national_job_offers(career.state,career.universe,day=date(1994,7,1),manager_reputation=100,seed=9001)
    assert offers
    event=accept_national_job(career.state,career.universe,offers[0]["id"],day=date(1994,7,1),development=career.state["player_development"])
    snap=international_manager_snapshot(career.state)
    assert event["kind"]=="national_job_started" and len(snap["selection"])==22 and not snap["job_offers"]
    set_national_selection(career.state,career.universe,list(snap["selection"]),development=career.state["player_development"])
    tournament=simulate_world_championship_24(
        career.universe,year=1994,development=career.state["player_development"],seed=9001,
        selections={int(snap["country_id"]):list(snap["selection"])},
        match_recorder=lambda result,home,away,stage: record_international_player_match(
            career.state,result=result,home_sheet=home,away_sheet=away,date_text="1994-06-17",
            competition="Campeonato Mundial",tournament=True,stage=stage),
    )
    assert tournament["format"]=="24_team_1994_frozen"
    assert len(tournament["participants"])==24 and len(tournament["matches"])==51
    assert tournament["generated_alternate_history"] and tournament["historical_results_claimed"] is False
    intl_stats=career.state.get("international_player_stats") or {}
    assert intl_stats and sum(int(row.get("caps") or 0) for row in intl_stats.values())>=51*22
    assert any(int(row.get("tournament_caps") or 0)>0 for row in intl_stats.values())


def test_p10_four_profiles_and_nomad_are_playable_in_fast_gate():
    profiles=profile_playability_gate(matches_per_profile=2,seed=10001)
    assert profiles["passed"] and len(profiles["profiles"])==4
    assert nomad_gate(seed=10002)["passed"]


def test_v016_save_migrates_to_p10_schema_without_losing_frozen_contract():
    career=ManagerCareerRuntime9394.create(team_id=3,league_id=1,seed=10101,through_matchday=0)
    legacy=dict(career.state)
    legacy["schema"]=16
    legacy.pop("market_ecosystem",None)
    legacy.pop("international_manager",None)
    legacy.pop("international_player_stats",None)
    restored=ManagerCareerRuntime9394(legacy)
    assert restored.state["schema"]==17
    assert restored.state["rules_policy"]=="frozen_1993_94"
    assert "international_manager" in restored.state and "international_player_stats" in restored.state


def test_p9_http_api_accepts_national_job_and_exposes_world_state(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    client=TestClient(webapp.app)
    monkeypatch.setattr(webapp,"CAREER_SAVE_ROOT",tmp_path)
    created=client.post('/api/football9394/careers',json={'team_id':3,'league_id':1,'seed':19094,'through_matchday':0})
    assert created.status_code==200
    cid=created.json()['career_id']
    career=webapp._load_manager_career(cid)
    offers=generate_national_job_offers(career.state,career.universe,day=date(1994,7,1),manager_reputation=100,seed=19094)
    webapp._career_store().save(career.state)
    accepted=client.post(f"/api/football9394/careers/{cid}/national-job/{offers[0]['id']}/accept")
    assert accepted.status_code==200
    payload=accepted.json()['career']['international_manager']
    assert payload['country_id']==offers[0]['country_id'] and len(payload['selection'])==22
    auto=client.put(f'/api/football9394/careers/{cid}/national-selection/auto')
    assert auto.status_code==200 and len(auto.json()['career']['international_manager']['selection'])==22
    world=client.get(f'/api/football9394/careers/{cid}/world')
    assert world.status_code==200
    assert world.json()['international_manager']['country_id']==offers[0]['country_id']
    assert 'international_tournaments' in world.json()
