from backend.app.football9394.argentina_runtime import simulate_argentina_1993_94
from backend.app.football9394.source_rules import CompetitionSourceRef9394, source_rule_audit


def test_argentina_source_is_complex_and_runtime_ready():
    audit=source_rule_audit(CompetitionSourceRef9394('league',16,'Campeonato de Primera División','Argentina'))
    assert audit.simulation_ready is True
    assert audit.format_id=='arg_apertura_clausura_1993_94'


def test_argentina_runs_two_nineteen_match_tournaments_and_three_year_average():
    season=simulate_argentina_1993_94(seed_base=169394)
    assert season.matches==380
    assert len(season.apertura_table)==20 and len(season.clausura_table)==20
    assert all(row.played==19 for row in season.apertura_table)
    assert all(row.played==19 for row in season.clausura_table)
    assert season.apertura_champion_team_id
    assert season.clausura_champion_team_id
    assert len(season.relegation_averages)==20
    assert len(set(season.relegated_team_ids))==2
    # Promoted clubs use only seasons actually played in Primera.
    by_id={row.team_id:row for row in season.relegation_averages}
    assert by_id['117'].prior_matches==0  # Banfield
    assert by_id['2339'].prior_matches==0  # Gimnasia y Tiro
    assert by_id['112'].prior_matches==38  # Lanús
