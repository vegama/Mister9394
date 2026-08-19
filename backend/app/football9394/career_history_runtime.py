from __future__ import annotations

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
from .domestic_cups import DOMESTIC_CUPS_9394, CWC_BASELINE_REPRESENTATIVE_BY_COUNTRY_9394, CWC_BASELINE_DEFENDING_CHAMPION_9394
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


class CareerHistoryRuntimeMixin:
    """Extracted V1.0-M runtime responsibilities; behavior is characterized by regression tests."""

    def league_standings(self, source_id: int) -> list[dict[str, Any]]:
        source_id=int(source_id)
        if source_id == int(self.state.get("league_id") or 0):
            return self.standings()
        league_state=(self.state.get("world_leagues") or {}).get(str(source_id))
        if league_state is None:
            return []
        rules=self._league_rules(source_id)
        matches=[LeagueMatch9394(str(r["home_team_id"]),str(r["away_team_id"]),int(r["home_goals"]),int(r["away_goals"])) for r in league_state.get("results") or []]
        ids=[str(team["source_id"]) for team in self._teams_for_league(source_id)]
        table=build_league_table(ids,matches,rules)
        return [{
            "team_id":int(row.team_id),"team_name":(self._team_api(int(row.team_id)) or {}).get("name",row.team_id),
            "position":row.position,"played":row.played,"wins":row.wins,"draws":row.draws,
            "losses":row.losses,"goals_for":row.goals_for,"goals_against":row.goals_against,
            "goal_difference":row.goal_difference,"points":row.points,
        } for row in table]

    def _league_result_rows(self, source_id: int) -> list[dict[str, Any]]:
        source_id=int(source_id)
        if source_id == int(self.state.get("league_id") or 0):
            return [{**row, "round": int(row.get("matchday") or row.get("round") or 0)} for row in self.state.get("results") or []]
        return list(((self.state.get("world_leagues") or {}).get(str(source_id)) or {}).get("results") or [])

    def _honour(self, *, competition_kind: str, source_id: int, name: str, champion_team_id: int) -> dict[str, Any]:
        team_id=int(champion_team_id)
        team=self._team_api(team_id) or self.universe.team(team_id) or {}
        dev=self.state.get("player_development") or {}
        squad=[]
        for player in self._career_players_by_team.get(team_id, []):
            pid=int(player.get("source_id") or 0)
            if pid<=0: continue
            d=dev.get(str(pid)) or {}
            squad.append({
                "player_id":pid,
                "name":player.get("display_name") or player.get("name") or str(pid),
                "position":player.get("position") or player.get("broad_position") or "—",
                "overall":int(d.get("overall") or player.get("overall") or player.get("category") or 60),
                "shirt_number":player.get("shirt_number") or player.get("number"),
            })
        squad.sort(key=lambda row:(str(row.get("position") or ""),-int(row.get("overall") or 0),str(row.get("name") or "")))
        coach=self._coach_profile(team_id) or {}
        manager={
            "id":coach.get("id") or coach.get("source_id"),
            "name":coach.get("name") or coach.get("display_name") or "Entrenador",
            "primary_tactic":coach.get("primary_tactic"),
            "game_tendency":coach.get("game_tendency"),
        }
        return {
            "season": str(self.state["season"]), "competition_kind": competition_kind,
            "source_id": int(source_id), "competition_name": name,
            "team_id": team_id, "team_name": team.get("name") or str(team_id),
            "honour": "Campeón",
            # Frozen at the moment the trophy is archived so future transfers or
            # managerial changes never rewrite who actually lifted it.
            "champion_manager":manager,"champion_squad":squad,
        }

    def _archive_honours(self, tables: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        honours: list[dict[str, Any]]=[]
        for source_id,table in tables.items():
            if not table:
                continue
            comp=self.universe.leagues_by_id.get(int(source_id)) or {}
            honour=self._honour(competition_kind="league",source_id=source_id,name=str(comp.get("name") or f"Liga {source_id}"),champion_team_id=int(table[0]["team_id"]))
            if len(table)>1:
                runner=int(table[1].get("team_id") or 0)
                honour["runner_up_team_id"]=runner or None
                honour["runner_up_team_name"]=self._team_name(runner) if runner else None
                honour["margin_points"]=int(table[0].get("points") or 0)-int(table[1].get("points") or 0)
                honour["champion_points"]=int(table[0].get("points") or 0)
            honours.append(honour)
        for key,special in (self.state.get("special_competitions") or {}).items():
            champion=special.get("champion_team_id")
            if champion:
                honours.append(self._honour(competition_kind="league",source_id=int(key),name=str(special.get("name") or f"Liga {key}"),champion_team_id=int(champion)))
        for key,tournament in (self.state.get("daily_tournaments") or {}).items():
            champion=tournament.get("champion_team_id")
            if champion:
                honour=self._honour(competition_kind="tournament",source_id=int(key),name=str(tournament.get("name") or f"Torneo {key}"),champion_team_id=int(champion))
                runner=int(tournament.get("runner_up_team_id") or 0)
                if runner:
                    honour["runner_up_team_id"]=runner;honour["runner_up_team_name"]=self._team_name(runner)
                honours.append(honour)
        for row in honours:
            self.state["honours"].append(row)
            self.state["club_honours"].setdefault(str(row["team_id"]),[]).append(row)
        return honours

    def _promotion_eligible(self, team_id: int, *, target_league_id: int) -> bool:
        team=self.universe.team(int(team_id)) or {}
        parent=team.get("reserve_of")
        if not parent or int(team.get("reserve_step") or 0) <= 0:
            return True
        parent_league=self._current_league_for_team(int(parent))
        if target_league_id == 1:
            return False
        if target_league_id == 2:
            return parent_league == 1
        return True

    def _spain_rollover(self, tables: dict[int,list[dict[str,Any]]]) -> list[dict[str,Any]]:
        movements: list[dict[str,Any]]=[]
        if not all(tables.get(lid) for lid in (1,2,3,9,10,11)):
            return movements
        primera=tables[1]; segunda=tables[2]
        primera_ids=list((self.state["league_memberships"])["1"]); segunda_ids=list((self.state["league_memberships"])["2"])
        direct_down=[int(row["team_id"]) for row in primera[18:20]]
        segunda_eligible=[int(row["team_id"]) for row in segunda if self._promotion_eligible(int(row["team_id"]),target_league_id=1)]
        direct_up=segunda_eligible[:2]; playoff_candidates=segunda_eligible[2:4]
        primera_playoff=[int(primera[16]["team_id"]),int(primera[17]["team_id"])]
        if len(playoff_candidates)<2:
            raise ValueError("Segunda no dispone de dos candidatos elegibles para la promoción")
        sheets={str(tid):self._sheet(tid) for tid in primera_playoff+playoff_candidates}
        playoff_up=[]; playoff_down=[]
        seed0=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000
        for idx,(top_id,candidate) in enumerate(zip(primera_playoff,playoff_candidates,strict=True)):
            tie=_play_primera_segunda_tie(str(top_id),str(candidate),sheets,seed=seed0+210000+idx*100)
            if int(tie.winner_team_id)==candidate:
                playoff_up.append(candidate); playoff_down.append(top_id)
        promoted_to_primera=direct_up+playoff_up; relegated_to_segunda=direct_down+playoff_down
        self.state["league_memberships"]["1"]=[tid for tid in primera_ids if tid not in relegated_to_segunda]+promoted_to_primera
        # Segunda B promotion uses the actual four group tables. The represented
        # B tier is the data floor: promoted clubs leave, but nobody is sent to
        # an invented Tercera; relegated Segunda clubs fill those vacancies.
        relegated_from_segunda=[int(row["team_id"]) for row in segunda[16:20]]
        qualifiers_by_group=[]
        for lid in (3,9,10,11):
            eligible=[]
            for row in tables[lid]:
                tid=int(row["team_id"]); team=self.universe.team(tid) or {}; parent=team.get("reserve_of")
                if not parent or int(team.get("reserve_step") or 0)<=0 or self._current_league_for_team(int(parent))==1:
                    eligible.append(tid)
                if len(eligible)==4: break
            if len(eligible)!=4:
                raise ValueError(f"Segunda B {lid}: faltan cuatro clubes elegibles para la promoción")
            qualifiers_by_group.append(eligible)
        rng=Random(seed0 ^ 0xB9394); offsets=[0,1,2,3]; rng.shuffle(offsets)
        promoted_from_b=[]; origin: dict[int,int]={}
        all_sheets={}
        for lid,qualifiers in zip((3,9,10,11),qualifiers_by_group,strict=True):
            for tid in qualifiers: all_sheets[str(tid)]=self._sheet(tid); origin[tid]=lid
        for pool in range(4):
            ids=tuple(str(qualifiers_by_group[src][(pool+offsets[src])%4]) for src in range(4))
            group=_play_promotion_group(chr(65+pool),ids,all_sheets,seed_base=seed0+310000+pool*1000)
            winner=int(group.promoted_team_id)
            team=self.universe.team(winner) or {}; parent=team.get("reserve_of")
            # A simultaneous parent relegation cancels a reserve promotion.
            if parent and int(parent) in relegated_to_segunda:
                replacement=next((int(r.team_id) for r in group.table[1:] if not (self.universe.team(int(r.team_id)) or {}).get("reserve_of")),None)
                if replacement is None: raise ValueError("no hay sustituto elegible en una liguilla de Segunda B")
                winner=replacement
            promoted_from_b.append(winner)
        new_segunda=[tid for tid in segunda_ids if tid not in promoted_to_primera and tid not in relegated_from_segunda]+relegated_to_segunda+promoted_from_b
        if len(new_segunda)!=len(segunda_ids) or len(set(new_segunda))!=len(new_segunda):
            raise AssertionError("el rollover de Segunda no conserva veinte clubes únicos")
        self.state["league_memberships"]["2"]=new_segunda
        incoming=list(relegated_from_segunda); cursor=0
        for lid in (3,9,10,11):
            current=list(self.state["league_memberships"][str(lid)])
            outgoing=[tid for tid in promoted_from_b if origin.get(tid)==lid]
            remaining=[tid for tid in current if tid not in outgoing]
            vacancies=len(current)-len(remaining)
            additions=incoming[cursor:cursor+vacancies]; cursor+=vacancies
            self.state["league_memberships"][str(lid)]=remaining+additions
        if cursor!=len(incoming):
            raise AssertionError("las vacantes de Segunda B no absorben los cuatro descensos de Segunda")
        for tid in promoted_to_primera: movements.append({"team_id":tid,"from_league_id":2,"to_league_id":1,"reason":"promotion"})
        for tid in relegated_to_segunda: movements.append({"team_id":tid,"from_league_id":1,"to_league_id":2,"reason":"relegation"})
        for tid in promoted_from_b: movements.append({"team_id":tid,"from_league_id":origin.get(tid),"to_league_id":2,"reason":"promotion"})
        for tid in relegated_from_segunda:
            target=next(lid for lid in (3,9,10,11) if tid in self.state["league_memberships"][str(lid)])
            movements.append({"team_id":tid,"from_league_id":2,"to_league_id":target,"reason":"relegation"})
        return movements

    def _italy_rollover(self, tables: dict[int,list[dict[str,Any]]]) -> list[dict[str,Any]]:
        if not tables.get(4) or not tables.get(102): return []
        down=[int(r["team_id"]) for r in tables[4][-4:]]; up=[int(r["team_id"]) for r in tables[102][:4]]
        a=list(self.state["league_memberships"]["4"]); b=list(self.state["league_memberships"]["102"])
        self.state["league_memberships"]["4"]=[x for x in a if x not in down]+up
        self.state["league_memberships"]["102"]=[x for x in b if x not in up]+down
        return ([{"team_id":x,"from_league_id":102,"to_league_id":4,"reason":"promotion"} for x in up]+[{"team_id":x,"from_league_id":4,"to_league_id":102,"reason":"relegation"} for x in down])

    def _netherlands_rollover(self, tables: dict[int,list[dict[str,Any]]]) -> list[dict[str,Any]]:
        if not tables.get(31) or not tables.get(54): return []
        ered=tables[31]; eerste=tables[54]
        direct_up=int(eerste[0]["team_id"]); direct_down=int(ered[-1]["team_id"])
        # Derive period winners from the career's own Eerste results.
        rows=self._league_result_rows(54); used={direct_up}; period_winners=[]
        ids=[str(t["source_id"]) for t in self._teams_for_league(54)]
        for first in (1,9,17,25):
            matches=[LeagueMatch9394(str(r["home_team_id"]),str(r["away_team_id"]),int(r["home_goals"]),int(r["away_goals"])) for r in rows if first<=int(r.get("round") or 0)<=first+7]
            table=build_league_table(ids,matches,NETHERLANDS_EERSTE_1993_94)
            winner=next((int(r.team_id) for r in table if int(r.team_id) not in used),None)
            if winner is None: raise ValueError("no se pudo asignar una plaza de periodo de Eerste")
            period_winners.append(winner); used.add(winner)
        extras=[int(r["team_id"]) for r in eerste if int(r["team_id"]) not in used][:2]
        candidates=period_winners+extras; Random(season_start_year(self.state)*1000+int(self.state["seed"])).shuffle(candidates)
        top_playoff=[int(ered[15]["team_id"]),int(ered[16]["team_id"])]
        promoted=[direct_up]; relegated=[direct_down]
        for idx,top_id in enumerate(top_playoff):
            group_ids=(top_id,*candidates[idx*3:(idx+1)*3])
            sheets={str(tid):self._sheet(tid) for tid in group_ids}
            season=LeagueSeason9394(NETHERLANDS_NACOMPETITIE_GROUP_1993_94,sheets,FootballMatchEngine9394(profile=ERA_BASELINE_1993_94))
            season.play_all(seed_base=season_start_year(self.state)*100000+int(self.state["seed"])+idx*10000)
            table=season.table()
            if table[0].requires_playoff: table=season.finalize_table(seed_base=season_start_year(self.state)*100000+9000+idx).table
            winner=int(table[0].team_id)
            if winner!=top_id: promoted.append(winner); relegated.append(top_id)
        a=list(self.state["league_memberships"]["31"]); b=list(self.state["league_memberships"]["54"])
        self.state["league_memberships"]["31"]=[x for x in a if x not in relegated]+promoted
        self.state["league_memberships"]["54"]=[x for x in b if x not in promoted]+relegated
        return ([{"team_id":x,"from_league_id":54,"to_league_id":31,"reason":"promotion"} for x in promoted]+[{"team_id":x,"from_league_id":31,"to_league_id":54,"reason":"relegation"} for x in relegated])

    def _continental_qualifiers(self, tables: dict[int,list[dict[str,Any]]]) -> dict[str,list[int]]:
        """Build next season's European fields with 1993-94 competition priority.

        Priority is title-holder CWC -> domestic league champion (European Cup)
        -> domestic cup representative (CWC) -> league UEFA places.  This keeps
        one club out of two European tournaments and makes a cup runner-up
        inherit the Recopa place when the cup winner is already in the European
        Cup, which is the important double-winner case.
        """
        european=(14,31,13,4,5,32,1,38)
        tournaments=self.state.get("daily_tournaments") or {}
        defending_raw=(tournaments.get("90") or {}).get("champion_team_id")
        defending=int(defending_raw) if defending_raw else None

        champions: list[int]=[]
        # The CWC title holder has priority over a simultaneous league title.
        for lid in european:
            table=tables.get(lid) or []
            chosen=next((int(row["team_id"]) for row in table if int(row["team_id"])!=defending),None)
            if chosen is not None: champions.append(chosen)
        if len(champions)!=8:
            raise ValueError("no se pudieron reconstruir las ocho plazas de Copa de Europa")

        reserved=set(champions)
        if defending is not None: reserved.add(defending)
        cup_reps: list[int]=[]
        for spec in DOMESTIC_CUPS_9394:
            cup=tournaments.get(str(spec.source_id)) or {}
            champion=int(cup.get("champion_team_id") or 0) or None
            runner=int(cup.get("runner_up_team_id") or 0) or None
            baseline=CWC_BASELINE_REPRESENTATIVE_BY_COUNTRY_9394.get(spec.country_id)
            representative=next((tid for tid in (champion,runner,baseline) if tid is not None and int(tid) not in reserved),None)
            if representative is None:
                continue
            representative=int(representative);cup_reps.append(representative);reserved.add(representative)

        # UEFA is lower priority: if a second/third placed club has already won
        # a cup place, the next league finisher inherits the UEFA berth.
        uefa: list[int]=[]
        for lid in european:
            table=tables.get(lid) or []
            for row in table:
                tid=int(row["team_id"])
                if tid in reserved or tid in uefa: continue
                uefa.append(tid)
                if sum(1 for x in uefa if any(int(r["team_id"])==x for r in table))>=2:
                    break
        if len(uefa)!=16:
            raise ValueError("no se pudieron reconstruir las dieciséis plazas de Copa de la UEFA")

        baseline=[int(x) for x in self.universe.payload.get("tournament_participants",{}).get("90",())]
        replaced=set(CWC_BASELINE_REPRESENTATIVE_BY_COUNTRY_9394.values())|{CWC_BASELINE_DEFENDING_CHAMPION_9394}
        cwc=[]
        if defending is not None:
            cwc.append(defending)
        cwc.extend(cup_reps)
        for tid in baseline:
            if tid in replaced or tid in cwc or tid in champions or tid in uefa:
                continue
            cwc.append(tid)
            if len(cwc)>=32: break
        # In a pathological overlap with one of the historical filler clubs, use
        # remaining baseline entrants before giving up a slot.
        if len(cwc)<32:
            for tid in baseline:
                if tid not in cwc and tid not in champions and tid not in uefa:
                    cwc.append(tid)
                    if len(cwc)>=32: break
        if len(cwc)!=32 or len(set(cwc))!=32:
            raise ValueError(f"Recopa: se esperaban 32 clasificados únicos y hay {len(set(cwc))}")
        return {"1":champions,"2":uefa,"90":cwc}

    def _league_player_awards(self, *, league_id: int, table: list[dict[str, Any]]) -> dict[str, Any]:
        """Build league-only player awards from the persisted 0-10 match ratings."""
        team_ids={int(row.get("team_id") or 0) for row in table if int(row.get("team_id") or 0)}
        candidates=[]
        for team_id in team_ids:
            for source in self._career_players_by_team.get(team_id, ()):
                pid=int(source.get("source_id") or 0)
                if not pid or source.get("retired"):
                    continue
                dev=(self.state.get("player_development") or {}).get(str(pid), {})
                appearances=int(dev.get("season_appearances") or 0)
                rating_count=int(dev.get("season_rating_count") or 0)
                if appearances <= 0 and rating_count <= 0:
                    continue
                average=(round(float(dev.get("season_rating_total") or 0.0)/rating_count,2) if rating_count else None)
                candidates.append({
                    "player_id":pid,"name":str(source.get("display_name") or source.get("name") or pid),
                    "team_id":team_id,"team_name":self._team_name(team_id),
                    "position":str(source.get("broad_position") or ""),
                    "appearances":appearances,"starts":int(dev.get("season_starts") or 0),
                    "goals":int(dev.get("season_goals") or 0),"assists":int(dev.get("season_assists") or 0),
                    "average_rating":average,"rating_count":rating_count,
                })
        max_played=max((int(row.get("played") or 0) for row in table),default=0)
        minimum=max(5,min(10,max_played//4 if max_played else 5))
        rated=[row for row in candidates if row["average_rating"] is not None and row["rating_count"]>=minimum]
        best=max(rated,key=lambda row:(float(row["average_rating"]),row["goals"],row["assists"],row["appearances"]),default=None)
        scorers=sorted(candidates,key=lambda row:(-row["goals"],-(float(row["average_rating"] or 0)),-row["assists"],-row["appearances"]))
        assisters=sorted(candidates,key=lambda row:(-row["assists"],-(float(row["average_rating"] or 0)),-row["goals"],-row["appearances"]))
        keepers=[row for row in rated if row["position"].upper() in {"POR","GK","PORTERO"}]
        keeper=max(keepers,key=lambda row:(float(row["average_rating"]),row["appearances"]),default=None)

        # XI of the season: 1-4-4-2 by broad historical positions.  We prefer
        # a coherent football team over simply taking the eleven highest
        # ratings, then fill any data gap with the best remaining rated player.
        ranked_rated=sorted(
            rated,
            key=lambda row:(-float(row["average_rating"]),-row["appearances"],-row["goals"],-row["assists"],row["name"]),
        )
        quotas=(("POR",1),("DEF",4),("MED",4),("DEL",2))
        team_of_season=[];used=set()
        for broad,count in quotas:
            pool=[row for row in ranked_rated if row["position"].upper()==broad and row["player_id"] not in used]
            for row in pool[:count]:
                team_of_season.append(row);used.add(row["player_id"])
        for row in ranked_rated:
            if len(team_of_season)>=11: break
            if row["player_id"] in used: continue
            team_of_season.append(row);used.add(row["player_id"])
        return {
            "league_id":int(league_id),"league_name":str((self.universe.leagues_by_id.get(int(league_id)) or {}).get("name") or f"Liga {league_id}"),
            "minimum_rated_matches":minimum,"best_player":best,"top_scorer":scorers[0] if scorers else None,
            "top_assister":assisters[0] if assisters and assisters[0]["assists"]>0 else None,"best_goalkeeper":keeper,
            "team_of_season":team_of_season,
        }

    def _build_season_recap(self, *, season: str, tables: dict[int,list[dict[str,Any]]], honours: list[dict[str,Any]], movements: list[dict[str,Any]], qualifiers: dict[str,list[int]]) -> dict[str,Any]:
        controlled=int(self.state["team_id"]);league_id=int(self.state["league_id"]);table=tables.get(league_id) or self.standings()
        row=next((r for r in table if int(r.get("team_id") or 0)==controlled),{})
        league_awards=self._league_player_awards(league_id=league_id,table=table)
        squad=self.squad(controlled)
        ranked_scorers=sorted(squad,key=lambda p:(-int((p.get("season_stats") or {}).get("goals") or 0),-int((p.get("season_stats") or {}).get("assists") or 0),-float((p.get("season_stats") or {}).get("average_rating") or 0)))
        rated=[p for p in squad if (p.get("season_stats") or {}).get("average_rating") is not None]
        rated.sort(key=lambda p:-float((p.get("season_stats") or {}).get("average_rating") or 0))
        movement=next((m for m in movements if int(m.get("team_id") or 0)==controlled),None)
        qualified=[]
        names={"1":"Copa de Europa","2":"Copa de la UEFA","90":"Recopa de Europa"}
        for key,ids in qualifiers.items():
            if controlled in {int(x) for x in ids}: qualified.append(names.get(str(key),str(key)))
        recent=[]
        for result in reversed(self.state.get("results") or []):
            if controlled not in (int(result["home_team_id"]),int(result["away_team_id"])): continue
            mine=int(result["home_goals"]) if int(result["home_team_id"])==controlled else int(result["away_goals"]);theirs=int(result["away_goals"]) if int(result["home_team_id"])==controlled else int(result["home_goals"])
            recent.append("V" if mine>theirs else "E" if mine==theirs else "D")
            if len(recent)==5: break
        recent.reverse();economy=self.economy_snapshot();previous=(self.state.get("board_state") or {}).get("score")
        board=evaluate_board(expectation=self.state.get("board_expectation") or self._board_expectation(),position=row.get("position"),played=int(row.get("played") or 0),recent_form=recent,projected_monthly_net=int(economy.get("projected_monthly_net") or 0),cash=int(economy.get("cash") or 0),debt=int(economy.get("debt") or 0),previous_score=int(previous) if previous is not None else None)
        board=apply_board_review(self.state,board,date=self.current_date.isoformat(),trigger="season_end")
        board={**board,"expectation":self.state.get("board_expectation") or self._board_expectation(),"warning_count":int(self.state.get("board_warning_count") or 0),"job_status":self.state.get("job_status") or "active"}
        club_titles=[h for h in honours if int(h.get("team_id") or 0)==controlled]
        result={
            "season":season,"team_id":controlled,"team_name":self._team_name(controlled),"league_id":league_id,
            "league_name":(self.universe.leagues_by_id.get(league_id) or {}).get("name"),"position":row.get("position"),"points":row.get("points"),
            "played":row.get("played"),"wins":row.get("wins"),"draws":row.get("draws"),"losses":row.get("losses"),"goals_for":row.get("goals_for"),"goals_against":row.get("goals_against"),
            "titles":club_titles,"movement":movement,"qualified_for":qualified,"board":board,
            "champions":honours,"league_awards":league_awards,
            "top_scorer":({"player_id":ranked_scorers[0]["id"],"name":ranked_scorers[0]["display_name"],"goals":ranked_scorers[0]["season_stats"]["goals"]} if ranked_scorers else None),
            "player_of_season":({"player_id":rated[0]["id"],"name":rated[0]["display_name"],"average_rating":rated[0]["season_stats"]["average_rating"]} if rated else None),
            "economy":self.economy_snapshot(),
        }
        if club_titles: result["headline"]=f"{self._team_name(controlled)} cierra {season} con {len(club_titles)} título{'s' if len(club_titles)!=1 else ''}."
        elif movement and movement.get("reason")=="promotion": result["headline"]=f"Ascenso conseguido en {season}."
        elif movement and movement.get("reason")=="relegation": result["headline"]=f"Descenso al cierre de {season}."
        else: result["headline"]=f"{season}: {row.get('position','—')}º en liga."
        return result

    def _rollover_season(self, day: date) -> list[dict[str,Any]]:
        old_season=str(self.state["season"])
        tables={lid:self.league_standings(lid) for lid in self._simple_world_league_ids()}
        honours=self._archive_honours(tables)
        qualifiers=self._continental_qualifiers(tables)
        status_changes=update_after_season(state=self.state,season=old_season,tables=tables,honours=honours,qualifiers=qualifiers,
            team_league_getter=lambda tid: next((lid for lid,table in tables.items() if any(int(r.get("team_id") or 0)==int(tid) for r in table)),self._current_league_for_team(tid)),
            league_level_getter=lambda lid:int((self.universe.leagues_by_id.get(int(lid)) or {}).get("level") or 1),
            finances=self.state.get("club_finances") or {},squad_strength_getter=self._team_strength)
        movements=[]
        movements.extend(self._spain_rollover(tables)); movements.extend(self._italy_rollover(tables)); movements.extend(self._netherlands_rollover(tables))
        for movement in movements:
            tid=int(movement.get("team_id") or 0); reason=str(movement.get("reason") or "")
            if not tid or reason not in {"promotion","relegation"}: continue
            register_structural_event(
                self.state,team_id=tid,season=old_season,date_text=day.isoformat(),kind=reason,
                detail=("El ascenso cambia la escala competitiva y el potencial comercial de la siguiente temporada." if reason=="promotion" else "El descenso reduce la escala competitiva y obliga a reajustar el proyecto de la siguiente temporada."),
                from_league_id=int(movement.get("from_league_id") or 0),to_league_id=int(movement.get("to_league_id") or 0),
            )
        # NF12: league merit creates a real end-of-season cash consequence.  The
        # figures are career-scale estimates, while sporting positions are the
        # actual simulated table; no historical accountancy is claimed.
        controlled=int(self.state["team_id"])
        for lid, table in tables.items():
            team_count=len(table)
            for row in table:
                tid=int(row.get("team_id") or 0)
                if not tid: continue
                prize=season_prize_money(position=int(row.get("position") or 0),team_count=team_count,club_score=float(club_status(self.state,tid).get("score") or 50),champion=int(row.get("position") or 0)==1)
                if prize<=0: continue
                finances=self.state["club_finances"].setdefault(str(tid),initial_club_finances(self.universe.team(tid) or {},players=self._career_players_by_team.get(tid,[])))
                finances["cash"]=int(finances.get("cash") or 0)+prize
                finances["prize_income"]=int(finances.get("prize_income") or 0)+prize
                post_long_economy(self.state,team_id=tid,season=old_season,category="prize_money",amount=prize)
                if tid==controlled:
                    self.state["finances"]=finances
                    self.state["economy_ledger"].append({"date":day.isoformat(),"kind":"prize_money","amount":prize,"league_id":int(lid),"position":int(row.get("position") or 0)})
        recap=self._build_season_recap(season=old_season,tables=tables,honours=honours,movements=movements,qualifiers=qualifiers)
        milestone_rows=register_season_closure(
            self.state,date_text=day.isoformat(),season=old_season,
            controlled_team_id=int(self.state["team_id"]),controlled_team_name=self._team_name(int(self.state["team_id"])),
            recap=recap,honours=honours,movements=movements,team_name_lookup=self._team_name,
        )
        controlled_milestones=[row for row in milestone_rows if int(row.get("team_id") or 0)==int(self.state["team_id"])]
        recap["milestones"]=controlled_milestones
        archive={
            "season":old_season,"closed_on":day.isoformat(),"honours":honours,"movements":movements,
            "continental_qualifiers":qualifiers,"managed_club":recap,"club_status_changes":status_changes,
            "league_tables":{str(lid):table for lid,table in tables.items()},
        }
        dossier=build_season_dossier(self.state,season=old_season,closed_on=day.isoformat(),tables=tables,honours=honours,movements=movements,qualifiers=qualifiers,recap=recap)
        self.state["season_archive"].append(archive);self.state["season_recaps"].append(recap);self.state["season_recaps"]=self.state["season_recaps"][-60:]
        self.state["season_dossiers"].append(dossier);self.state["season_dossiers"]=self.state["season_dossiers"][-60:]
        for honour in honours:
            publish_news(self.state,key=f"honour:{old_season}:{honour['competition_kind']}:{honour['source_id']}",date=day.isoformat(),category="Competiciones",importance=5,headline=f"{honour['team_name']} campeón de {honour['competition_name']}",detail=f"Palmarés de la temporada {old_season}.",entity={"team_id":honour["team_id"],"competition_id":honour["source_id"],"competition_kind":honour["competition_kind"]},cause=f"competition-title:{old_season}:{honour['competition_kind']}:{honour['source_id']}:{honour['team_id']}")
        controlled=int(self.state["team_id"])
        for movement in movements:
            tid=int(movement.get("team_id") or 0); reason=str(movement.get("reason") or "")
            from_lid=int(movement.get("from_league_id") or 0); to_lid=int(movement.get("to_league_id") or 0)
            from_name=str((self.universe.leagues_by_id.get(from_lid) or {}).get("name") or "su categoría")
            to_name=str((self.universe.leagues_by_id.get(to_lid) or {}).get("name") or "su nueva categoría")
            publish_news(
                self.state,key=f"movement:{old_season}:{tid}:{from_lid}:{to_lid}",date=day.isoformat(),category="Competiciones",
                importance=5 if tid==controlled else 3,
                headline=(f"{self._team_name(tid)} asciende" if reason=="promotion" else f"{self._team_name(tid)} desciende"),
                detail=f"{self._team_name(tid)} pasa de {from_name} a {to_name} para la próxima temporada.",
                entity={"team_id":tid,"competition_id":to_lid,"competition_kind":"league"},
            )
        if recap.get("qualified_for"):
            controlled=int(self.state["team_id"])
            publish_news(self.state,key=f"europe:{old_season}:{controlled}",date=day.isoformat(),category="Club",importance=4,headline=f"{self._team_name(controlled)} estará en Europa",detail="Clasificación para " + ", ".join(recap["qualified_for"]) + ".",entity={"team_id":controlled})
        old_start=season_start_year(self.state)
        self.state["season"]=season_label(old_start+1)
        self.state["continental_qualifiers"]=qualifiers
        self._team_league_cache.clear(); self._foreign_rule_cache.clear()
        self.state["league_id"]=int(self._current_league_for_team(int(self.state["team_id"])) or self.state["league_id"])
        self.state["completed_matchday"]=0; self.state["results"]=[]; self.state["world_leagues"]={}
        self.state["special_competitions"]={}; self.state["daily_tournaments"]={}; self.state["pending_world_match"]=None
        self.state["processed_international_windows"]=[]
        archive_managed_season(self.state, old_season)
        # Career demography is policy-driven. In frozen mode the original cast
        # remains permanently available: no age decay, retirement or academy/newgens.
        # Attributes still evolve through performance, coaching, injuries and dynamics.
        ageing_events = apply_ageing_and_retirement(
            self.state, players=self._all_player_rows(), game_date=day,
            seed=int(self.state["seed"]) ^ (old_start * 733),
        )
        rollover_player_development(self.state["player_development"])
        season_rollover_dynamics(self.state)
        reset_season_streaks(self.state)
        # Retirements modify team overrides. Rebuild once before academy promotion
        # so vacancies are measured against the post-retirement senior squad,
        # not the stale roster from June 30.
        self._rebuild_rosters()
        academy_events = generate_annual_academy_intake(
            self.state, universe=self.universe, team_ids=self._active_club_ids(), game_date=day,
            seed=int(self.state["seed"]) ^ ((old_start + 1) * 9394), players_by_team=self._career_players_by_team,
        )
        self._schedule_cache.clear(); self._rebuild_rosters()
        # H1: every new season refreshes the transfer envelope in period pesetas
        # from the current squad, without duplicating unspent budget every July.
        for finance_team_id in self._active_club_ids():
            finance_team = self.universe.team(finance_team_id) or {}
            finance_state = self.state["club_finances"].setdefault(
                str(finance_team_id),
                initial_club_finances(finance_team,players=self._career_players_by_team.get(finance_team_id,[])),
            )
            finance_players=self._career_players_by_team.get(finance_team_id,[])
            finance_commitment=annual_wage_commitment(
                finance_players,development=self.state.get("player_development") or {},
                contract_overrides=self.state.get("contract_overrides") or {},
            )
            refresh_season_transfer_budget(
                finance_state, team=finance_team, players=finance_players,current_wage_commitment=finance_commitment
            )
        self.state["finances"] = self.state["club_finances"][str(int(self.state["team_id"]))]
        self.state["selection"] = self._safe_auto_selection(); self.state["board_expectation"] = self._board_expectation()
        self._ensure_world_leagues(); self._ensure_preseason_schedule(); ensure_special_competitions(self.state); ensure_tournament_state(self.state,self.universe)
        self.board_snapshot(persist=True,trigger="season_start")
        self.engine=FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94 if int(self.state["league_id"])==1 else ERA_BASELINE_1993_94)
        self.live_engine=LiveMatchEngine9394(self.engine)
        self.state["live_match"] = None
        event={"kind":"season_rollover","date":day.isoformat(),"from_season":old_season,"to_season":self.state["season"],"movement_count":len(movements),"honour_count":len(honours),"club_status_change_count":len(status_changes),"retirement_count":len(ageing_events),"academy_intake_count":len(academy_events)}
        demographic={"kind":"career_demography","date":day.isoformat(),"season":self.state["season"],"age_policy":self.state.get("age_policy"),"retirements":len(ageing_events),"academy_intakes":len(academy_events)}
        self.state["season_transition_log"].append(event)
        controlled_academy=[row for row in academy_events if int(row.get("team_id") or 0)==controlled]
        if controlled_academy:
            names=", ".join(str(row.get("name") or "canterano") for row in controlled_academy[:3])
            publish_news(self.state,key=f"academy:{self.state['season']}:{controlled}",date=day.isoformat(),category="Plantilla",importance=3,headline="Nueva promoción de cantera",detail=f"Se incorporan al fútbol sénior: {names}.",entity={"team_id":controlled})
        return [event, demographic]
