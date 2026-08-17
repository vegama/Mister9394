from backend.app.football9394.career_market import estimated_transfer_value, negotiate_transfer


def test_transfer_negotiation_is_budgeted_and_can_accept():
    player={"overall":80,"contract":{"end":"1996"}}
    value=estimated_transfer_value(player)
    low=negotiate_transfer(player=player,current_overall=80,buyer_cash=value*2,fee_offer=1,salary_offer=1000,contract_years=3)
    assert not low["accepted"] and low["counter_fee"] > 1
    ok=negotiate_transfer(player=player,current_overall=80,buyer_cash=value*2,fee_offer=value,salary_offer=1000,contract_years=3)
    assert ok["accepted"]


def test_period_peseta_value_curve_reaches_superstar_scale_without_flattening_middle():
    assert estimated_transfer_value({'overall': 80}) == 85_000_000
    assert estimated_transfer_value({'overall': 85}) == 180_000_000
    assert estimated_transfer_value({'overall': 89}) == 450_000_000
    assert estimated_transfer_value({'overall': 95}) == 1_200_000_000
    assert estimated_transfer_value({'overall': 75}) < estimated_transfer_value({'overall': 80})
