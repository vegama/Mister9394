from backend.app.football9394.competition_runtime import source_league_runtime_info
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit


def test_scottish_source_row_is_certified_despite_wrong_mdb_turn_count():
    audit = source_rule_audit(CompetitionSourceRef9394('league', 38, 'Scottish Premier Division', 'Escocia'))
    assert audit.simulation_ready is True
    assert audit.ruleset_id == 'sco_premier_1993_94'
    assert any('MDB' in note for note in audit.notes)


def test_scottish_runtime_uses_44_historical_rounds_not_mdb_three_turns():
    info = source_league_runtime_info(38)
    assert info.team_count == 12
    assert info.rounds == 44
    assert info.matches == 264


def test_more_simple_european_leagues_are_runtime_certified():
    expected = {
        14: (20, 38, 380),   # France Division 1
        32: (18, 34, 306),   # Portugal Primeira
        102: (20, 38, 380),  # Italy Serie B
    }
    for source_id, triple in expected.items():
        audit = source_rule_audit(CompetitionSourceRef9394('league', source_id, 'x', None))
        assert audit.simulation_ready is True
        info = source_league_runtime_info(source_id)
        assert (info.team_count, info.rounds, info.matches) == triple
