from backend.app.football9394.competition_runtime import build_simple_source_league, source_league_runtime_info


def test_all_certified_simple_source_leagues_build_from_real_mdb_squads():
    expected = {
        1: (20, 38, 380),
        2: (20, 38, 380),
        5: (22, 42, 462),
        13: (18, 34, 306),
    }
    for source_id, fingerprint in expected.items():
        info = source_league_runtime_info(source_id)
        assert (info.team_count, info.rounds, info.matches) == fingerprint


def test_premier_and_bundesliga_complete_seasons_with_historical_points_math():
    for source_id, expected_matches in ((5, 462), (13, 306)):
        season = build_simple_source_league(source_id)
        season.play_all(seed_base=9394 + source_id)
        table = season.table()
        assert season.played_matches == expected_matches
        assert all(row.played == season.rules.rounds for row in table)
        assert sum(row.goals_for for row in table) == sum(row.goals_against for row in table)
        assert sum(row.points for row in table) == (
            sum(row.wins for row in table) * season.rules.points_win
            + sum(row.draws for row in table) * season.rules.points_draw
        )
