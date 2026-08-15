from dataclasses import replace

from backend.app.football9394.rules import ITALY_SERIE_A_1993_94, ITALY_SERIE_B_1993_94
from backend.app.football9394.season_decisions import identify_decisive_playoff, season_end_decisive_playoffs
from backend.app.football9394.standings import StandingRow9394


def row(team, pos, pts):
    return StandingRow9394(team, 38, 0, 0, 0, 0, 0, pts, position=pos)


def test_italian_midtable_tie_does_not_invent_a_playoff():
    table = tuple(row(str(i), i, 50-i) for i in range(1,19))
    assert identify_decisive_playoff(table, ITALY_SERIE_A_1993_94, context="relegation", cutoff_position=14) is None


def test_serie_a_equal_points_across_relegation_cutoff_requires_spareggio():
    table = [row(str(i), i, 60-i) for i in range(1,19)]
    table[13] = row("safe",14,30)
    table[14] = row("drop",15,30)
    need = identify_decisive_playoff(table, ITALY_SERIE_A_1993_94, context="relegation", cutoff_position=14)
    assert need is not None
    assert (need.upper_team_id, need.lower_team_id, need.points) == ("safe","drop",30)


def test_serie_b_checks_both_promotion_and_relegation_boundaries():
    table = [row(str(i), i, 70-i) for i in range(1,21)]
    table[3] = row("prom-a",4,50); table[4] = row("prom-b",5,50)
    table[15] = row("safe",16,25); table[16] = row("drop",17,25)
    needs = season_end_decisive_playoffs(table, ITALY_SERIE_B_1993_94)
    assert [(n.context,n.cutoff_position) for n in needs] == [("promotion",4),("relegation",16)]


def test_resolver_swaps_cutoff_positions_when_lower_club_wins(monkeypatch):
    from backend.app.football9394.season_decisions import (
        DecisivePlayoffResult9394, resolve_season_end_decisive_playoffs,
    )
    from backend.app.football9394.match_engine import FootballMatchEngine9394
    from backend.tests.test_football9394_match_engine import sheet
    table = [row(str(i), i, 70-i) for i in range(1,21)]
    table[3] = row('prom-a',4,50); table[4] = row('prom-b',5,50)
    sheets = {r.team_id: sheet(r.team_id, 70) for r in table}
    def fake(need, *_args, **_kwargs):
        return DecisivePlayoffResult9394(need, need.lower_team_id, need.upper_team_id, (0,1), 'regulation')
    monkeypatch.setattr('backend.app.football9394.season_decisions.play_neutral_decisive_playoff', fake)
    resolved = resolve_season_end_decisive_playoffs(table, ITALY_SERIE_B_1993_94, sheets, FootballMatchEngine9394())
    assert resolved.table[3].team_id == 'prom-b'
    assert resolved.table[4].team_id == 'prom-a'
    assert resolved.table[3].position == 4
    assert len(resolved.playoffs) == 1
