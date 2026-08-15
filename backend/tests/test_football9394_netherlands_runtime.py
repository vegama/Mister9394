from backend.app.football9394.netherlands_runtime import simulate_netherlands_1993_94
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit


def test_dutch_divisions_are_certified_as_one_coupled_format():
    for source_id in (31, 54):
        audit = source_rule_audit(CompetitionSourceRef9394('league', source_id, 'x', 'Países Bajos'))
        assert audit.simulation_ready is True
        assert audit.format_id == 'ned_nacompetitie_1993_94'


def test_netherlands_1993_94_runs_both_leagues_and_two_four_team_playoff_groups():
    season = simulate_netherlands_1993_94(seed_base=319394)
    assert season.eredivisie_matches == 306
    assert season.eerste_matches == 306
    assert season.playoff_matches == 24
    assert len(season.eredivisie_table) == 18
    assert len(season.eerste_table) == 18
    assert len(season.period_winners) == 4
    assert len(set(season.period_winners)) == 4
    assert len(season.playoff_qualifiers_eerste) == 6
    assert season.direct_promoted_team_id not in season.playoff_qualifiers_eerste
    assert all(len(group.team_ids) == 4 and group.matches == 12 for group in season.playoff_groups)
    assert 1 <= len(season.promoted_team_ids) <= 3
    assert len(season.promoted_team_ids) == len(season.relegated_team_ids)
