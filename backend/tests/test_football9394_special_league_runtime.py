from backend.app.football9394.special_league_runtime import simulate_apsl_1993, simulate_jleague_1993


def test_apsl_1993_executes_24_match_regular_season_and_four_team_playoff():
    season = simulate_apsl_1993(seed_base=1234)
    assert len(season.regular_table) == 7
    assert len(season.regular_matches) == 84
    assert all(row.played == 24 for row in season.regular_table)
    assert len(season.semifinal_winners) == 2
    assert season.champion_team_id != season.runner_up_team_id
    assert all(match.decided_by in {"regulation", "extra_time", "shootout"} for match in season.regular_matches)
    assert all(row.points is not None for row in season.regular_table)


def test_jleague_1993_executes_two_18_match_series_without_draws_and_championship():
    season = simulate_jleague_1993(seed_base=5678)
    assert len(season.suntory.matches) == 90
    assert len(season.nicos.matches) == 90
    assert all(row.played == 18 for row in season.suntory.table)
    assert all(row.played == 18 for row in season.nicos.table)
    assert all(row.wins + row.losses == 18 for row in season.suntory.table)
    assert all(row.wins + row.losses == 18 for row in season.nicos.table)
    assert season.champion_team_id != season.runner_up_team_id
    assert len(season.championship_teams) == 2
