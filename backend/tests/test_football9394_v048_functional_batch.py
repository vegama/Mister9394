from __future__ import annotations

from datetime import date

from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.scouting import process_scouting_day


def _career(seed: int = 4801) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=seed, through_matchday=0)


def test_v048_external_market_uses_persistent_imperfect_knowledge():
    career = _career()
    target = career.search_market(limit=20)[0]
    assert target["scout"]["level"] == 1
    assert target["overall_is_exact"] is False
    assert target["transfer_value_is_exact"] is False
    assert target["attributes"] == {}
    assert len(target["overall_range"]) == 2
    assert target["overall_range"][0] <= target["overall"] <= target["overall_range"][1]
    assert len(target["market"]["value_range"]) == 2
    again = career.player_detail(target["id"])
    assert again["overall"] == target["overall"]
    assert again["scout"]["level"] == 1


def test_v048_scouting_assignment_takes_time_and_unlocks_reliable_report():
    career = _career(4802)
    target = career.search_market(limit=20)[0]
    task = career.start_scouting_player(target["id"])
    assert task["status"] == "active"
    assert date.fromisoformat(task["due_on"]) > career.current_date
    assert target["id"] in career.state["watchlist"]
    assert career.scouting_snapshot()["active"][0]["player_id"] == target["id"]

    due = date.fromisoformat(task["due_on"])
    events = process_scouting_day(
        career.state,
        game_date=due,
        effectiveness=career._responsibility_effect("recruitment_search"),
        player_lookup=career._player_source,
    )
    assert events and events[0]["kind"] == "scouting_report_ready"
    report = career.player_detail(target["id"])
    assert report["scout"]["level"] >= 3
    assert report["attribute_ranges"]
    assert report["overall_is_exact"] is False
    assert report["overall_range"][1] - report["overall_range"][0] <= 6


def test_v048_squad_plan_converts_ai_audit_into_manager_actions():
    career = _career(4803)
    plan = career.squad_plan_snapshot()
    assert plan["squad_size"] == len(career.squad())
    assert plan["priorities"]
    assert all({"slot", "count", "minimum", "priority", "action"} <= set(row) for row in plan["priorities"])
    assert plan["primary_need"] in {row["slot"] for row in plan["priorities"]}


def test_v048_medical_information_is_filtered_through_responsible_staff():
    career = _career(4804)
    own = career.squad()[0]
    dev = career.state["player_development"][str(own["id"])]
    dev["injury_days"] = 10
    dev["current_injury"] = {
        "name": "Distensión muscular",
        "start": career.current_date.isoformat(),
        "expected_days": 10,
        "expected_return": date.fromordinal(career.current_date.toordinal() + 10).isoformat(),
    }
    detail = career.player_detail(own["id"])
    medical = detail["medical"]
    assert medical["assessment"]["responsible"]
    assert medical["assessment"]["quality"] >= 1
    assert medical["assessment"]["recommendation"]
    assert medical["current_injury"]["estimated_days_range"]
    assert medical["current_injury"]["estimated_return_from"] <= medical["current_injury"]["estimated_return_to"]


def test_v048_transfer_negotiation_records_and_uses_responsible_staff():
    career = _career(4805)
    target = career.search_market(limit=100)[0]
    row = career.open_transfer_negotiation(
        target["id"],
        fee_offer=max(1, int(target["estimated_transfer_value"] or 1)),
        salary_offer=max(1, int(target["market"]["minimum_salary_hint"] or 1)),
        contract_years=3,
    )
    assert row["handled_by"]
    assert row["handler_role"]
    assert 1 <= int(row["handler_quality"]) <= 20
    assert row["response_date"] > career.current_date.isoformat()


def test_v048_scouting_and_squad_plan_are_exposed_through_api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    client = TestClient(webapp.app)
    created = client.post("/api/football9394/careers", json={"team_id": 16, "league_id": 1, "seed": 4806, "through_matchday": 0})
    assert created.status_code == 200
    career_id = created.json()["career_id"]
    market = client.get(f"/api/football9394/careers/{career_id}/market", params={"limit": 10})
    assert market.status_code == 200 and market.json()
    target = market.json()[0]
    started = client.post(f"/api/football9394/careers/{career_id}/scouting/{target['id']}")
    assert started.status_code == 200
    assert started.json()["assignment"]["status"] == "active"
    scouting = client.get(f"/api/football9394/careers/{career_id}/scouting")
    assert scouting.status_code == 200 and scouting.json()["active"]
    plan = client.get(f"/api/football9394/careers/{career_id}/squad-plan")
    assert plan.status_code == 200 and plan.json()["priorities"]
