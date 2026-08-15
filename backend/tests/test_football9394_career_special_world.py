from datetime import date

from backend.app.football9394.career_special_world import ensure_special_competitions, process_special_competitions, special_competition_snapshot
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def test_special_competitions_bootstrap_to_october_and_then_progress_incrementally():
    career=ManagerCareerRuntime9394.create(team_id=16,seed=818,through_matchday=7)
    snap=special_competition_snapshot(career)
    assert set(snap)=={'47','111','120'}
    assert snap['120']['completed'] is True
    assert snap['47']['completed_round'] >= 7
    assert snap['111']['stage'] in {'nicos','championship_setup','championship_leg1','championship_leg2','completed'}
    before=snap['47']['completed_round']
    process_special_competitions(career,date(1993,10,24),bootstrap=False)
    after=special_competition_snapshot(career)['47']['completed_round']
    assert after >= before


def test_special_calendar_declares_date_fidelity_instead_of_claiming_historical_dates():
    state={};ensure_special_competitions(state)
    assert all('not_source_authoritative' in row['calendar_fidelity'] for row in state['special_competitions'].values())
