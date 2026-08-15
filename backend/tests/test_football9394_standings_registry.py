import pytest

from backend.app.football9394 import (
    LeagueMatch9394,
    SPAIN_PRIMERA_1993_94,
    UnresolvedHistoricalRulesError,
    build_league_table,
    default_registry_9394,
)


def test_two_points_per_win_are_used_in_real_table_math():
    table = build_league_table(
        ("a", "b", "c"),
        (
            LeagueMatch9394("a", "b", 1, 0),
            LeagueMatch9394("a", "c", 0, 0),
            LeagueMatch9394("b", "c", 2, 0),
        ),
        SPAIN_PRIMERA_1993_94,
    )
    rows = {row.team_id: row for row in table}
    assert rows["a"].points == 3  # 2 win + 1 draw, never modern 4 points.
    assert rows["b"].points == 2
    assert rows["c"].points == 1


def test_head_to_head_precedes_overall_goal_difference():
    # A and B both finish on four points. B has a much better overall GD due to
    # the C match, but A won their direct encounter and must stay above B.
    table = build_league_table(
        ("a", "b", "c"),
        (
            LeagueMatch9394("a", "b", 1, 0),
            LeagueMatch9394("a", "c", 0, 0),
            LeagueMatch9394("b", "c", 8, 0),
            LeagueMatch9394("c", "a", 0, 1),
            LeagueMatch9394("c", "b", 0, 0),
            LeagueMatch9394("b", "a", 0, 0),
        ),
        SPAIN_PRIMERA_1993_94,
    )
    assert [row.team_id for row in table][:2] == ["a", "b"]


def test_fully_unresolved_tie_is_marked_for_playoff_not_broken_by_hidden_fallback():
    table = build_league_table(
        ("a", "b"),
        (
            LeagueMatch9394("a", "b", 1, 1),
            LeagueMatch9394("b", "a", 1, 1),
        ),
        SPAIN_PRIMERA_1993_94,
    )
    assert all(row.requires_playoff for row in table)


def test_registry_never_applies_generic_rules_to_unknown_mdb_competition():
    registry = default_registry_9394()
    registry.discover("Recopa")
    with pytest.raises(UnresolvedHistoricalRulesError, match="no se aplicará un fallback genérico"):
        registry.resolve("Recopa")
    assert "Recopa" in registry.unresolved_discovered


def test_registry_resolves_known_historical_alias():
    registry = default_registry_9394()
    assert registry.resolve("Primera Division") is SPAIN_PRIMERA_1993_94
