from datetime import date
from backend.app.football9394.career_tournaments import process_daily_tournaments, tournament_snapshot
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def test_continental_and_cup_competitions_live_in_daily_career_state():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=333,through_matchday=7)
    snap=tournament_snapshot(career)
    assert set(snap)=={'1','2','3','90','940001','940003','940004','940005','940006','940010','940017','940040','940043','940047','940084'}
    process_daily_tournaments(career,date(1993,11,25),bootstrap=True)
    snap=tournament_snapshot(career)
    assert snap['1']['result_count']>0
    assert snap['2']['result_count']>0
    assert snap['3']['result_count']>0
    assert snap['90']['result_count']>0


def test_tournament_calendar_does_not_claim_source_exact_dates():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=334,through_matchday=0)
    assert all('not_source_authoritative' in row['calendar_fidelity'] for row in tournament_snapshot(career).values())
