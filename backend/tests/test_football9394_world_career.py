from __future__ import annotations

from backend.app.football9394.world_career import WorldCareerStore9394, simulate_world_season_1993_94


def test_world_season_runs_every_admitted_competition_and_builds_rollover_projection(tmp_path):
    payload = simulate_world_season_1993_94(seed=51)
    assert payload["status"] == "complete"
    assert payload["competition_count"] == 30
    assert payload["all_competitions_complete"] is True
    assert len(payload["honours"]) >= 20
    assert len(payload["movement"]["resolved_links"]) == 8

    projection = payload["rollover"]["participant_projection"]
    assert set(("league:1", "league:2", "league:4", "league:31", "league:54")) <= set(projection["ready_source_keys"])
    assert projection["competition_pools"]["league:1"]["actual"] == 20
    assert projection["competition_pools"]["league:2"]["actual"] == 20
    assert projection["competition_pools"]["league:4"]["actual"] == 18
    assert projection["competition_pools"]["league:31"]["actual"] == 18
    assert projection["competition_pools"]["league:54"]["actual"] == 18
    # The lowest represented division is a closed floor: no external feeder
    # is invented, but the represented pyramid can still roll forward.
    assert projection["competition_pools"]["league:102"]["ready"] is True
    assert projection["competition_pools"]["league:102"]["pyramid_floor"] is True
    assert projection["competition_pools"]["league:3"]["ready"] is True
    assert projection["competition_pools"]["league:3"]["sporting_relegation"] is False
    assert projection["blocked_source_keys"] == []
    assert projection["admitted_league_count"] == 22
    assert projection["projected_league_count"] == 22
    assert projection["all_admitted_leagues_ready"] is True
    assert projection["competition_pools"]["league:47"]["actual"] == 32
    assert payload["movement"]["unresolved_links"] == []
    assert payload["rollover"]["domestic_ready"] is True
    assert payload["rollover"]["ready"] is False  # continental 1994-95 seeding still incomplete
    assert payload["continental_qualification"]["complete"] is False

    store = WorldCareerStore9394(tmp_path)
    path = store.save(payload)
    restored = store.load(payload["career_id"])
    assert path.exists()
    assert restored["career_id"] == payload["career_id"]
    assert restored["competition_count"] == 30


def test_store_rejects_empty_career_id(tmp_path):
    store = WorldCareerStore9394(tmp_path)
    try:
        store.path_for("../")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe/empty career ids must be rejected")
