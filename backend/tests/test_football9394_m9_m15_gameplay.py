from __future__ import annotations

from datetime import date

from backend.app.football9394.career_ai import ensure_ai_squad_coverage, run_ai_transfer_window, squad_audit
from backend.app.football9394.career_board import apply_board_review, evaluate_board
from backend.app.football9394.career_news import ingest_events
from backend.app.football9394.career_special_world import process_special_competitions
from backend.app.football9394.career_tournaments import process_daily_tournaments
from backend.app.football9394.manager_career import ManagerCareerRuntime9394, _league_match_payload


def _close_season(career: ManagerCareerRuntime9394, end_year: int, offset: int = 0) -> dict:
    # Basic manager hygiene for a longitudinal gate: keep the controlled squad's
    # current contracts alive. The gate is about world/rollover integrity, not
    # deliberately ignoring renewal warnings for ten years.
    for player in career.squad():
        pid = str(int(player["id"]))
        contract = dict(player.get("contract") or {})
        salary = int(contract.get("salary") or 0)
        career.state["contract_overrides"][pid] = {
            **contract,
            "start": str(end_year - 1), "end": str(end_year + 2), "end_year": end_year + 2,
            "salary": salary, "career_inferred": True, "m15_gate_renewal": True,
        }
    schedule = career._league_schedule()
    controlled=int(career.state["team_id"])
    career.state["results"]=[]
    for index,row in enumerate(schedule):
        home,away=int(row["home_team_id"]),int(row["away_team_id"])
        if home==controlled: hg,ag=3,0
        elif away==controlled: hg,ag=0,3
        else: hg,ag=(1 if (index+offset)%3 else 0),(0 if (index+offset)%4 else 1)
        career.state["results"].append(_league_match_payload(row["matchday"],row["id"],home,away,hg,ag))
    career.state["completed_matchday"] = career._controlled_total_rounds()
    career._bootstrap_background_world(99)
    process_special_competitions(career, date(end_year, 6, 30), bootstrap=True)
    process_daily_tournaments(career, date(end_year, 6, 30), bootstrap=True)
    for month in range(1, 7):
        career._process_monthly_economy_and_ai(date(end_year, month, 1))
    career.state["current_date"] = f"{end_year}-06-30"
    return career.advance_day()


def test_m9_board_is_explainable_inertial_and_not_a_one_result_firing():
    expectation = {"expected_position": 8, "team_count": 20}
    healthy = evaluate_board(
        expectation=expectation, position=6, played=12, recent_form=["V", "E", "V", "D", "V"],
        projected_monthly_net=1_000_000, cash=20_000_000, debt=5_000_000,
    )
    poor = evaluate_board(
        expectation=expectation, position=20, played=12, recent_form=["D"] * 5,
        projected_monthly_net=-8_000_000, cash=2_000_000, debt=20_000_000,
        previous_score=healthy["score"],
    )
    assert healthy["score"] > poor["score"]
    assert healthy["reasons"] and poor["reasons"]
    state = {}
    critical = {**poor, "score": 10, "label": "Crítica", "risk": "RIESGO ALTO", "critical": True, "played": 12}
    first = apply_board_review(state, critical, date="1994-03-01", trigger="monthly")
    assert first.get("dismissed") is not True and state["job_status"] == "active"
    second = apply_board_review(state, critical, date="1994-04-01", trigger="monthly")
    assert second["dismissed"] is True and state["job_status"] == "dismissed"


def test_m10_news_is_causal_and_deduplicates_source_events():
    state = {"current_date": "1993-10-24"}
    event = {"kind": "ai_transfer", "date": "1993-10-24", "player_id": 1, "from_team_id": 10, "to_team_id": 20, "fee": 1_500_000}
    first = ingest_events(state, [event], team_name=lambda tid: f"Club {tid}", player_name=lambda pid: f"Jugador {pid}")
    second = ingest_events(state, [event], team_name=lambda tid: f"Club {tid}", player_name=lambda pid: f"Jugador {pid}")
    assert len(first) == 1 and second == []
    assert state["news_feed"][0]["category"] == "Mercado"
    assert "Jugador 1" in state["news_feed"][0]["headline"]


def test_m11_all_active_competitions_have_user_facing_directory_and_detail():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=1115, through_matchday=7)
    directory = career.competition_directory()
    assert len(directory) == 30
    assert {row["kind"] for row in directory} == {"league", "tournament"}
    league_ids={int(row["source_id"]) for row in directory if row["kind"]=="league"}
    assert {930057,930015,930047} <= league_ids
    league = career.competition_detail("league", 1)
    assert league["name"] == "Primera División" and len(league["standings"]) == 20
    assert league["calendar"] and league["participants"]
    special = career.competition_detail("league", 47)
    assert special["format"] == "special" and special["participants"]
    cup = career.competition_detail("tournament", 3)
    assert cup["format"] == "tournament" and "results" in cup and "honours" in cup


def test_m12_rollover_creates_memorable_recap_honours_news_and_history():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=1215, through_matchday=0)
    result = _close_season(career, 1994)
    snap = career.snapshot()
    assert result["date"] == "1994-07-01" and snap["season"] == "1994-95"
    assert len(snap["season_recaps"]) == 1
    recap = snap["season_recaps"][0]
    assert recap["season"] == "1993-94" and recap["league_name"] == "Primera División"
    assert recap["position"] is not None and recap["board"]["score"] is not None
    assert "economy" in recap and "headline" in recap
    assert len(snap["honours"]) == 29
    assert any(item["category"] in {"Competiciones", "Temporada"} for item in snap["news_feed"])


def _p(pid: int, slot: str, overall: int = 60, nationality: int = 11) -> dict:
    role_ids={"GK":0,"RB":1,"LB":2,"CB":3,"CM":7,"RM":9,"LM":13,"ST":17}
    broad={"GK":"POR","RB":"DEF","LB":"DEF","CB":"DEF","CM":"MED","RM":"MED","LM":"MED","ST":"DEL"}
    return {"source_id":pid,"primary_role":role_ids[slot],"broad_position":broad[slot],"overall":overall,"category":overall,"nationality_id":nationality}


def _balanced_without_strikers(base: int = 100) -> list[dict]:
    spec=[("GK",2),("RB",1),("LB",1),("CB",3),("CM",4),("RM",2),("LM",2),("ST",1)]
    rows=[];pid=base
    for slot,count in spec:
        for _ in range(count): rows.append(_p(pid,slot));pid+=1
    return rows


def test_m13_ai_recruits_for_specialist_need_and_repairs_summer_coverage():
    buyer=_balanced_without_strikers(100)
    seller=_balanced_without_strikers(500)+[_p(600+i,"ST",61+i%2) for i in range(5)]
    free=[_p(800+i,"ST",58+i) for i in range(4)]
    assert squad_audit(buyer,{})["primary_need"] == "ST"
    players={0:free.copy(),1:buyer.copy(),2:seller.copy()}
    finances={"1":{"cash":100_000_000,"transfer_spend":0,"transfer_income":0},"2":{"cash":10_000_000,"transfer_spend":0,"transfer_income":0}}
    overrides:dict[str,int]={};contracts:dict[str,dict]={}
    actions=run_ai_transfer_window(
        current_date=date(1994,7,1),controlled_team_id=999,eligible_team_ids=[1,2],
        players_by_team=players,development={},club_finances=finances,
        player_team_overrides=overrides,contract_overrides=contracts,seed=1315,max_deals=1,
    )
    assert actions and actions[0]["to_team_id"]==1 and actions[0]["need"]=="ST"
    players={0:free.copy(),1:buyer.copy(),2:seller.copy()};overrides={};contracts={}
    emergency=ensure_ai_squad_coverage(
        current_date=date(1994,7,1),controlled_team_id=999,eligible_team_ids=[1,2],
        players_by_team=players,development={},club_finances=finances,
        player_team_overrides=overrides,contract_overrides=contracts,seed=1316,max_signings=10,
    )
    own=[row for row in emergency if row["to_team_id"]==1]
    assert own and own[0]["need"]=="ST"
    assert any(row["need"]=="ST" for row in own)
    # After the specialist hole is fixed, a healthy club may also add ordinary
    # depth toward its senior-squad target instead of stopping at exactly 18.
    assert squad_audit(players[1],{})["coverage_ok"] is True


def test_m14_continue_skips_empty_days_until_next_decision_or_match():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=1415, through_matchday=7)
    assert career.advance_day()["requires_match"] is True
    career.play_next_matchday()
    before = career.current_date
    result = career.advance_until_event(max_days=14)
    assert result["advanced_days"] >= 2
    assert career.current_date > before
    assert result["requires_match"] is True or result["world_events"] or career.manager_dashboard()["pending_decisions"]


def test_m14_roster_shortage_never_crashes_career_and_is_surfaceable():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=1416, through_matchday=0)
    own = career.squad()
    # Simulate a catastrophic expiry wave: the game must remain navigable and
    # show a broken selection instead of throwing while repairing the XI.
    for player in own[8:]:
        career.state["player_team_overrides"][str(player["id"])] = 0
    career._rebuild_rosters()
    career.state["selection"] = career._safe_auto_selection()
    snap = career.selection_snapshot()
    assert snap["valid"] is False
    assert any("11" in issue for issue in snap["issues"])
    pending=career.manager_dashboard()["pending_decisions"]
    # Squad size and match-XI legality are separate concepts.  A catastrophic
    # shortage should surface the numeric 18-man floor *and* the broken XI.
    assert pending[0]["kind"] == "squad_depth"
    assert any(row["kind"] == "lineup" for row in pending)


def test_m15_three_season_product_gate_preserves_history_world_and_playability():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=1515, through_matchday=0)
    for index, end_year in enumerate((1994, 1995, 1996)):
        result = _close_season(career, end_year, offset=index)
        assert result["date"] == f"{end_year}-07-01"
        assert career.snapshot()["next_match"] is not None
    snap = career.snapshot()
    assert snap["season"] == "1996-97"
    assert len(snap["season_archive"]) == 3 and len(snap["season_recaps"]) == 3
    assert len(snap["honours"]) == 75 and len(snap["season_transition_log"]) == 3
    assert len(career.competition_directory()) == 30
    assert snap["news_feed"] and snap["job_status"] == "active"


def test_m10_news_ids_remain_unique_after_retention_trim():
    from backend.app.football9394.career_news import publish
    state={}
    for index in range(805):
        publish(state,key=f'k:{index}',date='1994-01-01',category='Mundo',importance=1,headline=f'Noticia {index}')
    ids=[item['id'] for item in state['news_feed']]
    assert len(ids)==800 and len(set(ids))==800
    assert state['news_serial']==805 and ids[-1]=='news-805'


def test_m13_ai_never_sells_the_only_goalkeeper_even_to_a_club_that_needs_one():
    buyer=[_p(1000+i,'CB' if i<5 else 'CM' if i<10 else 'ST',60) for i in range(16)]
    seller=_balanced_without_strikers(2000)+[_p(2100+i,'ST',62) for i in range(3)]
    # seller has exactly one natural goalkeeper; it is the only candidate for buyer's GK need
    seller=[p for i,p in enumerate(seller) if p['primary_role']!=0 or i==0]
    assert sum(1 for p in seller if p['primary_role']==0)==1 and len(seller)>16
    players={1:buyer,2:seller}
    finances={'1':{'cash':100_000_000,'transfer_spend':0,'transfer_income':0},'2':{'cash':10_000_000,'transfer_spend':0,'transfer_income':0}}
    actions=run_ai_transfer_window(
        current_date=date(1994,7,1),controlled_team_id=999,eligible_team_ids=[1,2],
        players_by_team=players,development={},club_finances=finances,
        player_team_overrides={},contract_overrides={},seed=1317,max_deals=1,
    )
    assert squad_audit(buyer,{})['primary_need']=='GK'
    assert actions==[]
    assert sum(1 for p in players[2] if p['primary_role']==0)==1


def test_m13_insolvent_ai_can_rebuild_a_minimum_real_squad_from_free_agents():
    roster=[_p(3000+i,'CB' if i<3 else 'CM' if i<6 else 'ST',54) for i in range(8)]
    slots=['GK','GK','RB','LB','CB','CB','CM','CM','RM','LM','ST','ST','CB','CM','ST','RM','LM','RB','LB','ST']
    free=[_p(4000+i,slot,52+i%5) for i,slot in enumerate(slots)]
    players={0:free,1:roster}
    finances={'1':{'cash':-5_000_000,'transfer_spend':0,'transfer_income':0}}
    actions=ensure_ai_squad_coverage(
        current_date=date(1994,7,1),controlled_team_id=999,eligible_team_ids=[1],
        players_by_team=players,development={},club_finances=finances,
        player_team_overrides={},contract_overrides={},seed=1318,max_signings=20,
    )
    assert actions and any(row.get('financial_distress') for row in actions)
    assert len(players[1])>=18
    assert any(p['primary_role']==0 for p in players[1])


def test_m15_four_manager_profiles_can_play_ten_matches_each_with_surfaced_lineup_decisions():
    """Technical playtest of four deliberately different career starts.

    A human manager is expected to react when an injury invalidates the saved
    lineup.  The test therefore uses the one-action best-XI helper when the
    inbox would surface that decision, then continues playing.  No game state is
    silently repaired before the decision exists.
    """
    profiles=(
        ("favorito",1,3),          # FC Barcelona
        ("medio",1,16),            # Real Sociedad
        ("modesto_primera",1,692), # UE Lleida
        ("division_inferior",10,27), # Deportivo Alavés
    )
    reports=[]
    for index,(label,league_id,team_id) in enumerate(profiles):
        career=ManagerCareerRuntime9394.create(team_id=team_id,league_id=league_id,seed=150826+team_id+index,through_matchday=0)
        lineup_decisions=0
        for _ in range(10):
            assert career.next_scheduled_fixture() is not None, (label,career.current_date)
            if not career.selection_snapshot()['valid']:
                assert any(row['kind']=='lineup' for row in career.manager_dashboard()['pending_decisions'])
                career.state['selection']=career._safe_auto_selection()
                lineup_decisions+=1
            assert career.selection_snapshot()['valid'], (label,career.selection_snapshot()['issues'])
            career.play_next_matchday()
        snap=career.snapshot();dash=career.manager_dashboard()
        assert snap['job_status']=='active'
        assert snap['next_match'] is not None
        assert len(career.squad())>=18
        assert dash['board']['score'] is not None
        reports.append((label,lineup_decisions))
    assert len(reports)==4
