from backend.app.football9394.career_economy import (
    apply_monthly_club_finances,
    effective_contract,
    inferred_annual_salary,
    initial_club_finances,
)


def test_inferred_contract_is_deterministic_and_explicitly_not_historical():
    p={"source_id":17,"overall":82}
    a=effective_contract(p)
    b=effective_contract(p)
    assert a==b
    assert a["career_inferred"] is True
    assert a["historical_contract_data_available"] is False
    assert 1994 <= a["end_year"] <= 1997
    assert inferred_annual_salary(p)>0


def test_monthly_economy_posts_income_wages_and_operating_costs():
    team={"budget":50_000_000,"debt":4_000_000,"members":20_000}
    finances=initial_club_finances(team)
    players=[{"source_id":i,"overall":75} for i in range(1,23)]
    before=finances["cash"]
    posting=apply_monthly_club_finances(
        team=team, finances=finances, players=players,
        development={str(i):{"overall":75} for i in range(1,23)}, contract_overrides={},
    )
    assert posting["commercial_income"]>0
    assert posting["wage_expense"]>0
    assert posting["operating_expense"]>0
    assert finances["cash"] == before + posting["net"]


def test_period_peseta_salary_curve_uses_credible_elite_order_of_magnitude():
    assert inferred_annual_salary({'overall': 75}) == 9_000_000
    assert inferred_annual_salary({'overall': 80}) == 18_000_000
    assert inferred_annual_salary({'overall': 89}) == 125_000_000
    assert inferred_annual_salary({'overall': 90}) > inferred_annual_salary({'overall': 89})
