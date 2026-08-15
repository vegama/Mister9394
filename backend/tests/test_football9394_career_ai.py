from datetime import date

from backend.app.football9394.career_ai import renew_ai_contracts, run_ai_transfer_window


def _p(pid,overall=70): return {"source_id":pid,"overall":overall}


def test_ai_renews_expiring_useful_player():
    players={1:[_p(1,82),_p(2,60)],2:[_p(3,75)]}
    overrides={"1":{"end":"1994","end_year":1994,"salary":1_000_000}}
    actions=renew_ai_contracts(current_date=date(1994,2,1),controlled_team_id=2,players_by_team=players,development={},contract_overrides=overrides,seed=5)
    assert any(a["player_id"]==1 for a in actions)
    assert overrides["1"]["end_year"]>1994


def test_ai_transfer_changes_roster_owner_and_both_club_cash():
    players={1:[_p(i,68+i%4) for i in range(1,23)],2:[_p(i,72+i%5) for i in range(100,122)],3:[_p(i,70+i%6) for i in range(200,222)]}
    finances={str(i):{"cash":50_000_000,"transfer_spend":0,"transfer_income":0} for i in players}
    overrides={}; contracts={}
    actions=run_ai_transfer_window(current_date=date(1994,1,1),controlled_team_id=3,eligible_team_ids=[1,2,3],players_by_team=players,development={},club_finances=finances,player_team_overrides=overrides,contract_overrides=contracts,seed=8,max_deals=2)
    assert actions
    a=actions[0]
    assert a["to_team_id"] != 3 and a["from_team_id"] != 3
    assert overrides[str(a["player_id"])] == a["to_team_id"]
    assert finances[str(a["to_team_id"])]["transfer_spend"]>0
    assert finances[str(a["from_team_id"])]["transfer_income"]>0


def test_ai_market_is_continuous_pre_bosman():
    players={1:[_p(i,68+i%4) for i in range(1,23)],2:[_p(i,72+i%5) for i in range(100,122)],3:[_p(i,70+i%6) for i in range(200,222)]}
    finances={str(i):{"cash":50_000_000,"transfer_spend":0,"transfer_income":0} for i in players}
    actions=run_ai_transfer_window(current_date=date(1993,11,1),controlled_team_id=3,eligible_team_ids=[1,2,3],players_by_team=players,development={},club_finances=finances,player_team_overrides={},contract_overrides={},seed=8,max_deals=1)
    assert actions, "El mercado 1993-94 no debe quedar restringido a ventanas modernas"
