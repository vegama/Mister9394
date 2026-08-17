from __future__ import annotations

from datetime import date, timedelta

from backend.app.football9394.board_project import register_sale_income
from backend.app.football9394.career_club_status import club_status
from backend.app.football9394.economy_longitudinal import post as post_long_economy, longitudinal_snapshot
from backend.app.football9394.information_world import process_information_day
from backend.app.football9394.manager_career import ManagerCareerRuntime9394, CAREER_SCHEMA_9394


def _career(seed: int = 9100, *, team_id: int = 3, league_id: int = 1, through: int = 0) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=team_id, league_id=league_id, seed=seed, through_matchday=through)


def _force_cross_league_job(career: ManagerCareerRuntime9394, league_id: int = 4) -> dict:
    target = career._teams_for_league(league_id)[0]
    team_id = int(target["source_id"])
    score = float(club_status(career.state, team_id).get("score") or 50)
    country = str((career.universe.leagues_by_id.get(league_id) or {}).get("country") or "")
    career.state.setdefault("manager_pressure", {})[str(team_id)] = {"score": 95}
    career.state["user_manager"]["reputation"] = score
    career.state["user_manager"].setdefault("reputation_by_country", {})[country] = score
    jobs = career._refresh_job_market(day=career.current_date, proactive=False)
    return next(row for row in jobs if int(row["team_id"]) == team_id)


def test_nf9_application_interview_contract_and_cross_league_world_handover():
    career = _career(9101, through=2)
    old_league = int(career.state["league_id"])
    old_completed = int(career.state["completed_matchday"])
    target = _force_cross_league_job(career, 4)
    target_background = dict(career.state["world_leagues"]["4"])

    application = career.apply_for_job(target["id"])
    assert application["passed"] is True
    offer = next(row for row in career.state["user_manager"]["career_offers"] if row.get("application_id"))
    snapshot = career.accept_job_offer(offer["id"])

    assert snapshot["league_id"] == 4
    assert snapshot["team"]["source_id"] == target["team_id"]
    assert snapshot["completed_matchday"] == target_background["completed_round"]
    assert len(career.state["results"]) == len(target_background["results"])
    assert career.state["world_leagues"][str(old_league)]["completed_round"] == old_completed
    assert snapshot["professional_career"]["active_contract"]["team_id"] == target["team_id"]
    assert snapshot["professional_career"]["reputation_by_country"]["Italia"] >= target["club_score"]
    assert snapshot["user_manager"]["tenures"][-1]["reason"] == "left_for_job"


def test_nf9_resignation_closes_contract_but_keeps_reputation_and_memories():
    career = _career(9102)
    before = career.professional_career_snapshot()
    result = career.resign_club_job()
    after = result["career"]["professional_career"]
    assert result["career"]["job_status"] == "dismissed"
    assert after["active_contract"] == {}
    assert after["reputation"] == before["reputation"]
    assert after["tenures"][-1]["reason"] == "resigned"
    assert any(row.get("kind") == "contract_closed" and row.get("end_reason") == "resigned" for row in after["career_memories"])
    assert result["offers"]


def test_nf10_financial_crisis_creates_causal_sale_pressure_and_real_sale_reduces_it():
    career = _career(9103)
    team_id = int(career.state["team_id"])
    finances = career.state["finances"]
    finances["cash"] = 0
    finances["debt"] = max(20_000_000, int(finances.get("starting_budget") or 0) * 3)
    career.state["club_finances"][str(team_id)] = finances
    project = career._update_board_project_state()
    pressure = project["sale_pressure"]
    assert pressure and pressure["status"] == "active" and pressure["required_income"] > 0
    assert any(row["headline"] == "El consejo pide una venta" for row in career.news_snapshot(limit=20))
    thread = next(row for row in career.information_world_snapshot()["threads"] if row["origin_kind"] == "board_sale_pressure")
    assert thread["consequences"] and thread["consequences"][0]["kind"] == "sale_required"

    half = max(1, int(pressure["required_income"]) // 2)
    reduced = register_sale_income(career.state, team_id=team_id, amount=half, date_text=career.current_date.isoformat())
    assert reduced and reduced["remaining"] == max(0, int(pressure["required_income"]) - half)
    resolved = register_sale_income(career.state, team_id=team_id, amount=int(reduced["remaining"]), date_text=career.current_date.isoformat())
    assert resolved and resolved["status"] == "resolved"


def test_nf10_board_requests_are_project_decisions_not_free_buttons():
    career = _career(9104)
    project_before = career.board_project_snapshot()
    result = career.submit_board_request("expand_staff")
    assert result["request"]["status"] in {"accepted", "rejected"}
    assert result["request"]["reason"]
    if result["request"]["status"] == "accepted":
        assert result["project"]["max_staff_size"] == project_before["max_staff_size"] + 1
    else:
        assert result["project"]["max_staff_size"] == project_before["max_staff_size"]
    assert result["project"]["requests"][-1]["id"] == result["request"]["id"]


def test_nf10_board_does_not_allow_repeating_an_accepted_seasonal_expansion():
    career = _career(9111)
    team_id = int(career.state["team_id"])
    project = career._update_board_project_state()
    max_staff_before = int(project["max_staff_size"])
    career.state["board_projects"][str(team_id)]["support"] = 95
    # Force a stable, high-support decision context while keeping the test on
    # the public request flow rather than mutating the project result itself.
    career.state["board_state"] = {"score": 95}
    career.state["finances"]["cash"] = max(int(career.state["finances"].get("cash") or 0), int(career.state["finances"].get("safety_reserve") or 0) * 2, 500_000_000)
    career.state["finances"]["projected_monthly_net"] = max(0, int(career.state["finances"].get("projected_monthly_net") or 0))
    career.state["club_finances"][str(team_id)] = career.state["finances"]
    # Call the domain function with deterministic approval conditions so the
    # second call can prove the seasonal lock regardless of board-form noise.
    from backend.app.football9394.board_project import submit_board_request
    first = submit_board_request(state=career.state, team_id=team_id, request_type="expand_staff", date_text=career.current_date.isoformat(), board_score=95, economy={"projected_monthly_net": 1, "cash": 500_000_000, "safety_reserve": 10_000_000})
    assert first["status"] == "accepted"
    second = submit_board_request(state=career.state, team_id=team_id, request_type="expand_staff", date_text=career.current_date.isoformat(), board_score=95, economy={"projected_monthly_net": 1, "cash": 500_000_000, "safety_reserve": 10_000_000})
    assert second["status"] == "rejected"
    assert "temporada actual" in second["reason"]
    assert career.state["board_projects"][str(team_id)]["max_staff_size"] == max_staff_before + 1


def test_nf11_real_market_rumour_is_not_promoted_to_truth_by_time_alone():
    career = _career(9105)
    target = career.search_market(limit=40)[0]
    career.inquire_player_availability(target["id"])
    thread = next(row for row in career.information_world_snapshot()["threads"] if row["origin_kind"] == "market_inquiry")
    assert thread["stage"] == "rumour" and thread["news"] is None
    process_information_day(career.state, day=career.current_date + timedelta(days=4))
    cooled = next(row for row in career.information_world_snapshot()["threads"] if row["id"] == thread["id"])
    assert cooled["stage"] == "cooled"
    assert cooled["news"] is None
    assert cooled["certainty"] < thread["certainty"]


def test_nf11_inquiry_negotiation_and_confirmed_transfer_share_one_causal_thread():
    career = _career(9106)
    target = career.search_market(limit=80)[0]
    pid = int(target["id"])
    inquiry = career.inquire_player_availability(pid)
    thread_before = next(row for row in career.information_world_snapshot()["threads"] if row["origin_kind"] == "market_inquiry" and int(row["fact"]["entity"]["player_id"]) == pid)
    # We do not depend on the negotiation AI accepting an arbitrary market
    # price here: the confirmed event uses the same real player and source club,
    # which is what the information linker must correlate.
    career._ingest_news([{"kind":"user_transfer","date":career.current_date.isoformat(),"player_id":pid,"from_team_id":int(inquiry["seller_team_id"] or 0),"to_team_id":int(career.state["team_id"]),"fee":max(0,int(inquiry["asking_range"][0]))}])
    rows = [row for row in career.information_world_snapshot()["threads"] if int((row.get("fact") or {}).get("entity",{}).get("player_id") or -1) == pid]
    linked = next(row for row in rows if row["id"] == thread_before["id"])
    assert linked["confirmed_fact"]["kind"] == "user_transfer"
    assert linked["news"] and linked["stage"] in {"news", "reaction", "consequence"} and linked["certainty"] == 100


def test_nf12_longitudinal_economy_records_matchday_and_season_history_without_double_cash():
    career = _career(9107)
    team_id = int(career.state["team_id"])
    before_cash = int(career.state["finances"]["cash"])
    income = career._post_matchday_income(team_id, competition="Liga", reference="nf12-test")
    snapshot = career.economy_snapshot()
    assert int(career.state["finances"]["cash"]) == before_cash + income
    assert snapshot["longitudinal"]["current_season"]["gate_receipts"] >= income
    assert snapshot["health"]["label"] in {"Sólida", "Controlada", "Vigilancia", "Crisis"}

    post_long_economy(career.state, team_id=team_id, season="1994-95", category="prize_money", amount=5_000_000)
    history = longitudinal_snapshot(career.state, team_id=team_id, season="1994-95")["history"]
    assert {row["season"] for row in history} >= {"1993-94", "1994-95"}


def test_nf9_nf12_save_schema_and_surfaces_survive_reload():
    career = _career(9108)
    career._update_board_project_state()
    state = dict(career.state)
    restored = ManagerCareerRuntime9394(state)
    snap = restored.snapshot()
    assert snap["professional_career"]["active_contract"]
    assert "board_project" in snap and "information_world" in snap
    assert "longitudinal" in snap["economy"] and "health" in snap["economy"]
    assert restored.state["schema"] == CAREER_SCHEMA_9394 == 22


def test_nf9_nf12_api_surfaces_persist(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    client = TestClient(webapp.app)
    created = client.post("/api/football9394/careers", json={"team_id": 3, "league_id": 1, "seed": 9110, "through_matchday": 0})
    assert created.status_code == 200
    cid = created.json()["career_id"]

    career = client.get(f"/api/football9394/careers/{cid}/professional-career")
    project = client.get(f"/api/football9394/careers/{cid}/board-project")
    information = client.get(f"/api/football9394/careers/{cid}/information-world")
    economy = client.get(f"/api/football9394/careers/{cid}/economy")
    assert career.status_code == project.status_code == information.status_code == economy.status_code == 200
    assert career.json()["active_contract"]["team_id"] == 3
    assert project.json()["objective"]
    assert "threads" in information.json()
    assert "longitudinal" in economy.json()["summary"]

    request = client.post(f"/api/football9394/careers/{cid}/board-project/requests/expand_staff")
    assert request.status_code == 200
    assert request.json()["request"]["status"] in {"accepted", "rejected"}
