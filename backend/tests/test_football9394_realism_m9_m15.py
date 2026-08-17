from __future__ import annotations

from datetime import date

import pytest

from backend.app.football9394.career_ai import squad_audit
from backend.app.football9394.career_club_status import update_after_season
from backend.app.football9394.foreign_rules import ForeignPlayerRule9394, validate_matchday_foreigners
from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.transfer_periods import transfer_period_status


def test_source_roles_are_exposed_as_specialist_positions_not_only_broad_groups():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2001,through_matchday=0)
    rows=career.squad()
    assert rows
    assert all(row.get('specialist_role',{}).get('name') for row in rows)
    assert all(row['position'] not in {'POR','DEF','MED','DEL'} for row in rows)
    assert any(row['specialist_role']['squad_slot'] in {'RB','LB','CB'} for row in rows)


def test_spain_source_foreign_rule_is_enforced_on_matchday_selection():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2002,through_matchday=0)
    rule=career._domestic_foreign_rule()
    assert rule is not None and rule.max_starting==3 and rule.max_squad==6
    domestic={'nationality_id':11}
    foreign={'nationality_id':1}
    issues=validate_matchday_foreigners([domestic]*7+[foreign]*4,[],ForeignPlayerRule9394('league',1,'Primera',11,3,6))
    assert issues and 'máximo 3 extranjeros' in issues[0]
    assert career.selection_snapshot()['foreign_issues']==[]


def test_era_registration_periods_remain_frozen_without_later_spanish_winter_market():
    summer=transfer_period_status(date(1993,7,15),country_id=11,season='1993-94')
    late=transfer_period_status(date(1994,3,31),country_id=11,season='1993-94')
    run_in=transfer_period_status(date(1994,4,1),country_id=11,season='1993-94')
    winter_open=transfer_period_status(date(1994,12,15),country_id=11,season='1994-95')
    winter_last=transfer_period_status(date(1995,1,15),country_id=11,season='1994-95')
    winter_closed=transfer_period_status(date(1995,1,16),country_id=11,season='1994-95')
    assert summer.open and summer.activity=='high'
    assert late.open and not run_in.open
    assert winter_open.open and winter_open.phase=='in_season'
    assert winter_last.open and winter_last.phase=='in_season'
    assert winter_closed.open and winter_closed.phase=='in_season'


def test_preseason_is_real_calendar_time_and_continue_uses_short_pulses():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2003,through_matchday=0)
    snap=career.snapshot()
    assert snap['game_date']=='1993-07-01' and snap['preseason']['active']
    calendar=career.career_calendar()
    friendlies=[row for row in calendar if row.get('fixture_type')=='friendly']
    assert len(friendlies)==4 and all(row.get('generated') for row in friendlies)
    result=career.advance_until_event(max_days=14)
    assert result['advanced_days']<=3 and result['pace']=='short'


def test_initial_ai_squads_are_audited_by_compatible_specialist_jobs():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2004,through_matchday=0)
    audits=[squad_audit(career._career_players_by_team.get(tid,[]),career.state['player_development']) for tid in career._active_club_ids()]
    # Specialist roles should describe the historical squads rather than falsely
    # claiming nearly every club is broken because it lacks every possible role.
    ratio=sum(1 for row in audits if row['coverage_ok'])/len(audits)
    assert ratio > .80
    assert all((row['primary_need'] is None) == row['coverage_ok'] for row in audits)


def test_club_hierarchy_moves_gradually_but_can_change_over_multiple_seasons():
    state={'club_status':{'1':{'score':50.0,'tier':'MODESTO','trend':0.0,'history':[]}}}
    finances={'1':{'cash':100_000_000,'debt':0}}
    before=state['club_status']['1']['score']
    for year in range(1994,2000):
        changes=update_after_season(
            state=state,season=f'{year-1}-{str(year)[-2:]}',
            tables={1:[{'team_id':1,'position':1},{'team_id':2,'position':2},{'team_id':3,'position':3},{'team_id':4,'position':4}]},
            honours=[{'team_id':1}],qualifiers={'1':[1]},team_league_getter=lambda tid:1,
            finances=finances,squad_strength_getter=lambda tid:82.0,
        )
        assert abs(changes[0]['change'])<=6.0
    assert state['club_status']['1']['score']>before+10
    assert len(state['club_status']['1']['history'])==6


def test_every_initial_active_club_can_name_a_competition_legal_ai_match_squad():
    """The foreign quota must be executable, not merely shown in the UI."""
    from backend.app.football9394.foreign_rules import competition_foreign_rule, is_foreign_player
    from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
    from backend.app.football9394.team_builder import build_snapshot_team_sheet

    universe=default_runtime_snapshot();checked=0
    for source_id, league in universe.leagues_by_id.items():
        if not league.get('admitted'):
            continue
        for team in universe.teams_by_league.get(int(source_id),[]):
            team_id=int(team['source_id'])
            rule=competition_foreign_rule(universe,kind='league',source_id=int(source_id),team_id=team_id)
            predicate=lambda player,r=rule:is_foreign_player(
                player,home_country_id=r.home_country_id,continental=r.continental,
                domestic_equivalent_country_ids=r.domestic_equivalent_country_ids,
            )
            sheet=build_snapshot_team_sheet(
                universe,team_id,foreign_predicate=predicate,
                max_foreign_starters=rule.max_starting,max_foreign_squad=rule.max_squad,
                allow_emergency_outfield_goalkeeper=True,
            )
            assert len(sheet.starters)==11
            checked+=1
    # Historical league activation has expanded beyond the earlier 374-club checkpoint.
    assert checked==444


def test_apsl_cross_border_quota_uses_club_association_not_us_for_canadian_clubs():
    from backend.app.football9394.foreign_rules import competition_foreign_rule
    from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
    universe=default_runtime_snapshot()
    montreal=competition_foreign_rule(universe,kind='league',source_id=120,team_id=840)
    los_angeles=competition_foreign_rule(universe,kind='league',source_id=120,team_id=734)
    assert montreal.home_country_id==22 and montreal.max_starting==7 and montreal.max_squad==7
    assert los_angeles.home_country_id==38 and los_angeles.max_starting==7 and los_angeles.max_squad==7


def test_ai_can_use_real_outfielder_as_emergency_goalkeeper_when_all_natural_gks_are_unavailable():
    from backend.app.football9394.position_roles import role_for_player
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2005,through_matchday=0)
    ai_team=next(tid for tid in career._active_club_ids() if tid!=16 and len(career._career_players_by_team.get(tid,[]))>=18)
    natural=[p for p in career._career_players_by_team[ai_team] if role_for_player(p).squad_slot=='GK']
    assert natural
    for player in natural:
        career.state['player_development'].setdefault(str(int(player['source_id'])),{})['injury_days']=30
    career._rebuild_rosters()
    sheet=career._sheet(ai_team)
    assert len(sheet.starters)==11
    keeper=next(p for p in sheet.starters if p.position=='GK')
    assert keeper.goalkeeping<=10


def test_foreign_quota_assignment_rebuilds_whole_xi_without_using_reserve_keeper_outfield():
    """A legal XI must be found even when a greedy local swap would get stuck.

    This mirrors the long-career J.League failure: three domestic goalkeepers,
    seven domestic outfielders and six foreigners.  Eight domestic starters are
    enough for a 3-foreigner limit, but only if the whole XI is reassigned.
    """
    from backend.app.football9394.position_roles import (
        assign_players_to_formation_with_foreign_limit,
        role_for_player,
    )

    rows=[]
    pid=1
    # Three domestic keepers: only one may ever occupy the GK formation slot.
    for overall in (82,70,65):
        rows.append({'source_id':pid,'primary_role':0,'overall':overall,'nationality_id':1});pid+=1
    # Seven domestic outfielders, deliberately not a perfect 4-4-2 shape.
    for role,overall in ((3,74),(4,72),(5,69),(13,73),(17,75),(17,70),(7,68)):
        rows.append({'source_id':pid,'primary_role':role,'overall':overall,'nationality_id':1});pid+=1
    # Six stronger foreigners tempt the unconstrained assignment.
    for role,overall in ((1,86),(2,85),(3,84),(9,83),(10,82),(17,88)):
        rows.append({'source_id':pid,'primary_role':role,'overall':overall,'nationality_id':2});pid+=1

    assignment=assign_players_to_formation_with_foreign_limit(
        rows,'4-4-2',foreign_predicate=lambda p:p['nationality_id']!=1,max_foreign=3,
    )
    assert len(assignment)==11
    assert sum(1 for item in assignment if item['player']['nationality_id']!=1)<=3
    assert sum(1 for item in assignment if item['slot']=='GK')==1
    assert role_for_player(next(item['player'] for item in assignment if item['slot']=='GK')).squad_slot=='GK'
    assert all(role_for_player(item['player']).squad_slot!='GK' for item in assignment if item['slot']!='GK')


def test_senior_squad_floor_is_eighteen_and_is_not_match_xi_size():
    from backend.app.football9394.career_ai import squad_audit
    from backend.app.football9394.position_roles import (
        MINIMUM_SENIOR_SQUAD_SIZE_9394,
        TARGET_SENIOR_SQUAD_SIZE_9394,
    )
    assert MINIMUM_SENIOR_SQUAD_SIZE_9394 == 18
    assert TARGET_SENIOR_SQUAD_SIZE_9394 == 22
    rows=[]
    # A legal-looking 17-man group can still field an XI, but it is not a
    # healthy senior squad.  The audit must keep those concepts separate.
    roles=[0,0,1,2,3,4,5,6,7,7,9,13,17,17,10,14,8]
    for index,role in enumerate(roles,1):
        rows.append({'source_id':index,'primary_role':role,'overall':65})
    audit=squad_audit(rows,{})
    assert audit['squad_size']==17
    assert audit['minimum_squad_size']==18
    assert audit['depth_shortage']==1
    assert audit['squad_size_ok'] is False
    assert audit['coverage_ok'] is False


def test_ai_summer_repair_builds_to_eighteen_not_merely_eleven():
    from datetime import date
    from backend.app.football9394.career_ai import ensure_ai_squad_coverage
    from backend.app.football9394.position_roles import MINIMUM_SENIOR_SQUAD_SIZE_9394, role_for_player
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2011,through_matchday=0)
    ai_team=next(tid for tid in career._active_club_ids() if tid!=16 and len(career._career_players_by_team.get(tid,[]))>=18)
    original=list(career._career_players_by_team[ai_team])
    # Keep a balanced but intentionally undersized group.
    keep=original[:12]
    assert any(role_for_player(p).squad_slot=='GK' for p in original)
    if not any(role_for_player(p).squad_slot=='GK' for p in keep):
        keeper=next(p for p in original if role_for_player(p).squad_slot=='GK')
        keep[-1]=keeper
    removed=[p for p in original if p not in keep]
    career._career_players_by_team[ai_team]=keep
    career._career_players_by_team.setdefault(0,[]).extend(removed)
    for p in removed:
        career.state['player_team_overrides'][str(int(p['source_id']))]=0
    actions=ensure_ai_squad_coverage(
        current_date=date(1994,7,1),controlled_team_id=16,eligible_team_ids=[ai_team],
        players_by_team=career._career_players_by_team,development=career.state['player_development'],
        club_finances=career.state['club_finances'],player_team_overrides=career.state['player_team_overrides'],
        contract_overrides=career.state['contract_overrides'],seed=2011,max_signings=40,
    )
    assert actions
    assert len(career._career_players_by_team[ai_team])>=MINIMUM_SENIOR_SQUAD_SIZE_9394


def test_user_cannot_accept_sale_that_breaks_senior_squad_floor():
    from backend.app.football9394.position_roles import MINIMUM_SENIOR_SQUAD_SIZE_9394
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2012,through_matchday=0)
    controlled=16
    roster=career._career_players_by_team[controlled]
    # Narrow the test state to the operational floor while keeping real players.
    for player in roster[MINIMUM_SENIOR_SQUAD_SIZE_9394:]:
        career.state['player_team_overrides'][str(int(player['source_id']))]=0
    career._rebuild_rosters()
    assert len(career._career_players_by_team[controlled])==MINIMUM_SENIOR_SQUAD_SIZE_9394
    player=career._career_players_by_team[controlled][-1]
    buyer=next(tid for tid in career._active_club_ids() if tid!=controlled and int(career.state['club_finances'][str(tid)].get('cash') or 0)>0)
    pid=int(player['source_id'])
    offer={'id':'floor-test','date':career.state['current_date'],'expires_on':'1994-12-31','player_id':pid,'buyer_team_id':buyer,'buyer_team_name':'Comprador','fee':1,'status':'open'}
    career.state['incoming_transfer_offers'].append(offer)
    with pytest.raises(ValueError,match='18 jugadores'):
        career.accept_incoming_transfer_offer('floor-test')


def test_ai_renewal_queue_is_fair_to_high_id_active_clubs():
    """A global renewal cap must not starve late/high source IDs.

    Regression for the long-career Haarlem failure: inactive snapshot clubs used
    to consume queue positions before some active clubs were even considered.
    """
    from backend.app.football9394.career_ai import renew_ai_contracts

    def player(pid:int, role:int=0, overall:int=68):
        return {
            'source_id':pid,'primary_role':role,'overall':overall,
            'name':f'P{pid}','surname':'TEST','nationality_id':11,
        }

    # Both active clubs have an expiring natural goalkeeper and must each get
    # one negotiation despite a deliberately huge source/team ID gap.
    players_by_team={
        10:[player(101,0),player(102,3),player(103,17)],
        9999:[player(99991,0),player(99992,3),player(99993,17)],
        # Inactive clubs that must not consume the active renewal queue.
        20:[player(201,0)],30:[player(301,0)],40:[player(401,0)],
    }
    overrides={}
    for tid in (10,9999):
        for row in players_by_team[tid]:
            overrides[str(row['source_id'])]={
                'start':'1993','end':'1994','end_year':1994,'salary':500_000,'career_inferred':True,
            }
    actions=renew_ai_contracts(
        current_date=date(1994,1,1),controlled_team_id=1,players_by_team=players_by_team,
        development={},contract_overrides=overrides,seed=9394,max_renewals=2,eligible_team_ids=[10,9999],
    )
    assert {row['team_id'] for row in actions}=={10,9999}


def test_ai_squad_target_is_a_depth_target_not_the_eighteen_player_floor():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2013,through_matchday=0)
    targets=[career._target_ai_squad_size(tid) for tid in career._active_club_ids() if tid!=16]
    assert min(targets)>=20
    assert max(targets)>=23
    assert all(target>18 for target in targets)


def test_economy_compresses_source_scale_extremes_without_erasing_club_size():
    from backend.app.football9394.career_economy import monthly_commercial_income
    small={'members':2_000,'budget':8_000_000}
    giant={'members':100_000,'budget':900_000_000}
    small_income=monthly_commercial_income(small,stature_score=35)
    giant_income=monthly_commercial_income(giant,stature_score=93)
    assert giant_income>small_income
    # Source fields come from heterogeneous national conventions.  A 50x
    # membership difference must not become a 50x monthly-income difference.
    assert giant_income < small_income*15


def test_club_hierarchy_is_relative_and_elite_growth_has_diminishing_returns():
    state={'club_status':{
        '1':{'score':94.0,'initial_score':94.0,'tier':'GIGANTE','trend':0.0,'history':[]},
        '2':{'score':60.0,'initial_score':60.0,'tier':'MEDIO','trend':0.0,'history':[]},
        '3':{'score':50.0,'initial_score':50.0,'tier':'MODESTO','trend':0.0,'history':[]},
    }}
    tables={
        1:[{'team_id':1,'position':1},{'team_id':3,'position':2}],
        2:[{'team_id':2,'position':1},{'team_id':99,'position':2}],
    }
    before=sum(row['score'] for row in state['club_status'].values())
    changes=update_after_season(
        state=state,season='1993-94',tables=tables,
        honours=[{'team_id':1},{'team_id':2}],qualifiers={'1':[1,2]},
        team_league_getter=lambda tid:1 if tid in {1,3} else 2,
        finances={str(tid):{'cash':100_000_000,'debt':0} for tid in (1,2,3)},
        squad_strength_getter=lambda tid:82.0 if tid in {1,2} else 60.0,
    )
    by_id={row['team_id']:row for row in changes}
    # The established giant can still improve, but the same elite season has
    # much more transformational value for a medium club.
    assert 0 < by_id[1]['change'] < by_id[2]['change']
    # The population should not manufacture large amounts of prestige globally.
    after=sum(row['score'] for row in state['club_status'].values())
    assert abs(after-before) < 1.5


def test_injury_to_selected_player_becomes_a_manager_decision_not_a_silent_auto_change():
    career=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=2014,through_matchday=0)
    selected=career.selection_snapshot()
    victim=selected['starter_ids'][1]
    career.state['player_development'].setdefault(str(victim),{})['injury_days']=12
    career._rebuild_rosters()
    assert career.selection_snapshot()['valid'] is False
    pending=career.manager_dashboard()['pending_decisions']
    assert any(row['kind']=='lineup' for row in pending)
    # Once the manager resolves it, the generated XI is legal again and can be
    # used without silently violating foreign-player or positional rules.
    career.state['selection']=career._safe_auto_selection()
    assert career.selection_snapshot()['valid'] is True


def test_lower_division_success_builds_stature_slower_than_top_flight_success():
    """A lower-tier title is meaningful, but not a shortcut to global-giant status."""
    def run(level:int)->float:
        state={'club_status':{
            '1':{'score':55.0,'tier':'MEDIO','trend':0.0,'history':[],'initial_score':55.0},
            '2':{'score':55.0,'tier':'MEDIO','trend':0.0,'history':[],'initial_score':55.0},
            '3':{'score':55.0,'tier':'MEDIO','trend':0.0,'history':[],'initial_score':55.0},
            '4':{'score':55.0,'tier':'MEDIO','trend':0.0,'history':[],'initial_score':55.0},
        }}
        update_after_season(
            state=state,season='1993-94',
            tables={99:[
                {'team_id':1,'position':1},{'team_id':2,'position':2},
                {'team_id':3,'position':3},{'team_id':4,'position':4},
            ]},
            honours=[{'team_id':1,'competition_kind':'league','source_id':99}],
            qualifiers={},team_league_getter=lambda tid:99,
            league_level_getter=lambda lid:level,
            finances={str(i):{'cash':1_000_000,'debt':0} for i in range(1,5)},
            squad_strength_getter=lambda tid:68.0,
        )
        return float(state['club_status']['1']['trend'])
    top=run(1);third=run(3)
    assert top>third
    assert third < 1.5
