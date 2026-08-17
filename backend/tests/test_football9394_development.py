from backend.app.football9394.development import (
    apply_match_development, initial_player_development, recover_one_day, season_rollover,
)


def test_match_development_changes_ability_without_doing_calendar_ageing():
    state = initial_player_development([{"source_id": 1, "overall": 70}])
    for i in range(20):
        apply_match_development(state, player_ids=["1"], won=True, drew=False, goal_ids=["1"], seed=100+i)
    assert state["1"]["overall"] > 70
    assert state["1"]["frozen_age"] is False
    before = state["1"]["overall"]
    season_rollover(state)
    assert state["1"]["overall"] == before
    assert state["1"]["frozen_age"] is False


def test_injuries_can_push_development_down_and_recovery_is_daily():
    state = initial_player_development([{"source_id": 1, "overall": 70}])
    for i in range(8):
        apply_match_development(state, player_ids=["1"], won=False, drew=False, injury_ids=["1"], seed=50+i)
    assert state["1"]["overall"] < 70
    injury = state["1"]["injury_days"]
    recover_one_day(state)
    assert state["1"]["injury_days"] == injury - 1


def test_sustained_bad_form_can_reduce_ability_before_season_ageing():
    state = initial_player_development([{"source_id": 9, "overall": 72}])
    for i in range(13):
        apply_match_development(state, player_ids=["9"], won=False, drew=False, seed=900+i)
    assert state["9"]["overall"] == 71
    assert state["9"]["frozen_age"] is False
