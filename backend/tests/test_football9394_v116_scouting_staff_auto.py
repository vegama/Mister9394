from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _career(team_id: int, seed: int = 11601) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=team_id, league_id=1, seed=seed, through_matchday=0)


def _knowledge_levels(career: ManagerCareerRuntime9394, league_ids: set[int]) -> list[int]:
    levels: list[int] = []
    for row in career.universe.payload.get("players", []):
        pid = int(row["source_id"])
        team_id = career._current_team_id(pid)
        if not team_id or team_id == int(career.state["team_id"]):
            continue
        if career._current_league_for_team(team_id) in league_ids:
            levels.append(int(career._scouting_knowledge_for_player(pid).get("level") or 0))
    return levels


def test_v116_big_club_has_broader_network_but_celta_knows_own_league_and_pyramid():
    madrid = _career(5, 11611)  # Real Madrid CF
    celta = _career(19, 11611)  # RC Celta

    madrid_network = madrid.scouting_snapshot()["network"]
    celta_network = celta.scouting_snapshot()["network"]
    assert int(madrid_network["rating"]) > int(celta_network["rating"])
    assert int(madrid_network["known_players_estimate"]) > int(celta_network["known_players_estimate"])

    celta_primera = _knowledge_levels(celta, {1})
    celta_pyramid = _knowledge_levels(celta, {2, 3})
    assert celta_primera and min(celta_primera) >= 2
    assert celta_pyramid and min(celta_pyramid) >= 1


def test_v116_unknown_player_can_be_found_by_identity_but_not_inspected_or_dossiered():
    career = _career(19, 11612)
    unknown = next(
        row
        for row in career._all_player_rows()
        if career._current_team_id(int(row["source_id"])) != 19
        and int(career._scouting_knowledge_for_player(int(row["source_id"])).get("level") or 0) == 0
    )
    view = career.player_detail(int(unknown["source_id"]))
    query = str(unknown.get("display_name") or unknown.get("name") or "").strip()
    located = career.search_market(query, limit=20)
    assert any(int(row["id"]) == int(unknown["source_id"]) and row["overall"] is None for row in located)
    assert view["overall"] is None
    assert view["attributes"] == {}
    assert view["estimated_transfer_value"] is None
    with pytest.raises(ValueError, match="todavía no conoce"):
        career.start_scouting_player(int(unknown["source_id"]))


def test_v116_autonomous_scouting_discovers_and_builds_staff_portfolio_without_watchlist():
    career = _career(19, 11613)
    initial_watchlist = list(career.state.get("watchlist") or [])
    for _ in range(18):
        career.advance_day()

    snapshot = career.scouting_snapshot()
    assert int(snapshot["network"]["discoveries"]) > 0
    assert int(snapshot["portfolio_count"]) > 0
    assert list(career.state.get("watchlist") or []) == initial_watchlist
    for row in snapshot["portfolio"]:
        assert 0.0 <= float(row["fit_score"]) <= 10.0
        assert 0 <= int(row["confidence"]) <= 100
        assert row.get("reasons")


def test_v116_training_and_match_preparation_default_to_auto_but_manager_keeps_tactics_selection_xi():
    career = _career(19, 11614)
    initial = career.training_snapshot()
    assert initial["mode"] == "auto"
    assert initial["match_preparation_mode"] == "auto"

    tactics_before = deepcopy(career.state.get("tactics"))
    selection_before = deepcopy(career.state.get("selection"))
    for _ in range(3):
        career.advance_day()
    assert career.state.get("tactics") == tactics_before
    assert career.state.get("selection") == selection_before
    assert career.state["training"]["mode"] == "auto"
    assert career.state["training"].get("auto_decision")
    assert career.state["training"].get("individual_focus")
    assert set((career.state["training"].get("individual_focus_source") or {}).values()) <= {"auto", "manual"}


def test_v116_training_manual_override_and_return_to_auto():
    career = _career(19, 11615)
    manual = career.set_training_plan(intensity="high", weekly_plan=["physical"] * 7)
    assert manual["mode"] == "manual"
    assert career.state["training"]["intensity"] == "high"

    automatic = career.set_training_plan(mode="auto")
    assert automatic["mode"] == "auto"
    assert career.state["training"]["mode"] == "auto"



def test_v116_manual_dossier_does_not_silently_add_personal_watchlist():
    career = _career(19, 11617)
    target = next(row for row in career.search_market(limit=30) if int((row.get("scout") or {}).get("level") or 0) > 0)
    pid = int(target["id"])
    assert pid not in {int(x) for x in (career.state.get("watchlist") or [])}
    career.start_scouting_player(pid)
    assert pid not in {int(x) for x in (career.state.get("watchlist") or [])}


def test_v116_auto_match_plan_only_adds_staff_opposition_instructions():
    career = _career(19, 11616)
    tactics_before = deepcopy(career.state.get("tactics"))
    selection_before = deepcopy(career.state.get("selection"))
    snapshot = career.tactical_plan_snapshot()

    staff = snapshot["staff_match_plan"]
    assert staff["mode"] == "auto"
    assert staff.get("fixture_key")
    assert career.state.get("tactics") == tactics_before
    assert career.state.get("selection") == selection_before
    assert isinstance((career.state.get("tactical_plan") or {}).get("opposition_instructions"), dict)
