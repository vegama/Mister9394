from __future__ import annotations

from datetime import date

from backend.app.football9394.career_tournaments import process_daily_tournaments
from backend.app.football9394.domestic_cups import DOMESTIC_CUPS_9394
from backend.app.football9394.foreign_rules import (
    competition_foreign_rule,
    is_foreign_player,
    validate_matchday_foreigners,
)
from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.team_builder import build_snapshot_team_sheet


def _table_for(career: ManagerCareerRuntime9394, league_id: int) -> list[dict]:
    return [
        {"team_id": int(team["source_id"]), "position": pos, "points": max(0, 90-pos)}
        for pos, team in enumerate(career._teams_for_league(league_id), start=1)
    ]


def test_v114_career_catalog_exposes_twelve_domestic_cups_without_source_pollution():
    universe=default_runtime_snapshot()
    source_ids={(row["kind"],int(row["source_id"])) for row in universe.competitions()}
    career_ids={(row["kind"],int(row["source_id"])) for row in universe.career_competitions()}
    assert len(DOMESTIC_CUPS_9394)==12
    assert ("tournament",3) in source_ids
    assert all(("tournament",spec.source_id) in career_ids for spec in DOMESTIC_CUPS_9394)
    assert all(("tournament",spec.source_id) not in source_ids for spec in DOMESTIC_CUPS_9394 if spec.source_id!=3)


def test_v114_all_domestic_cups_finish_with_champion_runner_up_and_real_participants():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=114,through_matchday=0)
    process_daily_tournaments(career,date(1994,6,30),bootstrap=True)
    real_ids={int(team["source_id"]) for team in career.universe.payload.get("teams",[]) if not team.get("market_container")}
    for spec in DOMESTIC_CUPS_9394:
        cup=career.state["daily_tournaments"][str(spec.source_id)]
        assert cup["completed"] is True, spec.name
        assert int(cup["champion_team_id"]) in real_ids, spec.name
        assert int(cup["runner_up_team_id"]) in real_ids, spec.name
        assert cup["champion_team_id"] != cup["runner_up_team_id"]


def test_v114_recopa_uses_cup_runner_up_when_winner_has_european_cup_place_and_has_no_duplicates():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=115,through_matchday=0)
    process_daily_tournaments(career,date(1994,6,30),bootstrap=True)
    tables={lid:_table_for(career,lid) for lid in (14,31,13,4,5,32,1,38)}
    spanish_champion=int(tables[1][0]["team_id"])
    spanish_runner=int(tables[1][4]["team_id"])
    copa=career.state["daily_tournaments"]["3"]
    copa["champion_team_id"]=str(spanish_champion);copa["runner_up_team_id"]=str(spanish_runner)
    qualifiers=career._continental_qualifiers(tables)
    assert spanish_champion in qualifiers["1"]
    assert spanish_champion not in qualifiers["90"]
    assert spanish_runner in qualifiers["90"]
    assert {key:(len(value),len(set(value))) for key,value in qualifiers.items()}=={"1":(8,8),"2":(16,16),"90":(32,32)}
    assert not (set(qualifiers["1"]) & set(qualifiers["2"]))
    assert not (set(qualifiers["1"]) & set(qualifiers["90"]))
    assert not (set(qualifiers["2"]) & set(qualifiers["90"]))


def test_v114_spanish_primera_is_four_named_three_on_pitch_and_copa_inherits_tier():
    universe=default_runtime_snapshot()
    primera=competition_foreign_rule(universe,kind="league",source_id=1,team_id=16)
    segunda=competition_foreign_rule(universe,kind="league",source_id=2,team_id=26)
    copa_primera=competition_foreign_rule(universe,kind="tournament",source_id=3,team_id=16)
    copa_segunda=competition_foreign_rule(universe,kind="tournament",source_id=3,team_id=26)
    assert (primera.max_starting,primera.max_squad)==(3,4)
    assert (segunda.max_starting,segunda.max_squad)==(3,3)
    assert (copa_primera.max_starting,copa_primera.max_squad)==(3,4)
    assert (copa_segunda.max_starting,copa_segunda.max_squad)==(3,3)

    predicate=lambda p:is_foreign_player(p,home_country_id=primera.home_country_id,continental=False,domestic_equivalent_country_ids=primera.domestic_equivalent_country_ids)
    sheet=build_snapshot_team_sheet(universe,16,foreign_predicate=predicate,max_foreign_starters=3,max_foreign_squad=4)
    starters=[universe.players_by_id[int(p.id)] for p in sheet.starters]
    bench=[universe.players_by_id[int(p.id)] for p in sheet.bench]
    assert sum(predicate(p) for p in starters)==3
    assert sum(predicate(p) for p in [*starters,*bench])==4
    assert validate_matchday_foreigners(starters,bench,primera)==[]
    fourth=next(p for p in bench if predicate(p))
    domestic=next(p for p in starters if not predicate(p))
    illegal=[fourth if int(p["source_id"])==int(domestic["source_id"]) else p for p in starters]
    assert any("máximo 3 extranjeros en el once" in issue for issue in validate_matchday_foreigners(illegal,[],primera))


def test_v114_scotland_domestic_has_no_false_numeric_quota_and_other_cup_detail_does_not_inherit_spain():
    universe=default_runtime_snapshot()
    league=competition_foreign_rule(universe,kind="league",source_id=38,team_id=492)
    cup=competition_foreign_rule(universe,kind="tournament",source_id=940043,team_id=492)
    fa_opened_from_spanish_team=competition_foreign_rule(universe,kind="tournament",source_id=940006,team_id=16)
    assert (league.max_starting,league.max_squad)==(None,None)
    assert (cup.max_starting,cup.max_squad)==(None,None)
    assert fa_opened_from_spanish_team.home_country_id==6
    assert fa_opened_from_spanish_team.name=="FA Cup"


def test_v114_live_manual_and_automatic_substitutions_keep_spanish_three_on_pitch():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=55114,through_matchday=0)
    career.state["preseason_friendlies"]=[]
    fixture=career.next_fixture();career.state["current_date"]=fixture["date"]
    selection=career.selection_snapshot();rule=career._domestic_foreign_rule(16)
    predicate=lambda p:is_foreign_player(p,home_country_id=rule.home_country_id,continental=False,domestic_equivalent_country_ids=rule.domestic_equivalent_country_ids)
    foreign_starters=[pid for pid in selection["starter_ids"] if predicate(career._player_source(pid))]
    foreign_bench=[pid for pid in selection["bench_ids"] if predicate(career._player_source(pid))]
    domestic_starters=[pid for pid in selection["starter_ids"] if not predicate(career._player_source(pid))]
    assert len(foreign_starters)==3 and len(foreign_bench)==1
    career.start_live_match()
    try:
        career.substitute_live_match(domestic_starters[0],foreign_bench[0])
    except ValueError as exc:
        assert "máximo 3 extranjeros" in str(exc)
    else:
        raise AssertionError("el cuarto extranjero no puede sustituir a un nacional con tres ya en el campo")
    # The same fourth foreigner is legal when replacing one of the three.
    snap=career.substitute_live_match(foreign_starters[0],foreign_bench[0])
    controlled_ids=[int(row["id"]) for row in snap["controlled_on_pitch"]]
    assert sum(predicate(career._player_source(pid)) for pid in controlled_ids)<=3

    # Instant Result / AI changes use the same validator.  A fresh match is used
    # so auto-control starts from the canonical 3+1 Spanish match squad.
    auto=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=120,through_matchday=0)
    auto.state["preseason_friendlies"]=[]
    auto_fixture=auto.next_fixture();auto.state["current_date"]=auto_fixture["date"]
    auto.start_live_match();report=auto.simulate_live_match()["match"]
    final_ids=[int(row["id"]) for row in report["controlled_on_pitch"]]
    auto_rule=auto._domestic_foreign_rule(16)
    auto_pred=lambda p:is_foreign_player(p,home_country_id=auto_rule.home_country_id,continental=False,domestic_equivalent_country_ids=auto_rule.domestic_equivalent_country_ids)
    assert sum(auto_pred(auto._player_source(pid)) for pid in final_ids)<=3
