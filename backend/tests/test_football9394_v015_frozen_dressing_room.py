from datetime import date

from backend.app.football9394.long_career import (
    AGE_POLICY_FROZEN, AGE_POLICY_DYNAMIC, apply_ageing_and_retirement,
    generate_annual_academy_intake,
)
from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.dressing_room import (
    dressing_room_snapshot, set_captain, update_after_match,
    register_important_departure, reencounters_for_opponent,
)
from backend.app.football9394.career_memory import adjust_player_manager_relationship


def test_frozen_age_is_default_and_api_age_does_not_advance():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    assert career.state['age_policy'] == AGE_POLICY_FROZEN
    player = career.squad()[0]
    age = player['age']
    career.state['current_date'] = '2003-10-23'
    career._rebuild_rosters()
    assert career.player_detail(player['id'])['age'] == age
    assert career.player_detail(player['id'])['age_frozen'] is True


def test_frozen_mode_disables_retirement_and_academy_generation():
    universe = default_runtime_snapshot()
    player = dict(universe.players_by_team[16][0])
    state = {'age_policy': AGE_POLICY_FROZEN, 'player_development': {str(player['source_id']): {'overall': 70}}, 'player_team_overrides': {}}
    assert apply_ageing_and_retirement(state, players=[player], game_date=date(2040, 7, 1), seed=1) == []
    assert generate_annual_academy_intake(state, universe=universe, team_ids=[16], game_date=date(2040, 7, 1), seed=1, players_by_team={16: [player]}) == []
    assert state.get('generated_players', {}) == {}


def test_dynamic_mode_still_exists_as_explicit_alternative():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0, age_policy=AGE_POLICY_DYNAMIC)
    assert career.state['age_policy'] == AGE_POLICY_DYNAMIC
    assert career.squad()[0]['age_frozen'] is False


def test_dressing_room_has_captain_leaders_competition_and_mentoring():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    snap = dressing_room_snapshot(career.state, players=career._career_players_by_team[16], game_date=career.current_date)
    assert snap['captain_id']
    assert len(snap['leaders']) >= 3
    assert isinstance(snap['competitions'], list)
    assert isinstance(snap['mentorships'], list)
    candidate = next(p for p in career._career_players_by_team[16] if int(p['source_id']) != int(snap['captain_id']))
    old = snap['captain_id']
    result = set_captain(career.state, player_id=int(candidate['source_id']), players=career._career_players_by_team[16], date_text=career.current_date.isoformat())
    assert result['captain_id'] == int(candidate['source_id'])
    assert result['previous_player_id'] == old


def test_leadership_and_departure_create_persistent_consequences_and_reencounters():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    players = career._career_players_by_team[16]
    snap = dressing_room_snapshot(career.state, players=players, game_date=career.current_date)
    captain = int(snap['captain_id'])
    starters = [int(p['source_id']) for p in players[:11]]
    before = {int(p['source_id']): int(career.state['player_development'][str(int(p['source_id']))]['morale']) for p in players}
    update_after_match(career.state, players=players, starter_ids=starters, won=False, drew=False, date_text=career.current_date.isoformat())
    register_important_departure(career.state, player_id=captain, players_before=players, date_text=career.current_date.isoformat())
    assert any(e['kind'] == 'important_departure' for e in career.state['dressing_room']['events'])
    assert any(int(career.state['player_development'][str(pid)]['morale']) <= val for pid, val in before.items() if pid != captain)
    other = players[1]
    adjust_player_manager_relationship(career.state, player_id=int(other['source_id']), date_text=career.current_date.isoformat(), delta=10, reason='etapa compartida')
    found = reencounters_for_opponent(career.state, opponent_players=[other])
    assert found and found[0]['player_id'] == int(other['source_id'])


def test_frozen_age_players_can_change_specific_attributes_without_ageing():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    striker = max(career._career_players_by_team[16], key=lambda p: int((p.get('attributes') or {}).get('finishing') or 0))
    pid = str(int(striker['source_id']))
    before_age = career.player_detail(int(pid))['age']
    before_finishing = int(career.player_detail(int(pid))['attributes'].get('finishing') or 0)
    # Sustained scoring evidence settles into a concrete finishing delta.
    from backend.app.football9394.development import apply_match_development
    for i in range(14):
        apply_match_development(
            career.state['player_development'], player_ids=[pid], starter_ids=[pid],
            won=True, drew=False, goal_ids=[pid], seed=9000+i,
            source_players=career._all_players_index(), game_date=career.current_date,
            age_reference_date=date(1993,10,23),
        )
    detail = career.player_detail(int(pid))
    assert detail['age'] == before_age
    assert int(detail['attributes'].get('finishing') or 0) > before_finishing
    assert int(detail['attribute_deltas'].get('finishing') or 0) >= 1


def test_role_promise_is_judged_by_actual_starts_and_kept_builds_trust():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    players = career._career_players_by_team[16]
    player = players[0]
    pid = int(player['source_id'])
    from backend.app.football9394.dressing_room import set_role_promise, role_promise_api
    from backend.app.football9394.career_memory import relationship_api
    before = int(relationship_api(career.state, pid)['trust'])
    set_role_promise(career.state, player_id=pid, role='Titular', players=players, date_text=career.current_date.isoformat())
    for _ in range(8):
        update_after_match(career.state, players=players, starter_ids=[pid], won=True, drew=False, date_text=career.current_date.isoformat())
    promise = role_promise_api(career.state, pid)
    assert promise['status'] == 'kept'
    assert promise['actual_start_share'] == 1.0
    assert int(relationship_api(career.state, pid)['trust']) > before


def test_broken_role_promise_damages_relationship_without_changing_ability():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    players = career._career_players_by_team[16]
    player = players[0]
    pid = int(player['source_id'])
    from backend.app.football9394.dressing_room import set_role_promise, role_promise_api
    from backend.app.football9394.career_memory import relationship_api
    before_overall = career.player_detail(pid)['overall']
    before = int(relationship_api(career.state, pid)['trust'])
    set_role_promise(career.state, player_id=pid, role='Figura', players=players, date_text=career.current_date.isoformat())
    starters = [int(p['source_id']) for p in players[1:12]]
    for _ in range(8):
        update_after_match(career.state, players=players, starter_ids=starters, won=False, drew=False, date_text=career.current_date.isoformat())
    promise = role_promise_api(career.state, pid)
    assert promise['status'] == 'broken'
    assert int(relationship_api(career.state, pid)['trust']) < before
    assert career.player_detail(pid)['overall'] == before_overall


def test_dismissal_closes_role_promises_without_blaming_manager():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    players = career._career_players_by_team[16]
    pid = int(players[0]['source_id'])
    from backend.app.football9394.dressing_room import set_role_promise, close_role_promises_on_manager_exit, role_promise_api
    from backend.app.football9394.career_memory import relationship_api
    set_role_promise(career.state, player_id=pid, role='Titular', players=players, date_text=career.current_date.isoformat())
    before = int(relationship_api(career.state, pid)['trust'])
    closed = close_role_promises_on_manager_exit(career.state, date_text=career.current_date.isoformat(), voluntary=False)
    assert closed and closed[0]['status'] == 'closed_by_dismissal'
    assert role_promise_api(career.state, pid)['status'] == 'closed_by_dismissal'
    assert int(relationship_api(career.state, pid)['trust']) == before


def test_long_injury_return_reopens_competition_without_restoring_starting_place_automatically():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, through_matchday=0)
    players = career._career_players_by_team[16]
    from backend.app.football9394.dressing_room import register_return_from_injury
    snap = dressing_room_snapshot(career.state, players=players, game_date=career.current_date)
    pid = int(snap['captain_id'])
    dev = career.state['player_development'][str(pid)]
    dev['injury_history'] = [{'name':'Lesión de prueba','days':28,'expected_days':28,'end':career.current_date.isoformat()}]
    original_selection = dict(career.state.get('selection') or {})
    event = register_return_from_injury(career.state, player_id=pid, players=players, date_text=career.current_date.isoformat())
    assert event and event['kind'] == 'important_return'
    assert event['days_out'] == 28
    assert event['leadership_return'] is True
    assert career.state.get('selection') == original_selection
    assert any(row['kind'] == 'important_return' for row in career.state['dressing_room']['events'])
