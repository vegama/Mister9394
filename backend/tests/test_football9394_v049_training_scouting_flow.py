from __future__ import annotations

from datetime import date, timedelta

from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.scouting import external_player_view, knowledge_at_date, scouting_geography


def _career(seed: int = 4901) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=seed, through_matchday=0)


def test_v049_training_plan_is_persistent_and_exposes_staff_effect():
    career = _career()
    initial = career.training_snapshot()
    assert initial["weekly_plan"] and len(initial["weekly_plan"]) == 7
    assert initial["responsibility"]["responsibility"] == "first_team_training"
    changed = career.set_training_plan(
        intensity="high",
        weekly_plan=["recovery", "physical", "physical", "tactical", "attack", "match_preparation", "rest"],
    )
    assert changed["intensity"] == "high"
    assert changed["weekly_plan"][1]["session"] == "physical"
    assert career.state["training"]["intensity"] == "high"


def test_v049_training_daily_pulse_changes_real_workload_and_medical_view():
    career = _career(4902)
    own = career.squad()[0]
    pid = own["id"]
    career.set_training_plan(intensity="high", weekly_plan=["physical"] * 7)
    before = dict(career.state["player_development"][str(pid)])
    result = career.advance_day()
    assert result["advanced"] is True
    after = career.state["player_development"][str(pid)]
    assert int(after["training_load"]) > int(before.get("training_load") or 0)
    assert int(after["fatigue"]) > int(before.get("fatigue") or 0)
    detail = career.player_detail(pid)
    assert detail["medical"]["workload"]["training_load"] == after["training_load"]
    assert detail["medical"]["workload"]["injury_risk"] == after["injury_risk"]


def test_v049_individual_focus_writes_slow_attribute_evidence():
    career = _career(4903)
    player = career.squad()[0]
    pid = player["id"]
    career.set_training_plan(intensity="high", weekly_plan=["attack"] * 7)
    career.set_player_training_focus(pid, "finishing")
    career.advance_day()
    points = career.state["player_development"][str(pid)].get("attribute_points") or {}
    assert float(points.get("finishing") or 0) > 0
    assert float(points.get("off_ball") or 0) > 0


def test_v049_scouting_has_real_capacity_and_rejects_infinite_assignments():
    career = _career(4904)
    cap = career.scouting_snapshot()["capacity"]
    assert 1 <= cap <= 6
    targets = career.search_market(limit=50)
    for target in targets[:cap]:
        career.start_scouting_player(target["id"])
    snap = career.scouting_snapshot()
    assert snap["used_capacity"] == cap
    assert snap["available_capacity"] == 0
    try:
        career.start_scouting_player(targets[cap]["id"])
    except ValueError as exc:
        assert "capacidad" in str(exc).casefold()
    else:
        raise AssertionError("scouting should reject assignments beyond capacity")


def test_v049_scouting_geography_and_report_age_are_visible():
    assert scouting_geography("España", "España")["travel_days"] == 0
    assert scouting_geography("España", "Bélgica")["travel_days"] > 0
    row = {"level": 4, "confidence": 92, "updated_on": "1993-07-01"}
    fresh = knowledge_at_date(row, date(1993, 7, 20))
    stale = knowledge_at_date(row, date(1994, 4, 1))
    assert fresh["level"] == 4 and fresh["stale"] is False
    assert stale["stale"] is True
    assert stale["level"] < 4
    assert stale["confidence"] < fresh["confidence"]


def test_v049_squad_plan_links_needs_to_market_position():
    career = _career(4905)
    plan = career.squad_plan_snapshot()
    assert plan["priorities"]
    assert all("market_position" in row for row in plan["priorities"])


def test_v049_training_api_and_snapshot(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    client = TestClient(webapp.app)
    created = client.post("/api/football9394/careers", json={"team_id": 16, "league_id": 1, "seed": 4906, "through_matchday": 0})
    assert created.status_code == 200
    career_id = created.json()["career_id"]
    training = client.get(f"/api/football9394/careers/{career_id}/training")
    assert training.status_code == 200
    assert training.json()["players"]
    updated = client.put(
        f"/api/football9394/careers/{career_id}/training",
        json={"intensity": "low", "weekly_plan": ["recovery", "physical", "tactical", "attack", "defence", "match_preparation", "rest"]},
    )
    assert updated.status_code == 200
    assert updated.json()["training"]["intensity"] == "low"
    pid = updated.json()["training"]["players"][0]["player_id"]
    focus = client.put(f"/api/football9394/careers/{career_id}/training/players/{pid}", json={"focus": "passing"})
    assert focus.status_code == 200
    selected = next(row for row in focus.json()["training"]["players"] if row["player_id"] == pid)
    assert selected["focus"] == "passing"
