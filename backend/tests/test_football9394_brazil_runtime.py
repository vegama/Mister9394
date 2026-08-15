from backend.app.football9394.brazil_runtime import BRAZIL_1993_GROUPS, simulate_brazil_serie_a_1993
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_brazil_1993_uses_historical_32_club_four_group_structure():
    assert set(BRAZIL_1993_GROUPS) == {"A", "B", "C", "D"}
    assert all(len(group) == 8 for group in BRAZIL_1993_GROUPS.values())
    assert len({team for group in BRAZIL_1993_GROUPS.values() for team in group}) == 32


def test_brazil_1993_completes_254_matches_and_eight_relegations():
    season = simulate_brazil_serie_a_1993(universe=default_runtime_snapshot(), seed_base=470001)
    assert season.simulated_matches == 254
    assert len(season.relegated_team_ids) == 8
    assert all(row.played == 14 for table in season.first_phase_tables.values() for row in table)
    assert all(row.played == 6 for table in season.second_phase_tables.values() for row in table)
    assert season.champion_team_id != season.runner_up_team_id


def test_brazil_source_repairs_are_explicit_not_hidden():
    season = simulate_brazil_serie_a_1993(universe=default_runtime_snapshot(), seed_base=470002)
    assert set(season.source_repair_club_ids) == {"hist:uniao-sao-joao", "hist:desportiva"}
    assert season.repaired_players >= 22
