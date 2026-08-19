from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394


def _career(seed: int = 5001) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=seed, through_matchday=0)


def _external_target(career: ManagerCareerRuntime9394) -> dict:
    """Primer objetivo de mercado que además se puede fichar de verdad.

    España Primera 1993-94 sólo permitía cuatro extranjeros inscritos, así que
    el primer resultado del mercado puede ser perfectamente alguien a quien el
    club no puede inscribir. Estos tests miden la mecánica de negociación, no
    el cupo de extranjeros: eligen un objetivo elegible para no confundir una
    regla aplicada correctamente con un fallo.
    """
    rows = career.search_market(limit=60)
    assert rows
    return next(row for row in rows if (row.get("market") or {}).get("foreign_quota_allowed"))


def test_nf3_individual_recovery_and_match_preparation_are_persistent():
    career = _career(5002)
    player = career.squad()[0]
    pid = player["id"]
    recovery = career.set_player_recovery_plan(pid, "recovery")
    assert next(row for row in recovery["players"] if row["player_id"] == pid)["recovery"] == "recovery"
    prep = career.set_match_preparation_focus("opponent")
    assert prep["match_preparation_focus"] == "opponent"
    assert next(row for row in prep["players"] if row["player_id"] == pid)["recovery"] == "recovery"


def test_nf4_phase_plan_changes_familiarity_and_reaches_match_sheet():
    career = _career(5003)
    before = float(career.tactical_plan_snapshot()["familiarity"]["overall"])
    plan = career.set_tactical_phase_plan(build_up="patient", final_third="through", transition="counter")
    assert plan["build_up"] == "patient"
    assert plan["final_third"] == "through"
    assert plan["transition"] == "counter"
    assert float(plan["familiarity"]["overall"]) <= before
    sheet = career._sheet(int(career.state["team_id"]))
    assert sheet.tactics.build_up == "patient"
    assert sheet.tactics.final_third == "through"
    assert sheet.tactics.transition == "counter"
    assert sheet.tactical_familiarity == round(float(plan["familiarity"]["overall"]))


def test_nf4_player_set_piece_and_opposition_instructions_share_one_plan():
    career = _career(5004)
    own = career.squad()[0]
    briefing = career.match_briefing_snapshot()
    assert briefing and briefing["threats"]
    rival = briefing["threats"][0]
    rival = {"id": rival["player_id"], **rival}
    career.set_tactical_individual_instruction(own["id"], {"duty": "attack", "freedom": "expressive", "pressing": "high"})
    career.set_tactical_set_piece_taker("penalties", own["id"])
    career.set_tactical_opposition_instruction(rival["id"], tight_mark=True, press=True, show_foot="left")
    plan = career.tactical_plan_snapshot()
    own_row = next(row for row in plan["individual_instructions"] if row["player_id"] == own["id"])
    rival_row = next(row for row in plan["opposition_instructions"] if row["player_id"] == rival["id"])
    assert own_row["duty"] == "attack" and own_row["pressing"] == "high"
    assert rival_row["tight_mark"] is True and rival_row["show_foot"] == "left"
    assert int(plan["set_piece_takers"]["penalties"]) == own["id"]


def test_nf5_staff_reports_are_authored_ranked_and_actionable():
    career = _career(5005)
    pack = career.staff_reports_snapshot()
    assert pack["reports"]
    assert all(row["author"] and 35 <= int(row["confidence"]) <= 96 for row in pack["reports"])
    assert all(row["action"] in {"home", "training", "market", "squad", "tactics"} for row in pack["reports"])
    assert pack["reports"][0]["urgency"] in {"high", "normal", "low"}


def test_nf6_failed_contract_talk_opens_real_concern_and_response_resolves_it():
    career = _career(5006)
    pid = career.squad()[0]["id"]
    renewal = career.renew_player_contract(pid, years=3, salary_offer=0)
    assert renewal["accepted"] is False
    room = career.snapshot()["dressing_room"]
    concern = next(row for row in room["concerns"] if row["player_id"] == pid and row["kind"] == "contract")
    resolved = career.respond_dressing_room_concern(concern["id"], "explain")
    assert resolved["resolution"]["status"] == "resolved"
    assert not any(row["id"] == concern["id"] for row in career.snapshot()["dressing_room"]["concerns"])


def test_nf6_discipline_changes_relationship_without_touching_ability():
    career = _career(5007)
    player = career.squad()[0]
    pid = player["id"]
    before_overall = career.player_detail(pid)["overall"]
    result = career.discipline_player(pid, "warning")
    assert result["discipline"]["action"] == "warning"
    assert career.player_detail(pid)["overall"] == before_overall


def test_nf7_inquiry_and_negotiation_carry_role_bonus_clause_and_handler():
    career = _career(5008)
    target = _external_target(career)
    inquiry = career.inquire_player_availability(target["id"])
    assert len(inquiry["asking_range"]) == 2
    assert inquiry["confidence"] >= 40
    fee = 0 if int(inquiry["seller_team_id"] or 0) == 0 else max(0, int(inquiry["asking_range"][0]))
    salary = max(1, int(inquiry["salary_range"][1]))
    cash = int(career.state["finances"]["cash"])
    bonus = min(10_000, max(0, cash - fee))
    row = career.open_transfer_negotiation(
        target["id"], fee_offer=min(fee, max(0, cash - bonus)), salary_offer=salary,
        contract_years=3, squad_role="starter", signing_bonus=bonus, release_clause=max(1, int(target.get("estimated_transfer_value") or 1) * 3),
    )
    assert row["squad_role"] == "starter"
    assert row["signing_bonus"] == bonus
    assert row["release_clause"] > 0
    assert row["handled_by"]
    withdrawn = career.withdraw_transfer_negotiation(row["id"])
    assert withdrawn["status"] == "withdrawn"


def test_nf8_briefing_contains_staff_quality_threats_absences_and_plan():
    career = _career(5009)
    briefing = career.match_briefing_snapshot()
    assert briefing
    assert briefing["opponent"]["team_id"]
    assert briefing["report"]["assignee_name"]
    assert "confidence" in briefing["report"]
    assert "known_tactics" in briefing
    assert "tactical_familiarity" in briefing
    assert "preparation_focus" in briefing


def test_nf8_live_advice_performance_diagnosis_and_phase_change_apply_immediately():
    career = _career(5010)
    fixture = career.next_scheduled_fixture()
    assert fixture
    career.state["current_date"] = fixture["date"]
    match = career.start_live_match()
    assert len(match["controlled_performance"]) == 11
    while match["minute"] < 25 and match["status"] == "live":
        match = career.advance_live_match(5)
    assert match["bench_advice"]
    career.set_tactical_phase_plan(transition="counter")
    live = career.state["live_match"]
    key = "home_tactics" if str(live["home_team_id"]) == str(live["controlled_team_id"]) else "away_tactics"
    assert live[key]["transition"] == "counter"
    while match["status"] != "finished":
        match = career.advance_live_match(15)
        if match["status"] == "halftime":
            match = career.advance_live_match(1)
    assert match["diagnosis"]["reasons"]
    assert match["diagnosis"]["next_actions"]



def test_nf7_loan_negotiation_completes_and_returns_player_to_parent_club(tmp_path):
    from datetime import date

    career = _career(5012)
    controlled = int(career.state["team_id"])
    target = next(
        row for row in career.search_market(limit=80)
        if career._current_team_id(int(row["id"])) not in {0, controlled}
        and career._signing_eligibility(controlled, career._player_source(int(row["id"])))[0]
    )
    pid = int(target["id"])
    parent = career._current_team_id(pid)
    value = max(1, int(target.get("estimated_transfer_value") or 1))
    fee = min(int(career.state["finances"]["cash"]), max(1, round(value * .03)))
    row = career.open_transfer_negotiation(
        pid, fee_offer=fee, salary_offer=0, contract_years=1, squad_role="rotation",
        deal_type="loan", loan_wage_share=100,
    )
    response_day = date.fromisoformat(row["response_date"])
    events = career._process_user_negotiations(response_day)
    assert any(event["kind"] == "user_loan_completed" for event in events)
    assert career._current_team_id(pid) == controlled
    contract = career.state["contract_overrides"][str(pid)]
    assert contract["loan"] is True
    assert int(contract["loan_parent_team_id"]) == parent
    deal = next(item for item in career.market_snapshot()["loans"] if int(item["player_id"]) == pid)
    assert deal["status"] == "active"
    store = ManagerCareerStore9394(tmp_path)
    store.save(career.state)
    career = ManagerCareerRuntime9394(store.load(career.state["career_id"]))
    deal = next(item for item in career.market_snapshot()["loans"] if int(item["player_id"]) == pid)
    assert career._current_team_id(pid) == controlled
    returned = career._process_user_loans(date.fromisoformat(deal["ends_on"]))
    assert any(event["kind"] == "loan_return" for event in returned)
    assert career._current_team_id(pid) == parent
    assert deal["status"] == "completed"

def test_nf3_nf8_api_surface(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    client = TestClient(webapp.app)
    created = client.post("/api/football9394/careers", json={"team_id": 16, "league_id": 1, "seed": 5011, "through_matchday": 0})
    assert created.status_code == 200
    career_id = created.json()["career_id"]

    snap = created.json()
    pid = snap["squad"][0]["id"]
    assert client.put(f"/api/football9394/careers/{career_id}/training/recovery/{pid}", json={"recovery": "reduced"}).status_code == 200
    assert client.put(f"/api/football9394/careers/{career_id}/training/match-preparation", json={"focus": "opponent"}).status_code == 200
    assert client.put(f"/api/football9394/careers/{career_id}/tactical-plan", json={"build_up": "patient", "transition": "counter"}).status_code == 200
    reports = client.get(f"/api/football9394/careers/{career_id}/staff-reports")
    assert reports.status_code == 200 and reports.json()["reports"]
    briefing = client.get(f"/api/football9394/careers/{career_id}/match-briefing")
    assert briefing.status_code == 200 and briefing.json()["opponent"]
