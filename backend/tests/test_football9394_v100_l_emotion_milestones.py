from __future__ import annotations

from pathlib import Path

from backend.app.football9394.career_milestones import (
    contextual_milestones,
    register_rivalry_result,
    register_season_closure,
)
from backend.app.football9394.manager_career import ManagerCareerRuntime9394

ROOT = Path(__file__).resolve().parents[2]


def test_l_season_closure_freezes_title_movement_and_manager_recap_without_duplicates():
    state = {}
    honours = [{
        "season": "1993-94", "competition_kind": "league", "source_id": 1,
        "competition_name": "Primera División", "team_id": 3, "team_name": "FC Barcelona",
        "champion_manager": {"name": "Tú"}, "runner_up_team_id": 5,
        "runner_up_team_name": "Real Madrid", "margin_points": 2,
    }]
    movements = [{"team_id": 3, "from_league_id": 2, "to_league_id": 1, "reason": "promotion"}]
    recap = {"position": 1, "points": 60, "top_scorer": {"name": "Romário", "goals": 30}, "player_of_season": {"name": "Romário", "average_rating": 8.1}}
    first = register_season_closure(
        state, date_text="1994-06-30", season="1993-94", controlled_team_id=3,
        controlled_team_name="FC Barcelona", recap=recap, honours=honours,
        movements=movements, team_name_lookup=lambda tid: {3: "FC Barcelona", 5: "Real Madrid"}.get(tid, f"Club {tid}"),
    )
    second = register_season_closure(
        state, date_text="1994-06-30", season="1993-94", controlled_team_id=3,
        controlled_team_name="FC Barcelona", recap=recap, honours=honours,
        movements=movements, team_name_lookup=lambda tid: {3: "FC Barcelona", 5: "Real Madrid"}.get(tid, f"Club {tid}"),
    )
    assert {row["kind"] for row in first} == {"champion", "promotion", "season_end"}
    assert len(state["career_milestones"]) == 3
    assert {row["key"] for row in first} == {row["key"] for row in second}
    title = next(row for row in state["career_milestones"] if row["kind"] == "champion")
    assert title["importance"] == 10
    assert title["metadata"]["runner_up_team_name"] == "Real Madrid"


def test_l_rivalry_milestone_reappears_only_when_context_is_relevant():
    state = {}
    milestone = register_rivalry_result(
        state, date_text="1993-12-18", season="1993-94", controlled_team_id=3,
        controlled_team_name="FC Barcelona", opponent_team_id=5, opponent_team_name="Real Madrid",
        competition_name="Primera División", goals_for=4, goals_against=0, heat=82,
    )
    assert milestone and milestone["kind"] == "rivalry_match"
    madrid = contextual_milestones(state, team_id=3, opponent_team_id=5, limit=5)
    other = contextual_milestones(state, team_id=3, opponent_team_id=16, limit=5)
    assert madrid and madrid[0]["opponent_relevant"] is True
    assert not any(row["kind"] == "rivalry_match" for row in other)


def test_l_archived_league_champion_keeps_runner_up_and_margin_context():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=15003, through_matchday=0)
    table = career.standings()
    honours = career._archive_honours({1: table})
    title = next(row for row in honours if row["source_id"] == 1)
    assert title["runner_up_team_id"] == table[1]["team_id"]
    assert title["runner_up_team_name"]
    assert title["margin_points"] == int(table[0]["points"]) - int(table[1]["points"])
    assert title["champion_squad"]
    assert title["champion_manager"]["name"]


def test_l_manager_change_becomes_persistent_career_chapter():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=15004, through_matchday=0)
    career.state["job_status"] = "dismissed"
    career._handle_user_dismissal()
    offer = career.snapshot()["user_manager"]["job_offers"][0]
    career.accept_job_offer(offer["id"])
    kinds = [row["kind"] for row in career.state["career_milestones"]]
    assert "dismissal" in kinds
    assert "job_change" in kinds
    move = next(row for row in reversed(career.state["career_milestones"]) if row["kind"] == "job_change")
    assert move["team_id"] == int(offer["team_id"])
    assert "cambia de proyecto" in move["summary"].casefold()


def test_l_snapshot_exposes_contextual_memory_for_next_opponent():
    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=15005, through_matchday=0)
    nxt = career.next_scheduled_fixture()
    opponent = int(nxt["away_team_id"] if int(nxt["home_team_id"]) == 3 else nxt["home_team_id"])
    register_rivalry_result(
        career.state, date_text="1993-08-01", season="1992-93", controlled_team_id=3,
        controlled_team_name=career._team_name(3), opponent_team_id=opponent,
        opponent_team_name=career._team_name(opponent), competition_name="Copa", goals_for=3, goals_against=2, heat=80,
    )
    snap = career.snapshot()
    assert snap["career_milestones"]
    assert any(row.get("opponent_relevant") for row in snap["next_match_memory"])


def test_l_frontend_contract_surfaces_emotion_without_forced_cinematics():
    history = (ROOT / "frontend/src/football9394/components/HistoryWorkspace.vue").read_text(encoding="utf-8")
    season_end = (ROOT / "frontend/src/football9394/components/SeasonEndOverlay.vue").read_text(encoding="utf-8")
    champions = (ROOT / "frontend/src/football9394/components/ChampionsWorkspace.vue").read_text(encoding="utf-8")
    live = (ROOT / "frontend/src/football9394/components/LiveMatchWorkspace.vue").read_text(encoding="utf-8")
    app = (ROOT / "frontend/src/football9394/Football9394App.vue").read_text(encoding="utf-8")

    assert "HITOS CANÓNICOS" in history
    assert "Mejor y peor temporada" in history
    assert "Figura:" in history and "Goleador:" in history
    assert "MOMENTOS DE LA TEMPORADA" in season_end
    assert "Continuar a la nueva temporada" in season_end
    assert "runner_up_team_name" in champions and "Margen" in champions
    assert "LO QUE ARRASTRA ESTE PARTIDO" in live
    assert "opponent.value?.history" in live
    assert "career_milestones" in app
