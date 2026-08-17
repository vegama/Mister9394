from collections import Counter
from datetime import date

from backend.app.football9394.career_economy import inferred_contract
from backend.app.football9394.career_market_flow import market_flags, new_negotiation
from backend.app.football9394.club_signing_policy import club_specific_signing_eligibility
from backend.app.football9394.coaching import coaching_development_factor, source_coach_for_team
from backend.app.football9394.development import initial_player_development
from backend.app.football9394.long_career import apply_ageing_and_retirement, generate_academy_player
from backend.app.football9394.match_engine import FootballMatchEngine9394, SPAIN_PRIMERA_SIMULATION_1993_94
from backend.app.football9394.player_identity import age_on, gameplay_traits, player_archetype
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.long_career import AGE_POLICY_DYNAMIC
from backend.app.football9394.squad_dynamics import dynamics_api, sync_team_dynamics, update_after_match
from backend.app.football9394.tactical_ai import ai_tactics_for_squad
from backend.app.football9394.team_builder import build_snapshot_team_sheet


def test_f1_source_identity_makes_similarly_elite_players_footballistically_distinct():
    universe = default_runtime_snapshot()
    romario = universe.players_by_id[9]
    guardiola = universe.players_by_id[7]
    assert player_archetype(romario)[0] == "Finalizador"
    assert player_archetype(guardiola)[0] == "Organizador"
    assert {row["code"] for row in gameplay_traits(romario)} != {row["code"] for row in gameplay_traits(guardiola)}
    assert len(romario["role_ratings"]) == 18
    assert len(guardiola["role_ratings"]) == 18


def test_f2_coach_identity_affects_plan_and_player_development_without_flat_rating_bonus():
    universe = default_runtime_snapshot()
    cruyff = source_coach_for_team(universe, 3)
    toshack = source_coach_for_team(universe, 16)
    barca_plan = ai_tactics_for_squad(universe.players_by_team[3], cruyff)
    sociedad_plan = ai_tactics_for_squad(universe.players_by_team[16], toshack)
    assert cruyff["display_name"] == "Johan Cruyff"
    assert toshack["display_name"] == "John Toshack"
    assert (barca_plan.mentality, barca_plan.pressing, barca_plan.width) != (sociedad_plan.mentality, sociedad_plan.pressing, sociedad_plan.width)
    assert coaching_development_factor(cruyff, universe.players_by_id[9], game_date=date(1993, 10, 23)) != coaching_development_factor(cruyff, universe.players_by_id[7], game_date=date(1993, 10, 23))
    # Same Barcelona squad, two coaches: formation/selection is interpreted through
    # the coach while every player's stored base rating remains untouched.
    cruyff_sheet = build_snapshot_team_sheet(universe, 3, tactics=barca_plan, coach_profile=cruyff)
    toshack_on_barca = ai_tactics_for_squad(universe.players_by_team[3], toshack)
    toshack_sheet = build_snapshot_team_sheet(universe, 3, tactics=toshack_on_barca, coach_profile=toshack)
    assert ([p.id for p in cruyff_sheet.starters], cruyff_sheet.tactics.formation) != ([p.id for p in toshack_sheet.starters], toshack_sheet.tactics.formation)
    assert universe.players_by_id[9]["overall"] == 89


def test_f3_match_engine_produces_causal_chains_errors_second_balls_set_pieces_and_coach_adjustments():
    universe = default_runtime_snapshot()
    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    sheets = {}
    for team_id in (2, 3):
        coach = source_coach_for_team(universe, team_id)
        plan = ai_tactics_for_squad(universe.players_by_team[team_id], coach)
        sheets[team_id] = build_snapshot_team_sheet(universe, team_id, tactics=plan, coach_profile=coach)
    kinds = Counter()
    for seed in range(36):
        result = engine.simulate(sheets[3], sheets[2], seed=9394 + seed)
        kinds.update(event.kind for event in result.events)
    for kind in ("chance", "defensive_error", "second_ball", "set_piece_chance", "free_kick_chance", "tactical_adjustment"):
        assert kinds[kind] > 0, (kind, kinds)


def test_f4_unused_star_becomes_a_real_squad_problem_instead_of_a_static_morale_number():
    universe = default_runtime_snapshot()
    players = list(universe.players_by_team[3])
    development = initial_player_development(players)
    state = {"player_dynamics": {}}
    sync_team_dynamics(state, players=players, development=development, game_date=date(1993, 10, 23))
    other_starters = [str(p["source_id"]) for p in players if int(p["source_id"]) != 9][:11]
    for _ in range(12):
        update_after_match(
            state, players=players, development=development,
            starter_ids=other_starters, appeared_ids=other_starters,
            won=False, drew=False, game_date=date(1993, 10, 23),
        )
    romario = dynamics_api(state, 9)
    assert romario["role"] == "Figura"
    assert romario["satisfaction"] <= 32
    assert romario["wants_move"] is True
    assert romario["reasons"]


def test_f5_market_signals_come_from_circumstances_not_player_id_lottery():
    base = {"display_name": "Mismo perfil", "overall": 72, "category": 72, "initially_reserve": False}
    contract = {"end_year": 1997}
    a = market_flags({**base, "source_id": 1}, overall=72, team_id=3, contract=contract, current_year=1993)
    b = market_flags({**base, "source_id": 9999}, overall=72, team_id=3, contract=contract, current_year=1993)
    assert a["transferable_hint"] is False and b["transferable_hint"] is False
    unhappy = market_flags({**base, "source_id": 1}, overall=72, team_id=3, contract=contract, current_year=1993, wants_move=True, satisfaction=25)
    assert unhappy["transferable_hint"] is True and unhappy["reason"] == "quiere_salir"
    state = {}
    negotiation = new_negotiation(state=state, player_id=1, seller_team_id=3, buyer_team_id=2, fee_offer=1_000_000, salary_offer=500_000, contract_years=3, current_date=date(1993, 11, 1), seed=42, rival_interest=False)
    assert negotiation["rival_interest"] is False


def test_f5_inferred_contract_duration_uses_football_context_and_is_explicitly_inferred():
    young_star = {"source_id": 101, "display_name": "A", "birth_date": "1972-01-01", "team_id": 3, "overall": 84, "initially_reserve": False, "previous_team_years": 5}
    old_reserve = {"source_id": 102, "display_name": "B", "birth_date": "1958-01-01", "team_id": 3, "overall": 63, "initially_reserve": True, "previous_team_years": 0}
    a = inferred_contract(young_star)
    b = inferred_contract(old_reserve)
    assert a["career_inferred"] and b["career_inferred"]
    assert a["end_year"] >= b["end_year"]
    assert 1994 <= b["end_year"] <= 1995


def test_f6_real_birth_dates_age_and_old_players_can_retire_at_rollover():
    universe = default_runtime_snapshot()
    guardiola = universe.players_by_id[7]
    assert age_on(guardiola, date(1993, 10, 23)) == 22
    assert age_on(guardiola, date(1994, 10, 23)) == 23
    veteran = universe.players_by_id[5638]  # John Burridge, 42 in summer 1994 in the source
    state = {"age_policy": AGE_POLICY_DYNAMIC, "player_development": initial_player_development([veteran]), "player_team_overrides": {}, "season": "1993-94"}
    events = apply_ageing_and_retirement(state, players=[veteran], game_date=date(1994, 7, 1), seed=0)
    assert any(row["kind"] == "player_retirement" for row in events)
    assert state["player_development"][str(veteran["source_id"])]["physical_delta"] < 0


def test_f6_academy_newgen_uses_mdb_country_names_and_career_provenance_and_athletic_can_keep_own_academy():
    universe = default_runtime_snapshot()
    state = {"player_development": initial_player_development(universe.players_by_id.values()), "season": "1994-95"}
    generated = generate_academy_player(
        state, universe=universe, team_id=6, game_date=date(1994, 7, 1), seed=9394,
        players_by_team={tid: list(rows) for tid, rows in universe.players_by_team.items()},
    )
    assert generated["generated"] is True
    assert generated["source_id"] >= 10_000_000
    assert generated["provenance"] == "career_generated_from_mdb_country_name_pool"
    assert generated["first_name"] and generated["surname1"]
    assert age_on(generated, date(1994, 7, 1)) in {16, 17, 18, 19}
    assert club_specific_signing_eligibility(6, generated)[0] is True


def test_f7_f8_product_contract_exposes_depth_without_hiding_the_source_player_rating():
    universe = default_runtime_snapshot()
    romario = universe.players_by_id[9]
    assert int(romario["overall"]) == 89
    assert player_archetype(romario)[0]
    assert gameplay_traits(romario)


def test_f2_source_coach_set_piece_preference_reaches_team_sheet_and_engine_behaviour():
    universe = default_runtime_snapshot()
    cruyff = source_coach_for_team(universe, 3)
    assert cruyff["set_piece_usage"] == "high"
    plan = ai_tactics_for_squad(universe.players_by_team[3], cruyff)
    sheet = build_snapshot_team_sheet(universe, 3, tactics=plan, coach_profile=cruyff)
    assert sheet.set_piece_usage == "high"
    assert sheet.manager_discipline in {"strict", "balanced", "permissive"}


def test_f3_source_stadium_context_is_visible_and_has_small_tactical_effects():
    from backend.app.football9394.match_engine import MatchVenue9394
    from backend.app.football9394.venue import venue_for_team

    universe = default_runtime_snapshot()
    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    home_coach = source_coach_for_team(universe, 2)
    away_coach = source_coach_for_team(universe, 3)
    home = build_snapshot_team_sheet(universe, 2, tactics=ai_tactics_for_squad(universe.players_by_team[2], home_coach), coach_profile=home_coach)
    away = build_snapshot_team_sheet(universe, 3, tactics=ai_tactics_for_squad(universe.players_by_team[3], away_coach), coach_profile=away_coach)
    source_venue = venue_for_team(universe, 2)
    assert source_venue and source_venue.name and source_venue.width_m and source_venue.length_m
    result = engine.simulate(home, away, seed=12345, venue=source_venue)
    assert result.venue_id == source_venue.source_id
    assert result.venue_name == source_venue.name

    poor_narrow = MatchVenue9394("x", "Campo pesado", width_m=60, length_m=100, grass_quality=30)
    good_wide = MatchVenue9394("y", "Campo amplio", width_m=78, length_m=110, grass_quality=95)
    # Use an aggregate so the test protects a real effect without requiring a
    # particular single-match scoreline to change.
    poor_actions = good_actions = 0
    for seed in range(24):
        a = engine.simulate(home, away, seed=7000 + seed, venue=poor_narrow)
        b = engine.simulate(home, away, seed=7000 + seed, venue=good_wide)
        poor_actions += a.home.shots + a.away.shots
        good_actions += b.home.shots + b.away.shots
    assert poor_actions != good_actions


def test_f4_source_backed_injury_has_diagnosis_history_and_recovery_date():
    from datetime import timedelta
    from backend.app.football9394.development import apply_match_development, recover_one_day
    from backend.app.football9394.medical import medical_api

    universe = default_runtime_snapshot()
    player = universe.players_by_id[9]
    state = initial_player_development([player])
    pid = str(player["source_id"])
    start = date(1993, 11, 6)
    apply_match_development(
        state, player_ids=[pid], starter_ids=[pid], won=False, drew=False,
        injury_ids=[pid], seed=9394, source_players={int(pid): player}, game_date=start,
    )
    medical = medical_api(state[pid])
    current = medical["current_injury"]
    assert medical["status"] == "Lesionado"
    assert current["name"] != "Problemas físicos"
    assert current["provenance"] == "career_generated_from_mdb_injury_catalog"
    assert current["body_area"]
    remaining = medical["injury_days"]
    day = start
    for _ in range(remaining):
        day += timedelta(days=1)
        recover_one_day(state, game_date=day)
    recovered = medical_api(state[pid])
    assert recovered["status"] == "Disponible"
    assert recovered["history"][-1]["recovered_on"] == day.isoformat()


def test_f6_ten_year_cohort_retires_and_academy_replaces_real_squad_gaps_without_roster_inflation():
    from backend.app.football9394.long_career import generate_annual_academy_intake

    universe = default_runtime_snapshot()
    team_id = 16  # Real Sociedad starts with several veterans and a full squad.
    roster = [dict(p) for p in universe.players_by_team[team_id]]
    state = {
        "age_policy": AGE_POLICY_DYNAMIC,
        "player_development": initial_player_development(roster),
        "player_team_overrides": {}, "season": "1993-94",
    }
    generated_ids = set()
    retirement_count = 0
    for offset, year in enumerate(range(1994, 2004)):
        when = date(year, 7, 1)
        events = apply_ageing_and_retirement(state, players=roster, game_date=when, seed=5000 + offset)
        retirement_count += sum(1 for row in events if row["kind"] == "player_retirement")
        roster = [p for p in roster if not state["player_development"].get(str(p["source_id"]), {}).get("retired")]
        players_by_team = {team_id: roster}
        intake = generate_annual_academy_intake(
            state, universe=universe, team_ids=[team_id], game_date=when,
            seed=7000 + offset, players_by_team=players_by_team,
        )
        roster = players_by_team[team_id]
        generated_ids.update(row["player_id"] for row in intake)
        state["season"] = f"{year}-{str(year + 1)[-2:]}"
        assert 18 <= len(roster) <= 25
    assert retirement_count > 0
    assert generated_ids
    assert all(pid >= 10_000_000 for pid in generated_ids)


def test_f2_manager_assignments_are_persistent_world_state_and_resolve_source_coach():
    from backend.app.football9394.manager_career import ManagerCareerRuntime9394

    career = ManagerCareerRuntime9394.create(team_id=3, league_id=1, seed=9394, through_matchday=0)
    assert int(career.state["manager_assignments"]["16"]) == 234
    coach = career._coach_profile(16)
    assert coach and coach["display_name"] == "John Toshack"
    # Serialisable assignment state survives a save/load style reconstruction.
    import json
    restored = ManagerCareerRuntime9394(json.loads(json.dumps(career.state)))
    assert restored._coach_profile(16)["source_id"] == 234
