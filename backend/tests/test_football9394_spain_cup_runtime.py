from backend.app.football9394.spain_cup_runtime import simulate_copa_del_rey_1993_94


def test_copa_del_rey_uses_every_available_non_reserve_spanish_club():
    season = simulate_copa_del_rey_1993_94(seed_base=404)
    assert season.source_eligible_clubs == 105
    assert season.historical_expected_clubs == 160
    assert season.missing_lower_tier_slots == 55
    assert season.round_sizes[-5:] == (
        ("Dieciseisavos", 32, 16),
        ("Octavos", 16, 8),
        ("Cuartos", 8, 4),
        ("Semifinales", 4, 2),
        ("Final", 2, 1),
    )
    assert season.champion_team_id != season.runner_up_team_id
    assert season.simulated_matches > 0
