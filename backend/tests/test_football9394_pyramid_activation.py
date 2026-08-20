from backend.app.football9394.pyramid_activation import audit_competition_activation
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_rules import audit_snapshot_competitions


def _activation():
    universe = default_runtime_snapshot()
    rows = universe.competitions()
    rules = audit_snapshot_competitions(rows)
    activations, pyramids = audit_competition_activation(rows, rules)
    return {(row.kind, row.source_id): row for row in activations}, pyramids


def test_admitted_standalone_top_flights_are_present_even_without_pyramid():
    activations, pyramids = _activation()
    assert pyramids["Francia"].has_pyramid is False
    for source_id in (14, 5, 13, 32, 38, 49, 120, 111, 40, 16):
        assert activations[("league", source_id)].active is True


def test_complete_ready_source_pyramids_keep_their_movement_graphs():
    activations, pyramids = _activation()
    assert pyramids["Países Bajos"].active is True
    assert activations[("league", 31)].active is True
    assert activations[("league", 54)].active is True

    assert pyramids["España"].active is True
    for source_id in (1, 2, 3, 9, 10, 11):
        assert activations[("league", source_id)].active is True
    assert activations[("tournament", 88)].active is True


def test_mdb_admitted_flag_is_authoritative_for_playable_leagues():
    activations, pyramids = _activation()
    assert activations[("league", 47)].active is True  # Série A is admitted, although runtime is still being completed.
    assert activations[("league", 105)].active is False
    assert activations[("league", 105)].reason == "source_not_admitted"
    assert activations[("league", 128)].active is False
    assert activations[("league", 128)].reason == "source_not_admitted"
    assert pyramids["Brasil"].has_pyramid is True  # source inventory still sees both rows


def test_admitted_continental_tournaments_are_in_career_catalogue():
    activations, _ = _activation()
    for source_id in (1, 2, 90):
        row = activations[("tournament", source_id)]
        assert row.active is True
        assert row.simulation_ready is True


def test_spanish_cup_and_segunda_b_promotion_are_admitted():
    activations, _ = _activation()
    for source_id in (3, 88):
        row = activations[("tournament", source_id)]
        assert row.active is True
        assert row.simulation_ready is True


def test_every_historical_source_row_has_admission_status():
    activations, _ = _activation()
    # Sube con las seis ligas del 93-94 incorporadas.
    assert len(activations) == 38
    # Seis competiciones mas: las ligas del 93-94 incorporadas.
    assert sum(row.active for row in activations.values()) == 36
    assert sum(row.reason == "source_not_admitted" for row in activations.values()) == 2


def test_belgium_historical_runtime_is_simulation_ready():
    activations, pyramids = _activation()
    row = activations[("league", 930052)]
    assert row.active is True
    assert row.simulation_ready is True
    assert row.reason == "included_simulation_ready_standalone"
    assert pyramids["Bélgica"].has_pyramid is False
