from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394


def test_persistent_career_starts_before_matchday_8_and_does_not_recompute_past(tmp_path):
    career = ManagerCareerRuntime9394.create(team_id=16, seed=123, through_matchday=7)
    snap = career.snapshot()
    assert snap["game_date"] == "1993-10-23"
    assert snap["completed_matchday"] == 7
    assert snap["result_count"] == 70
    assert snap["next_match"]["matchday"] == 8
    assert snap["next_match"]["date"] == "1993-10-24"
    assert all(row["played"] == 7 for row in snap["standings"])

    original_results = list(career.state["results"])
    store = ManagerCareerStore9394(tmp_path)
    store.save(career.state)
    restored = ManagerCareerRuntime9394(store.load(career.state["career_id"]))
    assert restored.state["results"] == original_results
    assert restored.snapshot()["standings"] == snap["standings"]


def test_advance_stops_for_controlled_match_and_playing_advances_whole_world_matchday():
    career = ManagerCareerRuntime9394.create(team_id=16, seed=321, through_matchday=7)
    advanced = career.advance_day()
    assert advanced["advanced"] is True
    assert advanced["date"] == "1993-10-24"
    assert advanced["requires_match"] is True

    blocked = career.advance_day()
    assert blocked["advanced"] is False
    assert blocked["requires_match"] is True

    before = career.snapshot()
    after = career.play_next_matchday()
    assert before["completed_matchday"] == 7
    assert after["completed_matchday"] == 8
    assert after["result_count"] == 80
    assert all(row["played"] == 8 for row in after["standings"])
    assert after["next_match"]["matchday"] == 9


def test_user_tactics_are_durable_between_days_and_matches(tmp_path):
    career = ManagerCareerRuntime9394.create(team_id=16, seed=555, through_matchday=7)
    career.set_tactics({"formation":"4-3-3", "mentality":"attacking", "pressing":"high", "tempo":"high"})
    assert career.snapshot()["tactics"]["formation"] == "4-3-3"
    assert career.snapshot()["tactics"]["pressing"] == "high"

    store = ManagerCareerStore9394(tmp_path)
    store.save(career.state)
    restored = ManagerCareerRuntime9394(store.load(career.state["career_id"]))
    assert restored.snapshot()["tactics"]["mentality"] == "attacking"


def test_controlled_continental_match_stops_daily_advance_and_is_played_by_career():
    from datetime import date
    career = ManagerCareerRuntime9394.create(team_id=3, seed=9394, through_matchday=7)  # Barcelona · UCL group pool
    while career.current_date < date(1993, 11, 24):
        step = career.advance_day()
        if step.get("requires_match"):
            fixture = step.get("next_match") or {}
            if fixture.get("fixture_type") == "tournament":
                break
            # M14 deliberately surfaces an invalid XI as a manager decision
            # instead of silently replacing an injured starter.  Resolve that
            # decision here because this test is about continental scheduling.
            if not career.selection_snapshot()["valid"]:
                career.state["selection"] = career._safe_auto_selection()
            career.play_next_matchday()
    pending = career.pending_world_fixture()
    assert pending is not None
    assert pending["competition_name"] == "Copa de Europa"
    assert pending["fixture_type"] == "tournament"
    assert 3 in (int(pending["home_team_id"]), int(pending["away_team_id"]))
    result = career.play_next_matchday()
    assert career.state.get("pending_world_match") is None
    assert result["played_match"]["fixture_type"] == "tournament"
    assert len(career.state["daily_tournaments"]["1"]["group_results"]["A"]) == 2


def test_career_can_start_from_another_certified_league_and_from_season_start():
    from backend.app.football9394.manager_career import career_selectable_leagues
    options={row['source_id']:row for row in career_selectable_leagues()}
    assert 14 in options and 1 in options and 47 not in options
    french_team=options[14]['teams'][0]['source_id']
    career=ManagerCareerRuntime9394.create(team_id=french_team,league_id=14,seed=777,through_matchday=0)
    snap=career.snapshot()
    assert snap['game_date']=='1993-07-01'
    assert snap['preseason']['active'] is True
    assert snap['league_id']==14
    assert snap['team']['source_id']==french_team
    assert len(snap['standings'])==20
    assert snap['total_matchdays']==38
    calendar=career.career_calendar()
    assert len(calendar)==42
    assert sum(1 for row in calendar if row.get('fixture_type')=='friendly')==4


def test_full_9394_rollover_builds_playable_9495_with_honours_europe_and_summer_market():
    from datetime import date
    from backend.app.football9394.manager_career import _league_match_payload
    from backend.app.football9394.career_special_world import process_special_competitions
    from backend.app.football9394.career_tournaments import process_daily_tournaments

    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=9394,through_matchday=0)
    schedule=career._league_schedule()
    career.state['results']=[
        _league_match_payload(row['matchday'],row['id'],row['home_team_id'],row['away_team_id'],1 if index%3 else 0,0 if index%4 else 1)
        for index,row in enumerate(schedule)
    ]
    career.state['completed_matchday']=career._controlled_total_rounds()
    career._bootstrap_background_world(99)
    process_special_competitions(career,date(1994,6,30),bootstrap=True)
    process_daily_tournaments(career,date(1994,6,30),bootstrap=True)
    career.state['current_date']='1994-06-30'

    result=career.advance_day()
    snap=career.snapshot()
    assert result['date']=='1994-07-01'
    assert snap['season']=='1994-95'
    assert len(snap['season_archive'])==1
    assert snap['honours']
    assert {key:len(value) for key,value in snap['continental_qualifiers'].items()}=={'1':8,'2':16,'90':32}
    assert any(event['kind']=='season_rollover' for event in result['world_events'])
    rollover = next(event for event in result['world_events'] if event['kind']=='season_rollover')
    assert rollover['retirement_count'] == 0
    assert rollover['academy_intake_count'] == 0
    assert career.state.get('generated_players', {}) == {}
    assert any(row.get('date')=='1994-07-01' for row in snap['ai_transfer_history'])
    assert any(row.get('kind')=='contract_expired' for row in snap['contract_history'])
    assert {key:len(career.state['league_memberships'][key]) for key in ('1','2','3','9','10','11')}=={'1':20,'2':20,'3':20,'9':20,'10':20,'11':20}
    assert len(career.state['league_memberships']['4'])==18 and len(career.state['league_memberships']['102'])==20
    assert len(career.state['league_memberships']['31'])==18 and len(career.state['league_memberships']['54'])==18

    fixture=snap['next_match']
    assert fixture and fixture['date'].startswith('1994-') and fixture['fixture_type']=='friendly'
    # Preseason is real career time: play/advance through friendlies before the first league round.
    while career.next_scheduled_fixture() and career.next_scheduled_fixture().get('fixture_type')=='friendly':
        target=career.next_scheduled_fixture()
        while career.current_date < __import__('datetime').date.fromisoformat(target['date']): career.advance_day()
        if not career.selection_snapshot()['valid']: career.state['selection']=career._safe_auto_selection()
        career.play_next_matchday()
    target=career.next_scheduled_fixture()
    while career.current_date < __import__('datetime').date.fromisoformat(target['date']): career.advance_day()
    if not career.selection_snapshot()['valid']: career.state['selection']=career._safe_auto_selection()
    played=career.play_next_matchday()
    assert played['completed_matchday']>=1
    assert played['result_count']>0


def test_rollover_can_repeat_into_9596_without_resetting_history():
    from datetime import date
    from backend.app.football9394.manager_career import _league_match_payload
    from backend.app.football9394.career_special_world import process_special_competitions
    from backend.app.football9394.career_tournaments import process_daily_tournaments

    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=9394,through_matchday=0)

    def close_season(end_year: int):
        schedule=career._league_schedule()
        controlled=int(career.state['team_id']);career.state['results']=[]
        for index,row in enumerate(schedule):
            home,away=int(row['home_team_id']),int(row['away_team_id'])
            if home==controlled: hg,ag=3,0
            elif away==controlled: hg,ag=0,3
            else: hg,ag=(1 if index%3 else 0),(0 if index%4 else 1)
            career.state['results'].append(_league_match_payload(row['matchday'],row['id'],home,away,hg,ag))
        career.state['completed_matchday']=career._controlled_total_rounds()
        career._bootstrap_background_world(99)
        process_special_competitions(career,date(end_year,6,30),bootstrap=True)
        process_daily_tournaments(career,date(end_year,6,30),bootstrap=True)
        for month in range(1,7):
            career._process_monthly_economy_and_ai(date(end_year,month,1))
        career.state['current_date']=f'{end_year}-06-30'
        return career.advance_day()

    first=close_season(1994)
    assert first['date']=='1994-07-01'
    assert career.snapshot()['next_match']['date'].startswith('1994-')

    second=close_season(1995)
    snap=career.snapshot()
    assert second['date']=='1995-07-01'
    assert snap['season']=='1995-96'
    assert len(snap['season_archive'])==2
    assert len(snap['season_transition_log'])==2
    assert career.state.get('generated_players', {}) == {}
    assert all(int(row.get('retirement_count') or 0) == 0 and int(row.get('academy_intake_count') or 0) == 0 for row in snap['season_transition_log'])
    # The canonical history includes 25 playable league champions plus the
    # four tracked tournament champions per season.  Older versions of this
    # gate counted leagues only and silently ignored cup/continental history.
    assert len(snap['honours'])==58
    assert sum(1 for row in snap['honours'] if row.get('competition_kind')=='league')==50
    assert sum(1 for row in snap['honours'] if row.get('competition_kind')=='tournament')==8
    assert {key:len(value) for key,value in snap['continental_qualifiers'].items()}=={'1':8,'2':16,'90':32}
    assert snap['next_match']['date'].startswith('1995-')
    assert snap['next_match']['fixture_type']=='friendly'


def test_uruguay_odd_team_calendar_keeps_two_historical_round_robins_and_byes():
    from backend.app.football9394.manager_career import career_selectable_leagues
    options={row['source_id']:row for row in career_selectable_leagues()}
    team_id=options[49]['teams'][0]['source_id']
    career=ManagerCareerRuntime9394.create(team_id=team_id,league_id=49,seed=9394,through_matchday=0)
    schedule=career._league_schedule()
    assert career.snapshot()['total_matchdays']==26
    assert len(schedule)==156
    assert len(career.career_calendar())==28
    assert sum(1 for row in career.career_calendar() if row.get('fixture_type')=='friendly')==4
    appearances=sum(1 for fixture in schedule if team_id in (fixture['home_team_id'],fixture['away_team_id']))
    assert appearances==24


def test_selection_is_persistent_and_drives_controlled_team_sheet(tmp_path):
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=8001, through_matchday=0)
    initial = career.selection_snapshot()
    assert initial['valid'] and len(initial['starter_ids']) == 11
    # Find a legal historical substitution: foreign quotas and specialised roles
    # are now part of selection validation, so an arbitrary swap is not valid QA.
    starter_ids=list(initial['starter_ids']);bench_ids=list(initial['bench_ids']);changed=None
    for bench_index,incoming in enumerate(list(bench_ids)):
        for outgoing_index,outgoing in enumerate(list(starter_ids)):
            if career.universe.players_by_id[outgoing].get('primary_role')==0: continue
            trial_starters=list(starter_ids);trial_bench=list(bench_ids)
            trial_starters[outgoing_index]=incoming;trial_bench[bench_index]=outgoing
            try:
                changed=career.set_selection(trial_starters,trial_bench)
            except ValueError:
                continue
            starter_ids,bench_ids=trial_starters,trial_bench
            break
        if changed: break
    assert changed and changed['valid']
    assert {int(p.id) for p in career._sheet(16).starters} == set(starter_ids)

    store = ManagerCareerStore9394(tmp_path)
    store.save(career.state)
    restored = ManagerCareerRuntime9394(store.load(career.state['career_id']))
    assert restored.selection_snapshot()['starter_ids'] == starter_ids


def test_selection_rejects_an_injured_starter():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=8002, through_matchday=0)
    selection = career.selection_snapshot()
    injured = selection['starter_ids'][1]
    career.state['player_development'][str(injured)]['injury_days'] = 10
    career._rebuild_rosters()
    try:
        career.set_selection(selection['starter_ids'], selection['bench_ids'])
        assert False, 'an injured starter must be rejected'
    except ValueError as exc:
        assert 'lesionado' in str(exc).lower() or 'disponible' in str(exc).lower()


def test_manager_dashboard_has_real_objective_confidence_and_pending_decisions():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=8003, through_matchday=0)
    dashboard = career.manager_dashboard()
    assert dashboard['board_expectation']['title']
    assert dashboard['board_expectation']['title'] != 'Por definir'
    assert dashboard['board_confidence'] == 'A la espera'
    assert isinstance(dashboard['pending_decisions'], list)
    snap = career.snapshot()
    assert snap['selection']['valid'] is True
    assert snap['manager_dashboard']['board_expectation']['title'] == dashboard['board_expectation']['title']


def test_career_options_expose_useful_club_preview_details():
    from backend.app.football9394.manager_career import career_selectable_leagues
    options = career_selectable_leagues()
    team = options[0]['teams'][0]
    assert team['squad_size'] >= 11
    assert team['average_top_11'] > 0
    assert len(team['top_players']) <= 3
    assert {'members', 'budget', 'debt', 'stadium_id'} <= set(team)
