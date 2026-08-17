from fastapi.testclient import TestClient

from backend.app.football9394.registry import UnresolvedHistoricalRulesError, default_registry_9394
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit
from backend.app.football9394.webapp import app


def test_real_sociedad_runtime_squad_comes_from_snapshot():
    universe = default_runtime_snapshot()
    team = universe.team(16)
    squad = universe.squad(16)
    assert team["name"] == "Real Sociedad"
    assert team["league"]["source_id"] == 1
    assert len(squad) == 25
    names = {row["display_name"] for row in squad}
    assert {"Alberto", "Kodro", "Carlos Xavier", "De Pedro", "Aranzabal"} <= names
    assert "Javier Martín" not in names
    kodro = next(row for row in squad if row["display_name"] == "Kodro")
    assert kodro["shirt_number"] == 9
    assert kodro["overall"] == 83


def test_real_sociedad_calendar_uses_mdb_fixture_rows():
    calendar = default_runtime_snapshot().team_calendar(16)
    assert len(calendar) == 38
    round8 = next(row for row in calendar if row["matchday"] == 8)
    assert round8["home_team"] == "Real Sociedad"
    assert round8["away_team"] == "Racing Santander"


def test_source_scoped_rules_do_not_collapse_same_competition_name():
    registry = default_registry_9394()
    assert registry.resolve_source("league", 1).id == "esp_primera_1993_94"
    mexico_rules = registry.resolve_source("league", 40)  # Mexico is also called Primera División.
    assert mexico_rules.id == "mex_primera_1993_94"
    assert mexico_rules.id != registry.resolve_source("league", 1).id
    mexico = source_rule_audit(CompetitionSourceRef9394("league", 40, "Primera División", "México"))
    spain = source_rule_audit(CompetitionSourceRef9394("league", 1, "Primera División", "España"))
    assert mexico.format_id == "mex_primera_1993_94"
    assert spain.ruleset_id == "esp_primera_1993_94"


def test_bootstrap_api_exposes_real_snapshot_and_simulated_matchday_state():
    client = TestClient(app)
    response = client.get("/api/football9394/career/bootstrap?team_id=16&through_matchday=7")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_origin"] == "normalized_mdb_snapshot"
    assert payload["team"]["name"] == "Real Sociedad"
    assert len(payload["squad"]) == 25
    assert len(payload["standings"]) == 20
    assert payload["next_match"]["matchday"] == 8
    assert payload["next_match"]["home_team"] == "Real Sociedad"
    assert payload["next_match"]["away_team"] == "Racing Santander"


def test_premier_and_bundesliga_are_source_bound_to_their_1993_94_scoring():
    from backend.app.football9394.registry import default_registry_9394
    registry = default_registry_9394()
    premier = registry.resolve_source("league", 5)
    bundesliga = registry.resolve_source("league", 13)
    assert (premier.teams, premier.rounds, premier.points_win, premier.direct_relegation_places) == (22, 42, 3, (20,21,22))
    assert (bundesliga.teams, bundesliga.rounds, bundesliga.points_win, bundesliga.direct_relegation_places) == (18, 34, 2, (16,17,18))


def test_player_api_exposes_source_polyvalence_traits_and_development_data():
    universe = default_runtime_snapshot()
    laudrup = universe.player(11)
    assert laudrup["display_name"] == "Laudrup"
    assert laudrup["position"] == "Mediapunta por el centro"
    assert laudrup["positions"] == ["Mediapunta por el centro", "Mediapunta izquierdo", "Mediapunta derecho"]
    assert laudrup["source_traits"] == {"killer_pass": True, "first_time_play": True}
    assert laudrup["development"]["progression_mean"] == 2
    assert laudrup["development"]["fan_affection"] == 8
    assert laudrup["medical"]["injury_proneness"] == 0


def test_player_source_roles_preserve_historical_polyvalence():
    universe = default_runtime_snapshot()
    hierro = universe.player(26)
    assert hierro["position"] == "Organizador defensivo"
    assert {item["code"] for item in hierro["position_profiles"]} >= {"MCD", "DFC-D", "DFC-I", "LIB", "MC"}
    assert all(item["aptitude"] == 100 for item in hierro["position_profiles"])


def test_source_preserves_basque_origin_flag_for_athletic_policy():
    universe = default_runtime_snapshot()
    athletic = universe.squad(6)
    assert len(athletic) >= 20
    assert all(player["basque_origin"] for player in athletic)
    assert universe.player(9)["basque_origin"] is False
