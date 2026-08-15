from backend.app.football9394.spain_segunda_b_runtime import simulate_spain_segunda_b_1993_94
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit


def test_all_four_segunda_b_groups_and_promotion_source_are_certified_together():
    for source_id in (3,10,11,9):
        audit=source_rule_audit(CompetitionSourceRef9394('league',source_id,'x','España'))
        assert audit.simulation_ready and audit.format_id=='esp_segundab_pyramid_1993_94'
    promo=source_rule_audit(CompetitionSourceRef9394('tournament',88,'Ascenso a Segunda','España'))
    assert promo.simulation_ready and promo.format_id=='esp_segundab_pyramid_1993_94'


def test_segunda_b_full_1993_94_runtime_closes_regular_promotion_and_survival():
    season=simulate_spain_segunda_b_1993_94(seed_base=8839394)
    assert len(season.regular_groups)==4
    assert season.regular_matches==4*380
    assert all(len(g.table)==20 and len(g.promotion_qualifiers)==4 and len(g.direct_relegated)==4 for g in season.regular_groups)
    assert len(season.promotion_groups)==4
    assert season.promotion_matches==48
    assert all(g.matches==12 and len(g.team_ids)==4 for g in season.promotion_groups)
    assert len(set(season.promoted_team_ids))==4
    assert season.survival_matches==3
    assert len(season.relegated_team_ids)==17
    assert season.survival.relegated_team_id in season.relegated_team_ids
