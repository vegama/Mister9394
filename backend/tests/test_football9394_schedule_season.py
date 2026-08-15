from backend.app.football9394 import (
    FootballMatchEngine9394,
    LeagueSeason9394,
    SPAIN_PRIMERA_1993_94,
    SPAIN_PRIMERA_SIMULATION_1993_94,
    generate_double_round_robin,
)
from backend.tests.test_football9394_match_engine import sheet


def test_twenty_team_double_round_robin_has_38_rounds_and_380_matches():
    teams = tuple(f"t{i:02d}" for i in range(20))
    fixtures = generate_double_round_robin(teams)
    assert len(fixtures) == 380
    assert max(f.round_number for f in fixtures) == 38
    for round_number in range(1, 39):
        round_fixtures = [f for f in fixtures if f.round_number == round_number]
        assert len(round_fixtures) == 10
        involved = [team for f in round_fixtures for team in (f.home_team_id, f.away_team_id)]
        assert len(involved) == len(set(involved)) == 20


def test_every_ordered_pair_occurs_once_home_and_away():
    teams = ("a", "b", "c", "d")
    fixtures = generate_double_round_robin(teams)
    pairs = {(f.home_team_id, f.away_team_id) for f in fixtures}
    assert len(pairs) == 12
    assert all((a, b) in pairs for a in teams for b in teams if a != b)


def test_full_spanish_top_flight_season_reaches_380_matches_and_historical_points_math():
    sheets = {f"t{i:02d}": sheet(f"t{i:02d}", 65 + (i % 8)) for i in range(20)}
    season = LeagueSeason9394(
        SPAIN_PRIMERA_1993_94,
        sheets,
        FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94),
    )
    season.play_all(seed_base=9394)
    table = season.table()
    assert season.played_matches == season.total_matches == 380
    assert len(table) == 20
    assert all(row.played == 38 for row in table)
    assert sum(row.wins for row in table) * 2 + sum(row.draws for row in table) == sum(row.points for row in table)
    assert sum(row.goals_for for row in table) == sum(row.goals_against for row in table)


def test_scotland_1993_94_four_cycle_schedule_has_44_rounds_and_264_matches():
    from backend.app.football9394 import generate_round_robin_cycles
    teams = tuple(f"s{i:02d}" for i in range(12))
    fixtures = generate_round_robin_cycles(teams, 4)
    assert len(fixtures) == 264
    assert max(f.round_number for f in fixtures) == 44
    for team in teams:
        games = [f for f in fixtures if team in (f.home_team_id, f.away_team_id)]
        assert len(games) == 44
        for opponent in teams:
            if opponent == team:
                continue
            pair = [f for f in games if opponent in (f.home_team_id, f.away_team_id)]
            assert len(pair) == 4
            assert sum(f.home_team_id == team for f in pair) == 2
            assert sum(f.away_team_id == team for f in pair) == 2


def test_scotland_rule_can_run_four_complete_cycles():
    from backend.app.football9394 import SCOTLAND_PREMIER_1993_94
    sheets = {f"s{i:02d}": sheet(f"s{i:02d}", 64 + (i % 8)) for i in range(12)}
    season = LeagueSeason9394(
        SCOTLAND_PREMIER_1993_94,
        sheets,
        FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94),
    )
    season.play_all(seed_base=3809394)
    assert season.played_matches == season.total_matches == 264
    assert max(f.round_number for f in season.fixtures) == 44
    assert all(row.played == 44 for row in season.table())
