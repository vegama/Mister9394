from __future__ import annotations

from datetime import date
from statistics import median
from collections import Counter
import json

import pytest

from backend.app.football9394.career_special_world import process_special_competitions
from backend.app.football9394.career_tournaments import process_daily_tournaments
from backend.app.football9394.manager_career import ManagerCareerRuntime9394, _league_match_payload
from backend.app.football9394.position_roles import role_for_player


def _close_season(career: ManagerCareerRuntime9394, end_year: int, offset: int = 0) -> None:
    # Keep the human-controlled squad together: this is a world-integrity gate,
    # not a test of a human deliberately ignoring contract renewals.
    for player in career.squad():
        pid=str(int(player['id'])); contract=dict(player.get('contract') or {}); salary=int(contract.get('salary') or 0)
        career.state['contract_overrides'][pid]={
            **contract,'start':str(end_year-1),'end':str(end_year+2),'end_year':end_year+2,
            'salary':salary,'career_inferred':True,'m15_gate_renewal':True,
        }
    schedule=career._league_schedule(); controlled=int(career.state['team_id']); career.state['results']=[]
    for index,row in enumerate(schedule):
        home,away=int(row['home_team_id']),int(row['away_team_id'])
        if home==controlled: hg,ag=3,0
        elif away==controlled: hg,ag=0,3
        else: hg,ag=(1 if (index+offset)%3 else 0),(0 if (index+offset)%4 else 1)
        career.state['results'].append(_league_match_payload(row['matchday'],row['id'],home,away,hg,ag))
    career.state['completed_matchday']=career._controlled_total_rounds()
    career._bootstrap_background_world(99)
    process_special_competitions(career,date(end_year,6,30),bootstrap=True)
    process_daily_tournaments(career,date(end_year,6,30),bootstrap=True)
    for month in range(1,7):
        career._process_monthly_economy_and_ai(date(end_year,month,1))
    career.state['current_date']=f'{end_year}-06-30'
    result=career.advance_day()
    assert result['date']==f'{end_year}-07-01'


@pytest.mark.longitudinal
def test_ten_seasons_preserve_a_playable_world_and_compact_persistent_history():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=159394,through_matchday=0)
    for index,end_year in enumerate(range(1994,2004)):
        _close_season(career,end_year,index)
        active=[tid for tid in career._active_club_ids() if tid!=int(career.state['team_id'])]
        assert active
        for tid in active:
            roster=career._career_players_by_team.get(tid,[])
            assert len(roster)>=18, (end_year,tid,len(roster))
            assert any(role_for_player(player).squad_slot=='GK' for player in roster), (end_year,tid,'no natural GK')
        # Building every tactical XI is intentionally a horizon gate rather than
        # a monthly/annual workload: summer health already audits structural
        # coverage cheaply.  At years 3 and 10 we still prove that *every* AI
        # club can produce a legal XI under specialist + foreign-player rules.
        if end_year in {1996,2003}:
            for tid in active:
                sheet=career._sheet(tid)
                assert len(sheet.starters)==11, (end_year,tid,'no legal XI')
        assert career.snapshot()['next_match'] is not None
        # Mid-career persistence is part of the longitudinal gate: caches and
        # in-memory helpers must not be required for the second half of a save.
        if end_year == 1998:
            career=ManagerCareerRuntime9394(json.loads(json.dumps(career.state)))

    snap=career.snapshot()
    assert snap['season']=='2003-04'
    assert len(snap['season_archive'])==10
    assert len(snap['season_recaps'])==10
    assert len(snap['honours'])==290
    assert len(snap['season_transition_log'])==10
    assert snap['job_status']=='active'
    assert len(snap['news_feed'])<=800
    assert len({row['id'] for row in snap['news_feed']})==len(snap['news_feed'])
    assert int(career.state.get('news_serial') or 0)>800

    # Ten-year balance guardrails.  Eighteen is an emergency floor, not the
    # normal destination for every AI squad.
    active=career._active_club_ids()
    sizes=[len(career._career_players_by_team.get(tid,[])) for tid in active]
    assert median(sizes)>=20
    assert max(sizes)<=25

    # The economy may create winners and distressed clubs, but should not
    # collapse a large share of the football world or create runaway cash.
    finances=[career.state['club_finances'].get(str(tid),{}) for tid in active]
    negative=sum(1 for row in finances if int(row.get('cash') or 0)<0)
    assert negative/len(finances) < .20
    assert max(int(row.get('cash') or 0) for row in finances) < 2_500_000_000

    # Hierarchy is dynamic but gradual.  Across a decade there must be genuine
    # movement without a single club teleporting several status bands at once.
    statuses=[career.state['club_status'][str(tid)] for tid in active if str(tid) in career.state['club_status']]
    shifts=[float(row.get('score') or 0)-float(row.get('initial_score') or row.get('score') or 0) for row in statuses]
    assert any(abs(value)>=8 for value in shifts)
    assert max(abs(value) for value in shifts)<=15
    assert all(abs(float(hist.get('change') or 0))<=3.5 for row in statuses for hist in row.get('history') or [])
    tiers=Counter(str(row.get('tier')) for row in statuses)
    # The hierarchy may evolve, but a decade must not flatten world football
    # into an army of global giants.  The 1993-94 baseline starts with 24.
    assert 15 <= tiers['GIGANTE'] <= 50
    assert tiers['MEDIO'] + tiers['MODESTO'] >= 150
