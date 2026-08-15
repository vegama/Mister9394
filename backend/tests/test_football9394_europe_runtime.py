from backend.app.football9394.europe_runtime import (
    simulate_champions_league_1993_94,
    simulate_cup_winners_cup_1993_94,
    simulate_uefa_cup_1993_94,
)


def test_champions_league_source_stage_completes():
    season = simulate_champions_league_1993_94(seed_base=101)
    assert len(season.start_stage_team_ids) == 8
    assert len(season.group_tables) == 2
    assert all(len(group) == 4 and all(row.played == 6 for row in group) for group in season.group_tables)
    assert len(season.knockout_ties) == 3
    assert season.simulated_matches == 27
    assert season.champion_team_id != season.runner_up_team_id


def test_uefa_cup_source_stage_completes():
    season = simulate_uefa_cup_1993_94(seed_base=202)
    assert len(season.start_stage_team_ids) == 16
    assert len(season.knockout_ties) == 15
    assert season.simulated_matches == 30
    assert season.champion_team_id != season.runner_up_team_id


def test_cup_winners_cup_source_stage_completes():
    season = simulate_cup_winners_cup_1993_94(seed_base=303)
    assert len(season.start_stage_team_ids) == 32
    assert len(season.knockout_ties) == 31
    assert season.simulated_matches == 61
    assert season.champion_team_id != season.runner_up_team_id
