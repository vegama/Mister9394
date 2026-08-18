from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _career(seed: int = 13001) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, seed=seed, through_matchday=7)


def test_v100_staff_delegation_explains_owner_effect_and_destination():
    career = _career()
    staff = career.staff_snapshot()
    rows = {row["key"]: row for row in staff["responsibilities"]}

    for key in ("first_team_training", "recruitment_search", "transfer_negotiation", "medical_assessment"):
        row = rows[key]
        assert row["mode"] in {"direct", "delegated"}
        assert row["mode_label"] in {"Control directo", "Delegado"}
        assert row["workspace"] in {"training", "market", "squad", "tactics", "home"}
        assert len(row["effect"]) > 20

    career.set_staff_responsibility("first_team_training", "manager")
    direct = career.training_snapshot()
    assert direct["responsibility_mode"] == "direct"
    assert direct["responsibility"]["assignee"] == "manager"
    assert "controlas directamente" in direct["responsibility_note"].lower()

    training_row = next(row for row in career.staff_snapshot()["responsibilities"] if row["key"] == "first_team_training")
    delegated_candidate = next(candidate for candidate in training_row["eligible_assignees"] if candidate["id"] != "manager")
    career.set_staff_responsibility("first_team_training", delegated_candidate["id"])
    delegated = career.training_snapshot()
    assert delegated["responsibility_mode"] == "delegated"
    assert delegated["responsibility"]["assignee"] == delegated_candidate["id"]
    assert "tus cambios aquí son instrucciones" in delegated["responsibility_note"].lower()


def test_v100_market_workflow_exposes_owner_waiting_and_required_decisions():
    career = _career(13002)
    initial = career.market_snapshot()
    steps = {row["key"]: row for row in initial["workflow"]["steps"]}
    assert list(steps) == ["need", "search", "scout", "inquiry", "deal"]
    assert initial["workflow"]["recruitment_owner"]["assignee_name"]
    assert initial["workflow"]["negotiation_owner"]["assignee_name"]

    target = career.search_market(limit=1)[0]
    player_id = int(target["id"])
    career.toggle_watchlist(player_id, True)
    career.start_scouting_player(player_id)
    inquiry = career.inquire_player_availability(player_id)
    negotiation = career.open_transfer_negotiation(
        player_id,
        fee_offer=0,
        salary_offer=0,
        contract_years=3,
        squad_role="rotation",
    )

    flow = career.market_snapshot()["workflow"]
    by_key = {row["key"]: row for row in flow["steps"]}
    assert by_key["search"]["count"] >= 1
    assert by_key["scout"]["count"] >= 1
    assert by_key["inquiry"]["count"] >= 1
    assert by_key["deal"]["count"] >= 1
    assert by_key["deal"]["state"] == "waiting"
    assert flow["waiting_count"] >= 2
    assert inquiry["handled_by"] == flow["negotiation_owner"]["assignee_name"]
    assert negotiation["handled_by"] == flow["negotiation_owner"]["assignee_name"]

    # A counter-offer is a user decision, not merely "activity".
    row = career.state["transfer_negotiations"][negotiation["id"]]
    row["status"] = "countered"
    row["counter_fee"] = 1
    row["counter_salary"] = 1
    countered = career.market_snapshot()["workflow"]
    assert countered["action_required"] >= 1
    assert next(step for step in countered["steps"] if step["key"] == "deal")["state"] == "attention"
