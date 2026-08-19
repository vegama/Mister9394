from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from pathlib import Path

from backend.app.football9394.product_meta import product_version

ROOT = Path(__file__).resolve().parents[2]


def test_v100_i_is_canonical_version():
    # La version avanza cada release, asi que fijar aqui una concreta convertia
    # cada publicacion en un fallo. Lo que debe sostenerse es el contrato del
    # repositorio: la unica fuente de version es el fichero VERSION.
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert product_version() == expected


def _career(seed: int = 21001) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, seed=seed, through_matchday=0)


def test_v100_i_dashboard_decisions_explain_owner_next_step_and_consequence():
    career = _career()
    dashboard = career.manager_dashboard()
    assert dashboard["pending_decisions"]
    for decision in dashboard["pending_decisions"]:
        assert decision["owner"]
        assert decision["status"] in {"Necesita tu decisión", "Revisar"}
        assert decision["next_step"]
        assert decision["consequence"]
        assert isinstance(decision["requires_action"], bool)
        assert isinstance(decision["blocking"], bool)
    assert set(dashboard["continue_status"]) >= {"state", "can_advance", "label", "detail", "action"}


def test_v100_i_dashboard_exposes_work_in_progress_without_turning_it_into_fake_user_work():
    career = _career(21002)
    target = career.search_market(limit=1)[0]
    task = career.start_scouting_player(int(target["id"]))
    dashboard = career.manager_dashboard()
    process = next(row for row in dashboard["active_processes"] if row["id"] == f"scout:{task['id']}")
    assert process["area"] == "Scouting"
    assert process["owner"]
    assert process["status"] == "En curso"
    assert process["requires_action"] is False
    assert "Informe previsto" in process["next_step"]


def test_v100_i_continue_stops_before_time_moves_when_a_real_decision_is_already_open():
    career = _career(21003)
    career.state["incoming_transfer_offers"].append({
        "id": "offer-ux-stop", "player_id": int(career.squad()[0]["id"]), "status": "open", "fee": 1_000_000,
    })
    before = career.current_date
    dashboard = career.manager_dashboard()
    assert dashboard["blocking_decisions"][0]["kind"] == "incoming_offers"
    assert dashboard["continue_status"]["state"] == "blocked"

    result = career.advance_until_event(max_days=14)
    assert result["advanced_days"] == 0
    assert result["date"] == before.isoformat()
    assert result["requires_decision"] is True
    assert result["decision"]["kind"] == "incoming_offers"
    assert career.current_date == before


def test_v100_i_recent_changes_are_personal_and_actionable():
    career = _career(21004)
    career.state["world_events"].append({
        "kind": "manager_note", "date": career.current_date.isoformat(), "title": "Convocatoria reajustada",
        "detail": "El staff ha retirado a un jugador no disponible del once.",
    })
    changes = career.manager_dashboard()["recent_changes"]
    assert changes
    assert changes[0]["title"] == "Convocatoria reajustada"
    assert changes[0]["area"] == "Staff"
    assert changes[0]["action"] == "home"
