from backend.app.football9394.colombia_runtime import (
    COLOMBIA_APERTURA_GROUPS_1993,
    _rank_phase,
    simulate_colombia_1993,
)
from backend.app.football9394.registry import default_registry_9394
from backend.app.football9394.rules import COLOMBIA_PRIMERA_A_1993
from backend.app.football9394.standings import LeagueMatch9394


def test_colombia_1993_rules_and_source_binding():
    assert COLOMBIA_PRIMERA_A_1993.points_win == 2
    assert COLOMBIA_PRIMERA_A_1993.teams == 16
    assert COLOMBIA_PRIMERA_A_1993.rounds == 44
    assert default_registry_9394().resolve_source("league", 128).id == "col_primera_a_1993"


def test_colombia_apertura_groups_are_the_exact_16_mdb_clubs():
    assert len(COLOMBIA_APERTURA_GROUPS_1993) == 2
    assert all(len(group) == 8 for group in COLOMBIA_APERTURA_GROUPS_1993)
    assert len({team for group in COLOMBIA_APERTURA_GROUPS_1993 for team in group}) == 16


def test_colombia_final_quadrangular_uses_bonus_as_tiebreak_not_added_points():
    # A and B each earn two raw points. B has the better season bonus and must
    # rank first in final mode without the bonus changing raw/effective points.
    matches = (
        LeagueMatch9394("A", "B", 1, 0),
        LeagueMatch9394("B", "A", 1, 0),
    )
    table = _rank_phase(("A", "B"), matches, bonuses={"A": 0.25, "B": 1.0}, bonus_mode="tiebreak", seed=7)
    assert table[0].team_id == "B"
    assert table[0].raw_points == table[1].raw_points == 2
    assert table[0].effective_points == table[1].effective_points == 2


def test_colombia_full_runtime_closes_every_historical_stage():
    season = simulate_colombia_1993(seed_base=1289393)
    assert season.official_matches == 388
    assert season.bonus_allocation_matches == 4
    assert season.simulated_matches == 392
    assert all(len(group) == 8 and all(row.played == 14 for row in group) for group in season.apertura_groups)
    assert len(season.finalizacion_table) == 16
    assert all(row.played == 30 for row in season.finalizacion_table)
    assert all(row.played == 44 for row in season.aggregate_table)
    assert all(len(group) == 4 and all(row.played == 6 for row in group) for group in season.semifinal_groups)
    assert len(season.final_table) == 4 and all(row.played == 6 for row in season.final_table)
    assert season.champion_team_id != season.runner_up_team_id
    assert season.relegated_team_id in {row.team_id for row in season.aggregate_table}
    # The supplied MDB genuinely has only one player for each of these clubs;
    # certification may repair match sheets but must expose the debt explicitly.
    assert season.repaired_team_ids == ("2236", "2252")
    assert season.repaired_players == 20
