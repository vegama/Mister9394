from backend.app.football9394.italy_runtime import simulate_italy_1993_94
from backend.app.football9394.pyramid_activation import audit_competition_activation
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_rules import audit_snapshot_competitions


def test_italian_source_pyramid_runs_as_one_movement_system():
    season = simulate_italy_1993_94(seed_base=49394)
    assert season.serie_a_matches == 306
    assert season.serie_b_matches == 380
    assert len(season.relegated_from_serie_a) == 4
    assert len(season.promoted_from_serie_b) == 4
    assert len(season.relegated_from_serie_b) == 4
    assert all(row.played == 34 for row in season.serie_a_table)
    assert all(row.played == 38 for row in season.serie_b_table)


def test_italy_becomes_active_only_when_both_source_tiers_are_certified():
    universe = default_runtime_snapshot()
    rows = universe.competitions()
    rules = audit_snapshot_competitions(rows)
    activations, pyramids = audit_competition_activation(rows, rules)
    by_key = {(row.kind, row.source_id): row for row in activations}
    assert pyramids["Italia"].active is True
    assert by_key[("league", 4)].active is True
    assert by_key[("league", 102)].active is True
