from datetime import date

from backend.app.football9394.career_ai import renew_ai_contracts, run_ai_transfer_window


def _p(pid,overall=70,slot='CM'):
    role={'GK':0,'RB':1,'LB':2,'CB':3,'CM':7,'RM':9,'LM':13,'ST':17}[slot]
    broad={'GK':'POR','RB':'DEF','LB':'DEF','CB':'DEF','CM':'MED','RM':'MED','LM':'MED','ST':'DEL'}[slot]
    return {'source_id':pid,'overall':overall,'primary_role':role,'broad_position':broad,'nationality_id':11}


def _balanced(base:int, *, strikers:int=3):
    rows=[]; pid=base
    for slot,count in [('GK',2),('RB',1),('LB',1),('CB',3),('CM',4),('RM',2),('LM',2),('ST',strikers)]:
        for _ in range(count):
            rows.append(_p(pid,68+(pid%5),slot)); pid+=1
    return rows


def test_ai_renews_expiring_useful_player():
    players={1:[_p(1,82),_p(2,60)],2:[_p(3,75)]}
    overrides={'1':{'end':'1994','end_year':1994,'salary':1_000_000}}
    actions=renew_ai_contracts(current_date=date(1994,2,1),controlled_team_id=2,players_by_team=players,development={},contract_overrides=overrides,seed=5)
    assert any(a['player_id']==1 for a in actions)
    assert overrides['1']['end_year']>1994


def test_ai_renewal_protects_essential_goalkeeper_before_rating():
    players={1:_balanced(10),2:_balanced(100)}
    # both keepers are expiring and deliberately weak; positional survival must
    # outrank their rating during the Jan-Jun renewal sequence.
    keepers=[p for p in players[1] if p['primary_role']==0]
    for p in keepers: p['overall']=45
    overrides={str(p['source_id']):{'end':'1994','end_year':1994,'salary':200_000} for p in keepers}
    actions=renew_ai_contracts(current_date=date(1994,1,1),controlled_team_id=2,players_by_team=players,development={},contract_overrides=overrides,seed=6)
    assert actions and actions[0]['player_id'] in {p['source_id'] for p in keepers}


def _market_world():
    # Buyer lacks strikers, seller has spare strikers and remains structurally
    # sound after one sale.  This reflects the need-driven M13 market contract.
    buyer=_balanced(1,strikers=1)
    seller=_balanced(100,strikers=5)
    controlled=_balanced(200,strikers=3)
    players={1:buyer,2:seller,3:controlled}
    finances={str(i):{'cash':50_000_000,'transfer_spend':0,'transfer_income':0} for i in players}
    return players,finances


def test_ai_transfer_changes_roster_owner_and_both_club_cash():
    players,finances=_market_world(); overrides={}; contracts={}
    actions=run_ai_transfer_window(current_date=date(1994,1,1),controlled_team_id=3,eligible_team_ids=[1,2,3],players_by_team=players,development={},club_finances=finances,player_team_overrides=overrides,contract_overrides=contracts,seed=8,max_deals=2)
    assert actions
    a=actions[0]
    assert a['to_team_id']==1 and a['from_team_id']==2 and a['need']=='ST'
    assert overrides[str(a['player_id'])] == a['to_team_id']
    assert finances[str(a['to_team_id'])]['transfer_spend']>0
    assert finances[str(a['from_team_id'])]['transfer_income']>0


def test_ai_market_is_continuous_pre_bosman():
    players,finances=_market_world()
    actions=run_ai_transfer_window(current_date=date(1993,11,1),controlled_team_id=3,eligible_team_ids=[1,2,3],players_by_team=players,development={},club_finances=finances,player_team_overrides={},contract_overrides={},seed=8,max_deals=1)
    assert actions, 'El mercado 1993-94 no debe quedar restringido a ventanas modernas'
