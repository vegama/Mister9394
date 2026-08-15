from backend.app.football9394.rules import (
    SPAIN_SEGUNDA_1993_94,
    SPAIN_SEGUNDA_B_G1_1993_94,
    SPAIN_SEGUNDA_B_G2_1993_94,
    SPAIN_SEGUNDA_B_G3_1993_94,
    SPAIN_SEGUNDA_B_G4_1993_94,
)
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit
from backend.app.football9394.spain_segundab_runtime import (
    _direct_relegations_with_forced_reserves,
    simulate_spain_segunda_b_1993_94,
)
from backend.app.football9394.standings import StandingRow9394


def _row(team_id: str, pos: int) -> StandingRow9394:
    return StandingRow9394(team_id, 38, 10, 10, 18, 40, 50, 30, position=pos)


def test_segunda_b_1993_94_rules_are_four_twenty_team_two_point_groups():
    for rules in (SPAIN_SEGUNDA_B_G1_1993_94, SPAIN_SEGUNDA_B_G2_1993_94, SPAIN_SEGUNDA_B_G3_1993_94, SPAIN_SEGUNDA_B_G4_1993_94):
        assert (rules.teams, rules.rounds) == (20, 38)
        assert (rules.points_win, rules.points_draw, rules.points_loss) == (2, 1, 0)
        assert rules.promotion_playoff_places == (1, 2, 3, 4)
        assert rules.relegation_playoff_places == (16,)
        assert rules.direct_relegation_places == (17, 18, 19, 20)
    assert SPAIN_SEGUNDA_1993_94.direct_relegation_places == (17, 18, 19, 20)


def test_forced_reserve_drop_consumes_one_sporting_relegation_slot():
    table = tuple(_row(f"t{pos}", pos) for pos in range(1, 21))
    dropped = _direct_relegations_with_forced_reserves(table, {"t8"}, slots=4)
    assert set(dropped) == {"t8", "t20", "t19", "t18"}
    assert "t17" not in dropped


def test_segunda_b_full_runtime_has_four_promotion_groups_and_permanence_series():
    season = simulate_spain_segunda_b_1993_94(seed_base=889394)
    assert season.regular_matches_segunda == 380
    assert season.regular_matches_segundab == 1520
    assert season.promotion_matches == 48
    assert len(season.promotion_groups) == 4
    assert len(season.promoted_to_segunda) == 4
    assert len(set(season.promoted_to_segunda)) == 4
    assert len(season.relegated_from_segunda) == 4
    assert len(season.permanence_matches) == 3
    for group in season.promotion_groups:
        assert group.matches == 12
        assert set(group.source_group_ids) == {3, 9, 10, 11}
        assert set(group.regular_positions) == {1, 2, 3, 4}
        assert all(row.played == 6 for row in group.table)
    # 4 direct sporting/forced slots per regional group plus exactly one loser
    # from the permanence tournament (unless a forced-drop overlap removes duplication).
    assert len(season.relegated_to_tercera) >= 17


def test_segunda_b_source_rows_and_ascenso_tournament_are_runtime_ready():
    for source_id in (3, 10, 11, 9):
        audit = source_rule_audit(CompetitionSourceRef9394("league", source_id, "x", "España"))
        assert audit.simulation_ready
        assert audit.status == "certified_complex"
        assert audit.format_id == "esp_segundab_pyramid_1993_94"
    tournament = source_rule_audit(CompetitionSourceRef9394("tournament", 88, "Ascenso a Segunda", "España"))
    assert tournament.simulation_ready
    assert tournament.format_id == "esp_segundab_pyramid_1993_94"
