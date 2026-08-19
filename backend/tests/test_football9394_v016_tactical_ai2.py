from __future__ import annotations

from dataclasses import asdict

from backend.app.football9394.manager_career import (
    ManagerCareerRuntime9394, RULES_POLICY_FROZEN_9394,
)
from backend.app.football9394.match_engine import FootballTactics9394
from backend.app.football9394.tactical_ai import (
    expected_managed_tactics, prepare_tactics_for_opponent,
    record_managed_tactical_usage, record_rival_preparation_outcome,
    rival_learning_for_preparation, tactical_context_for_fixture,
)
from backend.app.football9394.transfer_periods import transfer_period_status


def _player(pid: int, *, overall: int = 75, pace: int = 65, acceleration: int = 65,
            off_ball: int = 65, vision: int = 65, short_pass: int = 65,
            technique: int = 65, crossing: int = 60, dribbling: int = 60,
            heading: int = 60, jumping: int = 60, strength: int = 60,
            stamina: int = 68, work_rate: int = 68, aggression: int = 60,
            role: int = 17) -> dict:
    return {
        'source_id': pid, 'overall': overall, 'primary_role': role,
        'pace': pace, 'acceleration': acceleration, 'off_ball': off_ball,
        'vision': vision, 'short_pass': short_pass, 'technique': technique,
        'crossing': crossing, 'dribbling': dribbling,
        'heading': heading, 'jumping': jumping, 'strength': strength,
        'stamina': stamina, 'work_rate': work_rate, 'aggression': aggression,
        'free_kicks': 60,
    }


def test_recent_public_tactical_habits_are_predictable_without_reading_last_second_setup():
    state = {}
    exposed = FootballTactics9394(formation='4-4-2', directness='mixed', width='normal')
    for day in range(1, 6):
        record_managed_tactical_usage(state, date_text=f'1993-10-{day:02d}', opponent_team_id=100 + day, tactics=exposed)
    predicted = expected_managed_tactics(state, fallback=FootballTactics9394(formation='4-3-3', width='wide'))
    assert predicted['sample_size'] == 5
    assert predicted['predictability'] >= 90
    assert predicted['tactics']['formation'] == '4-4-2'
    assert predicted['tactics']['width'] == 'normal'


def test_good_coach_can_prepare_multiple_explainable_counters_without_player_rating_bonus():
    own = [_player(i, overall=74, stamina=76, work_rate=78) for i in range(1, 17)]
    opponent = [
        _player(100+i, overall=82, pace=88, acceleration=90, off_ball=86,
                vision=84, short_pass=83, technique=85, crossing=79,
                dribbling=82, heading=78, jumping=80, strength=76)
        for i in range(16)
    ]
    base = FootballTactics9394(defensive_line='high', pressing='medium', marking='zonal')
    expected = FootballTactics9394(formation='4-3-3', directness='short', width='wide')
    strong = prepare_tactics_for_opponent(
        base, own_players=own, opponent_players=opponent,
        expected_opponent_tactics=expected,
        manager={'coaching_quality': 90}, observed_sample=5, observed_predictability=85,
    )
    weak = prepare_tactics_for_opponent(
        base, own_players=own, opponent_players=opponent,
        expected_opponent_tactics=expected,
        manager={'coaching_quality': 52}, observed_sample=5, observed_predictability=85,
    )
    assert len(strong['adjustments']) >= 2
    assert len(weak['adjustments']) == 1
    assert strong['tactics'].defensive_line != 'high'
    assert strong['threat_profile']['pace'] >= 74
    assert all(p['overall'] == 74 for p in own)  # preparation never edits ability


def test_live_match_exposes_rival_preparation_based_on_previous_matches_not_current_screen():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=1616, through_matchday=0)
    for day in range(1, 6):
        record_managed_tactical_usage(
            career.state, date_text=f'1993-07-{day:02d}', opponent_team_id=700+day,
            tactics=FootballTactics9394(formation='4-4-2', width='normal', pressing='medium'),
        )
    # Last-second surprise: the player changes to 4-3-3. Rival preparation must
    # still show the exposed 4-4-2 habit rather than omnisciently reading it.
    career.set_tactics({'formation': '4-3-3', 'width': 'wide', 'pressing': 'high'})
    fixture = career.next_scheduled_fixture()
    career.state['current_date'] = fixture['date']
    snap = career.start_live_match()
    prep = snap['opponent_context']['preparation']
    assert prep['observed_sample'] == 5
    assert prep['expected_opponent']['formation'] == '4-4-2'
    assert snap['home_tactics']['formation'] == '4-3-3'  # actual human setup remains the surprise
    assert prep['confidence'] >= 60


def test_rules_and_registration_environment_remain_frozen_after_1994():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=1617, through_matchday=0)
    assert career.state['rules_policy'] == RULES_POLICY_FROZEN_9394
    source_rule = career._domestic_foreign_rule()
    career.state['season'] = '2002-03'
    later_rule = career._domestic_foreign_rule()
    assert (source_rule.max_starting, source_rule.max_squad) == (later_rule.max_starting, later_rule.max_squad) == (3, 4)
    december = transfer_period_status(__import__('datetime').date(2002, 12, 20), country_id=11, season='2002-03')
    january = transfer_period_status(__import__('datetime').date(2003, 1, 10), country_id=11, season='2002-03')
    assert december.phase == 'in_season' and december.open
    assert january.phase == 'in_season' and january.open


def test_scouting_separates_league_habits_from_tournament_phase_habits():
    state = {}
    league_plan = FootballTactics9394(formation='4-4-2', directness='mixed', width='normal')
    cup_plan = FootballTactics9394(formation='4-3-3', directness='short', width='wide')
    for day in range(1, 7):
        record_managed_tactical_usage(
            state, date_text=f'1993-09-{day:02d}', opponent_team_id=100 + day, tactics=league_plan,
            competition_context={'fixture_type': 'league', 'competition_id': 1, 'competition_name': 'Primera División'},
        )
    for day in range(10, 16):
        record_managed_tactical_usage(
            state, date_text=f'1993-09-{day:02d}', opponent_team_id=200 + day, tactics=cup_plan,
            competition_context={'fixture_type': 'tournament', 'competition_id': 77, 'competition_name': 'Copa', 'group': 'A'},
        )
    league = expected_managed_tactics(
        state, fallback=FootballTactics9394(),
        context={'fixture_type': 'league', 'competition_id': 1, 'competition_name': 'Primera División'},
    )
    group = expected_managed_tactics(
        state, fallback=FootballTactics9394(),
        context={'fixture_type': 'tournament', 'competition_id': 77, 'competition_name': 'Copa', 'group': 'A'},
    )
    assert league['tactics']['formation'] == '4-4-2'
    assert group['tactics']['formation'] == '4-3-3'
    assert group['tactics']['width'] == 'wide'
    assert league['context']['phase'] == 'league'
    assert group['context']['phase'] == 'group'


def test_coach_carries_successful_head_to_head_solution_into_later_rematch():
    state = {}
    expected = FootballTactics9394(formation='4-4-2', directness='mixed', width='normal')
    record_rival_preparation_outcome(
        state, manager_id=501, team_id=8, date_text='1993-10-10', goals_for=2, goals_against=0,
        preparation={
            'expected_opponent': asdict(expected),
            'prepared_tactics': asdict(FootballTactics9394(defensive_line='low', pressing='medium')),
            'adjustments': ['Protegió la espalda'],
        },
        competition_context={'fixture_type': 'league', 'competition_id': 1},
    )
    learning = rival_learning_for_preparation(
        state, manager_id=501, team_id=99, expected_opponent_tactics=expected,
    )
    prepared = prepare_tactics_for_opponent(
        FootballTactics9394(defensive_line='high', pressing='medium'),
        own_players=[_player(i, overall=72, pace=60) for i in range(1, 17)],
        opponent_players=[_player(100+i, overall=72, pace=60) for i in range(16)],
        expected_opponent_tactics=expected, manager={'coaching_quality': 70},
        observed_sample=4, observed_predictability=75,
        match_context={'fixture_type': 'league', 'competition_id': 1}, learning=learning,
    )
    assert learning['games'] == 1
    assert learning['success_rate'] == 1.0
    assert prepared['tactics'].defensive_line == 'low'
    assert any('ya funcionó' in reason for reason in prepared['adjustments'])
    assert prepared['learning_note']


def test_final_preparation_has_distinct_phase_focus_and_higher_intensity():
    context = tactical_context_for_fixture({
        'fixture_type': 'tournament', 'competition_id': 55, 'competition_name': 'Copa de Europa', 'stage': 'Final',
    })
    prepared = prepare_tactics_for_opponent(
        FootballTactics9394(),
        own_players=[_player(i, overall=76) for i in range(1, 17)],
        opponent_players=[_player(100+i, overall=78) for i in range(16)],
        expected_opponent_tactics=FootballTactics9394(), manager={'coaching_quality': 82},
        observed_sample=5, observed_predictability=80, match_context=context,
    )
    assert prepared['context']['phase'] == 'final'
    assert prepared['preparation_intensity'] == 'alta'
    assert 'final' in prepared['phase_focus'].lower()
