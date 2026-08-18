from __future__ import annotations

from copy import deepcopy

from backend.app.football9394.career_history import build_season_dossier, ensure_history_dossiers
from backend.app.football9394.career_news import ensure_news_state, publish
import backend.app.football9394.career_competition_view as competition_view


def _table(team_id: int, team_name: str, position: int) -> dict:
    return {
        "team_id": team_id, "team_name": team_name, "position": position,
        "played": 38, "wins": 20, "draws": 10, "losses": 8,
        "goals_for": 60, "goals_against": 35, "goal_difference": 25,
        "points": 50,
    }


def test_f_dossier_keeps_every_managed_club_when_manager_changes_midseason():
    state = {
        "user_manager": {
            "tenures": [{"team_id": 1, "team_name": "Club A", "started_on": "1993-07-01", "ended_on": "1994-01-15", "reason": "left_for_job"}],
            "current_tenure": {"team_id": 2, "team_name": "Club B", "started_on": "1994-01-15"},
        },
        "international_history": [],
    }
    dossier = build_season_dossier(
        state, season="1993-94", closed_on="1994-07-01",
        tables={1: [_table(1, "Club A", 4), _table(2, "Club B", 7)]},
        honours=[], movements=[], qualifiers={}, recap={"headline": "Temporada cerrada"},
    )
    assert [row["team_id"] for row in dossier["manager_segments"]] == [1, 2]
    assert dossier["manager_segments"][0]["final_table_row"]["position"] == 4
    assert dossier["manager_segments"][1]["final_table_row"]["position"] == 7


def test_f_old_save_without_dossiers_is_migrated_from_legacy_archive():
    state = {
        "user_manager": {"tenures": [], "current_tenure": {"team_id": 1, "team_name": "Club A", "started_on": "1993-07-01"}},
        "international_history": [],
        "season_recaps": [{"season": "1993-94", "headline": "Archivo legado", "league_awards": {}}],
        "season_archive": [{"season": "1993-94", "closed_on": "1994-07-01", "honours": [], "movements": [], "continental_qualifiers": {}, "league_tables": {"1": [_table(1, "Club A", 8)]}}],
    }
    ensure_history_dossiers(state)
    assert len(state["season_dossiers"]) == 1
    assert state["season_dossiers"][0]["migrated_from_legacy_archive"] is True
    assert state["season_dossiers"][0]["managed_recap"]["headline"] == "Archivo legado"


def test_f_champion_snapshot_is_immutable_after_later_club_moves():
    honours = [{
        "season": "1993-94", "competition_kind": "league", "source_id": 1,
        "competition_name": "Liga", "team_id": 1, "team_name": "Club A", "honour": "Campeón",
        "champion_manager": {"id": 10, "name": "Míster Histórico"},
        "champion_squad": [{"player_id": 99, "name": "Jugador Histórico", "position": "DEL", "overall": 88}],
    }]
    state = {"user_manager": {"tenures": [], "current_tenure": {}}, "international_history": []}
    dossier = build_season_dossier(state, season="1993-94", closed_on="1994-07-01", tables={}, honours=honours, movements=[], qualifiers={}, recap={})
    honours[0]["team_name"] = "Club Nuevo"
    honours[0]["champion_manager"]["name"] = "Otro entrenador"
    honours[0]["champion_squad"][0]["name"] = "Jugador transferido"
    frozen = dossier["champions"][0]
    assert frozen["team_name"] == "Club A"
    assert frozen["champion_manager"]["name"] == "Míster Histórico"
    assert frozen["champion_squad"][0]["name"] == "Jugador Histórico"


def test_f_news_deduplicates_same_cause_but_keeps_simultaneous_club_and_national_milestones():
    state = {"season": "1993-94"}
    ensure_news_state(state)
    first = publish(state, key="subsystem-a", date="1994-05-20", category="Competiciones", importance=5, headline="Club A campeón", cause="competition-title:1993-94:league:1:1")
    duplicate = publish(state, key="subsystem-b", date="1994-06-30", category="Competiciones", importance=5, headline="Club A campeón de Liga", cause="competition-title:1993-94:league:1:1")
    national = publish(state, key="national-milestone", date="1994-06-30", category="Selecciones", importance=5, headline="España alcanza una final", cause="national:1994:final:34")
    assert first is not None
    assert duplicate is None
    assert national is not None
    assert len(state["news_feed"]) == 2


def test_f_anomalous_season_without_awards_movements_or_fixtures_still_has_valid_dossier():
    state = {"user_manager": {"tenures": [], "current_tenure": {}}, "international_history": []}
    dossier = build_season_dossier(state, season="1994-95", closed_on="1995-07-01", tables={}, honours=[], movements=[], qualifiers={}, recap={})
    assert dossier["league_awards"] == {}
    assert dossier["movements"] == []
    assert dossier["league_tables"] == {}
    assert dossier["anomalies"] == {"no_awards": True, "no_movements": True, "no_champions": True}


def test_f_three_consecutive_dossiers_are_independent_objects():
    state = {"user_manager": {"tenures": [], "current_tenure": {}}, "international_history": []}
    base_honour = [{"team_id": 1, "team_name": "Club A", "champion_squad": [{"player_id": 1, "name": "Uno"}]}]
    dossiers = [
        build_season_dossier(state, season=season, closed_on=f"{year}-07-01", tables={}, honours=deepcopy(base_honour), movements=[], qualifiers={}, recap={"headline": season})
        for season, year in (("1993-94", 1994), ("1994-95", 1995), ("1995-96", 1996))
    ]
    dossiers[2]["champions"][0]["champion_squad"][0]["name"] = "Tres"
    assert dossiers[0]["champions"][0]["champion_squad"][0]["name"] == "Uno"
    assert dossiers[1]["champions"][0]["champion_squad"][0]["name"] == "Uno"


class _Rule:
    def as_dict(self):
        return {"limit": None}


class _Universe:
    def career_competitions(self):
        return [{"kind": "tournament", "source_id": 7, "name": "Copa", "country": "ES", "level": 1}]

    def team(self, team_id):
        return {"source_id": int(team_id), "name": f"Club {team_id}"}


class _Runtime:
    def __init__(self):
        self.universe = _Universe()
        self.state = {
            "season": "1993-94", "team_id": 1, "honours": [],
            "daily_tournaments": {"7": {"stage": "semifinal", "completed": False, "current_ids": [1, 2], "results": [], "group_results": {}, "pending_ties": []}},
        }

    def _team_api(self, team_id):
        return {"source_id": int(team_id), "name": f"Club {team_id}"}


def test_f_cup_detail_reads_current_phase_each_time_instead_of_stale_navigation_state(monkeypatch):
    monkeypatch.setattr(competition_view, "competition_foreign_rule", lambda *args, **kwargs: _Rule())
    runtime = _Runtime()
    first = competition_view.competition_detail(runtime, "tournament", 7)
    runtime.state["daily_tournaments"]["7"]["stage"] = "final"
    second = competition_view.competition_detail(runtime, "tournament", 7)
    assert first["stage"] == "semifinal"
    assert second["stage"] == "final"
