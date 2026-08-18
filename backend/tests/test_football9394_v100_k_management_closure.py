from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


ROOT = Path(__file__).resolve().parents[2]


def _career(seed: int = 14001) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=seed, through_matchday=7)


def _external_target(career: ManagerCareerRuntime9394) -> dict:
    return next(row for row in career.search_market(limit=80) if career._current_team_id(int(row["id"])) != int(career.state["team_id"]))


def _different_assignee(career: ManagerCareerRuntime9394, key: str) -> dict:
    row = next(item for item in career.staff_snapshot()["responsibilities"] if item["key"] == key)
    return next(candidate for candidate in row["eligible_assignees"] if str(candidate["id"]) != str(row["assignee"]))


def test_k_market_pipeline_exposes_journey_budget_process_and_cost_context():
    career = _career()
    target = _external_target(career)
    pid = int(target["id"])

    career.toggle_watchlist(pid, True)
    scout = career.start_scouting_player(pid)
    inquiry = career.inquire_player_availability(pid)
    deal = career.open_transfer_negotiation(pid, fee_offer=0, salary_offer=0, contract_years=3, squad_role="rotation")

    snapshot = career.market_snapshot()
    assert snapshot["workflow"]["journey"] == [
        "Necesidad", "Búsqueda", "Seguimiento", "Informe", "Consulta", "Negociación", "Decisión", "Consecuencia"
    ]
    assert snapshot["workflow"]["window_policy"]["can_search"] is True
    assert snapshot["workflow"]["window_policy"]["can_scout"] is True
    assert snapshot["workflow"]["window_policy"]["can_inquire"] is True
    assert snapshot["budget_context"]["transfer_room"] >= snapshot["budget_context"]["transfer_room_if_all_open_accepted"]
    assert snapshot["budget_context"]["wage_headroom"] >= snapshot["budget_context"]["wage_headroom_if_all_open_accepted"]

    process_ids = {str(row["id"]) for row in snapshot["processes"]}
    assert str(scout["id"]) in process_ids
    assert str(inquiry["id"]) in process_ids
    assert str(deal["id"]) in process_ids
    negotiation = next(row for row in snapshot["processes"] if str(row["id"]) == str(deal["id"]))
    assert negotiation["owner"]
    assert negotiation["next_step"]
    assert "plantilla" in negotiation["consequence"].casefold()


def test_k_transfer_handler_handoff_preserves_negotiation_identity_and_history():
    career = _career(14002)
    target = _external_target(career)
    deal = career.open_transfer_negotiation(int(target["id"]), fee_offer=0, salary_offer=0, contract_years=3)
    deal_id = str(deal["id"])
    row = career.state["transfer_negotiations"][deal_id]
    row["status"] = "countered"
    row["counter_fee"] = max(1, int(row.get("fee_offer") or 0) + 1)
    row["counter_salary"] = max(1, int(row.get("salary_offer") or 0) + 1)
    original_response = row["response_date"]

    replacement = _different_assignee(career, "transfer_negotiation")
    staff = career.set_staff_responsibility("transfer_negotiation", str(replacement["id"]))

    preserved = career.state["transfer_negotiations"][deal_id]
    assert preserved["id"] == deal_id
    assert preserved["response_date"] == original_response
    assert preserved["status"] == "countered"
    assert preserved["handled_by"] == replacement["name"]
    assert any(item.get("kind") == "handler_changed" for item in preserved.get("history") or [])
    handoff = staff["recent_handoffs"][0]
    assert handoff["responsibility"] == "transfer_negotiation"
    assert handoff["affected_count"] >= 1
    flow_row = next(item for item in career.market_snapshot()["processes"] if str(item["id"]) == deal_id)
    assert flow_row["owner"] == replacement["name"]
    assert flow_row["requires_action"] is True


def test_k_scouting_handoff_moves_live_assignment_without_resetting_work():
    career = _career(14003)
    target = _external_target(career)
    task = career.start_scouting_player(int(target["id"]))
    task_id = str(task["id"])
    original_due = task["due_on"]

    replacement = _different_assignee(career, "recruitment_search")
    staff = career.set_staff_responsibility("recruitment_search", str(replacement["id"]))

    preserved = career.state["scouting_assignments"][task_id]
    assert preserved["id"] == task_id
    assert preserved["due_on"] == original_due
    assert preserved["status"] == "active"
    assert preserved["responsible"] == replacement["name"]
    assert preserved.get("handoffs")
    assert preserved["handoffs"][-1]["to"] == replacement["name"]
    handoff = staff["recent_handoffs"][0]
    assert handoff["responsibility"] == "recruitment_search"
    assert handoff["affected_count"] >= 1


def test_k_closed_market_keeps_research_and_inquiry_but_blocks_offer():
    career = _career(14004)
    career.state["current_date"] = "1994-04-02"
    target = _external_target(career)
    pid = int(target["id"])

    task = career.start_scouting_player(pid)
    inquiry = career.inquire_player_availability(pid)
    snapshot = career.market_snapshot()

    assert snapshot["period"]["open"] is False
    assert snapshot["workflow"]["window_policy"] == {
        "can_search": True,
        "can_scout": True,
        "can_inquire": True,
        "can_offer": False,
        "label": "Seguimiento abierto · inscripciones cerradas",
        "detail": "El cierre impide nuevas altas y contraofertas, pero no detiene búsqueda, scouting ni comparación de alternativas.",
    }
    assert task["status"] == "active"
    assert inquiry["player_id"] == pid
    with pytest.raises(ValueError, match="negociación"):
        career.open_transfer_negotiation(pid, fee_offer=0, salary_offer=0, contract_years=3)


def test_k_medical_snapshot_separates_observation_estimate_and_action():
    career = _career(14005)
    pid = int(career.squad()[0]["id"])
    dev = career.state["player_development"][str(pid)]
    dev.update({"injury_days": 8, "injury_risk": 82, "training_load": 68, "condition": 48})

    training = career.training_snapshot()
    medical = training["medical"]
    case = next(row for row in medical["cases"] if int(row["player_id"]) == pid)

    assert medical["responsibility"]["assignee_name"]
    assert medical["action_required"] >= 1
    assert case["observed"] is True
    assert "8" in case["estimate"]
    assert case["requires_action"] is True
    assert case["recommendation"]
    assert "observaciones" in medical["data_note"].casefold()
    assert "estim" in medical["data_note"].casefold()
    assert training["process"]["requires_action"] is True
    assert training["process"]["next_step"]
    assert training["process"]["consequence"]


def test_k_frontend_contract_surfaces_comparison_handoffs_and_medical_truth():
    market = (ROOT / "frontend/src/football9394/components/MarketWorkspace.vue").read_text(encoding="utf-8")
    staff = (ROOT / "frontend/src/football9394/components/StaffWorkspace.vue").read_text(encoding="utf-8")
    training = (ROOT / "frontend/src/football9394/components/TrainingWorkspace.vue").read_text(encoding="utf-8")
    app = (ROOT / "frontend/src/football9394/Football9394App.vue").read_text(encoding="utf-8")

    assert "COMPARACIÓN A/B/C" in market
    assert "COSTE DE OPORTUNIDAD" in market
    assert "window_policy" in market
    assert ">Consultar</button>" in market
    assert ':disabled="t[6]?.market?.free_agent"' in market
    assert "procesos vivos" in staff
    assert "ÚLTIMO CAMBIO DE RESPONSABLE" in staff
    assert "active_processes" in staff
    assert "OBSERVADO" in training
    assert "ESTIMACIÓN" in training
    assert "SIGUIENTE PASO" in training
    assert "reasignados sin perder el trabajo" in app
