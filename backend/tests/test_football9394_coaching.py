from datetime import date

from backend.app.football9394.coaching import (
    coaching_development_factor,
    source_coach_for_team,
    tactics_from_source_manager,
)
from backend.app.football9394.development import apply_match_development, initial_player_development
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_catalog_runtime import default_source_catalog
from backend.app.football9394.team_builder import build_snapshot_team_sheet


def test_source_coaches_produce_distinct_stable_ai_plans():
    universe = default_runtime_snapshot()
    cruyff = source_coach_for_team(universe, 3)
    toshack = source_coach_for_team(universe, 16)
    assert cruyff["display_name"] == "Johan Cruyff"
    assert cruyff["engine_tactics"]["formation"] == "3-4-3"
    assert cruyff["engine_tactics"]["mentality"] == "attacking"
    assert toshack["display_name"] == "John Toshack"
    assert toshack["engine_tactics"]["formation"] == "4-2-3-1"
    assert cruyff["engine_tactics"] != toshack["engine_tactics"]


def test_source_coach_is_attached_to_ai_team_sheet_without_rating_bonus():
    universe = default_runtime_snapshot()
    coach = source_coach_for_team(universe, 3)
    tactics = tactics_from_source_manager(coach)
    sheet = build_snapshot_team_sheet(universe, 3, tactics=tactics, coach_profile=coach)
    assert sheet.manager_name == "Johan Cruyff"
    assert sheet.manager_quality == 85
    assert sheet.rotation_frequency == "normal"
    assert sheet.tactics.formation == "3-4-3"
    # Source coach quality does not alter the imported player base overall.
    romario_source = universe.players_by_id[9]
    romario_sheet = next(player for player in (*sheet.starters, *sheet.bench) if player.id == "9")
    assert romario_sheet.overall <= int(romario_source["overall"])


def test_coach_development_is_player_specific_not_flat_team_bonus():
    universe = default_runtime_snapshot()
    coach = source_coach_for_team(universe, 3)
    romario = universe.players_by_id[9]
    koeman = universe.players_by_id[5]
    romario_factor = coaching_development_factor(coach, romario, game_date=date(1993, 10, 23))
    koeman_factor = coaching_development_factor(coach, koeman, game_date=date(1993, 10, 23))
    assert romario_factor != koeman_factor
    assert 0.72 <= romario_factor <= 1.42
    assert 0.72 <= koeman_factor <= 1.42


def test_positive_match_development_uses_coach_factor_but_bad_events_still_hurt():
    universe = default_runtime_snapshot()
    coach = source_coach_for_team(universe, 3)
    player = universe.players_by_id[9]
    base_state = initial_player_development([player])
    coached = {key: dict(value) for key, value in base_state.items()}
    neutral = {key: dict(value) for key, value in base_state.items()}
    apply_match_development(
        coached, player_ids=["9"], won=True, drew=False, goal_ids=["9"], seed=2,
        coach_profile=coach, source_players=universe.players_by_id, game_date=date(1993, 10, 23),
    )
    apply_match_development(neutral, player_ids=["9"], won=True, drew=False, goal_ids=["9"], seed=2)
    assert coached["9"]["development_points"] != neutral["9"]["development_points"]
    injured = {key: dict(value) for key, value in base_state.items()}
    apply_match_development(
        injured, player_ids=["9"], won=False, drew=False, injury_ids=["9"], seed=2,
        coach_profile=coach, source_players=universe.players_by_id, game_date=date(1993, 10, 23),
    )
    assert injured["9"]["development_points"] < 0
