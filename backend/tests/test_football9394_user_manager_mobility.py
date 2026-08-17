from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394, CAREER_SCHEMA_9394


def test_dismissal_opens_same_league_jobs_and_old_club_gets_real_ai_replacement():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    old_team = int(career.state["team_id"])
    old_assignment = (career.state.get("manager_assignments") or {}).get(str(old_team))
    career.state["job_status"] = "dismissed"
    events = career._handle_user_dismissal()
    profile = career.snapshot()["user_manager"]
    assert events and events[0]["kind"] == "manager_change"
    assert (career.state.get("manager_assignments") or {}).get(str(old_team)) != old_assignment
    assert 1 <= len(profile["job_offers"]) <= 3
    assert all(int(row["league_id"]) == 1 for row in profile["job_offers"])
    assert all(int(row["team_id"]) != old_team for row in profile["job_offers"])
    assert profile["tenures"][-1]["team_id"] == old_team
    assert profile["tenures"][-1]["reason"] == "dismissed"


def test_accepting_job_keeps_world_table_but_changes_controlled_club_and_selection():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=3)
    before_table = {row["team_id"]: (row["played"], row["points"]) for row in career.standings()}
    records_before = dict(career.snapshot()["career_records"])
    career.state["job_status"] = "dismissed"
    career._handle_user_dismissal()
    offer = career.snapshot()["user_manager"]["job_offers"][0]
    new_team = int(offer["team_id"])
    snap = career.accept_job_offer(offer["id"])
    after_table = {row["team_id"]: (row["played"], row["points"]) for row in career.standings()}
    assert snap["team"]["source_id"] == new_team
    assert snap["league_id"] == 1
    assert snap["job_status"] == "active"
    assert before_table == after_table
    assert snap["selection"]["valid"] is True
    assert len(snap["selection"]["starter_ids"]) == 11
    assert snap["career_records"] == records_before
    assert snap["user_manager"]["current_tenure"]["team_id"] == new_team
    assert snap["source_manager"] is not None  # predecessor shown as context, not as active user manager


def test_dismissed_career_waits_for_job_choice_instead_of_game_over():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    career.state["job_status"] = "dismissed"
    career._handle_user_dismissal()
    result = career.advance_day()
    assert result["advanced"] is False
    assert result["career_over"] is False
    assert result["requires_job_decision"] is True
    assert result["job_offers"]


def test_manager_reputation_moves_with_official_results_but_not_friendlies():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    before = career.snapshot()["user_manager"]["reputation"]
    career._publish_controlled_result(competition="Pretemporada", home_team_id=3, away_team_id=5, home_goals=4, away_goals=0)
    assert career.snapshot()["user_manager"]["reputation"] == before
    career._publish_controlled_result(competition="Liga", home_team_id=3, away_team_id=5, home_goals=2, away_goals=0)
    assert career.snapshot()["user_manager"]["reputation"] > before


def test_manager_can_build_a_multi_club_career_without_erasing_previous_tenures():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    career.state["job_status"] = "dismissed"
    career._handle_user_dismissal()
    first_offer = career.snapshot()["user_manager"]["job_offers"][0]
    career.accept_job_offer(first_offer["id"])
    first_new_team = int(career.state["team_id"])
    career.state["job_status"] = "dismissed"
    career._handle_user_dismissal()
    second_offers = career.snapshot()["user_manager"]["job_offers"]
    assert second_offers and all(int(row["team_id"]) != first_new_team for row in second_offers)
    second_offer = second_offers[0]
    career.accept_job_offer(second_offer["id"])
    profile = career.snapshot()["user_manager"]
    assert len(profile["tenures"]) == 2
    assert profile["tenures"][0]["team_id"] == 3
    assert profile["tenures"][1]["team_id"] == first_new_team
    assert profile["current_tenure"]["team_id"] == second_offer["team_id"]


def test_schema_10_save_migrates_into_persistent_manager_career_state():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    state = dict(career.state)
    state["schema"] = 10
    state.pop("user_manager", None)
    restored = ManagerCareerRuntime9394(state)
    snap = restored.snapshot()
    assert restored.state["schema"] == CAREER_SCHEMA_9394
    assert snap["user_manager"]["current_tenure"]["team_id"] == 3
    assert snap["user_manager"]["reputation"] == 50.0


def test_old_terminal_dismissed_save_is_migrated_to_job_decision_on_load():
    base = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    state = dict(base.state)
    state["schema"] = 10
    state["job_status"] = "dismissed"
    state.pop("user_manager", None)
    state.pop("user_dismissal_handled", None)
    restored = ManagerCareerRuntime9394(state)
    snap = restored.snapshot()
    assert snap["job_status"] == "dismissed"
    assert snap["user_manager"]["job_offers"]
    waiting = restored.advance_day()
    assert waiting["requires_job_decision"] is True
    assert waiting["career_over"] is False
