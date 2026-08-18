from backend.app.football9394 import LAWS_1993_94, SPAIN_PRIMERA_1993_94, SPAIN_SEGUNDA_1993_94
from backend.app.football9394 import rules as rules_module
from backend.app.football9394.pyramid import compute_relegations, reserve_forced_drop_required, select_eligible_promotions


def test_global_1993_94_laws_are_not_modern_defaults():
    assert LAWS_1993_94.players_per_team == 11
    assert LAWS_1993_94.max_used_substitutes == 2
    assert LAWS_1993_94.max_named_substitutes == 5
    assert LAWS_1993_94.halftime_max_minutes == 5
    assert LAWS_1993_94.backpass_to_goalkeeper_hands_allowed is False
    assert LAWS_1993_94.goalkeeper_max_steps_in_control == 4


def test_spain_1993_94_uses_two_points_and_historical_promotion_places():
    assert SPAIN_PRIMERA_1993_94.points_win == 2
    assert SPAIN_PRIMERA_1993_94.direct_relegation_places == (19, 20)
    assert SPAIN_PRIMERA_1993_94.relegation_playoff_places == (17, 18)
    assert SPAIN_SEGUNDA_1993_94.points_win == 2
    assert SPAIN_SEGUNDA_1993_94.direct_promotion_places == (1, 2)
    assert SPAIN_SEGUNDA_1993_94.promotion_playoff_places == (3, 4)



def test_all_runtime_leagues_use_mister_two_one_zero_scoring():
    league_rules = [
        value for value in vars(rules_module).values()
        if isinstance(value, rules_module.CompetitionRules9394) and value.competition_type == "league"
    ]
    assert league_rules
    assert all((rule.points_win, rule.points_draw, rule.points_loss) == (2, 1, 0) for rule in league_rules)

def test_forced_reserve_drop_saves_one_sporting_relegation_place():
    # 20-team table.  Normally 17-20 would go down in this illustrative tier.
    ranking = tuple(f"club_{place}" for place in range(1, 21))
    relegated = compute_relegations(ranking, sporting_relegation_slots=4, forced_relegation_ids=("club_8",))
    assert relegated == ("club_8", "club_18", "club_19", "club_20")
    assert "club_17" not in relegated


def test_forced_reserve_already_in_drop_zone_does_not_count_twice():
    ranking = tuple(f"club_{place}" for place in range(1, 21))
    relegated = compute_relegations(ranking, sporting_relegation_slots=4, forced_relegation_ids=("club_19",))
    assert relegated == ("club_17", "club_18", "club_19", "club_20")


def test_reserve_ineligible_for_promotion_is_skipped():
    ranking = ("reserve_a", "club_b", "club_c", "club_d")
    assert select_eligible_promotions(ranking, 2, {"reserve_a"}) == ("club_b", "club_c")


def test_parent_drop_into_reserve_division_forces_reserve_down():
    assert reserve_forced_drop_required(parent_target_division="segunda", reserve_current_division="segunda")
    assert not reserve_forced_drop_required(parent_target_division="primera", reserve_current_division="segunda")
