from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def test_club_reference_screen_context_is_source_backed():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    snap = career.snapshot()
    assert snap['source_manager']['display_name'] == 'Johan Cruyff'
    assert snap['source_manager']['primary_tactic'] == '3-4-3 Rombo'
    assert snap['source_manager']['coaching_quality'] == 85
    assert snap['venue']['name'] == 'Camp Nou'
    assert snap['venue']['capacity'] == 115000


def test_player_reference_screen_has_identity_roles_and_dynamics():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    romario = career.player_detail(9)
    assert romario['display_name'] == 'Romário'
    assert romario['identity']['archetype'] == 'Finalizador'
    assert romario['position_profiles'][0]['primary'] is True
    assert romario['tactical_fit']['score'] > 0
    assert 'satisfaction' in romario['squad_dynamics']
