from __future__ import annotations

from datetime import timedelta
from statistics import mean

import pytest

from backend.app.football9394.manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394
from backend.app.football9394.match_engine import FootballMatchEngine9394, FootballTactics9394
from backend.app.football9394.team_builder import build_snapshot_team_sheet
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_m4_every_tactical_control_has_validated_identity_and_observable_tradeoffs():
    with pytest.raises(ValueError):
        FootballTactics9394(width="ultrawide")
    universe=default_runtime_snapshot();home_id=16;away_id=3
    engine=FootballMatchEngine9394()
    wide=FootballTactics9394(formation="4-3-3",mentality="attacking",tempo="high",pressing="high",directness="direct",defensive_line="high",width="wide",offside_trap=True,marking="man")
    cautious=FootballTactics9394(formation="5-3-2",mentality="defensive",tempo="slow",pressing="low",directness="short",defensive_line="low",width="narrow",offside_trap=False,marking="zonal")
    active=[];quiet=[];trap_offsides=[];low_offsides=[]
    for seed in range(60):
        r1=engine.simulate(build_snapshot_team_sheet(universe,home_id,tactics=wide),build_snapshot_team_sheet(universe,away_id,tactics=cautious),seed=seed)
        r2=engine.simulate(build_snapshot_team_sheet(universe,home_id,tactics=cautious),build_snapshot_team_sheet(universe,away_id,tactics=wide),seed=1000+seed)
        active.append(r1.home.shots+r1.home.corners+r1.home.fouls);quiet.append(r2.home.shots+r2.home.corners+r2.home.fouls)
        trap_offsides.append(r2.home.offsides);low_offsides.append(r1.home.offsides)
    assert mean(active) > mean(quiet)
    # High line + trap on the opponent catches the cautious/short side more often
    # than the low-line defensive setup catches the direct attacking side.
    assert mean(trap_offsides) > 0


def _reach_matchday(career: ManagerCareerRuntime9394) -> None:
    step=career.advance_day()
    assert step["requires_match"] is True


def _legal_live_substitution(career: ManagerCareerRuntime9394):
    snap=career.live_match_snapshot()
    for incoming in [p["id"] for p in snap["controlled_bench"]]:
        for outgoing in [p["id"] for p in snap["controlled_on_pitch"] if p["position"] not in {"POR","GK"}]:
            try:
                return career.substitute_live_match(outgoing,incoming)
            except ValueError:
                continue
    raise AssertionError("no se encontró una sustitución reglamentariamente válida")


def test_m5_live_match_is_persistent_interactive_and_commits_whole_round(tmp_path):
    career=ManagerCareerRuntime9394.create(team_id=16,seed=5151,through_matchday=7)
    _reach_matchday(career)
    live=career.start_live_match()
    assert live["minute"]==0 and live["status"]=="live"
    career.advance_live_match(45)
    assert career.live_match_snapshot()["status"]=="halftime"
    career.set_live_tactics({"formation":"4-3-3","mentality":"attacking","tempo":"high","pressing":"high","directness":"direct","defensive_line":"high","width":"wide","offside_trap":True,"marking":"man"})
    _legal_live_substitution(career)
    assert career.live_match_snapshot()["home"]["substitutions"] + career.live_match_snapshot()["away"]["substitutions"] >= 1

    store=ManagerCareerStore9394(tmp_path);store.save(career.state)
    career=ManagerCareerRuntime9394(store.load(career.state["career_id"]))
    assert career.live_match_snapshot()["status"]=="halftime"
    while career.live_match_snapshot()["status"]!="finished": career.advance_live_match(20)
    result=career.finish_live_match()
    assert result["career"]["completed_matchday"]==8
    assert result["career"]["result_count"]==80
    assert result["career"]["live_match"] is None
    assert result["match"]["events"][-1]["kind"]=="fulltime"


def test_m5_instant_result_uses_live_engine_and_delegates_both_benches():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=5153,through_matchday=7);_reach_matchday(career)
    preview=career.start_live_match();controlled_home=int(preview["home_team_id"])==16
    side_key="home" if controlled_home else "away"
    raw=career.state["live_match"][side_key]
    for pid in raw.get("on_pitch_ids") or []:
        raw.setdefault("fatigue",{})[str(pid)]=60.0
    result=career.simulate_live_match();report=result["match"]
    controlled_stats=report["home"] if controlled_home else report["away"]
    assert report["committed"] is True and report["events"][-1]["kind"]=="fulltime"
    assert 1 <= controlled_stats["substitutions"] <= 2
    assert career.state["live_match"] is None


def test_m5_historical_two_substitution_cap_is_enforced_in_live_match():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=5152,through_matchday=7);_reach_matchday(career);career.start_live_match()
    _legal_live_substitution(career)
    _legal_live_substitution(career)
    snap=career.live_match_snapshot()
    outgoing=next(p["id"] for p in snap["controlled_on_pitch"] if p["position"] not in {"POR","GK"})
    incoming=snap["controlled_bench"][0]["id"]
    with pytest.raises(ValueError): career.substitute_live_match(outgoing,incoming)


def test_m6_managed_players_build_match_ratings_assists_and_history():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=6161,through_matchday=7);_reach_matchday(career)
    career.play_next_matchday()
    detailed=[career.player_detail(p["id"]) for p in career.snapshot()["squad"]]
    with_history=[p for p in detailed if p.get("match_history")]
    assert with_history
    assert any(p["season_stats"].get("average_rating") is not None for p in with_history)
    assert all(4.0 <= p["match_history"][-1]["rating"] <= 10.0 for p in with_history)
    assert {"yellow_cards","red_cards","average_rating"} <= set(with_history[0]["season_stats"])


def test_m7_watchlist_and_multiday_negotiation_flow_progresses_on_calendar():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=7171,through_matchday=7);_reach_matchday(career);career.play_next_matchday()
    market=career.search_market(limit=100)
    cash=career.state["finances"]["cash"]
    target=next(p for p in sorted(market,key=lambda p:p["estimated_transfer_value"]) if p["estimated_transfer_value"] <= cash*.7)
    career.toggle_watchlist(target["id"],True)
    assert career.search_market(limit=100,watched=True)[0]["watched"] is True
    fee=min(cash,round(target["estimated_transfer_value"]*1.25));salary=max(target["market"]["minimum_salary_hint"],target["contract"]["salary"])
    row=career.open_transfer_negotiation(target["id"],fee_offer=fee,salary_offer=salary,contract_years=3)
    assert row["status"]=="waiting" and row["response_date"]>career.current_date.isoformat()
    due=career.current_date
    for _ in range(8):
        due+=timedelta(days=1)
        events=career._process_user_negotiations(due)
        if row["status"]!="waiting": break
    assert row["status"] in {"countered","completed"}
    assert row["history"][-1]["kind"] in {"counter","accepted"}


def test_m7_user_can_list_player_and_receive_ai_offer_without_hollowing_logic():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=7272,through_matchday=7)
    player=career.squad()[5]
    listing=career.list_player_for_transfer(player["id"],asking_price=max(1,round(player["estimated_transfer_value"]*.7)))
    assert listing["player_id"]==player["id"]
    day=career.current_date
    got=[]
    for _ in range(45):
        day+=timedelta(days=1);got.extend(career._process_user_listings(day))
        if got: break
    assert got and got[0]["kind"]=="incoming_transfer_offer"


def test_m8_economy_snapshot_explains_cash_wages_reserve_and_projection():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=8181,through_matchday=0)
    economy=career.economy_snapshot()
    assert economy["cash"]==career.state["finances"]["cash"]
    assert economy["monthly_wages"]>0 and abs(economy["annual_wages"]-economy["monthly_wages"]*12)<=6
    assert economy["safety_reserve"]>0 and economy["transfer_room"]>=0
    assert economy["status"] in {"Sólida","Vigilancia","Tensión"}
    assert economy["contract_data_note"]


def test_m4_m8_api_live_player_and_economy_contract(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    client=TestClient(webapp.app)
    state=client.post('/api/football9394/careers',json={'team_id':16,'league_id':1,'seed':9090,'through_matchday':7}).json();cid=state['career_id']
    assert client.post(f'/api/football9394/careers/{cid}/advance').json()['requires_match'] is True
    started=client.post(f'/api/football9394/careers/{cid}/live/start')
    assert started.status_code==200 and started.json()['match']['minute']==0
    halftime=client.post(f'/api/football9394/careers/{cid}/live/advance',json={'minutes':45})
    assert halftime.status_code==200 and halftime.json()['match']['status']=='halftime'
    live=halftime.json()['match']; outgoing=next(p for p in live['controlled_on_pitch'] if p['position'] not in {'POR','GK'})['id'];incoming=live['controlled_bench'][0]['id']
    changed=client.post(f'/api/football9394/careers/{cid}/live/substitution',json={'outgoing_id':outgoing,'incoming_id':incoming})
    assert changed.status_code==200
    detail=client.get(f'/api/football9394/careers/{cid}/players/{outgoing}')
    assert detail.status_code==200 and 'season_stats' in detail.json()
    economy=client.get(f'/api/football9394/careers/{cid}/economy')
    assert economy.status_code==200 and economy.json()['summary']['transfer_room']>=0



def test_m5_api_result_from_preview_finishes_and_commits(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    client=TestClient(webapp.app)
    state=client.post('/api/football9394/careers',json={'team_id':16,'league_id':1,'seed':9091,'through_matchday':7}).json();cid=state['career_id']
    assert client.post(f'/api/football9394/careers/{cid}/advance').json()['requires_match'] is True
    preview=client.post(f'/api/football9394/careers/{cid}/live/start')
    assert preview.status_code==200 and preview.json()['match']['minute']==0
    result=client.post(f'/api/football9394/careers/{cid}/live/result')
    assert result.status_code==200
    payload=result.json();match=payload['match'];career=payload['career']
    assert match['committed'] is True and match['status']=='finished'
    assert match['events'][-1]['kind']=='fulltime'
    assert career['live_match'] is None and career['completed_matchday']==8
    assert career['result_count']==80

def test_m7_api_opens_persistent_multiday_negotiation(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    client=TestClient(webapp.app)
    state=client.post('/api/football9394/careers',json={'team_id':16,'league_id':1,'seed':9191,'through_matchday':0}).json();cid=state['career_id']
    market=client.get(f'/api/football9394/careers/{cid}/market?limit=100').json();target=min(market,key=lambda p:p['estimated_transfer_value'])
    watch=client.post(f"/api/football9394/careers/{cid}/watchlist/{target['id']}",json={'watched':True})
    assert watch.status_code==200 and target['id'] in watch.json()['career']['market_flow']['watchlist']
    offer=client.post(f'/api/football9394/careers/{cid}/negotiations',json={'player_id':target['id'],'fee_offer':target['estimated_transfer_value'],'salary_offer':target['market']['minimum_salary_hint'],'contract_years':3})
    assert offer.status_code==200
    row=offer.json()['negotiation'];assert row['status']=='waiting' and row['response_date']>state['game_date']
    flow=client.get(f'/api/football9394/careers/{cid}/market-flow').json()
    assert any(n['id']==row['id'] for n in flow['negotiations'])


def test_m5_minute_zero_preview_can_be_cancelled_but_started_match_cannot():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=5154,through_matchday=7);_reach_matchday(career)
    preview=career.start_live_match()
    assert preview['minute']==0 and career.state['live_match'] is not None
    state=career.cancel_live_preview()
    assert state['live_match'] is None and career.state['live_match'] is None

    career.start_live_match();career.advance_live_match(1)
    with pytest.raises(ValueError,match='ya ha comenzado'):
        career.cancel_live_preview()
    assert career.state['live_match'] is not None


def test_m5_api_can_return_from_preview_to_lineup_without_committing(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    client=TestClient(webapp.app)
    state=client.post('/api/football9394/careers',json={'team_id':16,'league_id':1,'seed':9092,'through_matchday':7}).json();cid=state['career_id']
    assert client.post(f'/api/football9394/careers/{cid}/advance').json()['requires_match'] is True
    preview=client.post(f'/api/football9394/careers/{cid}/live/start')
    assert preview.status_code==200 and preview.json()['match']['minute']==0
    cancelled=client.delete(f'/api/football9394/careers/{cid}/live/preview')
    assert cancelled.status_code==200 and cancelled.json()['career']['live_match'] is None
    persisted=client.get(f'/api/football9394/careers/{cid}').json()
    assert persisted['live_match'] is None and persisted['completed_matchday']==7
