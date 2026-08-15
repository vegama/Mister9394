from backend.app.football9394.spain_runtime import simulate_spain_1993_94
from backend.app.football9394.spain_segundab_runtime import (
    _higher_family_member_in_division,
)


def test_full_spanish_pyramid_closes_primera_segunda_and_segunda_b():
    season = simulate_spain_1993_94(seed_base=119394)
    assert season.primera_matches == 380
    assert season.segunda_matches == 380
    assert len(season.primera_table) == 20
    assert len(season.segunda_table) == 20
    assert len(season.promotion_ties) == 2
    assert 4 <= season.primera_segunda_playoff_matches <= 6
    assert len(season.promoted_to_primera) == len(season.relegated_to_segunda)
    assert 2 <= len(season.promoted_to_primera) <= 4
    assert len(season.promoted_to_segunda) == 4
    assert len(season.relegated_to_segundab) == 4
    assert season.segundab.promotion_matches == 48
    assert len(season.segundab.permanence_matches) == 3


def test_1993_94_primera_segunda_promotion_has_no_away_goals_shortcut():
    season = simulate_spain_1993_94(seed_base=119394)
    # Any aggregate draw must reach the historical extra tiebreak match instead
    # of being decided by the away goal scored in one of the two legs.
    for tie in season.promotion_ties:
        if tie.aggregate[0] == tie.aggregate[1]:
            assert tie.matches == 3
            assert tie.resolved_by.startswith('tiebreak_')
        else:
            assert tie.matches == 2
            assert tie.resolved_by == 'aggregate'


def test_reserve_family_hierarchy_catches_b_to_c_cascade():
    meta = {
        '5': {'source_id': 5, 'reserve_of': None, 'reserve_step': 0},
        '26': {'source_id': 26, 'reserve_of': 5, 'reserve_step': 2},
        '2293': {'source_id': 2293, 'reserve_of': 5, 'reserve_step': 3},
    }
    assert _higher_family_member_in_division('26', meta, {'5'}) is True
    assert _higher_family_member_in_division('2293', meta, {'26'}) is True
    assert _higher_family_member_in_division('2293', meta, {'5'}) is True
    assert _higher_family_member_in_division('26', meta, {'2293'}) is False
