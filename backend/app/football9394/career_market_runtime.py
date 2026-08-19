from __future__ import annotations

from heapq import nsmallest

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta, timezone
from random import Random
import json
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from .atomic_json_store import atomic_json_save, recover_json_load

from .career_market import estimated_transfer_value, matchday_income, negotiate_transfer
from .career_economy import (
    annual_wage_commitment,
    apply_monthly_club_finances,
    effective_contract,
    inferred_annual_salary,
    initial_club_finances,
    grant_transfer_budget,
    merge_finances_with_peseta_baseline,
    receive_transfer_funds,
    refresh_season_transfer_budget,
    spend_transfer_funds,
    transfer_spending_power,
    wage_budget_headroom,
)
from .career_ai import renew_ai_contracts, run_ai_transfer_window, squad_audit, ensure_ai_squad_coverage
from .career_international import generated_international_windows_9394, simulate_generated_friendlies
from .calendar_cycle import generated_round_dates, season_label, season_start_year
from .career_special_world import ensure_special_competitions, process_special_competitions, special_competition_snapshot
from .career_tournaments import ensure_tournament_state, play_pending_tournament_match, commit_pending_tournament_result, process_daily_tournaments, tournament_snapshot
from .international_manager import (ensure_international_manager_state, ensure_international_player_stats, record_international_player_match, generate_national_job_offers, accept_national_job as accept_national_job_state, resign_national_job as resign_national_job_state, set_national_selection as set_national_selection_state, update_international_reputation, international_manager_snapshot)
from .international_tournaments import is_world_championship_summer, simulate_world_championship_24
from .league_engine import LeagueSeason9394
from .laws import LAWS_1993_94
from .registry import default_registry_9394
from .development import apply_match_development, initial_player_development, recover_one_day, season_rollover as rollover_player_development
from .match_signatures import match_signature_report
from .market_ecosystem import ensure_market_ecosystem_state, player_market_preferences, refresh_recruitment_plans, register_replacement_chain, agent_pressure_for_player
from .national_teams import select_national_squad
from .medical import medical_api, medical_staff_report
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, FootballTactics9394, Footballer9394, SPAIN_PRIMERA_SIMULATION_1993_94, TeamSheet9394, tactical_identity_9394
from .rules import (
    SPAIN_PRIMERA_1993_94, SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94,
    NETHERLANDS_EERSTE_1993_94, NETHERLANDS_NACOMPETITIE_GROUP_1993_94,
)
from .snapshot_runtime import DEFAULT_GAME_DATE, FootballUniverseSnapshot9394, default_runtime_snapshot
from .standings import LeagueMatch9394, build_league_table
from .schedule import generate_round_robin_cycles
from .spain_runtime import _play_primera_segunda_tie
from .spain_segunda_b_runtime import _play_promotion_group
from .team_builder import build_snapshot_team_sheet, footballer_from_snapshot
from .live_match import LiveMatchEngine9394
from .career_performance import ensure_performance_state, record_managed_match, archive_managed_season, match_ratings_for_side
from .career_market_flow import ensure_market_flow_state, market_flags, new_negotiation, resubmit_negotiation
from .career_finance_view import economy_snapshot
from .career_board import evaluate_board, apply_board_review
from .career_news import ensure_news_state, ingest_events as ingest_news_events, publish_managed_match, publish as publish_news
from .career_competition_view import competition_directory as build_competition_directory, competition_detail as build_competition_detail
from .position_roles import assign_players_to_formation, role_for_player, squad_role_audit, MINIMUM_SENIOR_SQUAD_SIZE_9394, TARGET_SENIOR_SQUAD_SIZE_9394
from .club_signing_policy import club_specific_signing_eligibility
from .era_policy import enforce_frozen_rules_policy, regulatory_integrity_report
from .foreign_rules import competition_foreign_rule, validate_matchday_foreigners, can_register_foreign_signing, foreign_count, is_foreign_player
from .transfer_periods import transfer_period_status, market_activity_budget
from .career_club_status import initialise_club_status, club_status, update_after_season, attraction_modifier
from .coaching import source_coach_for_team
from .refereeing import referee_for_match
from .venue import venue_for_team
from .source_catalog_runtime import default_source_catalog
from .player_identity import player_archetype, gameplay_traits, tactical_fit
from .tactical_ai import (
    ai_tactics_for_squad, tactical_summary, ensure_tactical_memory_state,
    record_managed_tactical_usage, expected_managed_tactics, prepare_tactics_for_opponent,
    tactical_context_for_fixture, rival_learning_for_preparation, record_rival_preparation_outcome,
)
from .squad_dynamics import (
    ensure_squad_dynamics_state, sync_team_dynamics, update_after_match as update_squad_dynamics_after_match,
    dynamics_api, season_rollover_dynamics,
)
from .long_career import (
    ensure_long_career_state, all_generated_players, generated_player,
    apply_ageing_and_retirement, generate_annual_academy_intake,
    AGE_POLICY_DYNAMIC, AGE_POLICY_FROZEN, uses_frozen_age,
)
from .career_memory import (
    ensure_career_memory, record_match_memory, record_transfer_memory, rivalry_between,
    rivalry_snapshot, update_relationships_after_match, adjust_player_manager_relationship, relationship_api,
)
from .manager_market import ensure_manager_market_state, pressure_score, choose_replacement, register_manager_change
from .career_storylines import ensure_storyline_state, refresh_storylines, storyline_snapshot
from .career_records import ensure_record_state, update_after_controlled_match as update_career_records_after_match, reset_season_streaks, records_snapshot
from .career_history import ensure_history_dossiers, build_season_dossier
from .career_milestones import (
    ensure_milestone_state, register_season_closure, register_manager_milestone,
    register_rivalry_result, contextual_milestones, milestone_snapshot,
)
from .user_manager_career import ensure_user_manager_state, manager_profile_snapshot, update_reputation_after_match, close_current_tenure, open_new_tenure, set_job_offers, accept_offer as accept_user_manager_offer
from .career_professional import (
    ensure_professional_state, professional_snapshot, update_country_reputation, adjust_club_relationship,
    build_manager_contract, register_contract, close_contract, job_suitability, application_interview, expire_job_market,
)
from .board_project import ensure_board_project, update_board_project, submit_board_request, project_snapshot, register_sale_income
from .information_world import ensure_information_state, register_information_event, process_information_day, information_snapshot, add_reaction
from .economy_longitudinal import ensure_longitudinal_economy, post as post_long_economy, season_prize_money, financial_health, longitudinal_snapshot, register_structural_event
from .dressing_room import (ensure_dressing_room_state, update_after_match as update_dressing_room_after_match, dressing_room_snapshot, set_captain as set_dressing_room_captain, set_role_promise as set_dressing_room_role_promise, role_promise_api, close_role_promises_on_manager_exit, register_important_departure, register_important_injury, register_return_from_injury, reencounters_for_opponent, register_new_signing, register_contract_decision, respond_to_concern as respond_dressing_concern, register_discipline as register_dressing_discipline)
from .club_staff import club_staff_snapshot, assign_responsibility as assign_staff_responsibility, ensure_club_staff_state, responsibility_effectiveness
from .scouting import ensure_scouting_state, external_player_view, process_scouting_day, scouting_snapshot as build_scouting_snapshot, start_scouting, scouting_geography
from .training import (
    ensure_training_state, process_training_day, training_snapshot as build_training_snapshot,
    set_training_plan as update_training_plan_state, set_individual_focus as set_training_focus_state,
    set_individual_recovery as set_training_recovery_state,
    set_match_preparation_focus as set_training_match_prep_state, session_for_date,
)
from .tactical_plan import (
    ensure_tactical_plan_state, set_tactical_plan as update_tactical_plan_state,
    set_individual_instruction as set_tactical_player_instruction,
    set_opposition_instruction as set_tactical_opposition_instruction,
    set_piece_taker as set_tactical_piece_taker, process_familiarity_day,
    tactical_plan_snapshot as build_tactical_plan_snapshot, engine_tactics_payload,
    reset_opposition_instructions,
)
from .staff_reports import build_staff_reports
from .match_analysis import live_player_performance, bench_advice, postmatch_diagnosis
from .squad_planning import squad_plan_snapshot as build_squad_plan_snapshot
from .longitudinal_health import AI_CONTRACT_LOG_LIMIT, ensure_longitudinal_health_state, finalize_summer_transition


class CareerMarketRuntimeMixin:
    """Extracted V1.0-M runtime responsibilities; behavior is characterized by regression tests."""

    def search_market(self, query: str = "", *, limit: int = 20, position: str = "", free_agents: bool = False, watched: bool = False) -> list[dict[str, Any]]:
        q = " ".join(query.casefold().split()); pos = str(position or "").upper()
        controlled = int(self.state["team_id"]); watched_ids = {int(x) for x in (self.state.get("watchlist") or [])}
        development = self.state.get("player_development") or {}
        overrides = self.state.get("player_team_overrides") or {}
        rows = []
        # Preserve source ordering/duplicates because equal market-order keys are
        # part of the established API behaviour. The hot-path win comes from
        # avoiding per-row source lookups and full-list sorting, not deduping.
        for row in self._all_player_rows():
            pid=int(row["source_id"]); team_id=int(overrides.get(str(pid), row.get("team_id") or 0))
            if team_id == controlled or row.get("retired") or bool((development.get(str(pid)) or {}).get("retired")):
                continue
            if q and q not in str(row.get("display_name") or "").casefold():
                continue
            if pos:
                role=role_for_player(row)
                if pos not in {str(row.get("broad_position") or "").upper(), str(row.get("position") or "").upper(),role.code.upper(),role.name.upper(),role.squad_slot.upper()}:
                    continue
            if free_agents and team_id != 0:
                continue
            if watched and pid not in watched_ids:
                continue
            # Browsing the market shows what the club network actually knows. A
            # name search may still locate an unknown identity, but it will be
            # redacted by `_external_player_api` until scouting discovers it.
            if not q and not watched and int((self._baseline_scouting_knowledge(pid, target_team_id=team_id) or {}).get("level") or 0) <= 0 and str(pid) not in (self.state.get("scouting_knowledge") or {}):
                continue
            rows.append(row)
        cash=transfer_spending_power(self.state.get("finances") or {})
        def market_order(player: dict[str, Any]) -> tuple[int, int, int, int]:
            pid=int(player["source_id"])
            overall=int((development.get(str(pid)) or {}).get("overall") or player.get("overall") or player.get("category") or 0)
            value=estimated_transfer_value(player, overall=overall)
            # A market screen should contain actual decisions for the current
            # club, not just the 100 best footballers on Earth.  Watched players
            # remain first; otherwise plausible targets precede aspirational
            # stars, which are still reachable by name/position searches.
            if cash and value <= cash * 0.70:
                affordability_band = 0  # leaves room to negotiate salary/counteroffers
            elif cash and value <= cash:
                affordability_band = 1  # possible, but consumes most of the window
            else:
                affordability_band = 2  # aspirational target
            return (0 if pid in watched_ids else 1, affordability_band, -overall, value)
        bounded_limit=max(1, min(int(limit), 100))
        selected=nsmallest(bounded_limit, rows, key=market_order) if len(rows)>bounded_limit else sorted(rows,key=market_order)
        return [self._external_player_api(row) for row in selected]

    def negotiate_player(self, player_id: int, *, fee_offer: int, salary_offer: int = 0, contract_years: int = 3) -> dict[str, Any]:
        pid = int(player_id)
        if self._player_source(pid) is None:
            raise KeyError(f"jugador {pid} no existe")
        controlled = int(self.state["team_id"])
        seller = self._current_team_id(pid)
        if seller == controlled:
            raise ValueError("el jugador ya pertenece a tu club")
        raw = self._player_source(pid)
        eligible,reason=self._signing_eligibility(controlled,raw)
        if not eligible: raise ValueError(f"No se puede inscribir el fichaje: {reason}")
        current_overall = int(self.state["player_development"].get(str(pid), {}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        decision = negotiate_transfer(
            player=self._career_player_api(raw), current_overall=current_overall,
            buyer_cash=transfer_spending_power(self.state["finances"]), fee_offer=int(fee_offer),
            salary_offer=int(salary_offer), contract_years=int(contract_years),
        )
        wage_room=self._current_wage_headroom()
        if decision.get("accepted") and int(salary_offer)>wage_room:
            decision={**decision,"accepted":False,"reason":"presupuesto_salarial_insuficiente","wage_budget_headroom":wage_room}
            decision.pop("fee",None)
        salary_minimum = round(inferred_annual_salary(raw, overall=current_overall) * 0.90 * attraction_modifier(self.state,from_team_id=seller,to_team_id=controlled) * (0.88 if dynamics_api(self.state,pid).get("wants_move") else 1.0))
        if decision.get("accepted") and int(salary_offer) < salary_minimum:
            decision = {
                **decision, "accepted": False, "reason": "salario_insuficiente",
                "counter_salary": salary_minimum, "counter_fee": int(fee_offer),
            }
            decision.pop("fee", None)
        record = {"date": self.state["current_date"], "player_id": pid, "from_team_id": seller, "to_team_id": controlled, **decision}
        if decision["accepted"]:
            self.state["player_team_overrides"][str(pid)] = controlled
            buyer_fin = self.state["club_finances"][str(controlled)]
            spend_transfer_funds(buyer_fin,int(decision["fee"]),recorded_fee=int(decision["fee"]))
            if seller and str(seller) in self.state["club_finances"]:
                seller_fin = self.state["club_finances"][str(seller)]
                receive_transfer_funds(seller_fin,int(decision["fee"]))
            self.state["finances"] = buyer_fin
            current_year = int(str(self.state["current_date"])[:4])
            self.state["contract_overrides"][str(pid)] = {
                "start": str(current_year), "end": str(current_year + int(contract_years)),
                "end_year": current_year + int(contract_years),
                "salary": int(salary_offer), "salary_display": f"{int(salary_offer):,} ptas.".replace(",", "."), "loan": False,
                "career_inferred": True,
            }
            self.state["economy_ledger"].append({"date": self.state["current_date"], "kind": "transfer_spend", "amount": -int(decision["fee"]), "player_id": pid})
            record_transfer_memory(self.state,self.universe,date_text=self.current_date.isoformat(),player_id=pid,from_team_id=int(seller),to_team_id=controlled,fee=int(decision["fee"]),player_overall=current_overall)
            self._rebuild_rosters()
            register_new_signing(self.state, player_id=pid, players_after=self._career_players_by_team.get(controlled,()), date_text=self.current_date.isoformat())
        self.state["transfer_history"].append(record)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return record

    def toggle_watchlist(self, player_id: int, watched: bool = True) -> dict[str, Any]:
        pid=int(player_id)
        if self._player_source(pid) is None: raise KeyError(f"jugador {pid} no existe")
        ids={int(x) for x in (self.state.get("watchlist") or [])}
        if watched: ids.add(pid)
        else: ids.discard(pid)
        self.state["watchlist"]=sorted(ids); self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {"player_id":pid,"watched":pid in ids,"watchlist":list(self.state["watchlist"])}

    def _complete_user_transfer(self, *, player_id:int, seller:int, fee:int, salary:int, years:int, date_text:str, source:str, signing_bonus:int=0, release_clause:int|None=None, squad_role:str="rotation") -> dict[str,Any]:
        pid=int(player_id); controlled=int(self.state["team_id"]); buyer_fin=self.state["club_finances"][str(controlled)]
        total_cost=int(fee)+int(signing_bonus)
        if total_cost>transfer_spending_power(buyer_fin): raise ValueError("ya no hay presupuesto de fichajes utilizable para completar la operación")
        wage_room=self._current_wage_headroom()
        if int(salary)>wage_room: raise ValueError("la ficha supera el margen salarial anual disponible")
        self.state["player_team_overrides"][str(pid)]=controlled
        spend_transfer_funds(buyer_fin,total_cost,recorded_fee=int(fee))
        if seller and str(seller) in self.state["club_finances"]:
            seller_fin=self.state["club_finances"][str(seller)]; receive_transfer_funds(seller_fin,int(fee))
        self.state["finances"]=buyer_fin
        year=self.current_date.year
        self.state["contract_overrides"][str(pid)]={"start":str(year),"end":str(year+int(years)),"end_year":year+int(years),"salary":int(salary),"salary_display":f"{int(salary):,} ptas.".replace(",","."),"loan":False,"career_inferred":True,"signed_by_user":True,"release_clause":int(release_clause) if release_clause is not None else None,"squad_role":str(squad_role)}
        record={"kind":"user_transfer","date":date_text,"player_id":pid,"from_team_id":int(seller),"to_team_id":controlled,"fee":int(fee),"salary":int(salary),"contract_years":int(years),"signing_bonus":int(signing_bonus),"release_clause":int(release_clause) if release_clause is not None else None,"squad_role":str(squad_role),"accepted":True,"source":source}
        self.state["transfer_history"].append(record); self.state["economy_ledger"].append({"date":date_text,"kind":"transfer_spend","amount":-int(fee),"player_id":pid})
        post_long_economy(self.state,team_id=controlled,season=str(self.state["season"]),category="transfer_spend",amount=int(fee))
        if seller:
            post_long_economy(self.state,team_id=int(seller),season=str(self.state["season"]),category="transfer_income",amount=int(fee))
        if int(signing_bonus):
            self.state["economy_ledger"].append({"date":date_text,"kind":"signing_bonus","amount":-int(signing_bonus),"player_id":pid})
            post_long_economy(self.state,team_id=controlled,season=str(self.state["season"]),category="bonuses",amount=int(signing_bonus))
        raw=self._player_source(pid) or {}
        overall=int(self.state.get("player_development",{}).get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        record_transfer_memory(self.state,self.universe,date_text=date_text,player_id=pid,from_team_id=int(seller),to_team_id=controlled,fee=int(fee),player_overall=overall)
        self._rebuild_rosters()
        concerns = register_new_signing(self.state, player_id=pid, players_after=self._career_players_by_team.get(controlled,()), date_text=date_text)
        promised={"star":"Figura","starter":"Titular","rotation":"Rotación","prospect":"Promesa","depth":"Fondo de plantilla"}.get(str(squad_role),"Rotación")
        set_dressing_room_role_promise(self.state,player_id=pid,role=promised,players=self._career_players_by_team.get(controlled,()),date_text=date_text)
        publish_news(
            self.state,
            key=f"user-signing:{date_text}:{pid}:{controlled}", date=date_text, category="Mercado", importance=4,
            headline=f"{self._team_name(controlled)} ficha a {self._player_name(pid)}",
            detail=(f"Llega desde {self._team_name(seller)} por {int(fee):,} ptas. con rol de {promised.lower()}." if seller else f"Llega libre con rol de {promised.lower()}."),
            entity={"player_id":pid,"team_id":controlled},
        )
        record["dressing_room_reactions"] = len(concerns or [])
        return record

    def _complete_user_loan(self, *, player_id:int, seller:int, loan_fee:int, wage_share:int, date_text:str, squad_role:str="rotation") -> dict[str,Any]:
        ensure_market_flow_state(self.state)
        pid=int(player_id); controlled=int(self.state["team_id"])
        if not seller: raise ValueError("un agente libre no puede llegar cedido")
        if self._current_team_id(pid)==controlled: raise ValueError("el jugador ya está en tu plantilla")
        buyer_fin=self.state["club_finances"][str(controlled)]
        if int(loan_fee)>transfer_spending_power(buyer_fin): raise ValueError("no hay presupuesto de fichajes utilizable para completar la cesión")
        raw=self._player_source(pid) or {}
        overall=int(self.state.get("player_development",{}).get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        previous_override=(self.state.get("contract_overrides") or {}).get(str(pid))
        current_contract=effective_contract(raw,overall=overall,override=previous_override)
        previous_team_override=(self.state.get("player_team_overrides") or {}).get(str(pid))
        end_year=self.current_date.year+1 if self.current_date.month>=7 else self.current_date.year
        ends_on=date(end_year,6,30)
        borrower_salary=round(int(current_contract.get("salary") or inferred_annual_salary(raw,overall=overall))*max(0,min(100,int(wage_share)))/100)
        if borrower_salary>self._current_wage_headroom(): raise ValueError("la parte de ficha de la cesión supera el margen salarial anual disponible")
        spend_transfer_funds(buyer_fin,int(loan_fee),recorded_fee=int(loan_fee))
        if str(seller) in self.state.get("club_finances",{}):
            seller_fin=self.state["club_finances"][str(seller)]; receive_transfer_funds(seller_fin,int(loan_fee))
        self.state["player_team_overrides"][str(pid)]=controlled
        self.state["contract_overrides"][str(pid)]={**current_contract,"salary":borrower_salary,"salary_display":f"{borrower_salary:,} ptas.".replace(",","."),"loan":True,"loan_parent_team_id":int(seller),"loan_end":ends_on.isoformat(),"squad_role":str(squad_role),"career_inferred":True}
        deal={"id":f"loan:{pid}:{date_text}:{controlled}","player_id":pid,"parent_team_id":int(seller),"borrower_team_id":controlled,"started_on":date_text,"ends_on":ends_on.isoformat(),"loan_fee":int(loan_fee),"wage_share":max(0,min(100,int(wage_share))),"squad_role":str(squad_role),"status":"active","previous_contract_override":previous_override,"previous_team_override":previous_team_override}
        self.state["loan_deals"].append(deal); self.state["loan_deals"]=self.state["loan_deals"][-120:]
        self.state["finances"]=buyer_fin; self.state["economy_ledger"].append({"date":date_text,"kind":"loan_fee","amount":-int(loan_fee),"player_id":pid})
        post_long_economy(self.state,team_id=controlled,season=str(self.state["season"]),category="transfer_spend",amount=int(loan_fee))
        post_long_economy(self.state,team_id=int(seller),season=str(self.state["season"]),category="transfer_income",amount=int(loan_fee))
        self._rebuild_rosters()
        concerns=register_new_signing(self.state,player_id=pid,players_after=self._career_players_by_team.get(controlled,()),date_text=date_text)
        promised={"star":"Figura","starter":"Titular","rotation":"Rotación","prospect":"Promesa","depth":"Fondo de plantilla"}.get(str(squad_role),"Rotación")
        set_dressing_room_role_promise(self.state,player_id=pid,role=promised,players=self._career_players_by_team.get(controlled,()),date_text=date_text)
        publish_news(self.state,key=f"user-loan:{date_text}:{pid}:{controlled}",date=date_text,category="Mercado",importance=3,headline=f"{self._team_name(controlled)} incorpora cedido a {self._player_name(pid)}",detail=f"Llega desde {self._team_name(seller)} hasta el 30 de junio. El club asume el {int(wage_share)}% de la ficha.",entity={"player_id":pid,"team_id":controlled})
        deal["dressing_room_reactions"]=len(concerns or [])
        return deal

    def _process_user_loans(self, day:date) -> list[dict[str,Any]]:
        ensure_market_flow_state(self.state); events=[]; changed=False
        for deal in self.state.get("loan_deals") or []:
            if deal.get("status")!="active" or date.fromisoformat(str(deal.get("ends_on")))>day: continue
            pid=int(deal["player_id"]); borrower=int(deal["borrower_team_id"]); parent=int(deal["parent_team_id"])
            if self._current_team_id(pid)==borrower:
                previous_team=deal.get("previous_team_override")
                if previous_team is None: self.state.get("player_team_overrides",{}).pop(str(pid),None)
                else: self.state["player_team_overrides"][str(pid)]=int(previous_team)
                previous_contract=deal.get("previous_contract_override")
                if previous_contract is None: self.state.get("contract_overrides",{}).pop(str(pid),None)
                else: self.state["contract_overrides"][str(pid)]=dict(previous_contract)
                room=(self.state.get("dressing_room") or {}); promise=(room.get("role_promises") or {}).get(str(pid))
                if promise and promise.get("status") in {"active","on_track","at_risk"}:
                    promise["status"]="closed_loan_end"; promise["closed_on"]=day.isoformat(); room.setdefault("promise_archive",[]).append(dict(promise))
                deal["status"]="completed"; deal["returned_on"]=day.isoformat(); changed=True
                events.append({"kind":"loan_return","date":day.isoformat(),"player_id":pid,"from_team_id":borrower,"to_team_id":parent})
                publish_news(self.state,key=f"loan-return:{day.isoformat()}:{pid}:{borrower}",date=day.isoformat(),category="Mercado",importance=2,headline=f"{self._player_name(pid)} regresa a {self._team_name(parent)}",detail=f"Termina su cesión en {self._team_name(borrower)}.",entity={"player_id":pid,"team_id":parent})
        if changed:
            self._rebuild_rosters()
            if int(self.state.get("team_id") or 0) in {int(d.get("borrower_team_id") or 0) for d in self.state.get("loan_deals") or [] if d.get("returned_on")==day.isoformat()}:
                if not self.selection_snapshot()["valid"]: self.state["selection"]=self._safe_auto_selection()
        return events

    def inquire_player_availability(self, player_id: int) -> dict[str, Any]:
        ensure_market_flow_state(self.state)
        pid=int(player_id); controlled=int(self.state["team_id"])
        raw=self._player_source(pid)
        if raw is None: raise KeyError(f"jugador {pid} no existe")
        seller=self._current_team_id(pid)
        if seller==controlled: raise ValueError("la disponibilidad de tu propia plantilla se gestiona internamente")
        overall=int((self.state.get("player_development",{}).get(str(pid)) or {}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        value=estimated_transfer_value(raw,overall=overall)
        contract=effective_contract(raw,overall=overall,override=self.state.get("contract_overrides",{}).get(str(pid)))
        dynamics=dynamics_api(self.state,pid); wants_move=bool(dynamics.get("wants_move"))
        effect=self._responsibility_effect("transfer_negotiation"); q=max(1,min(20,int(effect.get("quality") or 10)))
        expiring=int(contract.get("end_year") or 9999)<=self.current_date.year+1
        reserve=bool(raw.get("initially_reserve"))
        if seller==0: stance="free"; multiplier=.0
        elif wants_move or reserve: stance="open"; multiplier=.88
        elif expiring: stance="negotiable"; multiplier=.95
        else: stance="difficult"; multiplier=1.10
        center=round(value*multiplier) if seller else 0
        spread=max(.05,.22-(q-1)*.008)
        low=max(0,round(center*(1-spread))); high=max(low,round(center*(1+spread)))
        wage=inferred_annual_salary(raw,overall=overall); wspread=max(.06,.20-(q-1)*.006)
        inquiry={
            "id":f"inquiry:{pid}:{self.current_date.isoformat()}:{len(self.state.get('market_inquiries') or [])}",
            "date":self.current_date.isoformat(),"expires_on":(self.current_date+timedelta(days=14)).isoformat(),
            "player_id":pid,"player_name":raw.get("display_name") or raw.get("name"),"seller_team_id":seller,"seller_team_name":self._team_name(seller) if seller else "Libre",
            "stance":stance,"asking_range":[low,high],"salary_range":[round(wage*(1-wspread)),round(wage*(1+wspread))],
            "confidence":max(40,min(96,42+q*3)),"handled_by":effect.get("assignee_name"),"handler_quality":q,
            "note":("Puede negociar libremente." if seller==0 else "El club parece dispuesto a escuchar." if stance=="open" else "Hay margen, pero no parece una salida prioritaria." if stance=="negotiable" else "La operación exigirá convencer al club y al jugador."),
        }
        self.state["market_inquiries"].append(inquiry); self.state["market_inquiries"]=self.state["market_inquiries"][-80:]
        ids={int(x) for x in (self.state.get("watchlist") or [])};ids.add(pid);self.state["watchlist"]=sorted(ids)
        register_information_event(self.state,{"kind":"market_inquiry","date":self.current_date.isoformat(),"player_id":pid,"team_id":controlled,"from_team_id":seller},headline=f"{self._team_name(controlled)} pregunta por {inquiry['player_name']}",detail="El rumor nace de una consulta real de disponibilidad y conserva incertidumbre hasta que haya una operación.")
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return inquiry

    def open_transfer_negotiation(self, player_id:int, *, fee_offer:int, salary_offer:int, contract_years:int=3, squad_role:str="rotation", signing_bonus:int=0, release_clause:int|None=None, deal_type:str="transfer", loan_wage_share:int=100) -> dict[str,Any]:
        pid=int(player_id); controlled=int(self.state["team_id"])
        if self._player_source(pid) is None: raise KeyError(f"jugador {pid} no existe")
        seller=self._current_team_id(pid)
        if seller==controlled: raise ValueError("el jugador ya pertenece a tu club")
        deal_type=str(deal_type or "transfer")
        if deal_type not in {"transfer","loan"}: raise ValueError("tipo de operación no válido")
        if deal_type=="loan" and not seller: raise ValueError("un agente libre no puede llegar cedido")
        if not 0<=int(loan_wage_share)<=100: raise ValueError("el porcentaje de ficha de la cesión debe estar entre 0 y 100")
        eligible,reason=self._signing_eligibility(controlled,self._player_source(pid))
        if not eligible: raise ValueError(f"No se puede abrir la negociación: {reason}")
        if not 1<=int(contract_years)<=6: raise ValueError("el contrato debe durar entre 1 y 6 años")
        if int(fee_offer)<0 or int(salary_offer)<0 or int(signing_bonus)<0: raise ValueError("oferta inválida")
        squad_role=str(squad_role or "rotation")
        if squad_role not in {"star","starter","rotation","prospect","depth"}: raise ValueError("rol de plantilla no válido")
        if release_clause is not None and int(release_clause)<=0: raise ValueError("cláusula de rescisión no válida")
        if int(fee_offer)+int(signing_bonus)>transfer_spending_power(self.state.get("finances",{})): raise ValueError("la oferta y la prima superan el presupuesto de fichajes utilizable")
        raw=self._player_source(pid) or {}
        if deal_type=="loan":
            overall_for_wage=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
            current_contract=effective_contract(raw,overall=overall_for_wage,override=self.state.get("contract_overrides",{}).get(str(pid)))
            annual_wage_cost=round(int(current_contract.get("salary") or inferred_annual_salary(raw,overall=overall_for_wage))*int(loan_wage_share)/100)
        else:
            annual_wage_cost=int(salary_offer)
        if annual_wage_cost>self._current_wage_headroom(): raise ValueError("la oferta supera el margen salarial anual disponible")
        value=estimated_transfer_value(raw,overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60))
        slot=role_for_player(raw).squad_slot
        competitors=[]
        for tid in self._active_club_ids():
            if tid in {controlled,seller}: continue
            fin=transfer_spending_power((self.state.get("club_finances",{}).get(str(tid)) or {}))
            if fin < value * .75: continue
            audit=squad_audit(self._career_players_by_team.get(tid,[]),self.state["player_development"])
            shortage=max((int(n.get("shortage") or 0) for n in audit.get("needs") or [] if str(n.get("slot"))==slot),default=0)
            if shortage<=0: continue
            score=float(club_status(self.state,tid).get("score") or 50)
            competitors.append((shortage*10+score/10,tid,fin))
        competitors.sort(reverse=True)
        row=new_negotiation(state=self.state,player_id=pid,seller_team_id=seller,buyer_team_id=controlled,fee_offer=int(fee_offer),salary_offer=int(salary_offer),contract_years=int(contract_years),current_date=self.current_date,seed=int(self.state["seed"]),rival_interest=bool(competitors))
        negotiation_effect = self._responsibility_effect("transfer_negotiation")
        q = int(negotiation_effect.get("quality") or 10)
        response = date.fromisoformat(str(row["response_date"]))
        if q >= 17 and response > self.current_date + timedelta(days=1): response -= timedelta(days=1)
        elif q <= 8: response += timedelta(days=1)
        row.update({
            "response_date": response.isoformat(), "handled_by": negotiation_effect.get("assignee_name"),
            "handler_role": negotiation_effect.get("assignee_role"), "handler_quality": q,
            "handler_quality_label": negotiation_effect.get("quality_label"),
            "squad_role":squad_role,"signing_bonus":int(signing_bonus),"release_clause":int(release_clause) if release_clause is not None else None,
            "deal_type":deal_type,"loan_wage_share":int(loan_wage_share),
        })
        if competitors:
            rival_tid=competitors[0][1]
            rival_salary=round(inferred_annual_salary(raw,overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60))*1.05)
            row.update({"rival_team_id":rival_tid,"rival_team_name":self._team_name(rival_tid),"rival_fee":min(int(competitors[0][2]),round(value*1.03)),"rival_salary":rival_salary})
        register_information_event(self.state,{"kind":"transfer_negotiation_opened","date":self.current_date.isoformat(),"player_id":pid,"team_id":controlled,"from_team_id":seller,"negotiation_id":row.get("id")},headline=f"Movimiento por {raw.get('display_name') or raw.get('name')}",detail="La conversación pública sólo puede nacer porque existe una negociación abierta.")
        return row

    def withdraw_transfer_negotiation(self, negotiation_id: str) -> dict[str, Any]:
        row=(self.state.get("transfer_negotiations") or {}).get(str(negotiation_id))
        if row is None: raise KeyError("negociación no encontrada")
        if row.get("status") not in {"waiting","countered"}: raise ValueError("la negociación ya está cerrada")
        row["status"]="withdrawn";row["closed_on"]=self.current_date.isoformat();row.setdefault("history",[]).append({"date":self.current_date.isoformat(),"kind":"withdrawn"})
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return dict(row)

    def resubmit_transfer_negotiation(self, negotiation_id:str, *, fee_offer:int, salary_offer:int, contract_years:int=3, loan_wage_share:int|None=None) -> dict[str,Any]:
        row=(self.state.get("transfer_negotiations") or {}).get(str(negotiation_id))
        if row is None: raise KeyError("negociación no encontrada")
        raw=self._player_source(int(row["player_id"]))
        if raw is not None:
            eligible,reason=self._signing_eligibility(int(self.state["team_id"]),raw)
            if not eligible: raise ValueError(f"No se puede renegociar ahora: {reason}")
        if loan_wage_share is not None:
            if not 0<=int(loan_wage_share)<=100: raise ValueError("el porcentaje de ficha de la cesión debe estar entre 0 y 100")
            row["loan_wage_share"]=int(loan_wage_share)
        if str(row.get("deal_type") or "transfer")=="loan" and raw is not None:
            overall=int(self.state.get("player_development",{}).get(str(int(row["player_id"])),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
            current=effective_contract(raw,overall=overall,override=self.state.get("contract_overrides",{}).get(str(int(row["player_id"]))))
            annual_cost=round(int(current.get("salary") or inferred_annual_salary(raw,overall=overall))*int(row.get("loan_wage_share") or 0)/100)
        else:
            annual_cost=int(salary_offer)
        if annual_cost>self._current_wage_headroom(): raise ValueError("la oferta supera el margen salarial anual disponible")
        return resubmit_negotiation(row,fee_offer=int(fee_offer),salary_offer=int(salary_offer),contract_years=int(contract_years),current_date=self.current_date,seed=int(self.state["seed"]))

    def _process_user_negotiations(self, day:date) -> list[dict[str,Any]]:
        events=[]; controlled=int(self.state["team_id"])
        for row in (self.state.get("transfer_negotiations") or {}).values():
            if row.get("status")!="waiting" or date.fromisoformat(str(row["response_date"]))>day: continue
            pid=int(row["player_id"]); raw=self._player_source(pid)
            if raw is None: row["status"]="rejected"; row["reason"]="jugador_no_disponible"; continue
            seller=self._current_team_id(pid)
            if seller==controlled: row["status"]="completed"; continue
            eligible,eligibility_reason=self._signing_eligibility(controlled,raw,day=day)
            if not eligible:
                row.update({"status":"rejected","reason":"inscripcion_no_permitida","detail":eligibility_reason});events.append({"kind":"transfer_rejected_registration","date":day.isoformat(),"player_id":pid,"reason":eligibility_reason});continue
            if seller!=int(row.get("seller_team_id") or seller): row["status"]="rejected";row["reason"]="cambio_de_club";continue
            overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
            wants_move=bool(dynamics_api(self.state,pid).get("wants_move"))
            current_contract=effective_contract(raw,overall=overall,override=self.state.get("contract_overrides",{}).get(str(pid)))
            buyer_audit=squad_audit(self._career_players_by_team.get(controlled,[]),self.state["player_development"]);slot=role_for_player(raw).squad_slot
            role_shortage=max((int(n.get("shortage") or 0) for n in buyer_audit.get("needs") or [] if str(n.get("slot"))==slot),default=0)
            preferences=player_market_preferences(raw,overall=overall,current_club_score=float(club_status(self.state,seller).get("score") or 40) if seller else 20.0,target_club_score=float(club_status(self.state,controlled).get("score") or 50),coach_profile=self._coach_profile(controlled),wants_move=wants_move,current_salary=int(current_contract.get("salary") or 0),offered_salary=int(row.get("salary_offer") or 0),role_shortage=role_shortage)
            row["player_preferences"]=preferences
            agent=agent_pressure_for_player(self.state,player_id=pid,current_year=day.year,contract_end_year=int(current_contract.get("end_year") or day.year+3),satisfaction=int(dynamics_api(self.state,pid).get("satisfaction") or 70),wants_move=wants_move,rival_interest=bool(row.get("rival_interest")))
            row["agent_pressure"]=agent
            reluctance=max(0.88,min(1.22,1.10-(float(preferences["openness"])/100.0)*.22))
            negotiation_quality=max(1,min(20,int(row.get("handler_quality") or self._responsibility_effect("transfer_negotiation").get("quality") or 10)))
            negotiation_multiplier=max(.95,min(1.05,1.02-(negotiation_quality-10)*.004))
            role_multiplier={"star":1.08,"starter":1.02,"rotation":.96,"prospect":.91,"depth":.90}.get(str(row.get("squad_role") or "rotation"),.96)
            salary_min=round(inferred_annual_salary(raw,overall=overall)*.90*attraction_modifier(self.state,from_team_id=seller,to_team_id=controlled)*(0.88 if wants_move else 1.0)*reluctance*float(agent["wage_multiplier"])*negotiation_multiplier*role_multiplier)
            fee_offer=int(row.get("fee_offer") or 0); salary_offer=int(row.get("salary_offer") or 0); years=int(row.get("contract_years") or 3)
            if str(row.get("deal_type") or "transfer")=="loan":
                reserve=bool(raw.get("initially_reserve")); share=int(row.get("loan_wage_share") or 0)
                loan_floor=max(0,round(estimated_transfer_value(raw,overall=overall)*(.008 if wants_move or reserve else .018)))
                share_floor=40 if wants_move or reserve else 65
                if fee_offer>=loan_floor and share>=share_floor:
                    deal=self._complete_user_loan(player_id=pid,seller=seller,loan_fee=fee_offer,wage_share=share,date_text=day.isoformat(),squad_role=str(row.get("squad_role") or "rotation"))
                    row.update({"status":"completed","completed_on":day.isoformat(),"loan_deal_id":deal["id"],"fee":fee_offer}); row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"loan_accepted","fee":fee_offer,"wage_share":share})
                    events.append({"kind":"user_loan_completed","date":day.isoformat(),"player_id":pid,"fee":fee_offer,"wage_share":share}); continue
                row.update({"status":"countered","reason":"loan_terms","counter_fee":max(fee_offer,loan_floor),"counter_wage_share":max(share,share_floor),"counter_salary":0})
                row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"loan_counter","fee":max(fee_offer,loan_floor),"wage_share":max(share,share_floor)})
                events.append({"kind":"transfer_counteroffer","date":day.isoformat(),"player_id":pid,"counter_fee":max(fee_offer,loan_floor),"counter_wage_share":max(share,share_floor),"reason":"loan_terms"}); continue
            if seller==0:
                fee_decision={"accepted":True,"fee":0,"counter_fee":0,"estimated_value":estimated_transfer_value(raw,overall=overall)}
            else:
                fee_decision=negotiate_transfer(player=self._career_player_api(raw),current_overall=overall,buyer_cash=transfer_spending_power(self.state["finances"]),fee_offer=fee_offer,salary_offer=salary_offer,contract_years=years)
            # A concrete rival can close the deal if the user drags a contested
            # negotiation through multiple rounds with a clearly weaker package.
            if row.get("rival_interest") and seller and int(row.get("round") or 1)>=2 and row.get("rival_team_id"):
                rival_tid=int(row["rival_team_id"]);rival_fee=int(row.get("rival_fee") or 0);rival_salary=int(row.get("rival_salary") or 0)
                rival_fin=self.state.get("club_finances",{}).get(str(rival_tid)) or {}
                rival_ok,_=self._signing_eligibility(rival_tid,raw,day=day)
                rival_wage_room=wage_budget_headroom(
                    rival_fin,players=self._career_players_by_team.get(rival_tid,[]),
                    development=self.state.get("player_development") or {},contract_overrides=self.state.get("contract_overrides") or {},
                )
                if rival_ok and transfer_spending_power(rival_fin)>=rival_fee and rival_salary<=rival_wage_room and (fee_offer<rival_fee or salary_offer<round(rival_salary*.95)):
                    spend_transfer_funds(rival_fin,rival_fee,recorded_fee=rival_fee)
                    if str(seller) in self.state.get("club_finances",{}):
                        sf=self.state["club_finances"][str(seller)];receive_transfer_funds(sf,rival_fee)
                    self.state["player_team_overrides"][str(pid)]=rival_tid
                    self.state["contract_overrides"][str(pid)]={"start":str(day.year),"end":str(day.year+3),"end_year":day.year+3,"salary":rival_salary,"salary_display":f"{rival_salary:,} ptas.".replace(",","."),"loan":False,"career_inferred":True,"signed_by_ai":True}
                    row.update({"status":"lost_to_rival","completed_on":day.isoformat(),"reason":"competencia","winner_team_id":rival_tid});row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"lost_to_rival","team_id":rival_tid,"fee":rival_fee,"salary":rival_salary})
                    event={"kind":"transfer_lost_to_rival","date":day.isoformat(),"player_id":pid,"to_team_id":rival_tid,"fee":rival_fee};events.append(event);self.state["ai_transfer_history"].append(event);self._rebuild_rosters();continue
            # Rival interest makes waiting costly without forcing every first
            # contact into an instant auction.
            if row.get("rival_interest") and seller and fee_decision.get("accepted") and int(row.get("round") or 1)==1:
                rival_floor=round(int(fee_decision.get("estimated_value") or fee_offer)*1.02)
                if fee_offer<rival_floor:
                    fee_decision={**fee_decision,"accepted":False,"reason":"competencia","counter_fee":rival_floor}
            wage_room=self._current_wage_headroom()
            if fee_decision.get("accepted") and salary_offer>=salary_min and salary_offer<=wage_room:
                transfer=self._complete_user_transfer(player_id=pid,seller=seller,fee=int(fee_decision.get("fee") or 0),salary=salary_offer,years=years,date_text=day.isoformat(),source="negotiation",signing_bonus=int(row.get("signing_bonus") or 0),release_clause=row.get("release_clause"),squad_role=str(row.get("squad_role") or "rotation"))
                row.update({"status":"completed","completed_on":day.isoformat(),"fee":transfer["fee"],"salary":salary_offer}); row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"accepted","fee":transfer["fee"],"salary":salary_offer})
                events.append({"kind":"user_transfer_completed","date":day.isoformat(),"player_id":pid,"fee":transfer["fee"]})
            else:
                counter_fee=int(fee_decision.get("counter_fee") or fee_offer)
                if str(fee_decision.get("reason") or "") == "oferta_insuficiente":
                    counter_fee=max(fee_offer,round(counter_fee*negotiation_multiplier))
                counter_salary=max(salary_min,int(row.get("salary_offer") or 0))
                if fee_decision.get("accepted") and salary_offer>wage_room:
                    reason="presupuesto_salarial_insuficiente"
                else:
                    reason="salario_insuficiente" if fee_decision.get("accepted") and salary_offer<salary_min else str(fee_decision.get("reason") or "oferta_insuficiente")
                row.update({"status":"countered","reason":reason,"counter_fee":counter_fee,"counter_salary":counter_salary,"wage_budget_headroom":wage_room})
                row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"counter","fee":counter_fee,"salary":counter_salary,"reason":reason})
                events.append({"kind":"transfer_counteroffer","date":day.isoformat(),"player_id":pid,"counter_fee":counter_fee,"counter_salary":counter_salary,"reason":reason})
        return events

    def list_player_for_transfer(self, player_id:int, *, asking_price:int|None=None) -> dict[str,Any]:
        pid=int(player_id); controlled=int(self.state["team_id"])
        if self._player_source(pid) is None: raise KeyError(f"jugador {pid} no existe")
        if self._current_team_id(pid)!=controlled: raise ValueError("sólo puedes poner transferibles futbolistas de tu club")
        if bool((self.state.get("contract_overrides") or {}).get(str(pid),{}).get("loan")): raise ValueError("un jugador cedido debe volver a su club antes de poder ofrecerlo en propiedad")
        raw=self._player_source(pid); overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60); value=estimated_transfer_value(raw,overall=overall)
        row={"player_id":pid,"listed_on":self.current_date.isoformat(),"asking_price":int(asking_price if asking_price is not None else value),"estimated_value":value}
        self.state["transfer_listings"][str(pid)]=row
        adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=-12,reason="puesto en el mercado por el mánager")
        return row

    def unlist_player(self, player_id:int) -> None:
        pid=int(player_id)
        existed=str(pid) in self.state.get("transfer_listings",{})
        self.state.get("transfer_listings",{}).pop(str(pid),None)
        if existed:
            adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=2,reason="retirado de la lista de transferibles")

    def _process_user_listings(self, day:date) -> list[dict[str,Any]]:
        events=[]; controlled=int(self.state["team_id"]); offers=self.state.setdefault("incoming_transfer_offers",[])
        for pid_text,listing in list((self.state.get("transfer_listings") or {}).items()):
            pid=int(pid_text)
            if self._current_team_id(pid)!=controlled: self.state["transfer_listings"].pop(pid_text,None);continue
            if any(int(o.get("player_id") or 0)==pid and o.get("status")=="open" for o in offers): continue
            if day<=date.fromisoformat(str(listing["listed_on"])): continue
            raw=self._player_source(pid); overall=int(self.state["player_development"].get(pid_text,{}).get("overall") or raw.get("overall") or raw.get("category") or 60); value=int(listing.get("estimated_value") or estimated_transfer_value(raw,overall=overall)); asking=int(listing.get("asking_price") or value)
            rng=Random(int(self.state["seed"]) ^ pid*9394 ^ day.toordinal())
            chance=.12 + max(0,min(.28,(value/max(1,asking)-.7)*.5))
            if rng.random()>chance: continue
            candidates=[]
            target_slot=role_for_player(raw).squad_slot
            for tid in self._active_club_ids():
                if tid==controlled: continue
                eligible,_=self._signing_eligibility(tid,raw,day=day)
                if not eligible: continue
                fin=self.state["club_finances"].get(str(tid),{}); cash=transfer_spending_power(fin)
                if cash<value*.75: continue
                squad=self._career_players_by_team.get(tid,[]); audit=squad_audit(squad,self.state["player_development"]); target_need=next((n for n in audit["needs"] if n["slot"]==target_slot),{"shortage":0})
                need=int(target_need["shortage"])*3+max(0,20-len(squad))+float(club_status(self.state,tid).get("score") or 50)/100
                candidates.append((need+rng.random(),tid,cash))
            if not candidates: continue
            candidates.sort(reverse=True); buyer=candidates[0][1]; fee=round(value*(.82+rng.random()*.20)); fee=min(fee,transfer_spending_power(self.state["club_finances"][str(buyer)]))
            offer={"id":f"sale:{pid}:{day.isoformat()}:{buyer}","date":day.isoformat(),"expires_on":(day+timedelta(days=4)).isoformat(),"player_id":pid,"buyer_team_id":buyer,"buyer_team_name":(self._team_api(buyer) or {}).get("name"),"fee":fee,"status":"open"}
            offers.append(offer);events.append({"kind":"incoming_transfer_offer",**offer})
        for offer in offers:
            if offer.get("status")=="open" and date.fromisoformat(str(offer["expires_on"]))<day: offer["status"]="expired"
        return events

    def accept_incoming_transfer_offer(self, offer_id:str) -> dict[str,Any]:
        offer=next((o for o in self.state.get("incoming_transfer_offers",[]) if o.get("id")==offer_id),None)
        if offer is None: raise KeyError("oferta no encontrada")
        if offer.get("status")!="open": raise ValueError("la oferta ya no está disponible")
        pid=int(offer["player_id"]);controlled=int(self.state["team_id"]);buyer=int(offer["buyer_team_id"]);fee=int(offer["fee"])
        if self._current_team_id(pid)!=controlled: raise ValueError("el jugador ya no pertenece a tu club")
        current_squad=self._career_players_by_team.get(controlled,[])
        if len(current_squad)-1 < MINIMUM_SENIOR_SQUAD_SIZE_9394:
            raise ValueError(f"la plantilla sénior no puede quedar por debajo de {MINIMUM_SENIOR_SQUAD_SIZE_9394} jugadores")
        eligible,reason=self._signing_eligibility(buyer,self._player_source(pid))
        if not eligible: offer["status"]="withdrawn";raise ValueError(f"el comprador no puede inscribir al jugador: {reason}")
        buyer_fin=self.state["club_finances"][str(buyer)]
        if transfer_spending_power(buyer_fin)<fee: offer["status"]="withdrawn";raise ValueError("el comprador ya no dispone de presupuesto de fichajes")
        raw=self._player_source(pid);overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60); salary=round(inferred_annual_salary(raw,overall=overall)*1.04); years=3
        buyer_wage_room=wage_budget_headroom(
            buyer_fin,players=self._career_players_by_team.get(buyer,[]),development=self.state.get("player_development") or {},
            contract_overrides=self.state.get("contract_overrides") or {},
        )
        if salary>buyer_wage_room: offer["status"]="withdrawn";raise ValueError("el comprador ya no dispone de margen salarial")
        seller_fin=self.state["club_finances"][str(controlled)]; spend_transfer_funds(buyer_fin,fee,recorded_fee=fee); receive_transfer_funds(seller_fin,fee)
        register_important_departure(self.state,player_id=pid,players_before=list(current_squad),date_text=self.current_date.isoformat())
        self.state["player_team_overrides"][str(pid)]=buyer; self.state["contract_overrides"][str(pid)]={"start":str(self.current_date.year),"end":str(self.current_date.year+years),"end_year":self.current_date.year+years,"salary":salary,"salary_display":f"{salary:,} ptas.".replace(",","."),"career_inferred":True,"signed_by_ai":True,"loan":False}
        offer["status"]="accepted"; self.state["transfer_listings"].pop(str(pid),None); record={"kind":"user_sale","date":self.current_date.isoformat(),"player_id":pid,"from_team_id":controlled,"to_team_id":buyer,"fee":fee,"accepted":True};self.state["transfer_history"].append(record);self.state["economy_ledger"].append({"date":self.current_date.isoformat(),"kind":"transfer_income","amount":fee,"player_id":pid})
        post_long_economy(self.state,team_id=controlled,season=str(self.state["season"]),category="transfer_income",amount=fee)
        post_long_economy(self.state,team_id=buyer,season=str(self.state["season"]),category="transfer_spend",amount=fee)
        pressure_before=dict(((self.state.get("board_projects") or {}).get(str(controlled)) or {}).get("sale_pressure") or {})
        pressure_after=register_sale_income(self.state,team_id=controlled,amount=fee,date_text=self.current_date.isoformat())
        if pressure_after and pressure_before.get("status")=="active" and pressure_after.get("status")=="resolved":
            event={"kind":"board_sale_pressure_resolved","date":self.current_date.isoformat(),"team_id":controlled,"amount":fee,"player_id":pid}
            self.state.setdefault("world_events",[]).append(event); self._ingest_news([event])
        record_transfer_memory(self.state,self.universe,date_text=self.current_date.isoformat(),player_id=pid,from_team_id=controlled,to_team_id=buyer,fee=fee,player_overall=overall)
        self.state["finances"]=seller_fin;self._rebuild_rosters()
        if not self.selection_snapshot()["valid"]: self.state["selection"]=self._auto_selection()
        return record

    def set_captain(self, player_id:int) -> dict[str,Any]:
        controlled=int(self.state["team_id"])
        result=set_dressing_room_captain(self.state,player_id=int(player_id),players=self._career_players_by_team.get(controlled,()),date_text=self.current_date.isoformat())
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {**result,"dressing_room":dressing_room_snapshot(self.state,players=self._career_players_by_team.get(controlled,()),game_date=self.current_date)}

    def set_role_promise(self, player_id:int, role:str) -> dict[str,Any]:
        controlled=int(self.state["team_id"])
        result=set_dressing_room_role_promise(self.state,player_id=int(player_id),role=str(role),players=self._career_players_by_team.get(controlled,()),date_text=self.current_date.isoformat())
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {**result,"player":self.player_detail(int(player_id)),"dressing_room":dressing_room_snapshot(self.state,players=self._career_players_by_team.get(controlled,()),game_date=self.current_date)}

    def respond_dressing_room_concern(self, concern_id: str, response: str) -> dict[str, Any]:
        row=respond_dressing_concern(self.state,concern_id=str(concern_id),response=str(response),date_text=self.current_date.isoformat())
        controlled=int(self.state["team_id"])
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {"resolution":row,"dressing_room":dressing_room_snapshot(self.state,players=self._career_players_by_team.get(controlled,()),game_date=self.current_date)}

    def discipline_player(self, player_id: int, action: str) -> dict[str, Any]:
        pid=int(player_id)
        if self._current_team_id(pid)!=int(self.state["team_id"]): raise ValueError("sólo puedes disciplinar futbolistas de tu plantilla")
        raw=self._player_source(pid) or {}; dev=self.state.get("player_development",{}).get(str(pid),{})
        justified=bool(int(dev.get("season_reds") or raw.get("season_reds") or 0)>0 or int(dev.get("red_cards") or 0)>0)
        row=register_dressing_discipline(self.state,player_id=pid,action=str(action),date_text=self.current_date.isoformat(),justified=justified)
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {"discipline":row,"player":self.player_detail(pid)}

    def market_snapshot(self) -> dict[str,Any]:
        ensure_market_flow_state(self.state)
        period=self.transfer_period_snapshot(); rule=self._domestic_foreign_rule(); squad=self._career_players_by_team.get(int(self.state["team_id"]),[])
        scouting=self.scouting_snapshot(); squad_plan=self.squad_plan_snapshot()
        raw_negotiations=list(self.state["transfer_negotiations"].values()); raw_inquiries=list(self.state.get("market_inquiries") or [])[-30:]
        today=self.current_date
        inquiries=[]
        for source in raw_inquiries:
            row=dict(source)
            expires=row.get("expires_on")
            active=not expires or date.fromisoformat(str(expires))>=today
            row["status"]="active" if active else "expired"
            row["status_label"]="Consulta vigente" if active else "Consulta caducada"
            row["next_step"]=("Puedes usar esta referencia para comparar y preparar una oferta." if active and period.get("open") else
                              "Puedes seguir comparando y actualizando información; las altas están cerradas." if active else
                              "Actualiza la consulta si vuelves a considerar al jugador.")
            inquiries.append(row)
        negotiations=[]
        for source in raw_negotiations:
            row=dict(source)
            status=str(row.get("status") or "")
            active=status in {"waiting","countered"}
            window_blocked=bool(active and not period.get("open"))
            row["window_blocked"]=window_blocked
            row["requires_action"]=status=="countered"
            row["status_label"]=("Mercado cerrado" if window_blocked else "Requiere decisión" if status=="countered" else "Esperando respuesta" if status=="waiting" else
                                 "Completada" if status=="completed" else "Perdida" if status=="lost_to_rival" else "Cerrada")
            row["next_step"]=("Retira la operación o espera a que el proceso se cierre; no puedes registrar al jugador ahora." if window_blocked else
                              "Acepta las condiciones implícitas respondiendo con la contraoferta, mejora tu propuesta o retírate." if status=="countered" else
                              f"La respuesta está prevista para {row.get('response_date') or 'los próximos días'}." if status=="waiting" else
                              "La consecuencia ya está aplicada a plantilla, economía y memoria de mercado.")
            negotiations.append(row)
        active_negotiations=[row for row in negotiations if row.get("status") in {"waiting","countered"}]
        waiting=[row for row in active_negotiations if row.get("status")=="waiting"]
        countered=[row for row in active_negotiations if row.get("status")=="countered"]
        incoming_open=[dict(row) for row in self.state["incoming_transfer_offers"] if row.get("status")=="open"]
        recruitment=self._responsibility_effect("recruitment_search")
        negotiation=self._responsibility_effect("transfer_negotiation")
        transfer_room=transfer_spending_power(self.state.get("finances") or {})
        wage_room=self._current_wage_headroom()
        committed_transfer=sum(max(0,int(row.get("fee_offer") or 0))+max(0,int(row.get("signing_bonus") or 0)) for row in active_negotiations)
        committed_wages=sum(max(0,int(row.get("salary_offer") or 0)) for row in active_negotiations if str(row.get("deal_type") or "transfer")=="transfer")
        processes=[]
        for task in scouting.get("active") or []:
            processes.append({
                "id":str(task.get("id")),"stage":"informe","player_id":int(task.get("player_id") or 0),"player_name":task.get("player_name"),
                "owner":task.get("responsible") or recruitment.get("assignee_name"),"status":"En curso","requires_action":False,
                "next_step":f"Informe previsto para {task.get('due_on') or 'los próximos días'}.",
                "consequence":"Al completarse aumentará la confianza del dossier y reducirá incertidumbre antes de negociar.",
            })
        for row in [item for item in inquiries if item.get("status")=="active"][-4:]:
            processes.append({
                "id":str(row.get("id")),"stage":"consulta","player_id":int(row.get("player_id") or 0),"player_name":row.get("player_name"),
                "owner":row.get("handled_by") or negotiation.get("assignee_name"),"status":row.get("status_label"),"requires_action":False,
                "next_step":row.get("next_step"),"consequence":"Sirve de referencia de precio y postura; no compromete presupuesto por sí sola.",
            })
        for row in active_negotiations:
            processes.append({
                "id":str(row.get("id")),"stage":"negociación","player_id":int(row.get("player_id") or 0),"player_name":self._player_name(int(row.get("player_id") or 0)),
                "owner":row.get("handled_by") or negotiation.get("assignee_name"),"status":row.get("status_label"),"requires_action":bool(row.get("requires_action")),
                "blocked_by_window":bool(row.get("window_blocked")),"next_step":row.get("next_step"),
                "consequence":"Si se cierra, actualizará plantilla, presupuesto, salario, rol prometido, vestuario y noticias.",
            })
        workflow={
            "journey":["Necesidad","Búsqueda","Seguimiento","Informe","Consulta","Negociación","Decisión","Consecuencia"],
            "steps":[
                {"key":"need","label":"Necesidad","count":len(squad_plan.get("priorities") or []),"state":"attention" if squad_plan.get("priorities") else "clear","owner":"Plantilla"},
                {"key":"search","label":"Seguimiento","count":len(self.state["watchlist"]),"state":"active" if self.state["watchlist"] else "idle","owner":recruitment.get("assignee_name") or "Responsable de scouting"},
                {"key":"scout","label":"Informes","count":len(scouting.get("active") or []),"state":"active" if scouting.get("active") else "idle","owner":recruitment.get("assignee_name") or "Responsable de scouting"},
                {"key":"inquiry","label":"Consulta","count":len([row for row in inquiries if row.get("status")=="active"]),"state":"active" if any(row.get("status")=="active" for row in inquiries) else "idle","owner":negotiation.get("assignee_name") or "Responsable de mercado"},
                {"key":"deal","label":"Negociación","count":len(active_negotiations),"state":"attention" if countered else "waiting" if waiting else "idle","owner":negotiation.get("assignee_name") or "Responsable de mercado"},
            ],
            "action_required":len(countered)+len(incoming_open),
            "waiting_count":len(waiting)+len(scouting.get("active") or []),
            "blocked_by_window":sum(1 for row in active_negotiations if row.get("window_blocked")),
            "recruitment_owner":recruitment,
            "negotiation_owner":negotiation,
            "window_policy":{
                "can_search":True,"can_scout":True,"can_inquire":True,"can_offer":bool(period.get("open")),
                "label":"Seguimiento abierto · inscripciones cerradas" if not period.get("open") else "Operativa de mercado disponible",
                "detail":"El cierre impide nuevas altas y contraofertas, pero no detiene búsqueda, scouting ni comparación de alternativas." if not period.get("open") else "Puedes investigar, consultar y negociar; sólo las decisiones reales deben interrumpir Continuar.",
            },
        }
        recent_outcomes=[]
        for row in reversed(negotiations):
            if row.get("status") in {"waiting","countered"}: continue
            recent_outcomes.append({
                "id":row.get("id"),"player_id":row.get("player_id"),"player_name":self._player_name(int(row.get("player_id") or 0)),
                "status":row.get("status"),"status_label":row.get("status_label"),"detail":row.get("detail") or row.get("reason") or "Proceso cerrado",
            })
            if len(recent_outcomes)>=5: break
        return {
            "watchlist":list(self.state["watchlist"]),"negotiations":negotiations,"inquiries":inquiries,"loans":list(self.state.get("loan_deals") or [])[-40:],"listings":list(self.state["transfer_listings"].values()),"incoming_offers":list(self.state["incoming_transfer_offers"])[-30:],
            "period":period,"foreign_rule":rule.as_dict() if rule else None,"foreign_count":foreign_count(squad,rule) if rule else 0,"club_status":self.club_status_snapshot(),
            "recruitment_plan":dict((self.state.get("recruitment_plans") or {}).get(str(int(self.state["team_id"]))) or {}),"market_storylines":list(self.state.get("market_storylines") or [])[-30:],
            "scouting":scouting,"squad_plan":squad_plan,"workflow":workflow,"processes":processes[-12:],"recent_outcomes":recent_outcomes,
            "budget_context":{
                "transfer_room":int(transfer_room),"wage_headroom":int(wage_room),"open_offer_commitment":int(committed_transfer),"open_wage_commitment":int(committed_wages),
                "transfer_room_if_all_open_accepted":max(0,int(transfer_room)-int(committed_transfer)),
                "wage_headroom_if_all_open_accepted":max(0,int(wage_room)-int(committed_wages)),
            },
            "squad_size":len(squad),"minimum_squad_size":MINIMUM_SENIOR_SQUAD_SIZE_9394,"target_squad_size":TARGET_SENIOR_SQUAD_SIZE_9394,
        }

    def _current_wage_headroom(self, *, exclude_player_id: int | None = None) -> int:
        controlled=int(self.state["team_id"])
        return wage_budget_headroom(
            self.state.get("finances") or {}, players=self._career_players_by_team.get(controlled,[]),
            development=self.state.get("player_development") or {}, contract_overrides=self.state.get("contract_overrides") or {},
            exclude_player_id=exclude_player_id,
        )

    def economy_snapshot(self) -> dict[str,Any]:
        team_id=int(self.state["team_id"]); team=self.universe.team(team_id) or {}; players=self._career_players_by_team.get(team_id,[])
        base=economy_snapshot(team=team,finances=self.state["finances"],players=players,development=self.state["player_development"],contract_overrides=self.state["contract_overrides"],ledger=self.state["economy_ledger"],stature_score=float(club_status(self.state,team_id).get("score") or 50.0),accounting_month=self.current_date.month)
        health=financial_health(
            cash=int(base.get("cash") or 0),debt=int(base.get("debt") or 0),projected_monthly_net=int(base.get("projected_monthly_net") or 0),
            safety_reserve=int(base.get("safety_reserve") or 0),annual_wages=int(base.get("annual_wages") or 0),starting_budget=int((self.state.get("club_finances") or {}).get(str(team_id),{}).get("starting_budget") or team.get("budget") or 0),
        )
        project=project_snapshot(self.state,team_id)
        return {**base,"health":health,"longitudinal":longitudinal_snapshot(self.state,team_id=team_id,season=str(self.state["season"])),"sale_pressure":project.get("sale_pressure"),"board_transfer_adjustment":int(project.get("budget_adjustment") or 0)}

    def renew_player_contract(self, player_id: int, *, years: int = 3, salary_offer: int | None = None) -> dict[str, Any]:
        pid=int(player_id); controlled=int(self.state["team_id"])
        if self._player_source(pid) is None:
            raise KeyError(f"jugador {pid} no existe")
        if self._current_team_id(pid) != controlled:
            raise ValueError("sólo puedes renovar futbolistas de tu club")
        if bool((self.state.get("contract_overrides") or {}).get(str(pid),{}).get("loan")):
            raise ValueError("el contrato pertenece al club de origen mientras el jugador está cedido")
        if not 1 <= int(years) <= 6:
            raise ValueError("la renovación debe durar entre 1 y 6 años")
        raw=self._player_source(pid)
        overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        current=effective_contract(raw,overall=overall,override=self.state["contract_overrides"].get(str(pid)))
        relationship=relationship_api(self.state,pid)
        trust=int(relationship.get("trust") or 55)
        trust_multiplier=max(.88,min(1.16,1.0 + (55-trust)*.004))
        wants_move=bool(dynamics_api(self.state,pid).get("wants_move"))
        retention_multiplier=trust_multiplier*(1.08 if wants_move else 1.0)
        minimum=round(max(inferred_annual_salary(raw,overall=overall),int(current.get("salary") or 0))*.96*retention_multiplier)
        offered=minimum if salary_offer is None else int(salary_offer)
        wage_room=self._current_wage_headroom(exclude_player_id=pid)
        accepted=offered>=minimum and offered<=wage_room
        record={"kind":"user_renewal","date":self.state["current_date"],"player_id":pid,"years":int(years),"salary_offer":offered,"minimum_salary":minimum,"accepted":accepted,"relationship_trust":trust,"relationship_multiplier":round(trust_multiplier,3),"wants_move":wants_move,"wage_budget_headroom":wage_room}
        if accepted:
            year=self.current_date.year
            self.state["contract_overrides"][str(pid)]={**current,"start":str(year),"end":str(year+int(years)),"end_year":year+int(years),"salary":offered,"salary_display":f"{offered:,} ptas.".replace(",","."),"career_inferred":True,"renewed_by_user":True}
            adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=7,reason="renovación acordada")
        else:
            record["counter_salary"]=minimum
            record["reason"]="presupuesto_salarial_insuficiente" if offered>wage_room else "salario_insuficiente"
            adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=-2,reason="oferta de renovación insuficiente")
        register_contract_decision(self.state, player_id=pid, accepted=accepted, date_text=self.current_date.isoformat())
        self.state["contract_history"].append(record)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return record
