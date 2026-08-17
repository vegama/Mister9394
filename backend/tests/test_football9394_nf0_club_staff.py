from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.football9394.club_staff import (
    RESPONSIBILITIES,
    assign_responsibility,
    club_staff_snapshot,
    ensure_club_staff_state,
)
from backend.app.football9394.manager_career import CAREER_SCHEMA_9394, ManagerCareerRuntime9394
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def _team(team_id: int = 16):
    universe = default_runtime_snapshot()
    team = universe.team(team_id)
    assert team is not None
    return universe, team


def test_nf0_staff_generation_is_deterministic_and_marked_generated():
    _, team = _team()
    state_a = {"seed": 9394}
    state_b = {"seed": 9394}
    a = ensure_club_staff_state(state_a, team=team, strength=72.0)
    b = ensure_club_staff_state(state_b, team=team, strength=72.0)
    assert a["members"] == b["members"]
    assert len(a["members"]) >= 4
    assert all(member["provenance"] == "generated_career_staff" for member in a["members"])
    assert all(member["generated"] is True for member in a["members"])
    assert set(a["responsibilities"]) == set(RESPONSIBILITIES)


def test_nf0_responsibility_assignment_validates_role_and_persists():
    _, team = _team()
    state = {"seed": 9394}
    first = club_staff_snapshot(state, team=team, strength=72.0)
    training = next(row for row in first["responsibilities"] if row["key"] == "first_team_training")
    coach = next(candidate for candidate in training["eligible_assignees"] if candidate["id"] != "manager")
    changed = assign_responsibility(
        state,
        team=team,
        strength=72.0,
        responsibility_key="first_team_training",
        assignee=coach["id"],
    )
    row = next(row for row in changed["responsibilities"] if row["key"] == "first_team_training")
    assert row["assignee"] == coach["id"]
    assert row["quality"] is not None
    assert state["club_staff"][str(team["source_id"])]["responsibilities"]["first_team_training"] == coach["id"]

    physio = next(member for member in changed["members"] if member["role"] == "physio")
    with pytest.raises(ValueError):
        assign_responsibility(
            state,
            team=team,
            strength=72.0,
            responsibility_key="transfer_negotiation",
            assignee=physio["id"],
        )


def test_nf0_manager_can_take_back_any_responsibility():
    _, team = _team()
    state = {"seed": 1234}
    result = assign_responsibility(
        state,
        team=team,
        strength=68.0,
        responsibility_key="medical_assessment",
        assignee="manager",
    )
    row = next(row for row in result["responsibilities"] if row["key"] == "medical_assessment")
    assert row["assignee"] == "manager"
    assert row["quality"] is None
    assert row["quality_label"] == "Decisión directa"


def test_nf0_runtime_snapshot_migrates_old_save_and_exposes_staff():
    universe, _ = _team()
    runtime = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=9394, through_matchday=0, universe=universe)
    old = deepcopy(runtime.state)
    old.pop("club_staff", None)
    old["schema"] = CAREER_SCHEMA_9394 - 1
    migrated = ManagerCareerRuntime9394(old, universe=universe)
    snapshot = migrated.snapshot()
    assert snapshot["staff"]["team_id"] == 16
    assert snapshot["staff"]["members"]
    assert migrated.state["schema"] == CAREER_SCHEMA_9394


def test_nf0_staff_is_stored_per_club_not_globally():
    universe, team = _team(16)
    other = next(t for t in universe.teams(league_id=1) if int(t["source_id"]) != 16)
    state = {"seed": 9394}
    ensure_club_staff_state(state, team=team, strength=72.0)
    ensure_club_staff_state(state, team=other, strength=72.0)
    assert str(team["source_id"]) in state["club_staff"]
    assert str(other["source_id"]) in state["club_staff"]
    first_names = {m["name"] for m in state["club_staff"][str(team["source_id"])]["members"]}
    second_names = {m["name"] for m in state["club_staff"][str(other["source_id"])]["members"]}
    assert first_names != second_names
