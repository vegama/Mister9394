from __future__ import annotations

from backend.app.football9394.pyramid_floor import active_pyramid_floors, is_floor_league
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.world_competitions import simulate_runtime_competitions


def test_lowest_admitted_level_is_closed_floor_per_country():
    universe = default_runtime_snapshot()
    rows = universe.competitions()
    floors = active_pyramid_floors(rows)
    assert floors["España"].lowest_level == 3
    assert set(floors["España"].league_source_ids) == {3, 9, 10, 11}
    assert floors["Italia"].league_source_ids == (102,)
    assert floors["Países Bajos"].league_source_ids == (54,)
    assert floors["Brasil"].league_source_ids == (47,)
    assert floors["Inglaterra"].league_source_ids == (5,)

    by_id = {int(r["source_id"]): r for r in rows if r["kind"] == "league"}
    assert is_floor_league(by_id[3], floors)
    assert not is_floor_league(by_id[2], floors)
    assert is_floor_league(by_id[47], floors)


def test_world_runtime_suppresses_sporting_relegation_at_represented_floor():
    payload = simulate_runtime_competitions(seed_offset=77)
    rows = {r["source_key"]: r for r in payload["competitions"]}

    for key in ("league:3", "league:9", "league:10", "league:11", "league:102", "league:54", "league:47", "league:5"):
        assert rows[key]["pyramid_floor"] is True
        assert rows[key]["relegation_enabled"] is False

    assert rows["league:47"]["relegated_team_ids"] == ()
    assert len(rows["league:47"]["historical_relegation_candidates"]) == 8
    assert rows["league:102"]["relegated_team_ids"] == ()
    assert len(rows["league:102"]["historical_relegation_candidates"]) == 4
    assert rows["league:5"]["relegated_team_ids"] == ()

    # Divisions with a represented level below them retain normal movement.
    assert rows["league:1"]["relegation_enabled"] is True
    assert len(rows["league:1"]["relegated_team_ids"]) > 0
    assert rows["league:31"]["relegation_enabled"] is True
    assert len(rows["league:31"]["relegated_team_ids"]) > 0

    # Segunda-B permanence can be simulated internally for historical QA, but
    # it no longer ejects clubs into an absent Tercera in career mode.
    assert rows["tournament:88"]["relegated_to_tercera"] == ()
    assert rows["tournament:88"]["survival_matches"] == 0
