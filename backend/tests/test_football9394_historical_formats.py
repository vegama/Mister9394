from backend.app.football9394.historical_formats import (
    APSL_1993_FORMAT, BRAZIL_SERIE_A_1993_FORMAT, JLEAGUE_1993_FORMAT, MEXICO_1993_94_FORMAT,
)
from backend.app.football9394.scoring import APSL_1993, JLEAGUE_1993


def test_apsl_scoring_keeps_goal_bonus_and_shootout_points():
    assert APSL_1993.points_for('regulation_win', goals_scored=4) == 9
    assert APSL_1993.points_for('shootout_win', goals_scored=2) == 6
    assert APSL_1993.points_for('shootout_loss', goals_scored=1) == 3


def test_jleague_1993_ranks_by_wins_and_disallows_draws():
    assert JLEAGUE_1993.ranking_basis == 'wins'
    assert JLEAGUE_1993.draws_allowed is False
    assert JLEAGUE_1993.extra_time_on_draw is True
    assert JLEAGUE_1993.shootout_after_extra_time is True


def test_complex_historical_formats_validate():
    for spec in (APSL_1993_FORMAT, JLEAGUE_1993_FORMAT, BRAZIL_SERIE_A_1993_FORMAT, MEXICO_1993_94_FORMAT):
        spec.validate()


def test_brazil_1993_has_branch_merge_before_second_phase():
    incoming = [t for t in BRAZIL_SERIE_A_1993_FORMAT.transitions if t.target == 'second_phase']
    assert sum(t.slots for t in incoming) == 8
    assert {t.source for t in incoming} == {'groups_ab', 'intermediate'}
