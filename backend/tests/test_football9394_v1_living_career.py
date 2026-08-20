from __future__ import annotations

from datetime import date

from backend.app.football9394.career_memory import (
    adjust_player_manager_relationship,
    record_match_memory,
    relationship_api,
    rivalry_between,
    rivalry_snapshot,
)
from backend.app.football9394.career_news import ingest_events
from backend.app.football9394.career_storylines import refresh_storylines
from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.manager_market import choose_replacement, pressure_score, register_manager_change
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_source_rivalries_seed_career_memory_and_match_result_increases_heat():
    universe = default_runtime_snapshot()
    state = {"team_id": 3}
    before = rivalry_snapshot(state, universe, 3)
    madrid = next(row for row in before if row["opponent_id"] == 5)
    assert madrid["heat"] >= 72
    record_match_memory(
        state, universe, date_text="1993-11-01", competition="Liga",
        home_team_id=3, away_team_id=5, home_goals=2, away_goals=1,
    )
    after = rivalry_between(state, 3, 5)
    assert after["heat"] > madrid["heat"]
    assert after["meetings"] == 1
    assert after["history"][-1]["home_goals"] == 2


def test_player_manager_trust_is_persistent_and_exposed_in_real_player_detail():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    initial = career.player_detail(9)["manager_relationship"]
    assert initial["trust"] == 55
    career.list_player_for_transfer(9)
    listed = career.player_detail(9)["manager_relationship"]
    assert listed["trust"] == 43
    assert "mercado" in listed["last_change"]["reason"]
    career.unlist_player(9)
    career.renew_player_contract(9, years=3)
    renewed = career.player_detail(9)["manager_relationship"]
    assert renewed["trust"] > listed["trust"]
    assert renewed["label"] in {"Profesional", "Buena relación", "Leal al mánager"}


def test_nf9_cross_league_job_swap_preserves_both_competition_timelines():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=9411, through_matchday=3)
    old_results = list(career.state.get("results") or [])
    target_team = next(row for row in career.universe.payload.get("teams", []) if int(row.get("league_id") or 0) == 2)
    target_id = int(target_team["source_id"])
    career.state["user_manager"]["career_offers"] = [{
        "id": "cross-league-test", "status": "open", "team_id": target_id,
        "team_name": target_team.get("name"), "league_id": 2, "league_name": "Premier Division",
        "country": "Inglaterra", "suitability": 72, "expected_position": 8, "club_score": 60,
    }]
    career.accept_job_offer("cross-league-test")
    assert int(career.state["league_id"]) == 2
    assert career.state["world_leagues"]["1"]["results"]
    assert len(career.state["world_leagues"]["1"]["results"]) == len(old_results)
    assert career.next_scheduled_fixture()


def test_emergent_storylines_exist_only_when_real_conditions_exist_and_resolve():
    state = {"storylines": [], "manager_history": []}
    standings = [
        {"team_id": 3, "position": 1, "played": 8},
        {"team_id": 5, "position": 2, "played": 8},
        {"team_id": 2, "position": 3, "played": 8},
        {"team_id": 4, "position": 4, "played": 8},
    ]
    squad = [{"id": 9, "display_name": "Romário", "overall": 89, "squad_dynamics": {"satisfaction": 24, "wants_move": True}}]
    rows = refresh_storylines(
        state, date_text="1993-11-10", controlled_team_id=3, standings=standings,
        recent_form=["V", "V", "V"], squad=squad, negotiations=[], next_match=None,
        rivalry=None, team_name="FC Barcelona", player_name_lookup=lambda _: "Romário",
    )
    kinds = {row["kind"] for row in rows}
    assert {"table_pressure", "streak", "player_tension"} <= kinds
    rows = refresh_storylines(
        state, date_text="1993-11-11", controlled_team_id=3,
        standings=[{"team_id": 3, "position": 4, "played": 9}, {"team_id": 5, "position": 1, "played": 9}, {"team_id": 2, "position": 2, "played": 9}, {"team_id": 4, "position": 3, "played": 9}],
        recent_form=["E", "V", "D"], squad=[{"id": 9, "display_name": "Romário", "overall": 89, "squad_dynamics": {"satisfaction": 70, "wants_move": False}}],
        negotiations=[], next_match=None, rivalry=None, team_name="FC Barcelona", player_name_lookup=lambda _: "Romário",
    )
    assert not any(row["kind"] in {"table_pressure", "streak", "player_tension"} for row in rows)
    assert any(row["status"] == "resolved" for row in state["storylines"])


def test_manager_market_uses_source_coaches_and_assignment_changes_ai_coach_identity():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    team_id = 16
    old = career._coach_profile(team_id)
    assert old and old["display_name"] == "John Toshack"
    assert pressure_score(position=18, expected_position=6, team_count=20, played=14, recent_points=1) >= 90
    replacement = choose_replacement(
        career.state, when=date(1993, 12, 1), team_id=team_id,
        squad=career._career_players_by_team[team_id], club_score=62, seed=9394,
    )
    assert replacement and replacement["source_id"] != old["source_id"]
    assert replacement["display_name"]
    event = register_manager_change(
        career.state, when=date(1993, 12, 1), team_id=team_id,
        old_manager_id=old["source_id"], new_manager_id=replacement["source_id"],
        reason="resultados_por_debajo_de_expectativa", pressure=94,
    )
    new = career._coach_profile(team_id)
    assert new and new["source_id"] == replacement["source_id"]
    assert event["provenance"] == "career_generated_from_mdb_manager_pool"
    assert old["source_id"] in career.state["manager_unemployed"]


def test_manager_change_becomes_causal_news_not_filler():
    state = {}
    event = {
        "kind": "manager_change", "date": "1993-12-01", "team_id": 16,
        "from_manager_name": "John Toshack", "to_manager_name": "Entrenador B", "to_manager_id": 777,
    }
    created = ingest_events(state, [event], team_name=lambda tid: "Real Sociedad", player_name=lambda pid: str(pid))
    assert len(created) == 1
    assert created[0]["category"] == "Entrenadores"
    assert "cambia de entrenador" in created[0]["headline"]
    assert "John Toshack" in created[0]["detail"]


def test_career_snapshot_exposes_storylines_rivalries_and_manager_world_without_overwriting_base_rating():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    adjust_player_manager_relationship(career.state, player_id=9, date_text=career.current_date.isoformat(), delta=-20, reason="prueba de tensión")
    career.state["player_dynamics"]["9"]["satisfaction"] = 25
    career.state["player_dynamics"]["9"]["wants_move"] = True
    snapshot = career.snapshot()
    assert "storylines" in snapshot and isinstance(snapshot["storylines"], list)
    assert "rivalries" in snapshot and any(row["opponent_id"] == 5 for row in snapshot["rivalries"])
    assert "manager_world" in snapshot and "history" in snapshot["manager_world"]
    romario = next(row for row in snapshot["squad"] if row["id"] == 9)
    assert romario["overall"] == 89
    assert romario["manager_relationship"]["trust"] == relationship_api(career.state, 9)["trust"]


def test_career_records_persist_real_milestones_and_publish_distinct_news():
    from backend.app.football9394.career_records import update_after_controlled_match, records_snapshot
    state = {"team_id": 3}
    events = []
    for i, score in enumerate([(2, 0), (1, 0), (3, 1), (2, 1), (4, 0)], start=1):
        events.extend(update_after_controlled_match(
            state, date_text=f"1993-11-{i:02d}", competition="Liga", controlled_team_id=3,
            home_team_id=3, away_team_id=5, home_goals=score[0], away_goals=score[1],
            home_name="FC Barcelona", away_name="Real Madrid",
        ))
    records = records_snapshot(state)
    assert records["matches_managed"] == 5
    assert records["wins"] == 5
    assert records["longest_win_streak"] == 5
    assert records["longest_unbeaten_streak"] == 5
    assert records["biggest_win"]["result"] == "4-0"
    assert any(row.get("record") == "longest_win_streak" and row.get("value") == 5 for row in events)
    news = ingest_events(state, events, team_name=lambda tid: "FC Barcelona", player_name=lambda pid: str(pid))
    assert any("5 victorias seguidas" in row["headline"] for row in news)
    assert any("mayor victoria" in row["headline"] for row in news)


def test_two_manager_changes_same_day_generate_two_distinct_news_items():
    state = {}
    events = [
        {"kind":"manager_change","date":"1994-01-03","team_id":16,"from_manager_id":1,"to_manager_id":1001,"from_manager_name":"A","to_manager_name":"B"},
        {"kind":"manager_change","date":"1994-01-03","team_id":21,"from_manager_id":2,"to_manager_id":1002,"from_manager_name":"C","to_manager_name":"D"},
    ]
    created = ingest_events(state, events, team_name=lambda tid: f"Club {tid}", player_name=lambda pid: str(pid))
    assert len(created) == 2
    assert {row["headline"] for row in created} == {"Club 16 cambia de entrenador", "Club 21 cambia de entrenador"}


def test_career_snapshot_exposes_records_without_counting_friendlies():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    career._publish_controlled_result(competition="Pretemporada", home_team_id=3, away_team_id=5, home_goals=3, away_goals=0)
    assert career.snapshot()["career_records"]["matches_managed"] == 0
    career._publish_controlled_result(competition="Liga", home_team_id=3, away_team_id=5, home_goals=2, away_goals=0)
    records = career.snapshot()["career_records"]
    assert records["matches_managed"] == 1
    assert records["wins"] == 1


def test_manager_player_trust_changes_real_renewal_cost_without_touching_player_rating():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    pid = 9
    base_overall = career.player_detail(pid)["overall"]
    current = career.renew_player_contract(pid, years=3, salary_offer=0)
    neutral_minimum = current["minimum_salary"]
    adjust_player_manager_relationship(career.state, player_id=pid, date_text=career.current_date.isoformat(), delta=-30, reason="conflicto prolongado")
    tense = career.renew_player_contract(pid, years=3, salary_offer=0)
    assert tense["relationship_trust"] < current["relationship_trust"]
    assert tense["minimum_salary"] > neutral_minimum
    assert career.player_detail(pid)["overall"] == base_overall


def test_monthly_world_pulse_can_really_sack_and_replace_an_ai_manager(monkeypatch):
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    team_id = 16
    before = career._coach_profile(team_id)
    assert before
    table = [{"team_id": team_id, "position": 20, "played": 14}]
    # team_count comes from the table length, so include harmless rows to model a real 20-team league.
    table.extend({"team_id": 10000+i, "position": i, "played": 14} for i in range(1, 20))
    monkeypatch.setattr(career, "_simple_world_league_ids", lambda: [1])
    monkeypatch.setattr(career, "league_standings", lambda league_id: table)
    monkeypatch.setattr(career, "_teams_for_league", lambda league_id: [career.universe.team(team_id)])
    monkeypatch.setattr(career, "_expected_position_for_team", lambda tid, lid: 5)
    monkeypatch.setattr(career, "_recent_points_for_team", lambda tid, lid: 0)
    events = career._process_manager_market(date(1993, 12, 1))
    assert len(events) == 1
    assert events[0]["kind"] == "manager_change"
    assert events[0]["team_id"] == team_id
    after = career._coach_profile(team_id)
    assert after and after["source_id"] != before["source_id"]
    assert events[0]["to_manager_name"] == after["display_name"]
