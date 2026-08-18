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


def test_h1_finances_separate_source_budget_treasury_and_transfer_budget_in_pesetas():
    from backend.app.football9394.career_economy import transfer_spending_power
    team={"budget":400_000,"debt":0,"members":1_000}
    players=[{"source_id":i,"overall":70} for i in range(1,23)]
    finances=initial_club_finances(team,players=players)
    assert finances["currency_code"] == "ESP"
    assert finances["currency_name"] == "pesetas"
    assert finances["currency_label"] == "ptas."
    assert finances["source_budget"] == 400_000
    assert finances["transfer_budget_total"] >= 11_000_000  # 10% of 22 x 5M annual wages
    assert finances["cash"] >= finances["transfer_budget_total"]
    assert finances["cash"] >= finances["operating_reserve_target"]
    assert transfer_spending_power(finances) <= finances["transfer_budget_remaining"]


def test_h1_transfer_spending_respects_budget_and_operating_reserve_and_sale_replenishes_it():
    from backend.app.football9394.career_economy import receive_transfer_funds, spend_transfer_funds, transfer_spending_power
    finances={
        "cash":30_000_000,"operating_reserve_target":10_000_000,
        "transfer_budget_total":15_000_000,"transfer_budget_remaining":15_000_000,
        "transfer_spend":0,"transfer_income":0,
    }
    assert transfer_spending_power(finances) == 15_000_000
    spend_transfer_funds(finances,8_000_000,recorded_fee=7_000_000)
    assert finances["cash"] == 22_000_000
    assert finances["transfer_budget_remaining"] == 7_000_000
    assert finances["transfer_spend"] == 7_000_000
    receive_transfer_funds(finances,5_000_000)
    assert finances["cash"] == 27_000_000
    assert finances["transfer_budget_remaining"] == 12_000_000
    assert finances["transfer_income"] == 5_000_000


def test_h1_source_budget_is_never_reduced_by_normalisation():
    from backend.app.football9394.career_economy import normalized_transfer_budget
    team={"budget":525_272_000,"debt":0,"members":50_000}
    players=[{"source_id":i,"overall":75} for i in range(1,23)]
    assert normalized_transfer_budget(team,players=players) == 525_272_000


def test_h1_real_snapshot_keeps_elite_source_budgets_and_repairs_tiny_source_scales():
    from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
    from backend.app.football9394.career_economy import transfer_spending_power
    universe=default_runtime_snapshot()
    by_name={str(t.get("name")):t for t in universe.payload["teams"]}
    barca=by_name["FC Barcelona"]
    bplayers=list(universe.players_by_team.get(int(barca["source_id"]),()))
    bf=initial_club_finances(barca,players=bplayers)
    assert bf["source_budget"] == 360_526_000
    assert bf["transfer_budget_total"] == 360_526_000
    assert transfer_spending_power(bf) == 360_526_000

    buceo=by_name["Huracán Buceo"]
    hplayers=list(universe.players_by_team.get(int(buceo["source_id"]),()))
    hf=initial_club_finances(buceo,players=hplayers)
    assert hf["source_budget"] == 400_000
    assert hf["transfer_budget_total"] >= 10_000_000
    assert transfer_spending_power(hf) == hf["transfer_budget_total"]


def test_h2_wage_budget_opens_with_headroom_and_legacy_states_do_not_freeze_market():
    from backend.app.football9394.career_economy import annual_wage_commitment, wage_budget_headroom
    team={"budget":50_000_000,"debt":0,"members":20_000}
    players=[{"source_id":i,"overall":70} for i in range(1,23)]
    finances=initial_club_finances(team,players=players)
    used=annual_wage_commitment(players)
    assert finances["wage_budget_annual"] >= round(used*1.10)
    assert wage_budget_headroom(finances,players=players) > 0
    # Compatibility with pre-H2 fixtures/saves that lack the explicit field.
    assert wage_budget_headroom({"cash":50_000_000},players=players) > 0


def test_h2_monthly_revenue_is_split_and_memberships_are_front_loaded():
    from backend.app.football9394.career_economy import monthly_revenue_breakdown
    team={"budget":100_000_000,"debt":0,"members":40_000}
    summer=monthly_revenue_breakdown(team,fixed_costs=10_000_000,stature_score=70,month=8)
    winter=monthly_revenue_breakdown(team,fixed_costs=10_000_000,stature_score=70,month=1)
    assert summer["memberships"] > 0
    assert winter["memberships"] == 0
    assert summer["television"] > 0 and summer["sponsorship"] > 0
    assert sum(summer.values()) >= 9_400_000


def test_h2_debt_service_separates_interest_and_reduces_principal():
    team={"budget":50_000_000,"debt":100_000_000,"members":20_000}
    finances=initial_club_finances(team)
    before_debt=finances["debt"]
    posting=apply_monthly_club_finances(team=team,finances=finances,players=[],development={},contract_overrides={},month=10)
    assert posting["debt_interest"] > 0
    assert posting["debt_principal"] > 0
    assert posting["debt_service"] == posting["debt_interest"] + posting["debt_principal"]
    assert finances["debt"] == before_debt - posting["debt_principal"]


def test_h2_accounting_never_changes_currency_from_period_pesetas():
    team={"budget":30_000_000,"debt":0,"members":8_000}
    finances=initial_club_finances(team,players=[])
    apply_monthly_club_finances(team=team,finances=finances,players=[],development={},contract_overrides={},month=3)
    assert (finances["currency_code"],finances["currency_name"],finances["currency_label"]) == ("ESP","pesetas","ptas.")


def test_h2_recurring_income_does_not_self_finance_a_wage_spike():
    team={"budget":80_000_000,"debt":0,"members":25_000}
    players=[{"source_id":i,"overall":70} for i in range(1,19)]
    finances=initial_club_finances(team,players=players)
    base=dict(finances)
    normal=apply_monthly_club_finances(team=team,finances=base,players=players,development={},contract_overrides={},month=10)
    inflated=dict(finances)
    overrides={"1":{"salary":80_000_000,"end_year":1997}}
    high=apply_monthly_club_finances(team=team,finances=inflated,players=players,development={},contract_overrides=overrides,month=10)
    assert high["commercial_income"] == normal["commercial_income"]
    assert high["wage_expense"] > normal["wage_expense"]
    assert high["net"] < normal["net"]


def test_h2_board_tightens_next_season_discretionary_budgets_after_financing_draw():
    from backend.app.football9394.career_economy import refresh_season_transfer_budget
    team={"budget":100_000_000,"debt":0,"members":25_000}
    players=[{"source_id":i,"overall":70} for i in range(1,23)]
    finances=initial_club_finances(team,players=players)
    healthy_budget=finances["transfer_budget_remaining"]
    finances["financing_draws"]=20_000_000
    finances["debt"]=30_000_000
    refresh_season_transfer_budget(finances,team=team,players=players,current_wage_commitment=110_000_000)
    assert finances["budget_constraint_multiplier"] < 1.0
    assert finances["transfer_budget_remaining"] < healthy_budget
    assert finances["wage_budget_annual"] >= 110_000_000


def test_h2_recurring_revenue_recalibrates_between_seasons_without_following_salary_overrides():
    from backend.app.football9394.career_economy import refresh_season_transfer_budget
    team={"budget":120_000_000,"debt":0,"members":30_000}
    elite=[{"source_id":i,"overall":80} for i in range(1,23)]
    modest=[{"source_id":i,"overall":65} for i in range(1,23)]
    finances=initial_club_finances(team,players=elite)
    overpaid=dict(finances)
    before=finances["recurring_revenue_base_monthly"]
    modest_baseline=initial_club_finances(team,players=modest)["recurring_revenue_base_monthly"]
    refresh_season_transfer_budget(finances,team=team,players=modest,current_wage_commitment=100_000_000)
    refresh_season_transfer_budget(overpaid,team=team,players=modest,current_wage_commitment=900_000_000)
    after=finances["recurring_revenue_base_monthly"]
    assert modest_baseline < after < before
    # The current-wage commitment can be a huge overpay; the revenue target is
    # identical because it follows squad structure, not negotiated wages.
    assert overpaid["recurring_revenue_base_monthly"] == after
