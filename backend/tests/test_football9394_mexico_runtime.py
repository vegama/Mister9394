from backend.app.football9394.mexico_runtime import (
    MEXICO_GROUPS_1993_94,
    mexico_relegation_coefficients,
    simulate_mexico_1993_94,
)
from backend.app.football9394.rules import MEXICO_PRIMERA_1993_94
from backend.app.football9394.standings import StandingRow9394


def _historical_table_points():
    points = {
        2341: 51, 929: 48, 928: 46, 394: 45, 1584: 43, 1580: 43,
        1020: 42, 833: 40, 1586: 39, 1583: 39, 927: 38, 1438: 38,
        775: 36, 1579: 34, 1581: 34, 2342: 31, 832: 30, 1585: 29,
        2343: 27, 1490: 27,
    }
    return tuple(
        StandingRow9394(str(team_id), 38, 0, 0, 0, 0, 0, pts, position=index)
        for index, (team_id, pts) in enumerate(points.items(), 1)
    )


def test_mexico_rules_are_1993_94_and_not_modern():
    assert MEXICO_PRIMERA_1993_94.points_win == 2
    assert MEXICO_PRIMERA_1993_94.teams == 20
    assert MEXICO_PRIMERA_1993_94.rounds == 38
    assert MEXICO_PRIMERA_1993_94.country == "México"


def test_mexico_historical_quotient_relegates_queretaro():
    coefficients = mexico_relegation_coefficients(_historical_table_points())
    assert coefficients[-1].team_id == "1490"
    assert round(coefficients[-1].coefficient, 4) == 0.7456


def test_mexico_runtime_closes_groups_liguilla_and_relegation():
    season = simulate_mexico_1993_94(seed_base=409394)
    assert season.regular_matches == 380
    assert len(season.regular_table) == 20
    assert all(row.played == 38 for row in season.regular_table)
    assert len(season.group_tables) == 4
    assert all(len(group) == 5 for group in season.group_tables)
    assert {int(row.team_id) for group in season.group_tables for row in group} == {
        team_id for group in MEXICO_GROUPS_1993_94 for team_id in group
    }
    assert 0 <= len(season.reclassification_ties) <= 2
    assert len(season.quarterfinal_ties) == 4
    assert len(season.semifinal_ties) == 2
    assert season.final_tie.winner_team_id == season.champion_team_id
    assert season.postseason_matches == 14 + 2 * len(season.reclassification_ties)
    assert len(season.relegation_coefficients) == 20
    assert season.relegated_team_id == season.relegation_coefficients[-1].team_id
