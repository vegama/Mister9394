from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def test_live_match_exposes_opponent_coach_key_players_referee_and_venue():
    career = ManagerCareerRuntime9394.create(team_id=16, seed=9394, through_matchday=7)
    step = career.advance_day()
    assert step["requires_match"] is True
    live = career.start_live_match()

    opponent = live["opponent_context"]
    assert opponent["team_id"] in {live["home_team_id"], live["away_team_id"]}
    assert opponent["team_id"] != live["controlled_team_id"]
    assert opponent["team_name"]
    assert opponent["manager"] and opponent["manager"]["display_name"]
    assert opponent["tactics"].get("formation")
    assert len(opponent["key_players"]) == 3
    assert all(row["display_name"] and row["overall"] > 0 for row in opponent["key_players"])

    assert live["referee"] and live["referee"]["name"]
    assert live["venue"] and live["venue"]["name"]
    assert len(live["controlled_on_pitch"]) == 11
    assert len(live["opponent_on_pitch"]) == 11
    assert all(row["id"] and row["display_name"] and row["position"] for row in live["opponent_on_pitch"])
