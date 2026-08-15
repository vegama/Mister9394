from backend.app.football9394.career_market import estimated_transfer_value, negotiate_transfer


def test_transfer_negotiation_is_budgeted_and_can_accept():
    player={"overall":80,"contract":{"end":"1996"}}
    value=estimated_transfer_value(player)
    low=negotiate_transfer(player=player,current_overall=80,buyer_cash=value*2,fee_offer=1,salary_offer=1000,contract_years=3)
    assert not low["accepted"] and low["counter_fee"] > 1
    ok=negotiate_transfer(player=player,current_overall=80,buyer_cash=value*2,fee_offer=value,salary_offer=1000,contract_years=3)
    assert ok["accepted"]
