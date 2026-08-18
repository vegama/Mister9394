from __future__ import annotations

"""Persistent playable career loop for Míster 93/94.

The controlled career is intentionally simple on the surface but stateful under
it: results are written once, player form/ability can evolve while age is
ageing is calendar-driven, injuries recover day by day, transfers alter actual squads and the
club's source-scale cash balance moves with matches and deals.
"""

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
from .career_history_runtime import CareerHistoryRuntimeMixin
from .career_market_runtime import CareerMarketRuntimeMixin

CAREER_SCHEMA_9394 = 23
RULES_POLICY_FROZEN_9394 = "frozen_1993_94"
CAREER_START_DATE_9394 = date(1993, 10, 23)
CAREER_PRESEASON_START_9394 = date(1993, 7, 1)
FIRST_LEAGUE_MATCH_DATE_9394 = date(1993, 9, 5)


def league_matchday_date_9394(matchday: int) -> date:
    if not 1 <= int(matchday) <= 38:
        raise ValueError("jornada fuera del calendario 1993-94")
    return FIRST_LEAGUE_MATCH_DATE_9394 + timedelta(days=(int(matchday) - 1) * 7)


def _default_tactics() -> dict[str, Any]:
    return {
        "formation": "4-4-2", "mentality": "balanced", "tempo": "normal",
        "pressing": "medium", "directness": "mixed", "defensive_line": "medium",
        "width": "normal", "offside_trap": False, "marking": "zonal",
        "build_up": "balanced", "final_third": "mixed", "transition": "balanced",
    }


def career_selectable_leagues(universe: FootballUniverseSnapshot9394 | None = None) -> list[dict[str, Any]]:
    """Return admitted regular leagues that can host a managed career.

    Special-format leagues remain simulated in the world but are not offered as
    the user's primary job until their controlled-match flow is implemented.
    """
    universe = universe or default_runtime_snapshot()
    registry = default_registry_9394()

    def team_preview(team: dict[str, Any]) -> dict[str, Any]:
        tid = int(team["source_id"])
        players = list(universe.players_by_team.get(tid, ()))
        ranked = sorted(players, key=lambda player: -int(player.get("overall") or player.get("category") or 0))
        core = ranked[:11]
        average = round(sum(int(player.get("overall") or player.get("category") or 60) for player in core) / max(1, len(core)), 1)
        finance_preview = initial_club_finances(team, players=players)
        return {
            "source_id": tid, "name": team.get("name"), "long_name": team.get("long_name"),
            "initials": team.get("initials"), "squad_size": len(players), "average_top_11": average,
            "members": team.get("members"), "budget": finance_preview["transfer_budget_total"],
            "source_budget": finance_preview["source_budget"], "currency": "ESP", "debt": team.get("debt"),
            "stadium_id": team.get("stadium_id"), "previous_position": team.get("league_position"),
            "top_players": [
                {"id": int(player["source_id"]), "name": player.get("display_name"),
                 "position": role_for_player(player).name,
                 "overall": int(player.get("overall") or player.get("category") or 60)}
                for player in ranked[:3]
            ],
        }

    rows: list[dict[str, Any]] = []
    for comp in universe.career_competitions():
        if comp.get("kind") != "league":
            continue
        source_id = int(comp["source_id"])
        try:
            rules = registry.resolve_source("league", source_id)
        except Exception:
            continue
        if rules.competition_type != "league":
            continue
        teams = universe.teams(league_id=source_id)
        selectable = [team for team in teams if len(universe.players_by_team.get(int(team["source_id"]), ())) >= 11]
        if not selectable:
            continue
        rows.append({
            "source_id": source_id, "name": comp.get("name"), "country": comp.get("country"),
            "level": comp.get("level"), "team_count": len(teams), "rounds": int(rules.rounds or 0),
            "teams": [team_preview(team) for team in selectable],
        })
    rows.sort(key=lambda row: (str(row.get("country") or ""), int(row.get("level") or 99), str(row.get("name") or "")))
    return rows


def _league_match_payload(matchday: int, fixture_id: int, home_id: int, away_id: int, goals_home: int, goals_away: int, *, referee_id: str | None = None, referee_name: str | None = None, referee_source_confidence: str | None = None) -> dict[str, Any]:
    return {
        "matchday": int(matchday), "fixture_id": int(fixture_id),
        "home_team_id": int(home_id), "away_team_id": int(away_id),
        "home_goals": int(goals_home), "away_goals": int(goals_away),
        "referee_id": referee_id, "referee_name": referee_name,
        "referee_source_confidence": referee_source_confidence,
    }


@dataclass(slots=True)
class ManagerCareerStore9394:
    root: Path
    backup_root: Path

    def __init__(self, root: str | Path, backup_root: str | Path | None = None):
        self.root = Path(root)
        self.backup_root = Path(backup_root) if backup_root is not None else self.root.parent / "backups"

    def path_for(self, career_id: str) -> Path:
        safe = "".join(ch for ch in str(career_id) if ch.isalnum() or ch in "-_")
        if not safe:
            raise ValueError("career_id inválido")
        return self.root / f"{safe}.json"

    @staticmethod
    def _validate(payload: dict[str, Any]) -> None:
        schema = int(payload.get("schema") or 0)
        if schema < 1 or schema > CAREER_SCHEMA_9394:
            raise ValueError("save de carrera Míster 93/94 incompatible")
        if not str(payload.get("career_id") or "").strip():
            raise ValueError("save de carrera sin career_id")

    def save(self, state: dict[str, Any]) -> Path:
        state["schema"] = CAREER_SCHEMA_9394
        path = self.path_for(str(state.get("career_id") or ""))
        return atomic_json_save(path, state, validator=self._validate, backup_root=self.backup_root)

    def load(self, career_id: str) -> dict[str, Any]:
        path = self.path_for(career_id)
        return recover_json_load(path, validator=self._validate, backup_root=self.backup_root)


class _CareerUniverseView:
    """Tiny adapter consumed by `build_snapshot_team_sheet`.

    Matchday views normally expose only available footballers.  The all-roster
    variant exists solely for AI emergency selection: if temporary injuries
    make a quota-legal XI impossible, an AI club may risk one of its own
    injured players rather than violate competition rules or crash the world.
    """
    def __init__(self, runtime: "ManagerCareerRuntime9394", *, include_injured: bool = False, exclude_league_suspended: bool = False):
        self.runtime = runtime
        base = runtime._career_players_by_team if include_injured else runtime._match_players_by_team
        if exclude_league_suspended:
            dev = runtime.state.get("player_development") or {}
            self.players_by_team = {
                int(team_id): [row for row in rows if int((dev.get(str(int(row.get("source_id") or 0))) or {}).get("league_suspension_matches") or 0) <= 0]
                for team_id, rows in base.items()
            }
        else:
            self.players_by_team = base

    def team(self, team_id: int):
        return self.runtime._team_api(team_id)

    def teams(self, *, league_id: int | None = None):
        return self.runtime._teams_for_league(league_id) if league_id is not None else [self.runtime._team_api(int(t["source_id"])) for t in self.runtime.universe.payload.get("teams", [])]


class ManagerCareerRuntime9394(CareerHistoryRuntimeMixin, CareerMarketRuntimeMixin):
    def __init__(self, state: dict[str, Any], *, universe: FootballUniverseSnapshot9394 | None = None):
        self.state = state
        self.universe = universe or default_runtime_snapshot()
        self._ensure_state_v3()
        profile = SPAIN_PRIMERA_SIMULATION_1993_94 if int(self.state.get("league_id") or 0) == 1 else ERA_BASELINE_1993_94
        self.engine = FootballMatchEngine9394(profile=profile)
        self.live_engine = LiveMatchEngine9394(self.engine)
        self._schedule_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        self._strength_cache: dict[int, float] = {}
        self._team_league_cache: dict[int, int] = {}
        self._foreign_rule_cache: dict[tuple[int, int], Any] = {}
        self._rebuild_rosters()
        current_team = self._team_api(int(self.state["team_id"])) or self.universe.team(int(self.state["team_id"])) or {"source_id": int(self.state["team_id"])}
        ensure_club_staff_state(self.state, team=current_team, strength=self._team_strength(int(self.state["team_id"])), game_date=self.current_date)
        self._ensure_manager_layer()
        initialise_club_status(state=self.state,active_team_ids=self._active_club_ids(),team_getter=lambda tid:self._team_api(tid),strength_getter=self._team_strength)
        self._ensure_nf9_nf12_layers()
        self._ensure_preseason_schedule()
        self._ensure_world_leagues()
        ensure_special_competitions(self.state)
        ensure_tournament_state(self.state, self.universe)
        # Older saves could already be in the old terminal dismissed state.
        # Migrate that dead end into the v0.11 job decision once the runtime is
        # fully built and candidate squads/club status are available.
        if self.state.get("job_status")=="dismissed" and not manager_profile_snapshot(self.state).get("job_offers"):
            self._handle_user_dismissal()

    def _ensure_state_v3(self) -> None:
        self.state["schema"] = CAREER_SCHEMA_9394
        if not self.state.get("player_development"):
            self.state["player_development"] = initial_player_development(self.universe.payload.get("players", []))
        self.state.setdefault("player_team_overrides", {})
        self.state.setdefault("contract_overrides", {})
        self.state.setdefault("transfer_history", [])
        team = self.universe.team(int(self.state["team_id"])) or {}
        self.state.setdefault("finances", initial_club_finances(team, players=list(self.universe.players_by_team.get(int(self.state["team_id"]), ()))))
        self.state.setdefault("economy_ledger", [])
        self.state.setdefault("age_policy", AGE_POLICY_FROZEN)
        # Product rule: the 1993-94 regulatory environment is permanent.
        # No Bosman-era liberalisation or automatic future-law migration.
        enforce_frozen_rules_policy(self.state)
        self.state.setdefault("world_events", [])
        self.state.setdefault("international_history", [])
        self.state.setdefault("ai_transfer_history", [])
        self.state.setdefault("ai_contract_history", [])
        self.state.setdefault("contract_history", [])
        self.state.setdefault("processed_months", [])
        self.state.setdefault("processed_international_windows", [])
        self.state.setdefault("pending_world_match", None)
        self.state.setdefault("season_archive", [])
        self.state.setdefault("honours", [])
        self.state.setdefault("club_honours", {})
        self.state.setdefault("continental_qualifiers", {})
        self.state.setdefault("season_transition_log", [])
        self.state.setdefault("live_match", None)
        self.state.setdefault("board_history", [])
        self.state.setdefault("board_warning_count", 0)
        self.state.setdefault("job_status", "active")
        self.state.setdefault("season_recaps", [])
        self.state.setdefault("season_dossiers", [])
        self.state.setdefault("club_strategy", {})
        self.state.setdefault("ai_squad_audits", [])
        self.state.setdefault("preseason_friendlies", [])
        self.state.setdefault("preseason_history", [])
        self.state.setdefault("club_status", {})
        ensure_news_state(self.state)
        ensure_performance_state(self.state)
        ensure_market_flow_state(self.state)
        ensure_scouting_state(self.state)
        ensure_training_state(self.state)
        ensure_tactical_plan_state(self.state)
        ensure_market_ecosystem_state(self.state)
        ensure_squad_dynamics_state(self.state)
        ensure_long_career_state(self.state)
        ensure_career_memory(self.state, self.universe)
        ensure_manager_market_state(self.state)
        ensure_storyline_state(self.state)
        ensure_record_state(self.state)
        ensure_user_manager_state(self.state)
        ensure_history_dossiers(self.state)
        ensure_milestone_state(self.state)
        ensure_professional_state(self.state, team=team)
        ensure_information_state(self.state)
        ensure_longitudinal_economy(self.state)
        ensure_longitudinal_health_state(self.state)
        ensure_dressing_room_state(self.state)
        ensure_tactical_memory_state(self.state)
        ensure_international_manager_state(self.state)
        ensure_international_player_stats(self.state)
        current_tenure=(self.state.get("user_manager") or {}).get("current_tenure") or {}
        if int(current_tenure.get("team_id") or 0)==int(self.state.get("team_id") or 0) and not current_tenure.get("team_name"):
            current_tenure["team_name"]=str((self.universe.team(int(self.state.get("team_id") or 0)) or {}).get("name") or self.state.get("team_id"))
        if "controlled_predecessor_manager_id" not in self.state:
            assigned=(self.state.get("manager_assignments") or {}).get(str(int(self.state.get("team_id") or 0)))
            if not isinstance(assigned,int):
                assigned=(self.universe.team(int(self.state.get("team_id") or 0)) or {}).get("manager_id")
            self.state["controlled_predecessor_manager_id"]=assigned if isinstance(assigned,int) else None
        assignments = self.state.setdefault("manager_assignments", {})
        for club in self.universe.payload.get("teams", []):
            manager_id = club.get("manager_id")
            if isinstance(manager_id, int):
                assignments.setdefault(str(int(club["source_id"])), int(manager_id))
        self.state.setdefault("manager_history", [])
        memberships = self.state.setdefault("league_memberships", {})
        if not memberships:
            for league in self.universe.payload.get("leagues", []):
                lid = int(league["source_id"])
                team_ids = [int(team["source_id"]) for team in self.universe.teams(league_id=lid)]
                if team_ids:
                    memberships[str(lid)] = team_ids
        # Old saves were hard-wired to Primera. Preserve them while allowing new
        # careers to select any regular admitted league.
        if not self.state.get("league_id"):
            source_team = self.universe.team(int(self.state["team_id"])) or {}
            league = source_team.get("league") or {}
            self.state["league_id"] = int(league.get("source_id") or 1)
        club_finances = self.state.setdefault("club_finances", {})
        for club in self.universe.payload.get("teams", []):
            club_id = int(club["source_id"])
            tid = str(club_id)
            baseline = initial_club_finances(club, players=list(self.universe.players_by_team.get(club_id, ())))
            club_finances[tid] = merge_finances_with_peseta_baseline(baseline, club_finances.get(tid))
        controlled_key = str(int(self.state["team_id"]))
        # Migrate previous saves: the user's ledger/cash remains authoritative,
        # while H1 adds the explicit peseta budget envelopes.
        controlled_team = self.universe.team(int(self.state["team_id"])) or {}
        controlled_baseline = initial_club_finances(controlled_team, players=list(self.universe.players_by_team.get(int(self.state["team_id"]), ())))
        controlled_existing = {**club_finances.get(controlled_key, {}), **(self.state.get("finances") or {})}
        club_finances[controlled_key] = merge_finances_with_peseta_baseline(controlled_baseline, controlled_existing)
        self.state["finances"] = club_finances[controlled_key]

    def _teams_for_league(self, league_id: int) -> list[dict[str, Any]]:
        ids = (self.state.get("league_memberships") or {}).get(str(int(league_id)))
        if ids is None:
            return self.universe.teams(league_id=int(league_id))
        rows = [self._team_api(int(team_id), resolve_league=False) for team_id in ids]
        return [row for row in rows if row is not None]

    def _current_league_for_team(self, team_id: int) -> int | None:
        team_id = int(team_id)
        cache=getattr(self,"_team_league_cache",None)
        if cache is None:
            cache={};self._team_league_cache=cache
        if team_id in cache:
            return cache[team_id]
        # Memberships are stable between summer rollovers.  Building a fresh set
        # for every foreign-rule/market query made transfer pulses much slower
        # than the football itself, so resolve each club once per season.
        for source_id, ids in (self.state.get("league_memberships") or {}).items():
            if team_id in ids or str(team_id) in ids:
                cache[team_id]=int(source_id)
                return int(source_id)
        team = self.universe.team(team_id) or {}
        league = team.get("league") or {}
        resolved=int(league["source_id"]) if league.get("source_id") is not None else None
        if resolved is not None: cache[team_id]=resolved
        return resolved

    def _team_api(self, team_id: int, *, resolve_league: bool = True) -> dict[str, Any] | None:
        team = self.universe.team(int(team_id))
        if team is None:
            return None
        if not resolve_league:
            return dict(team)
        league_id = self._current_league_for_team(int(team_id))
        league = self.universe.leagues_by_id.get(int(league_id)) if league_id is not None else None
        return {**team, "league_id": league_id, "league": ({
            "source_id": int(league["source_id"]), "name": league.get("name"), "country": league.get("country")
        } if league else None)}

    def _league_rules(self, source_id: int | None = None):
        return default_registry_9394().resolve_source("league", int(source_id if source_id is not None else self.state["league_id"]))

    def _league_schedule(self, source_id: int | None = None) -> list[dict[str, Any]]:
        source_id = int(source_id if source_id is not None else self.state["league_id"])
        rules = self._league_rules(source_id)
        current_teams = self._teams_for_league(source_id)
        team_ids = [str(int(team["source_id"])) for team in current_teams]
        if len(team_ids) < 2:
            return []
        cache_key = (str(self.state.get("season")), source_id, tuple(team_ids))
        cached = self._schedule_cache.get(cache_key)
        if cached is not None:
            return cached
        # Primera 1993-94 has a source-backed fixture order. Preserve it exactly
        # in the historical opening season; regenerated seasons use the same
        # era format with the new participant pool.
        if source_id == 1 and season_start_year(self.state) == 1993:
            original = {int(team["source_id"]) for team in self.universe.teams(league_id=1)}
            if {int(team_id) for team_id in team_ids} == original:
                out = [{**row, "round": int(row["matchday"]), "date": league_matchday_date_9394(int(row["matchday"])).isoformat()} for row in self.universe.league_calendar(1)]
                self._schedule_cache[cache_key] = out
                return out
        calendar_rounds_per_cycle = len(team_ids) - 1 + (1 if len(team_ids) % 2 else 0)
        matches_per_team_per_cycle = len(team_ids) - 1
        # `rules.rounds` expresses matches per club.  With an odd number of
        # teams a round-robin cycle needs one extra calendar round for byes,
        # so dividing by calendar rounds would incorrectly collapse Uruguay
        # 1993 from two vueltas (24 matches/club) to one.
        cycles = max(1, int(rules.rounds or matches_per_team_per_cycle * 2) // matches_per_team_per_cycle)
        fixtures = generate_round_robin_cycles(tuple(team_ids), cycles)
        max_round = max((fixture.round_number for fixture in fixtures), default=0)
        dates = generated_round_dates(self.state, max_round)
        per_round_index: dict[int, int] = {}
        out=[]
        for fixture in fixtures:
            index=per_round_index.get(fixture.round_number,0); per_round_index[fixture.round_number]=index+1
            out.append({
                "id": source_id*1_000_000 + fixture.round_number*100 + index,
                "matchday": int(fixture.round_number),
                "round": int(fixture.round_number),
                "date": dates[fixture.round_number-1].isoformat(),
                "home_team_id": int(fixture.home_team_id), "away_team_id": int(fixture.away_team_id),
            })
        self._schedule_cache[cache_key] = out
        return out

    def _controlled_total_rounds(self) -> int:
        return max((row["matchday"] for row in self._league_schedule()), default=0)

    def _active_club_ids(self) -> list[int]:
        ids: set[int] = set()
        for comp in self.universe.career_competitions():
            if comp.get("kind") != "league" or not comp.get("admitted", True):
                continue
            ids.update(int(team["source_id"]) for team in self._teams_for_league(int(comp["source_id"])))
        return sorted(ids)

    def _market_container_ids(self) -> list[int]:
        """Non-playing contract owners such as ``Otros-Camerún``.

        They can sell players into the active world but are never career clubs,
        competition entrants or AI buyers.
        """
        return sorted(int(team["source_id"]) for team in self.universe.payload.get("teams", []) if team.get("market_container"))

    def _simple_world_league_ids(self) -> list[int]:
        ids: list[int] = []
        registry = default_registry_9394()
        for comp in self.universe.career_competitions():
            if comp.get("kind") != "league":
                continue
            source_id = int(comp["source_id"])
            try:
                rules = registry.resolve_source("league", source_id)
            except Exception:
                continue
            if rules.competition_type == "league":
                ids.append(source_id)
        return sorted(ids)

    def _ensure_world_leagues(self) -> None:
        world = self.state.setdefault("world_leagues", {})
        controlled = int(self.state.get("league_id") or 1)
        world.pop(str(controlled), None)
        for source_id in self._simple_world_league_ids():
            if source_id == controlled:
                continue
            world.setdefault(str(source_id), {"completed_round": 0, "results": []})

    @classmethod
    def create(cls, *, team_id: int = 16, league_id: int | None = None, seed: int = 9394, through_matchday: int = 7,
               age_policy: str = AGE_POLICY_FROZEN, universe: FootballUniverseSnapshot9394 | None = None) -> "ManagerCareerRuntime9394":
        universe = universe or default_runtime_snapshot()
        team = universe.team(int(team_id))
        if team is None:
            raise ValueError(f"equipo {team_id} no existe en el snapshot 1993-94")
        source_league = (team.get("league") or {}).get("source_id")
        selected_league = int(league_id if league_id is not None else (source_league or 0))
        selectable = {int(row["source_id"]): row for row in career_selectable_leagues(universe)}
        if selected_league not in selectable:
            raise ValueError("la liga seleccionada todavía no admite una carrera controlada")
        if int(team_id) not in {int(row["source_id"]) for row in selectable[selected_league]["teams"]}:
            raise ValueError("el equipo seleccionado no pertenece a la liga elegida o no dispone de plantilla jugable")
        through_requested=max(0,int(through_matchday))
        playable_date=CAREER_PRESEASON_START_9394 if through_requested==0 else CAREER_START_DATE_9394
        state = {
            "schema": CAREER_SCHEMA_9394,
            "career_id": str(uuid4()), "season": "1993-94", "seed": int(seed),
            "team_id": int(team_id), "league_id": selected_league,
            "current_date": playable_date.isoformat(),
            "completed_matchday": 0, "results": [], "tactics": _default_tactics(),
            "player_development": initial_player_development(universe.payload.get("players", [])),
            "player_team_overrides": {}, "contract_overrides": {}, "transfer_history": [],
            "finances": initial_club_finances(team, players=list(universe.players_by_team.get(int(team_id), ()))), "economy_ledger": [],
            "age_policy": (AGE_POLICY_DYNAMIC if str(age_policy) == AGE_POLICY_DYNAMIC else AGE_POLICY_FROZEN),
            "rules_policy": RULES_POLICY_FROZEN_9394,
            "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        runtime = cls(state, universe=universe)
        # The historical backfill can create injuries. The user has not chosen
        # an XI yet, so selection is regenerated after the backfill.
        runtime.state.pop("selection", None)
        through = max(0, min(through_requested, runtime._controlled_total_rounds()))
        for matchday in range(1, through + 1):
            runtime._simulate_matchday(matchday)
        runtime._bootstrap_background_world(through)
        # Special formats and cup/continental legs are brought forward to the
        # playable date. Bootstrap results persist but do not alter player form.
        process_special_competitions(runtime, playable_date, bootstrap=True)
        process_daily_tournaments(runtime, playable_date, bootstrap=True)
        runtime.state["current_date"] = playable_date.isoformat()
        runtime.state["selection"] = runtime._auto_selection()
        runtime.state["board_expectation"] = runtime._board_expectation()
        runtime.board_snapshot(persist=True,trigger="season_start")
        runtime._refresh_storyline_state()
        return runtime

    @property
    def current_date(self) -> date:
        return date.fromisoformat(str(self.state["current_date"]))

    def _player_source(self, player_id: int) -> dict[str, Any] | None:
        pid = int(player_id)
        row = self.universe.players_by_id.get(pid)
        return row if row is not None else generated_player(self.state, pid)

    def _all_player_rows(self) -> list[dict[str, Any]]:
        return list(self.universe.payload.get("players", [])) + all_generated_players(self.state)

    def _all_players_index(self) -> dict[int, dict[str, Any]]:
        return {int(row["source_id"]): row for row in self._all_player_rows()}

    def _current_team_id(self, player_id: int) -> int:
        override = self.state.get("player_team_overrides", {}).get(str(int(player_id)))
        if override is not None:
            return int(override)
        row = self._player_source(int(player_id))
        if row is None:
            raise KeyError(f"jugador {player_id} no existe")
        return int(row.get("team_id") or 0)

    def _rebuild_rosters(self) -> None:
        all_by_team: dict[int, list[dict[str, Any]]] = {}
        match_by_team: dict[int, list[dict[str, Any]]] = {}
        dev = self.state.get("player_development") or {}
        for base in self._all_player_rows():
            pid = int(base["source_id"])
            team_id = self._current_team_id(pid)
            row = dict(base)
            row["team_id"] = team_id
            d = dev.get(str(pid), {})
            if d.get("overall") is not None:
                row["overall"] = int(d["overall"])
            all_by_team.setdefault(team_id, []).append(row)
            if int(d.get("injury_days") or 0) <= 0 and not row.get("retired") and not bool(d.get("retired")):
                match_by_team.setdefault(team_id, []).append(row)
        self._career_players_by_team = all_by_team
        self._match_players_by_team = match_by_team
        for team_id, rows in all_by_team.items():
            if int(team_id) != 0:
                sync_team_dynamics(self.state, players=rows, development=dev, game_date=self.current_date)
        self._career_universe = _CareerUniverseView(self)
        self._all_career_universe = _CareerUniverseView(self, include_injured=True)
        if hasattr(self, "_strength_cache"):
            self._strength_cache.clear()

    def _apply_development_to_footballer(self, player: Footballer9394) -> Footballer9394:
        d = self.state.get("player_development", {}).get(str(player.id))
        if not d:
            return player
        target = int(d.get("overall") or player.overall)
        delta = target - int(player.overall)
        physical_delta = int(d.get("physical_delta") or 0)
        technical_delta = int(d.get("technical_delta") or 0)
        specific = dict(d.get("attribute_deltas") or {})
        condition = max(0, min(100, int(d.get("condition") or 100)))
        accumulated_fatigue = max(0, min(100, int(d.get("fatigue") or 0)))
        physical_match_penalty = max(0, min(14, round(max(0, 82 - condition) / 7 + accumulated_fatigue / 24)))
        def c(v: int, extra: int = 0, key: str = "", temporary_penalty: int = 0) -> int:
            return max(1, min(100, int(v) + delta + extra + int(specific.get(key) or 0) - int(temporary_penalty)))
        source_player=self._player_source(int(player.id)) if str(player.id).isdigit() else None
        natural_goalkeeper=bool(source_player and role_for_player(source_player).squad_slot == "GK")
        return replace(
            player, overall=target,
            pace=c(player.pace, physical_delta, "pace", physical_match_penalty), acceleration=c(player.acceleration, physical_delta, "acceleration", physical_match_penalty),
            stamina=c(player.stamina, physical_delta, "stamina", physical_match_penalty), strength=c(player.strength, physical_delta, "strength", physical_match_penalty // 2), jumping=c(player.jumping, physical_delta, "jumping", physical_match_penalty // 2),
            technique=c(player.technique, technical_delta, "technique"), short_pass=c(player.short_pass, technical_delta, "short_pass"),
            long_pass=c(player.long_pass, technical_delta, "long_pass"), creativity=c(player.creativity, technical_delta, "creativity"),
            vision=c(player.vision, technical_delta, "vision"), dribbling=c(player.dribbling, technical_delta, "dribbling"),
            finishing=c(player.finishing, technical_delta, "finishing"), heading=c(player.heading, technical_delta, "heading"),
            shot_power=c(player.shot_power, technical_delta, "shot_power"), free_kicks=c(player.free_kicks, technical_delta, "free_kicks"), penalties=c(player.penalties, technical_delta, "penalties"),
            tackling=c(player.tackling, 0, "tackling"), marking=c(player.marking, 0, "marking"), positioning=c(player.positioning, 0, "positioning"), anticipation=c(player.anticipation, 0, "anticipation"),
            work_rate=c(player.work_rate, 0, "work_rate"), off_ball=c(player.off_ball, 0, "off_ball"),
            leadership=c(player.leadership, 0, "leadership"), consistency=c(player.consistency, 0, "consistency"),
            discipline=c(player.discipline, 0, "discipline"), aggression=c(player.aggression, 0, "aggression"),
            injury_proneness=min(3, int(player.injury_proneness) + (1 if accumulated_fatigue >= 48 or condition <= 68 else 0)),
            # An outfield player assigned as an emergency goalkeeper must not
            # magically inherit goalkeeper skill from his outfield development.
            goalkeeping=(c(player.goalkeeping, technical_delta, "goalkeeping") if natural_goalkeeper else player.goalkeeping),
        )

    def _apply_ai_emergency_injury_penalty(self, player: Footballer9394) -> Footballer9394:
        """Make using an injured footballer a genuine last resort for world AI.

        Injuries are not ignored: the player remains the same real squad member
        but suffers a large temporary match penalty that scales with the
        remaining lay-off.  This path is used only after the healthy roster has
        failed to produce a legal XI under the competition's foreign-player
        rule.
        """
        d = self.state.get("player_development", {}).get(str(player.id)) or {}
        days = int(d.get("injury_days") or 0)
        if days <= 0:
            return player
        # Even a short injury hurts; a multi-week lay-off makes selection
        # extremely costly.  Technical quality falls less than mobility/stamina.
        base = min(38, 12 + days // 2)
        physical = min(48, base + 8)
        technical = max(6, base // 2)
        def c(value: int, penalty: int) -> int:
            return max(1, int(value) - int(penalty))
        return replace(
            player,
            overall=c(player.overall, base),
            pace=c(player.pace, physical),
            stamina=c(player.stamina, physical),
            technique=c(player.technique, technical),
            short_pass=c(player.short_pass, technical),
            long_pass=c(player.long_pass, technical),
            creativity=c(player.creativity, technical),
            finishing=c(player.finishing, technical),
            heading=c(player.heading, technical),
            tackling=c(player.tackling, technical),
            marking=c(player.marking, technical),
            positioning=c(player.positioning, technical),
            goalkeeping=c(player.goalkeeping, technical),
        )

    def _team_strength(self, team_id: int) -> float:
        team_id = int(team_id)
        cached = self._strength_cache.get(team_id)
        if cached is not None:
            return cached
        values = sorted((int(p.get("overall") or p.get("category") or 60) for p in self._career_players_by_team.get(team_id, [])), reverse=True)[:11]
        value = sum(values) / len(values) if values else 60.0
        self._strength_cache[team_id] = value
        return value

    def _league_yellow_cycle(self, team_id: int) -> int:
        league_id=self._current_league_for_team(int(team_id))
        league=self.universe.leagues_by_id.get(int(league_id)) if league_id is not None else None
        return max(1,int((league or {}).get("yellow_card_cycle") or 5))

    def _league_suspension_ids(self, team_id: int) -> set[int]:
        dev=self.state.get("player_development") or {}
        return {
            int(row["source_id"]) for row in self._career_players_by_team.get(int(team_id),[])
            if int((dev.get(str(int(row["source_id"]))) or {}).get("league_suspension_matches") or 0)>0
        }

    def _selection_fixture_kind(self) -> str:
        fixture=self.pending_world_fixture() or self.next_scheduled_fixture()
        return str((fixture or {}).get("fixture_type") or "league")

    def _controlled_absences_for_fixture(self, fixture: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """One canonical availability story for every pre-match surface.

        Injury always wins over suspension as the immediate reason a footballer
        cannot be selected.  League suspensions only apply to league fixtures;
        cup/friendly screens must not make a player look globally unavailable.
        """
        controlled=int(self.state["team_id"]); fixture=fixture or self.next_scheduled_fixture()
        is_league=str((fixture or {}).get("fixture_type") or "league")=="league"
        rows=[]
        for raw in self._career_players_by_team.get(controlled, []):
            if raw.get("retired"): continue
            pid=int(raw.get("source_id") or 0); dev=(self.state.get("player_development") or {}).get(str(pid)) or {}
            injury_days=int(dev.get("injury_days") or 0); suspension=int(dev.get("league_suspension_matches") or 0)
            if injury_days>0:
                api=self._career_player_api(raw); medical=api.get("medical") or {}; current=medical.get("current_injury") or {}
                name=str(current.get("name") or "Lesión")
                rows.append({"player_id":pid,"name":api.get("display_name") or self._player_name(pid),"kind":"injury","status":f"{name} · {injury_days} d","detail":f"Baja médica estimada: {injury_days} días.","days":injury_days})
            elif is_league and suspension>0:
                reason=str(dev.get("league_suspension_reason") or "Sanción disciplinaria")
                rows.append({"player_id":pid,"name":self._player_name(pid),"kind":"suspension","status":f"Sancionado (liga) · {suspension} partido"+("s" if suspension!=1 else ""),"detail":reason,"matches":suspension})
        return rows

    def calendar_context_snapshot(self, fixture: dict[str, Any] | None = None) -> dict[str, Any]:
        """Describe calendar edge states without inventing an opponent or date."""
        fixture=self.next_scheduled_fixture() if fixture is None else fixture
        if not fixture:
            completed=int(self.state.get("completed_matchday") or 0)
            total=int(self._controlled_total_rounds())
            if completed>=total and total>0:
                return {"state":"season_complete","label":"Calendario completado","detail":"No quedan jornadas oficiales por disputar en esta temporada.","availability_count":0}
            return {"state":"empty","label":"Sin partido programado","detail":"No hay fecha ni rival confirmados. El juego puede continuar hasta que aparezca el siguiente compromiso.","availability_count":0}
        home=int(fixture.get("home_team_id") or 0); away=int(fixture.get("away_team_id") or 0); controlled=int(self.state["team_id"])
        opponent=away if home==controlled else home if away==controlled else 0
        absences=self._controlled_absences_for_fixture(fixture)
        if bool(fixture.get("postponed")) or str(fixture.get("schedule_status") or "").lower()=="postponed":
            return {"state":"postponed","label":"Partido aplazado","detail":"El encuentro no tiene una nueva fecha confirmada todavía.","fixture_id":fixture.get("id"),"availability_count":len(absences),"availability":absences}
        if opponent<=0:
            return {"state":"opponent_pending","label":"Rival por confirmar","detail":"La fecha existe, pero el rival aún no está determinado.","fixture_id":fixture.get("id"),"date":fixture.get("date"),"availability_count":len(absences),"availability":absences}
        return {"state":"scheduled","label":"Próximo partido confirmado","detail":f"{self._team_name(opponent)} · {fixture.get('date') or 'fecha pendiente'}","fixture_id":fixture.get("id"),"date":fixture.get("date"),"opponent_id":opponent,"opponent_name":self._team_name(opponent),"availability_count":len(absences),"availability":absences}

    def _eligible_match_rows(self, team_id: int, *, competition_kind: str | None = None, include_injured: bool = False) -> list[dict[str,Any]]:
        rows=list((self._career_players_by_team if include_injured else self._match_players_by_team).get(int(team_id),[]))
        if competition_kind=="league":
            suspended=self._league_suspension_ids(int(team_id))
            rows=[row for row in rows if int(row.get("source_id") or 0) not in suspended]
        return rows

    def _auto_selection(self) -> dict[str, list[int]]:
        tactics = FootballTactics9394(**{**_default_tactics(), **(self.state.get("tactics") or {})})
        controlled=int(self.state["team_id"]);rule=self._domestic_foreign_rule(controlled)
        predicate=(lambda row:is_foreign_player(
            row,home_country_id=rule.home_country_id,continental=False,
            domestic_equivalent_country_ids=rule.domestic_equivalent_country_ids,
        )) if rule is not None else None
        kind=self._selection_fixture_kind()
        universe_view=_CareerUniverseView(self,exclude_league_suspended=(kind=="league"))
        sheet = build_snapshot_team_sheet(universe_view, controlled, tactics=tactics,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None))
        return {"starter_ids": [int(p.id) for p in sheet.starters], "bench_ids": [int(p.id) for p in sheet.bench]}

    def _safe_auto_selection(self) -> dict[str, list[int]]:
        """Return the best legal XI when possible, otherwise an explicit incomplete draft.

        Contract expiry must never crash a career.  If the manager lets the squad
        fall below eleven available players the game stays alive, surfaces the
        shortage in the inbox and blocks match play until the roster is repaired.
        """
        try:
            return self._auto_selection()
        except ValueError:
            players=sorted(self._eligible_match_rows(int(self.state["team_id"]),competition_kind=self._selection_fixture_kind()), key=lambda p:(-int(p.get("overall") or p.get("category") or 0),int(p.get("source_id") or 0)))
            chosen=players[:LAWS_1993_94.players_per_team]
            if chosen and not any(role_for_player(p).squad_slot=="GK" for p in chosen):
                keeper=next((p for p in players if role_for_player(p).squad_slot=="GK"),None)
                if keeper is not None:
                    chosen[-1]=keeper
            starter_ids=[int(p["source_id"]) for p in chosen]
            bench=[int(p["source_id"]) for p in players if int(p["source_id"]) not in set(starter_ids)][:LAWS_1993_94.max_named_substitutes]
            return {"starter_ids":starter_ids,"bench_ids":bench}

    def _board_expectation(self) -> dict[str, Any]:
        league_id = int(self.state["league_id"])
        teams = sorted(self._teams_for_league(league_id), key=lambda team: -(self._team_strength(int(team["source_id"]))*0.65 + float(club_status(self.state,int(team["source_id"])).get("score") or 50)*0.35))
        team_id = int(self.state["team_id"]); count = len(teams)
        expected = next((i + 1 for i, team in enumerate(teams) if int(team["source_id"]) == team_id), max(1, count))
        if expected <= 2: title = "Pelear por el título"
        elif expected <= 4: title = "Clasificarse para Europa"
        elif expected <= max(6, round(count * .35)): title = "Acabar en la zona alta"
        elif expected >= max(1, count - 3): title = "Lograr la permanencia"
        else: title = "Completar una temporada competitiva"
        return {"title": title, "expected_position": expected, "team_count": count}

    def _ensure_manager_layer(self) -> None:
        if not self.state.get("selection"):
            self.state["selection"] = self._safe_auto_selection()
        if not self.state.get("board_expectation"):
            self.state["board_expectation"] = self._board_expectation()

    def _ensure_nf9_nf12_layers(self) -> None:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id}
        ensure_professional_state(self.state, team=team)
        ensure_information_state(self.state)
        ensure_longitudinal_economy(self.state)
        ensure_longitudinal_health_state(self.state)
        economy = self.economy_snapshot()
        staff = self.staff_snapshot()
        expectation = self.state.get("board_expectation") or self._board_expectation()
        ensure_board_project(
            self.state, team=team, club_score=float(club_status(self.state, team_id).get("score") or 50.0),
            expected_position=int(expectation.get("expected_position") or 1), team_count=int(expectation.get("team_count") or len(self._teams_for_league(int(self.state["league_id"])))),
            squad_size=len(self._career_players_by_team.get(team_id, [])), staff_size=len(staff.get("members") or []), economy=economy, date_text=self.current_date.isoformat(),
        )
        profile = self.state["user_manager"]
        if self.state.get("job_status") == "active" and not profile.get("active_contract"):
            league = team.get("league") or {}
            contract = build_manager_contract(
                team_id=team_id, team_name=self._team_name(team_id), league_id=int(self.state["league_id"]),
                league_name=str(league.get("name") or f"Liga {self.state['league_id']}"), date_text=str((profile.get("current_tenure") or {}).get("started_on") or self.current_date.isoformat()),
                reputation=float(profile.get("reputation") or 50.0), club_score=float(club_status(self.state, team_id).get("score") or 50.0),
                expected_position=int(expectation.get("expected_position") or 1),
            )
            register_contract(self.state, contract)

    def _professional_career_view(self) -> dict[str, Any]:
        snap = professional_snapshot(self.state)
        for relationship in snap.get("relationships") or []:
            team_id = int(relationship.get("team_id") or 0)
            relationship["team_name"] = self._team_name(team_id) if team_id else "Sin club"
        return snap

    def professional_career_snapshot(self) -> dict[str, Any]:
        profile=self.state.get("user_manager") or {}
        if str(profile.get("last_job_search_on") or "") != self.current_date.isoformat():
            self._refresh_job_market(day=self.current_date, proactive=False)
        else:
            expire_job_market(self.state,day=self.current_date)
        return self._professional_career_view()

    def board_project_snapshot(self) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        self._update_board_project_state()
        return project_snapshot(self.state, team_id)

    def information_world_snapshot(self, *, limit: int = 80) -> dict[str, Any]:
        return information_snapshot(self.state, limit=limit)

    def selection_snapshot(self) -> dict[str, Any]:
        controlled = int(self.state["team_id"]); raw = self.state.get("selection") or {}
        starter_ids = [int(x) for x in raw.get("starter_ids") or []]
        bench_ids = [int(x) for x in raw.get("bench_ids") or []]
        available = {int(p["source_id"]): p for p in self._match_players_by_team.get(controlled, [])}
        owned = {int(p["source_id"]): p for p in self._career_players_by_team.get(controlled, [])}
        suspended=self._league_suspension_ids(controlled) if self._selection_fixture_kind()=="league" else set()
        issues: list[str] = []; warnings: list[str] = []
        if len(starter_ids) != LAWS_1993_94.players_per_team: issues.append("El once debe tener exactamente 11 jugadores.")
        if len(starter_ids) != len(set(starter_ids)): issues.append("Hay jugadores repetidos en el once.")
        if any(pid not in owned for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador que no pertenece al club.")
        if any(pid not in available for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador lesionado o no disponible.")
        if any(pid in suspended for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador sancionado para el próximo partido de liga.")
        if len(bench_ids) > LAWS_1993_94.max_named_substitutes: issues.append(f"Sólo se pueden nombrar {LAWS_1993_94.max_named_substitutes} suplentes.")
        if len(set(starter_ids + bench_ids)) != len(starter_ids + bench_ids): issues.append("Un jugador no puede ser titular y suplente a la vez.")
        if starter_ids and not any(role_for_player(owned.get(pid, {})).squad_slot == "GK" for pid in starter_ids): issues.append("El once necesita portero.")
        formation=str((self.state.get("tactics") or {}).get("formation") or "4-4-2")
        assigned=assign_players_to_formation([owned[pid] for pid in starter_ids if pid in owned],formation) if starter_ids else []
        if len(assigned)==11:
            severe=[r for r in assigned if int(r.get("penalty") or 0)>=20]
            if severe: warnings.append(f"Hay {len(severe)} futbolista{'s' if len(severe)!=1 else ''} muy fuera de posición.")
        rule=self._domestic_foreign_rule(controlled)
        foreign_issues=[]
        if rule is not None:
            foreign_issues=validate_matchday_foreigners([owned[pid] for pid in starter_ids if pid in owned],[owned[pid] for pid in bench_ids if pid in owned],rule)
            issues.extend(foreign_issues)
        def api(pid: int): return self._career_player_api(owned[pid]) if pid in owned else {"id": pid}
        assigned_by_id={int(r["player_id"]):r for r in assigned}
        starters_api=[]
        for pid in starter_ids:
            row=api(pid);fit=assigned_by_id.get(pid)
            if fit: row={**row,"assigned_slot":fit["slot"],"position_fit":fit["label"],"position_penalty":fit["penalty"]}
            starters_api.append(row)
        return {"starter_ids": starter_ids, "bench_ids": bench_ids, "starters": starters_api, "bench": [api(pid) for pid in bench_ids], "valid": not issues, "issues": issues,
            "formation":formation,"foreign_rule":rule.as_dict() if rule else None,"foreign_issues":foreign_issues,"warnings":warnings,
            "role_coverage":squad_role_audit(list(owned.values()))}

    def set_selection(self, starter_ids: list[int], bench_ids: list[int] | None = None) -> dict[str, Any]:
        starters = [int(x) for x in starter_ids]
        if bench_ids is None:
            candidates = [int(p["source_id"]) for p in sorted(self._eligible_match_rows(int(self.state["team_id"]),competition_kind=self._selection_fixture_kind()), key=lambda p: -int(p.get("overall") or p.get("category") or 0)) if int(p["source_id"]) not in set(starters)]
            bench = candidates[:LAWS_1993_94.max_named_substitutes]
        else:
            bench = [int(x) for x in bench_ids]
        previous = self.state.get("selection")
        self.state["selection"] = {"starter_ids": starters, "bench_ids": bench}
        snap = self.selection_snapshot()
        if not snap["valid"]:
            if previous is None: self.state.pop("selection", None)
            else: self.state["selection"] = previous
            raise ValueError(" ".join(snap["issues"]))
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return snap

    def _team_name(self, team_id: int) -> str:
        if not team_id: return "Sin club"
        row=self._team_api(int(team_id)) or self.universe.team(int(team_id)) or {}
        return str(row.get("name") or row.get("long_name") or team_id)

    def _player_name(self, player_id: int) -> str:
        row=self._player_source(int(player_id)) or {}
        return str(row.get("display_name") or row.get("name") or player_id)

    def board_snapshot(self, *, persist: bool = False, trigger: str = "snapshot") -> dict[str, Any]:
        table=self.standings(); team_id=int(self.state["team_id"])
        own=next((r for r in table if int(r["team_id"])==team_id),None) or {}
        recent=[]
        for result in reversed(self.state.get("results") or []):
            if team_id not in (int(result["home_team_id"]),int(result["away_team_id"])): continue
            mine=int(result["home_goals"]) if int(result["home_team_id"])==team_id else int(result["away_goals"]);theirs=int(result["away_goals"]) if int(result["home_team_id"])==team_id else int(result["home_goals"])
            recent.append("V" if mine>theirs else "E" if mine==theirs else "D")
            if len(recent)==5: break
        recent.reverse()
        economy=self.economy_snapshot(); previous=(self.state.get("board_state") or {}).get("score")
        review=evaluate_board(expectation=self.state.get("board_expectation") or self._board_expectation(),position=own.get("position"),played=int(own.get("played") or 0),recent_form=recent,projected_monthly_net=int(economy.get("projected_monthly_net") or 0),cash=int(economy.get("cash") or 0),debt=int(economy.get("debt") or 0),previous_score=int(previous) if previous is not None else None)
        if persist:
            before=self.state.get("job_status") or "active"
            review=apply_board_review(self.state,review,date=self.current_date.isoformat(),trigger=trigger)
            if before!="dismissed" and self.state.get("job_status")=="dismissed":
                publish_news(self.state,key=f"dismissed:{self.state.get('season')}:{self.current_date.isoformat()}",date=self.current_date.isoformat(),category="Club",importance=5,headline="El consejo destituye al mánager",detail="La decisión llega tras dos revisiones críticas consecutivas y al menos doce partidos de liga. Tu carrera como entrenador no termina aquí.",entity={"team_id":int(self.state["team_id"])})
                self._handle_user_dismissal()
        payload={**review,"expectation":self.state.get("board_expectation") or self._board_expectation(),"warning_count":int(self.state.get("board_warning_count") or 0),"job_status":self.state.get("job_status") or "active","history":list(self.state.get("board_history") or [])[-12:]}
        if persist and self.state.get("job_status")=="active":
            self._update_board_project_state(board=payload)
        return payload

    def _update_board_project_state(self, *, board: dict[str, Any] | None = None) -> dict[str, Any]:
        team_id=int(self.state["team_id"]); team=self._team_api(team_id) or self.universe.team(team_id) or {"source_id":team_id}
        economy=self.economy_snapshot(); staff=self.staff_snapshot(); expectation=self.state.get("board_expectation") or self._board_expectation()
        ensure_board_project(self.state,team=team,club_score=float(club_status(self.state,team_id).get("score") or 50),expected_position=int(expectation.get("expected_position") or 1),team_count=int(expectation.get("team_count") or len(self._teams_for_league(int(self.state["league_id"])))),squad_size=len(self._career_players_by_team.get(team_id,[])),staff_size=len(staff.get("members") or []),economy=economy,date_text=self.current_date.isoformat())
        board = board or {**evaluate_board(expectation=expectation,position=next((r.get("position") for r in self.standings() if int(r.get("team_id") or 0)==team_id),None),played=next((int(r.get("played") or 0) for r in self.standings() if int(r.get("team_id") or 0)==team_id),0),recent_form=[],projected_monthly_net=int(economy.get("projected_monthly_net") or 0),cash=int(economy.get("cash") or 0),debt=int(economy.get("debt") or 0),previous_score=(self.state.get("board_state") or {}).get("score"))}
        before=project_snapshot(self.state,team_id).get("sale_pressure")
        project=update_board_project(state=self.state,team_id=team_id,board=board,economy=economy,squad_size=len(self._career_players_by_team.get(team_id,[])),staff_size=len(staff.get("members") or []),date_text=self.current_date.isoformat())
        after=project.get("sale_pressure")
        if after and after.get("status")=="active" and (not before or before.get("created_on")!=after.get("created_on")):
            event={"kind":"board_sale_pressure","date":self.current_date.isoformat(),"team_id":team_id,"required_income":int(after.get("required_income") or 0)}
            self.state.setdefault("world_events",[]).append(event); self.state["world_events"]=self.state["world_events"][-600:]
            thread=register_information_event(self.state,event,headline="El consejo pide equilibrar la caja con una venta",detail=str(after.get("reason") or ""))
            publish_news(self.state,key=f"board-sale-pressure:{team_id}:{after.get('created_on')}",date=self.current_date.isoformat(),category="Club",importance=4,headline="El consejo pide una venta",detail=f"La situación financiera exige generar aproximadamente {int(after.get('required_income') or 0):,} ptas. en ingresos antes de ampliar el gasto.".replace(",","."),entity={"team_id":team_id})
            if thread: add_reaction(self.state,thread_id=thread["id"],actor="Consejo",sentiment="negative",text="La prioridad inmediata es proteger la viabilidad deportiva del club.",date_text=self.current_date.isoformat(),consequence={"kind":"sale_required","amount":int(after.get("required_income") or 0)})
        return project

    def submit_board_request(self, request_type: str) -> dict[str, Any]:
        if self.state.get("job_status")!="active": raise ValueError("necesitas estar al frente de un club para pedir respaldo al consejo")
        team_id=int(self.state["team_id"]); board=self.board_snapshot(persist=False); economy=self.economy_snapshot()
        self._update_board_project_state(board=board)
        request=submit_board_request(state=self.state,team_id=team_id,request_type=request_type,date_text=self.current_date.isoformat(),board_score=int(board.get("score") or 50),economy=economy)
        if request.get("status")=="accepted" and request_type=="extra_transfer_budget":
            amount=int(request.get("amount") or 0); grant_transfer_budget(self.state["finances"],amount); self.state["club_finances"][str(team_id)]=self.state["finances"]
            self.state["economy_ledger"].append({"date":self.current_date.isoformat(),"kind":"board_injection","amount":amount})
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="board_injections",amount=amount)
        publish_news(self.state,key=f"board-request:{request['id']}",date=self.current_date.isoformat(),category="Club",importance=3 if request.get("status")=="accepted" else 2,headline=("El consejo respalda tu petición" if request.get("status")=="accepted" else "El consejo rechaza tu petición"),detail=str(request.get("reason") or ""),entity={"team_id":team_id})
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {"request":request,"project":self.board_project_snapshot(),"economy":self.economy_snapshot()}

    def _active_work_for_responsibility(self, responsibility_key: str) -> list[dict[str, Any]]:
        """Return user-facing work currently owned by one responsibility.

        V1.0-K treats delegation as a live process hand-off, not a preference
        toggle.  This helper intentionally reads canonical career state only so
        Staff can explain what will move before the assignee is changed.
        """
        key = str(responsibility_key)
        rows: list[dict[str, Any]] = []
        if key == "recruitment_search":
            for task in (self.state.get("scouting_assignments") or {}).values():
                if task.get("status") != "active":
                    continue
                rows.append({
                    "id": str(task.get("id") or f"scout:{task.get('player_id')}"),
                    "kind": "scouting",
                    "title": f"Informe de {task.get('player_name') or self._player_name(int(task.get('player_id') or 0))}",
                    "status": "En curso",
                    "due_on": task.get("due_on"),
                    "workspace": "market",
                })
        elif key == "transfer_negotiation":
            for deal in (self.state.get("transfer_negotiations") or {}).values():
                if deal.get("status") not in {"waiting", "countered"}:
                    continue
                rows.append({
                    "id": str(deal.get("id") or f"deal:{deal.get('player_id')}"),
                    "kind": "negotiation",
                    "title": f"Negociación por {self._player_name(int(deal.get('player_id') or 0))}",
                    "status": "Requiere decisión" if deal.get("status") == "countered" else "Esperando respuesta",
                    "due_on": deal.get("response_date"),
                    "workspace": "market",
                })
        elif key == "first_team_training":
            training = self.state.get("training") or {}
            if training:
                rows.append({
                    "id": "training:weekly-plan",
                    "kind": "training",
                    "title": "Plan semanal del primer equipo",
                    "status": "Plan activo",
                    "due_on": self.current_date.isoformat(),
                    "workspace": "training",
                })
        elif key == "medical_assessment":
            for player in self._career_players_by_team.get(int(self.state["team_id"]), ()): 
                pid = int(player.get("source_id") or 0)
                dev = (self.state.get("player_development") or {}).get(str(pid), {})
                injury_days = max(0, int(dev.get("injury_days") or 0))
                risk = max(0, int(dev.get("injury_risk") or 0))
                if injury_days <= 0 and risk < 70:
                    continue
                rows.append({
                    "id": f"medical:{pid}",
                    "kind": "medical",
                    "title": f"{self._player_name(pid)} · {'baja' if injury_days else 'riesgo alto'}",
                    "status": f"{injury_days} días estimados" if injury_days else f"Riesgo {risk}/100",
                    "due_on": None,
                    "workspace": "training",
                })
        elif key == "contract_renewal":
            for player in self.squad(int(self.state["team_id"])):
                end_year = int((player.get("contract") or {}).get("end_year") or 9999)
                if end_year > self.current_date.year + 1:
                    continue
                rows.append({
                    "id": f"contract:{player.get('id')}",
                    "kind": "contract",
                    "title": f"Contrato de {player.get('display_name') or player.get('name')}",
                    "status": f"Termina en {end_year}",
                    "due_on": None,
                    "workspace": "squad",
                })
        return rows[:12]

    def staff_snapshot(self) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id, "name": self._team_name(team_id)}
        snapshot = club_staff_snapshot(
            self.state, team=team, strength=self._team_strength(team_id), game_date=self.current_date,
        )
        handoffs = list(self.state.get("staff_handoffs") or [])
        for row in snapshot.get("responsibilities") or []:
            active = self._active_work_for_responsibility(str(row.get("key") or ""))
            row["active_processes"] = active
            row["active_process_count"] = len(active)
            row["last_handoff"] = next((dict(item) for item in reversed(handoffs) if item.get("responsibility") == row.get("key")), None)
        snapshot["recent_handoffs"] = [dict(row) for row in handoffs[-8:]][::-1]
        snapshot["active_process_count"] = sum(int(row.get("active_process_count") or 0) for row in snapshot.get("responsibilities") or [])
        return snapshot

    def set_staff_responsibility(self, responsibility_key: str, assignee: str) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id, "name": self._team_name(team_id)}
        before = club_staff_snapshot(self.state, team=team, strength=self._team_strength(team_id), game_date=self.current_date)
        before_row = next((row for row in before.get("responsibilities") or [] if row.get("key") == str(responsibility_key)), None)
        affected = self._active_work_for_responsibility(str(responsibility_key))
        updated = assign_staff_responsibility(
            self.state, team=team, strength=self._team_strength(team_id),
            responsibility_key=responsibility_key, assignee=assignee, game_date=self.current_date,
        )
        after_row = next((row for row in updated.get("responsibilities") or [] if row.get("key") == str(responsibility_key)), None)
        if before_row and after_row and str(before_row.get("assignee")) != str(after_row.get("assignee")):
            effect = self._responsibility_effect(str(responsibility_key))
            if str(responsibility_key) == "recruitment_search":
                for task in (self.state.get("scouting_assignments") or {}).values():
                    if task.get("status") != "active":
                        continue
                    task["responsible"] = effect.get("assignee_name")
                    task["responsible_role"] = effect.get("assignee_role")
                    task["quality_at_start"] = int(effect.get("quality") or task.get("quality_at_start") or 10)
                    task.setdefault("handoffs", []).append({"date": self.current_date.isoformat(), "to": effect.get("assignee_name"), "quality": int(effect.get("quality") or 10)})
            elif str(responsibility_key) == "transfer_negotiation":
                for deal in (self.state.get("transfer_negotiations") or {}).values():
                    if deal.get("status") not in {"waiting", "countered"}:
                        continue
                    deal.update({
                        "handled_by": effect.get("assignee_name"),
                        "handler_role": effect.get("assignee_role"),
                        "handler_quality": int(effect.get("quality") or 10),
                        "handler_quality_label": effect.get("quality_label"),
                    })
                    deal.setdefault("history", []).append({
                        "date": self.current_date.isoformat(), "kind": "handler_changed",
                        "from": before_row.get("assignee_name"), "to": effect.get("assignee_name"),
                    })
            handoff = {
                "id": f"handoff:{responsibility_key}:{self.current_date.isoformat()}:{len(self.state.get('staff_handoffs') or [])}",
                "date": self.current_date.isoformat(), "responsibility": str(responsibility_key),
                "label": after_row.get("label"), "from_assignee": before_row.get("assignee"),
                "from_name": before_row.get("assignee_name"), "to_assignee": after_row.get("assignee"),
                "to_name": after_row.get("assignee_name"), "affected_count": len(affected),
                "affected_processes": affected,
            }
            self.state.setdefault("staff_handoffs", []).append(handoff)
            self.state["staff_handoffs"] = self.state["staff_handoffs"][-60:]
            self.state.setdefault("world_events", []).append({
                "kind": "staff_responsibility_handoff", "date": self.current_date.isoformat(),
                "responsibility": str(responsibility_key), "from_name": before_row.get("assignee_name"),
                "to_name": after_row.get("assignee_name"), "affected_count": len(affected),
            })
            self.state["world_events"] = self.state["world_events"][-600:]
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.staff_snapshot()

    def _responsibility_effect(self, responsibility_key: str) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id, "name": self._team_name(team_id)}
        return responsibility_effectiveness(
            self.state, team=team, strength=self._team_strength(team_id),
            responsibility_key=responsibility_key, game_date=self.current_date,
        )

    def _scouting_capacity(self) -> int:
        staff = self.staff_snapshot()
        members = [row for row in (staff.get("members") or []) if row.get("active", True)]
        specialists = [row for row in members if row.get("role") in {"scout", "chief_scout"}]
        capacity = max(1, len(specialists))
        chief = next((row for row in specialists if row.get("role") == "chief_scout"), None)
        if chief and int((chief.get("skills") or {}).get("market_knowledge") or 0) >= 15:
            capacity += 1
        recruitment = next((row for row in (staff.get("responsibilities") or []) if row.get("key") == "recruitment_search"), {})
        if recruitment.get("assignee") == "manager":
            capacity += 1
        return max(1, min(6, capacity))

    def _team_country(self, team_id: int) -> str:
        team = self._team_api(int(team_id)) or self.universe.team(int(team_id)) or {}
        return str(team.get("country") or (team.get("league") or {}).get("country") or "")

    def scouting_snapshot(self) -> dict[str, Any]:
        return {
            **build_scouting_snapshot(self.state, game_date=self.current_date, capacity=self._scouting_capacity()),
            "responsibility": self._responsibility_effect("recruitment_search"),
        }

    def start_scouting_player(self, player_id: int) -> dict[str, Any]:
        pid = int(player_id)
        raw = self._player_source(pid)
        if raw is None:
            raise KeyError(f"jugador {pid} no existe")
        target_team = self._current_team_id(pid)
        if target_team == int(self.state["team_id"]):
            raise ValueError("tu propia plantilla se evalúa mediante el cuerpo técnico, no con un dossier de mercado")
        geography = scouting_geography(self._team_country(int(self.state["team_id"])), self._team_country(target_team) if target_team else None)
        task = start_scouting(
            self.state, player_id=pid, game_date=self.current_date,
            effectiveness=self._responsibility_effect("recruitment_search"),
            player_name=str(raw.get("display_name") or raw.get("name") or pid),
            capacity=self._scouting_capacity(), geography=geography,
        )
        ids={int(x) for x in (self.state.get("watchlist") or [])}; ids.add(pid); self.state["watchlist"]=sorted(ids)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return task

    def training_snapshot(self) -> dict[str, Any]:
        controlled = int(self.state["team_id"])
        fixture = self.next_scheduled_fixture()
        next_date = date.fromisoformat(str(fixture["date"])) if fixture and fixture.get("date") else None
        snapshot = build_training_snapshot(
            self.state, players=list(self._career_players_by_team.get(controlled, [])),
            development=self.state["player_development"], effectiveness=self._responsibility_effect("first_team_training"),
            game_date=self.current_date, next_match_date=next_date,
        )
        medical = self._responsibility_effect("medical_assessment")
        cases = []
        for row in snapshot.get("players") or []:
            injury_days = int(row.get("injury_days") or 0)
            risk = int(row.get("risk") or 0)
            if injury_days <= 0 and risk < 52:
                continue
            observed = injury_days > 0
            cases.append({
                "player_id": int(row.get("player_id") or 0), "name": row.get("name"),
                "state": "lesionado" if observed else "riesgo",
                "observed": observed,
                "estimate": f"{injury_days} día{'s' if injury_days != 1 else ''}" if observed else f"riesgo {risk}/100",
                "risk": risk, "risk_label": row.get("risk_label"),
                "recommendation": row.get("recommendation"),
                "requires_action": bool(risk >= 70 or (observed and int(row.get("training_load") or 0) >= 45)),
            })
        cases.sort(key=lambda item: (0 if item["requires_action"] else 1, 0 if item["observed"] else 1, -int(item["risk"])))
        snapshot["medical"] = {
            "responsibility": medical,
            "cases": cases[:10],
            "action_required": sum(1 for row in cases if row.get("requires_action")),
            "data_note": "La lesión y la condición actual son observaciones del estado de carrera; días de baja y riesgo son estimaciones que pueden cambiar con evolución, carga o recaída.",
        }
        snapshot["process"] = {
            "need": "Preparar al equipo sin convertir la carga en riesgo evitable.",
            "owner": snapshot.get("responsibility", {}).get("assignee_name") or "Tú (mánager)",
            "status": "Requiere revisión" if snapshot["medical"]["action_required"] else "En curso",
            "next_step": "Revisar recuperación/carga de los casos críticos." if snapshot["medical"]["action_required"] else "Mantener el plan y avanzar hasta la siguiente sesión.",
            "consequence": "Los cambios afectan carga, condición, familiaridad y riesgo físico de las próximas sesiones.",
            "requires_action": bool(snapshot["medical"]["action_required"]),
        }
        return snapshot

    def set_training_plan(self, *, intensity: str | None = None, weekly_plan: list[str] | None = None) -> dict[str, Any]:
        update_training_plan_state(self.state, intensity=intensity, weekly_plan=weekly_plan)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.training_snapshot()

    def set_player_training_focus(self, player_id: int, focus: str) -> dict[str, Any]:
        pid = int(player_id)
        if self._current_team_id(pid) != int(self.state["team_id"]):
            raise ValueError("sólo puedes asignar trabajo individual a futbolistas de tu plantilla")
        set_training_focus_state(self.state, player_id=pid, focus=focus)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.training_snapshot()

    def set_player_recovery_plan(self, player_id: int, recovery: str) -> dict[str, Any]:
        pid = int(player_id)
        if self._current_team_id(pid) != int(self.state["team_id"]):
            raise ValueError("sólo puedes ajustar la recuperación de futbolistas de tu plantilla")
        set_training_recovery_state(self.state, player_id=pid, recovery=recovery)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.training_snapshot()

    def set_match_preparation_focus(self, focus: str) -> dict[str, Any]:
        set_training_match_prep_state(self.state, focus=focus)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.training_snapshot()

    def tactical_plan_snapshot(self) -> dict[str, Any]:
        controlled = int(self.state["team_id"])
        fixture = self.next_scheduled_fixture()
        opponent_id = 0
        if fixture:
            home = int(fixture.get("home_team_id") or 0); away = int(fixture.get("away_team_id") or 0)
            opponent_id = away if home == controlled else home
        return build_tactical_plan_snapshot(
            self.state,
            players=self._career_players_by_team.get(controlled, ()),
            opponent_players=self._career_players_by_team.get(opponent_id, ()) if opponent_id else (),
        )

    def set_tactical_phase_plan(self, *, build_up: str | None = None, final_third: str | None = None, transition: str | None = None) -> dict[str, Any]:
        update_tactical_plan_state(self.state, build_up=build_up, final_third=final_third, transition=transition, game_date=self.current_date)
        plan = ensure_tactical_plan_state(self.state)
        self.state["tactics"].update({"build_up": plan["build_up"], "final_third": plan["final_third"], "transition": plan["transition"]})
        # A phase change made from the bench must affect the very next minute,
        # not only the next fixture. Keep the serialised live tactical state in
        # sync while preserving the match's other tactical fields.
        if self.state.get("live_match"):
            live = self.state["live_match"]
            key = "home_tactics" if str(live.get("home_team_id")) == str(live.get("controlled_team_id")) else "away_tactics"
            current = {**_default_tactics(), **dict(live.get(key) or {}), **{k: self.state["tactics"][k] for k in ("build_up", "final_third", "transition")}}
            live[key] = asdict(FootballTactics9394(**current))
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.tactical_plan_snapshot()

    def set_tactical_individual_instruction(self, player_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        pid = int(player_id)
        if self._current_team_id(pid) != int(self.state["team_id"]):
            raise ValueError("las instrucciones individuales sólo pueden asignarse a tu plantilla")
        set_tactical_player_instruction(self.state, player_id=pid, payload=payload, game_date=self.current_date)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.tactical_plan_snapshot()

    def set_tactical_opposition_instruction(self, player_id: int, *, tight_mark: bool = False, press: bool = False, show_foot: str = "none") -> dict[str, Any]:
        fixture = self.next_scheduled_fixture()
        controlled = int(self.state["team_id"])
        if not fixture:
            raise ValueError("no hay próximo rival para preparar")
        opponent = int(fixture["away_team_id"] if int(fixture["home_team_id"]) == controlled else fixture["home_team_id"])
        if self._current_team_id(int(player_id)) != opponent:
            raise ValueError("el futbolista no pertenece al próximo rival")
        set_tactical_opposition_instruction(self.state, player_id=int(player_id), tight_mark=tight_mark, press=press, show_foot=show_foot)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.tactical_plan_snapshot()

    def set_tactical_set_piece_taker(self, kind: str, player_id: int | None) -> dict[str, Any]:
        if player_id is not None and self._current_team_id(int(player_id)) != int(self.state["team_id"]):
            raise ValueError("el lanzador debe pertenecer a tu plantilla")
        set_tactical_piece_taker(self.state, kind=kind, player_id=player_id)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.tactical_plan_snapshot()

    def squad_plan_snapshot(self) -> dict[str, Any]:
        return build_squad_plan_snapshot(
            players=list(self._career_players_by_team.get(int(self.state["team_id"]), [])),
            development=self.state["player_development"], contract_overrides=self.state.get("contract_overrides", {}),
            current_year=self.current_date.year,
        )

    def match_briefing_snapshot(self) -> dict[str, Any] | None:
        fixture = self.next_scheduled_fixture()
        if not fixture:
            return None
        controlled = int(self.state["team_id"])
        home = int(fixture.get("home_team_id") or 0); away = int(fixture.get("away_team_id") or 0)
        opponent = away if home == controlled else home
        if opponent <= 0:
            return None
        report = self._responsibility_effect("opposition_reports")
        quality = int(report.get("quality") or 10)
        opponent_rows = [p for p in self._career_players_by_team.get(opponent, ()) if not p.get("retired")]
        opponent_tactics = ai_tactics_for_squad(self._match_players_by_team.get(opponent, ()), self._coach_profile(opponent))
        tactics = {"formation": opponent_tactics.formation}
        if quality >= 10: tactics.update({"mentality": opponent_tactics.mentality, "tempo": opponent_tactics.tempo})
        if quality >= 13: tactics.update({"pressing": opponent_tactics.pressing, "directness": opponent_tactics.directness})
        if quality >= 16: tactics.update({"defensive_line": opponent_tactics.defensive_line, "width": opponent_tactics.width, "marking": opponent_tactics.marking})
        def level(p: dict[str, Any]) -> int:
            pid=int(p.get("source_id") or 0)
            return int((self.state.get("player_development",{}).get(str(pid)) or {}).get("overall") or p.get("overall") or p.get("category") or 60)
        threats=[]; radius=2 if quality>=17 else 5 if quality>=13 else 9
        for p in sorted(opponent_rows,key=level,reverse=True)[:3 if quality>=13 else 2]:
            pid=int(p["source_id"]); value=level(p)
            threats.append({"player_id":pid,"name":p.get("display_name"),"position":p.get("position") or p.get("broad_position"),"level_range":[max(35,value-radius),min(99,value+radius)],"identity":player_archetype(p)[0] if quality>=12 else "Amenaza a estudiar"})
        absences=[]
        for p in opponent_rows:
            pid=int(p["source_id"]); days=int((self.state.get("player_development",{}).get(str(pid)) or {}).get("injury_days") or 0)
            if days>0: absences.append({"player_id":pid,"name":p.get("display_name"),"days":days})
        training=self.training_snapshot(); tactical=self.tactical_plan_snapshot()
        own_risk=[p for p in training.get("players") or [] if int(p.get("risk") or 0)>=52]
        prep_focus=str((self.state.get("training") or {}).get("match_preparation_focus") or "balanced")
        recommendation = "Mantener la estructura base y preparar sólo ajustes concretos."
        if prep_focus=="opponent": recommendation="La semana está enfocada al rival: conviene trabajar sus amenazas sin rehacer el plan base."
        elif prep_focus=="attacking": recommendation="La preparación prioriza mecanismos ofensivos y último tercio."
        elif prep_focus=="defensive": recommendation="La preparación prioriza bloque, coberturas y control de pérdidas."
        elif prep_focus=="set_pieces": recommendation="El balón parado es el foco específico de la preparación."
        return {"fixture":dict(fixture),"opponent":{"team_id":opponent,"team_name":self._team_name(opponent),"manager":self._coach_profile(opponent)},"report":report,"known_tactics":tactics,"threats":threats,"absences":absences[:8],"own_absences":self._controlled_absences_for_fixture(fixture)[:8],"own_risk":own_risk[:6],"tactical_familiarity":tactical.get("familiarity"),"preparation_focus":prep_focus,"recommendation":recommendation}

    def staff_reports_snapshot(self) -> dict[str, Any]:
        controlled=int(self.state["team_id"])
        dressing=dressing_room_snapshot(self.state,players=self._career_players_by_team.get(controlled,()),game_date=self.current_date)
        return build_staff_reports(
            game_date=self.current_date, effects=self._responsibility_effect,
            training=self.training_snapshot(), scouting=self.scouting_snapshot(), squad_plan=self.squad_plan_snapshot(),
            dressing_room=dressing, negotiations=list((self.state.get("transfer_negotiations") or {}).values()),
            squad=self.squad(controlled), tactical_plan=self.tactical_plan_snapshot(), next_match=self.next_scheduled_fixture(),
        )

    def competition_directory(self) -> list[dict[str, Any]]:
        return build_competition_directory(self)

    def competition_detail(self, kind: str, source_id: int) -> dict[str, Any]:
        return build_competition_detail(self,kind,source_id)

    def news_snapshot(self, *, category: str = "", limit: int = 80) -> list[dict[str, Any]]:
        rows=list(self.state.get("news_feed") or [])
        if category: rows=[row for row in rows if str(row.get("category") or "")==str(category)]
        rows.sort(key=lambda row:(str(row.get("date") or ""),int(row.get("importance") or 0),str(row.get("id") or "")),reverse=True)
        return rows[:max(1,min(400,int(limit)))]

    def _ingest_news(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        created=[]
        for event in events:
            row=dict(event)
            if row.get("kind")=="competition_completed":
                sid=int(row.get("source_id") or 0)
                preferred_kind=("tournament" if str(sid) in (self.state.get("daily_tournaments") or {}) else "league" if str(sid) in (self.state.get("special_competitions") or {}) else None)
                comp=next((c for c in self.universe.career_competitions() if int(c.get("source_id") or -1)==sid and (preferred_kind is None or c.get("kind")==preferred_kind)),None)
                if comp:
                    row.setdefault("competition_name",comp.get("name"))
                    row.setdefault("competition_kind",comp.get("kind"))
            published=ingest_news_events(self.state,[row],team_name=self._team_name,player_name=self._player_name)
            item=published[0] if published else None
            thread=register_information_event(self.state,row,headline=str((item or {}).get("headline") or ""),detail=str((item or {}).get("detail") or ""),news_id=(item or {}).get("id"))
            if thread and item and row.get("kind") in {"user_transfer","user_sale","ai_transfer","manager_change","competition_completed"}:
                actor="Afición" if row.get("kind") in {"user_transfer","user_sale"} else "Prensa"
                sentiment="positive" if row.get("kind") in {"user_transfer","competition_completed"} else "neutral"
                text="El hecho entra en la conversación pública porque ya ha ocurrido en el mundo de la partida."
                try: add_reaction(self.state,thread_id=thread["id"],actor=actor,sentiment=sentiment,text=text,date_text=str(row.get("date") or self.current_date.isoformat()))
                except KeyError: pass
            created.extend(published)
        return created

    def manager_dashboard(self) -> dict[str, Any]:
        table = self.standings(); team_id = int(self.state["team_id"])
        own = next((r for r in table if int(r["team_id"]) == team_id), None) or {}
        recent = []
        for result in reversed(self.state.get("results") or []):
            if team_id not in (int(result["home_team_id"]), int(result["away_team_id"])): continue
            mine = int(result["home_goals"]) if int(result["home_team_id"]) == team_id else int(result["away_goals"]); theirs = int(result["away_goals"]) if int(result["home_team_id"]) == team_id else int(result["home_goals"])
            recent.append("V" if mine > theirs else "E" if mine == theirs else "D")
            if len(recent) == 5: break
        recent.reverse(); form_points = sum(3 if x == "V" else 1 if x == "E" else 0 for x in recent)
        form_label = "Sin partidos" if not recent else "Excelente" if form_points >= 11 else "Buena" if form_points >= 8 else "Irregular" if form_points >= 5 else "Mala"
        squad = self.squad(team_id); morale = round(sum(int(p.get("morale") or 70) for p in squad) / max(1, len(squad)))
        next_is_league = self._selection_fixture_kind() == "league"
        unavailable = [p for p in squad if int(p.get("injury_days") or 0) > 0 or p.get("status") == "Retirado" or (next_is_league and int(p.get("league_suspension_matches") or 0) > 0)]
        expectation = self.state.get("board_expectation") or self._board_expectation()
        board=self.board_snapshot(persist=False)
        confidence="A la espera" if not recent else board["label"]
        pending = []
        selection = self.selection_snapshot()
        if len(squad) < MINIMUM_SENIOR_SQUAD_SIZE_9394:
            missing=MINIMUM_SENIOR_SQUAD_SIZE_9394-len(squad)
            pending.append({"priority":"high","kind":"squad_depth","title":f"Plantilla incompleta · {len(squad)}/{MINIMUM_SENIOR_SQUAD_SIZE_9394}","detail":f"Faltan {missing} futbolista{'s' if missing!=1 else ''} para alcanzar el mínimo sénior del club.","action":"market"})
        if not selection["valid"]: pending.append({"priority":"high","kind":"lineup","title":"El once necesita atención","detail":" ".join(selection["issues"]),"action":"squad"})
        expiring = [p for p in squad if p.get("contract",{}).get("end_year") and int(p["contract"]["end_year"]) <= self.current_date.year + (1 if self.current_date.month >= 1 else 0)]
        if expiring: pending.append({"priority":"medium","kind":"contracts","title":f"{len(expiring)} contratos próximos a expirar","detail":"Revisa las renovaciones antes de perder jugadores.","action":"squad"})
        if unavailable: pending.append({"priority":"medium","kind":"availability","title":f"{len(unavailable)} futbolistas no disponibles","detail":"Revisa el once y la convocatoria.","action":"squad"})
        risk_rows=[]
        for raw_player in self._career_players_by_team.get(team_id, []):
            dev=(self.state.get("player_development") or {}).get(str(int(raw_player["source_id"])), {})
            if int(dev.get("injury_days") or 0)<=0 and int(dev.get("injury_risk") or 0)>=70:
                risk_rows.append(raw_player)
        if risk_rows: pending.append({"priority":"medium","kind":"training_load","title":f"{len(risk_rows)} futbolista{'s' if len(risk_rows)!=1 else ''} con riesgo físico muy alto","detail":"El área médica recomienda revisar carga e intensidad antes del próximo partido.","action":"training"})
        unhappy=[p for p in squad if bool((p.get("squad_dynamics") or {}).get("wants_move")) or int((p.get("squad_dynamics") or {}).get("satisfaction") or 70)<=38]
        if unhappy: pending.append({"priority":"high" if any((p.get("squad_dynamics") or {}).get("wants_move") for p in unhappy) else "medium","kind":"squad_tension","title":f"{len(unhappy)} futbolista{'s' if len(unhappy)!=1 else ''} descontento{'s' if len(unhappy)!=1 else ''}","detail":"Los minutos y la jerarquía están generando tensión de plantilla.","action":"squad"})
        counters=[row for row in (self.state.get("transfer_negotiations") or {}).values() if row.get("status")=="countered"]
        if counters: pending.append({"priority":"high","kind":"transfer_counters","title":f"{len(counters)} contraoferta{'s' if len(counters)!=1 else ''} pendiente{'s' if len(counters)!=1 else ''}","detail":"El mercado espera tu respuesta.","action":"market"})
        incoming=[row for row in (self.state.get("incoming_transfer_offers") or []) if row.get("status")=="open"]
        if incoming: pending.append({"priority":"high","kind":"incoming_offers","title":f"{len(incoming)} oferta{'s' if len(incoming)!=1 else ''} por tus jugadores","detail":"Acepta o deja expirar las propuestas.","action":"market"})
        if self.state.get("live_match"): pending.insert(0,{"priority":"high","kind":"live_match","title":"Partido en directo pendiente","detail":"Vuelve al banquillo antes de continuar el calendario.","action":"match"})
        if board.get("risk") in {"RIESGO","RIESGO ALTO"}: pending.append({"priority":"high","kind":"board_risk","title":"El puesto está bajo presión","detail":board["reasons"][0]["text"] if board.get("reasons") else "El consejo exige una reacción.","action":"club"})
        career_offers=[row for row in (self.state.get("user_manager") or {}).get("career_offers") or [] if row.get("status")=="open"]
        if career_offers: pending.append({"priority":"medium","kind":"career_offer","title":f"{len(career_offers)} propuesta{'s' if len(career_offers)!=1 else ''} de banquillo","detail":"Hay proyectos profesionales que requieren una decisión.","action":"career"})
        sale_pressure=((self.state.get("board_projects") or {}).get(str(team_id)) or {}).get("sale_pressure") or {}
        if sale_pressure.get("status")=="active": pending.append({"priority":"high","kind":"sale_pressure","title":"El consejo exige generar ingresos","detail":f"Quedan {int(sale_pressure.get('remaining') or 0):,} ptas. por cubrir antes del {sale_pressure.get('deadline')}.","action":"club"})
        pending=self._decorate_dashboard_decisions(pending)
        calendar_context=self.calendar_context_snapshot()
        preseason=self.preseason_snapshot()
        summer=dict(self.state.get("summer_briefing") or {})
        if str(summer.get("season") or "")!=str(self.state.get("season") or "") or not preseason.get("active"):
            summer={}
        blocking=[row for row in pending if row.get("blocking")]
        next_match=self.next_scheduled_fixture()
        continue_status=self._dashboard_continue_status(blocking=blocking,next_match=next_match)
        return {"position": own.get("position"), "team_count": len(table), "points": own.get("points", 0), "recent_form": recent, "form_label": form_label, "morale_average": morale, "unavailable_count": len(unavailable), "unavailable_players":calendar_context.get("availability") or [], "board_expectation": expectation, "board_confidence": confidence, "board":board, "pending_decisions": pending, "blocking_decisions":blocking, "active_processes":self._dashboard_active_processes(squad=squad), "recent_changes":self._dashboard_recent_changes(), "continue_status":continue_status, "next_match": next_match, "calendar_context":calendar_context, "preseason":preseason, "market_period":self.transfer_period_snapshot(), "club_status":self.club_status_snapshot(), "summer_briefing":summer}

    def _decorate_dashboard_decisions(self, pending: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Turn system alerts into user-facing decisions with a clear owner and consequence."""
        recruitment=self._responsibility_effect("recruitment_search")
        negotiation=self._responsibility_effect("transfer_negotiation")
        medical=self._responsibility_effect("medical_assessment")
        owners={
            "squad_depth":negotiation.get("assignee_name") or "Secretaría técnica",
            "lineup":"Tú (mánager)",
            "contracts":negotiation.get("assignee_name") or "Secretaría técnica",
            "availability":medical.get("assignee_name") or "Cuerpo médico",
            "training_load":medical.get("assignee_name") or "Cuerpo médico",
            "squad_tension":"Tú (mánager)",
            "transfer_counters":negotiation.get("assignee_name") or "Secretaría técnica",
            "incoming_offers":negotiation.get("assignee_name") or "Secretaría técnica",
            "live_match":"Tú (mánager)",
            "board_risk":"Consejo directivo",
            "career_offer":"Tú (mánager)",
            "sale_pressure":"Consejo directivo",
        }
        next_steps={
            "squad_depth":"Abre Mercado y cubre la necesidad prioritaria.",
            "lineup":"Completa y guarda los 11 titulares y los 5 suplentes.",
            "contracts":"Revisa quién termina contrato y decide qué renovaciones iniciar.",
            "availability":"Comprueba las bajas y reajusta convocatoria y roles.",
            "training_load":"Reduce carga o activa recuperación en los casos de mayor riesgo.",
            "squad_tension":"Revisa minutos, rol prometido y situación del jugador.",
            "transfer_counters":"Acepta, contraoferta o retírate de la negociación.",
            "incoming_offers":"Acepta o rechaza las ofertas abiertas por tus jugadores.",
            "live_match":"Vuelve al partido y termínalo antes de avanzar el calendario.",
            "board_risk":"Revisa las causas de la presión y el objetivo del consejo.",
            "career_offer":"Decide si continúas en el club o escuchas el nuevo proyecto.",
            "sale_pressure":"Planifica ventas suficientes antes de la fecha límite.",
        }
        consequences={
            "squad_depth":"Una plantilla corta reduce margen ante lesiones, sanciones y calendario.",
            "lineup":"No podrás disputar el siguiente partido con una convocatoria inválida.",
            "contracts":"Esperar demasiado aumenta el riesgo de salida o encarece la renovación.",
            "availability":"Una baja mal gestionada puede dejar el XI inválido el día de partido.",
            "training_load":"Mantener la carga eleva la probabilidad de lesión y fatiga.",
            "squad_tension":"El malestar puede deteriorar moral, relaciones y voluntad de continuar.",
            "transfer_counters":"La otra parte espera respuesta y la operación puede enfriarse.",
            "incoming_offers":"La oferta puede desaparecer y afecta a la planificación de plantilla.",
            "live_match":"El mundo no puede avanzar mientras tu partido sigue abierto.",
            "board_risk":"La continuidad del mánager depende de recuperar confianza.",
            "career_offer":"La oportunidad profesional no permanecerá abierta indefinidamente.",
            "sale_pressure":"Incumplir la exigencia puede empeorar apoyo, presupuesto y confianza.",
        }
        # These are true interruptions: advancing time before answering them would
        # hide a user decision or make the flow harder to understand.
        blocking_kinds={"transfer_counters","incoming_offers","live_match"}
        decorated=[]
        for index,row in enumerate(pending):
            item=dict(row);kind=str(item.get("kind") or "")
            priority=str(item.get("priority") or "medium")
            item.update({
                "owner":owners.get(kind,"Tú (mánager)"),
                "status":"Necesita tu decisión" if priority=="high" else "Revisar",
                "next_step":next_steps.get(kind,"Abre el área indicada y revisa el contexto."),
                "consequence":consequences.get(kind,"Resolverlo evita que el problema se propague a otros sistemas."),
                "requires_action":priority=="high",
                "blocking":kind in blocking_kinds,
                "order":index,
            })
            decorated.append(item)
        rank={"high":0,"medium":1,"low":2}
        decorated.sort(key=lambda row:(rank.get(str(row.get("priority")),3),0 if row.get("blocking") else 1,int(row.get("order") or 0)))
        return decorated

    def _dashboard_active_processes(self, *, squad: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Cross-system processes that continue without pretending the user must act."""
        rows=[]
        recruitment=self._responsibility_effect("recruitment_search")
        negotiation=self._responsibility_effect("transfer_negotiation")
        medical=self._responsibility_effect("medical_assessment")
        scouting=self.scouting_snapshot()
        for task in (scouting.get("active") or [])[:3]:
            rows.append({
                "id":f"scout:{task.get('id')}","area":"Scouting","title":f"Informe sobre {task.get('player_name') or 'objetivo'}",
                "owner":task.get("responsible") or recruitment.get("assignee_name") or "Scouting","status":"En curso",
                "next_step":f"Informe previsto para {task.get('due_on') or 'los próximos días'}.",
                "consequence":"Cuando termine, mejorará la confianza del dossier y la comparación de mercado.","action":"market","requires_action":False,
            })
        negotiations=list((self.state.get("transfer_negotiations") or {}).values())
        for deal in [row for row in negotiations if row.get("status")=="waiting"][:3]:
            player_id=int(deal.get("player_id") or 0)
            rows.append({
                "id":f"deal:{deal.get('id') or player_id}","area":"Mercado","title":f"Negociación por {self._player_name(player_id)}",
                "owner":negotiation.get("assignee_name") or "Secretaría técnica","status":"Esperando respuesta",
                "next_step":f"La otra parte responderá a partir de {deal.get('next_response_date') or deal.get('response_due') or 'los próximos días'}.",
                "consequence":"No requiere clics ahora; Continuar puede llevarte hasta su respuesta.","action":"market","requires_action":False,
            })
        injured=[]
        for player in (squad if squad is not None else self.squad(int(self.state["team_id"]))):
            days=int(player.get("injury_days") or 0)
            if days>0: injured.append((days,player))
        for days,player in sorted(injured,key=lambda item:item[0])[:2]:
            rows.append({
                "id":f"medical:{player.get('id')}","area":"Área médica","title":f"Recuperación de {player.get('display_name') or player.get('name')}",
                "owner":medical.get("assignee_name") or "Cuerpo médico","status":"En recuperación","next_step":f"Estimación actual: {days} día{'s' if days!=1 else ''} de baja.",
                "consequence":"El estado se actualizará al avanzar; la carga y una recaída pueden cambiar el plazo.","action":"training","requires_action":False,
            })
        return rows[:6]

    def _dashboard_recent_changes(self) -> list[dict[str, Any]]:
        """Small, personalised 'what changed' feed for the daily home screen."""
        allowed={
            "scouting_report_ready","training_injury","injury","important_injury","important_return","suspension","manager_note",
            "incoming_transfer_offer","transfer_counteroffer","user_transfer","user_sale","user_renewal","contract_agreed","contract_closed",
            "board_risk","board_sale_pressure","board_sale_pressure_resolved","career_offer","job_offer","season_rollover","competition_completed",
            "controlled_match_pending","player_concern","player_concern_resolved","role_promise_resolved","role_promise_interrupted","staff_responsibility_handoff",
        }
        action_by_kind={
            "scouting_report_ready":"market","incoming_transfer_offer":"market","transfer_counteroffer":"market","user_transfer":"market","user_sale":"market",
            "user_renewal":"squad","contract_agreed":"squad","contract_closed":"squad","training_injury":"training","injury":"training","important_injury":"training","important_return":"squad","suspension":"squad",
            "board_risk":"club","board_sale_pressure":"club","board_sale_pressure_resolved":"club","career_offer":"career","job_offer":"career","season_rollover":"home","competition_completed":"champions",
            "controlled_match_pending":"match","player_concern":"squad","player_concern_resolved":"squad","role_promise_resolved":"squad","role_promise_interrupted":"squad","staff_responsibility_handoff":"staff","manager_note":"home",
        }
        labels={
            "scouting_report_ready":"Scouting","training_injury":"Área médica","injury":"Área médica","important_injury":"Área médica","important_return":"Plantilla","suspension":"Disciplina",
            "incoming_transfer_offer":"Mercado","transfer_counteroffer":"Mercado","user_transfer":"Mercado","user_sale":"Mercado","user_renewal":"Contratos","contract_agreed":"Contratos","contract_closed":"Contratos",
            "board_risk":"Consejo","board_sale_pressure":"Consejo","board_sale_pressure_resolved":"Consejo","career_offer":"Carrera","job_offer":"Carrera","season_rollover":"Temporada","competition_completed":"Palmarés",
            "controlled_match_pending":"Partido","player_concern":"Vestuario","player_concern_resolved":"Vestuario","role_promise_resolved":"Vestuario","role_promise_interrupted":"Vestuario","staff_responsibility_handoff":"Staff","manager_note":"Staff",
        }
        def text(event: dict[str, Any]) -> tuple[str,str]:
            kind=str(event.get("kind") or "")
            player=str(event.get("player_name") or (self._player_name(int(event.get("player_id") or 0)) if event.get("player_id") else ""))
            if kind=="scouting_report_ready": return f"Informe listo: {player or 'objetivo'}",f"{event.get('responsible') or 'Scouting'} completó el seguimiento con {int(event.get('confidence') or 0)}% de confianza."
            if kind in {"training_injury","injury","important_injury"}: return f"Baja médica: {player or 'jugador'}",str(event.get("detail") or event.get("injury") or "La disponibilidad de la plantilla ha cambiado.")
            if kind=="important_return": return f"Vuelve {player or 'un jugador'}",str(event.get("detail") or "El jugador vuelve a estar disponible para competir.")
            if kind=="suspension": return f"Sanción: {player or 'jugador'}",str(event.get("detail") or event.get("reason") or "La próxima convocatoria queda afectada.")
            if kind=="incoming_transfer_offer": return f"Oferta por {player or 'tu jugador'}",str(event.get("detail") or "Ha llegado una propuesta que requiere revisión.")
            if kind=="transfer_counteroffer": return f"Contraoferta por {player or 'objetivo'}",str(event.get("detail") or "La negociación espera tu respuesta.")
            if kind=="user_transfer": return f"Fichaje cerrado: {player or 'nuevo jugador'}",str(event.get("detail") or "La operación ya forma parte de tu plantilla.")
            if kind=="user_sale": return f"Salida cerrada: {player or 'jugador'}",str(event.get("detail") or "La plantilla y la economía ya reflejan la venta.")
            if kind in {"user_renewal","contract_agreed","contract_closed"}: return f"Contrato actualizado: {player or 'jugador'}",str(event.get("detail") or "La situación contractual ha cambiado.")
            if kind in {"board_risk","board_sale_pressure","board_sale_pressure_resolved"}: return str(event.get("title") or "El consejo actualiza su posición"),str(event.get("detail") or event.get("reason") or "Hay un cambio en la relación con la directiva.")
            if kind in {"career_offer","job_offer"}: return "Nueva opción de banquillo",str(event.get("detail") or "Tu carrera profesional tiene una nueva decisión disponible.")
            if kind=="season_rollover": return "Comienza una nueva temporada",str(event.get("detail") or "La carrera ha completado la transición de verano.")
            if kind=="competition_completed": return str(event.get("competition_name") or "Competición terminada"),str(event.get("detail") or "El palmarés de la temporada se ha actualizado.")
            if kind=="controlled_match_pending": return "Día de partido",str(event.get("detail") or "Tu equipo tiene un encuentro pendiente de disputar.")
            if kind=="staff_responsibility_handoff": return "Cambio de responsable",f"{event.get('from_name') or 'Responsable anterior'} → {event.get('to_name') or 'nuevo responsable'} · {int(event.get('affected_count') or 0)} proceso(s) activo(s) reasignados."
            if kind in {"player_concern","player_concern_resolved","role_promise_resolved","role_promise_interrupted"}: return str(event.get("title") or (f"Situación de {player}" if player else "Vestuario actualizado")),str(event.get("detail") or "Ha cambiado una relación o compromiso de vestuario.")
            return str(event.get("title") or "Actualización del staff"),str(event.get("detail") or "El estado de la carrera ha cambiado.")
        output=[]
        seen=set()
        for event in reversed(list(self.state.get("world_events") or [])[-160:]):
            kind=str(event.get("kind") or "")
            if kind not in allowed: continue
            title,detail=text(event);marker=(kind,title,str(event.get("date") or ""))
            if marker in seen: continue
            seen.add(marker)
            output.append({"id":str(event.get("id") or f"{kind}:{len(output)}"),"date":str(event.get("date") or self.current_date.isoformat()),"area":labels.get(kind,"Carrera"),"title":title,"detail":detail,"action":action_by_kind.get(kind,"home")})
            if len(output)>=5: break
        return output

    def _dashboard_continue_status(self, *, blocking: list[dict[str, Any]], next_match: dict[str, Any] | None) -> dict[str, Any]:
        if self.state.get("live_match"):
            return {"state":"blocked","can_advance":False,"label":"Volver al partido","detail":"El partido abierto debe resolverse antes de mover el calendario.","action":"match"}
        if blocking:
            first=blocking[0]
            return {"state":"blocked","can_advance":False,"label":"Resolver primero","detail":str(first.get("title") or "Hay una decisión pendiente."),"action":first.get("action") or "home"}
        if next_match and str(next_match.get("date") or "")==self.current_date.isoformat():
            return {"state":"matchday","can_advance":True,"label":"Ir al partido","detail":f"Hoy: {next_match.get('home_team')} - {next_match.get('away_team')}","action":"match"}
        detail=f"Próximo partido: {next_match.get('date')}" if next_match else "Avanza hasta el siguiente acontecimiento relevante."
        return {"state":"ready","can_advance":True,"label":"Continuar","detail":detail,"action":"home"}

    def _coach_profile(self, team_id: int) -> dict[str, Any] | None:
        manager_id = (self.state.get("manager_assignments") or {}).get(str(int(team_id)))
        return source_coach_for_team(
            self.universe, int(team_id),
            manager_id=(int(manager_id) if manager_id is not None else None),
        )

    def _manager_name(self, manager_id: int | None) -> str:
        if not isinstance(manager_id, int):
            return "Sin entrenador"
        row = default_source_catalog().manager(manager_id) or {}
        return str(row.get("display_name") or f"Entrenador {manager_id}")

    def _recent_points_for_team(self, team_id: int, league_id: int, *, limit: int = 5) -> int:
        rows = [r for r in self._league_result_rows(int(league_id)) if int(team_id) in (int(r.get("home_team_id") or 0), int(r.get("away_team_id") or 0))]
        rules = self._league_rules(int(league_id))
        points = 0
        for row in rows[-max(1, int(limit)):]:
            home = int(row.get("home_team_id") or 0) == int(team_id)
            mine = int(row.get("home_goals") or 0) if home else int(row.get("away_goals") or 0)
            theirs = int(row.get("away_goals") or 0) if home else int(row.get("home_goals") or 0)
            points += int(rules.points_win) if mine > theirs else int(rules.points_draw) if mine == theirs else int(rules.points_loss)
        return points

    def _expected_position_for_team(self, team_id: int, league_id: int) -> int:
        teams = list(self._teams_for_league(int(league_id)))
        ranked = sorted(teams, key=lambda team: -(self._team_strength(int(team["source_id"])) * .72 + float(club_status(self.state, int(team["source_id"])).get("score") or 50) * .28))
        return next((index + 1 for index, team in enumerate(ranked) if int(team["source_id"]) == int(team_id)), max(1, len(ranked)))

    def _process_manager_market(self, day: date) -> list[dict[str, Any]]:
        if day.day != 1 or day.month in (7, 8):
            return []
        events: list[dict[str, Any]] = []
        controlled = int(self.state["team_id"])
        for league_id in self._simple_world_league_ids():
            table = self.league_standings(int(league_id))
            if not table:
                continue
            by_team = {int(row["team_id"]): row for row in table}
            for team in self._teams_for_league(int(league_id)):
                tid = int(team["source_id"])
                if tid == controlled or tid not in by_team:
                    continue
                row = by_team[tid]
                played = int(row.get("played") or 0)
                if played < 8:
                    continue
                expected = self._expected_position_for_team(tid, int(league_id))
                recent_points = self._recent_points_for_team(tid, int(league_id))
                pressure = pressure_score(position=int(row.get("position") or len(table)), expected_position=expected, team_count=len(table), played=played, recent_points=recent_points)
                self.state.setdefault("manager_pressure", {})[str(tid)] = {"score": pressure, "date": day.isoformat(), "position": int(row.get("position") or 0), "expected_position": expected, "recent_points": recent_points}
                if pressure < 74:
                    continue
                last_change = (self.state.get("manager_last_change") or {}).get(str(tid))
                if last_change and (day - date.fromisoformat(str(last_change))).days < 90:
                    continue
                rng = Random(int(self.state["seed"]) ^ day.toordinal() ^ tid * 193)
                if pressure < 90 and rng.random() > min(.72, (pressure - 65) / 40):
                    continue
                old_id = (self.state.get("manager_assignments") or {}).get(str(tid))
                replacement = choose_replacement(
                    self.state, when=day, team_id=tid, squad=self._career_players_by_team.get(tid, []),
                    club_score=float(club_status(self.state, tid).get("score") or 50), seed=int(self.state["seed"]),
                )
                if not replacement:
                    continue
                event = register_manager_change(
                    self.state, when=day, team_id=tid, old_manager_id=(int(old_id) if isinstance(old_id, int) else None),
                    new_manager_id=int(replacement["source_id"]), reason="resultados_por_debajo_de_expectativa", pressure=pressure,
                )
                event.update({
                    "team_name": self._team_name(tid), "from_manager_name": self._manager_name(int(old_id)) if isinstance(old_id, int) else "Sin entrenador",
                    "to_manager_name": str(replacement.get("display_name") or self._manager_name(int(replacement["source_id"]))),
                    "expected_position": expected, "position": int(row.get("position") or 0),
                })
                events.append(event)
                if len(events) >= 6:
                    return events
        return events

    def _refresh_job_market(self, *, day: date, proactive: bool = True) -> list[dict[str, Any]]:
        ensure_professional_state(self.state, team=self._team_api(int(self.state["team_id"])))
        expire_job_market(self.state, day=day)
        profile=self.state["user_manager"]; current_team=int(self.state["team_id"]); current_league=int(self.state["league_id"])
        unemployed=self.state.get("job_status")!="active"
        opportunities=[]
        for league_id in self._simple_world_league_ids():
            league=self.universe.leagues_by_id.get(int(league_id)) or {}
            country=str(league.get("country") or "")
            league_name=str(league.get("name") or f"Liga {league_id}")
            table={int(row["team_id"]):row for row in self.league_standings(int(league_id))}
            for team in self._teams_for_league(int(league_id)):
                tid=int(team["source_id"])
                if tid==current_team: continue
                score=float(club_status(self.state,tid).get("score") or 50.0)
                expected=self._expected_position_for_team(tid,int(league_id))
                row=table.get(tid) or {}; position=int(row.get("position") or expected)
                pressure=int(((self.state.get("manager_pressure") or {}).get(str(tid)) or {}).get("score") or 0)
                # A club can be approached when its bench is genuinely under
                # review. An unemployed manager also sees realistic lower-risk
                # openings so a dismissal never becomes a dead end.
                if not unemployed and pressure < 55: continue
                suitability=job_suitability(profile=profile,team_id=tid,country=country,club_score=score,pressure=pressure,position=position,expected_position=expected,currently_employed=not unemployed)
                if suitability < (38 if unemployed else 52): continue
                opportunities.append({
                    "id":f"job-market:{day.isoformat()}:{tid}","date":day.isoformat(),"expires_on":(day+timedelta(days=21)).isoformat(),
                    "team_id":tid,"team_name":self._team_name(tid),"league_id":int(league_id),"league_name":league_name,"country":country,
                    "club_score":round(score,1),"position":position,"expected_position":expected,"manager_pressure":pressure,
                    "suitability":round(suitability,1),"status":"open","kind":"vacancy" if pressure>=72 else "bench_under_review",
                    "project_preview":{"objective":self._objective_title(expected,len(self._teams_for_league(int(league_id)))),"inherit_live_world":True},
                })
        opportunities.sort(key=lambda row:(-float(row["suitability"]),-int(row["manager_pressure"]),int(row["team_id"])))
        profile["available_jobs"]=opportunities[:16]
        profile["last_job_search_on"]=day.isoformat()
        if proactive and not unemployed and day.day==1:
            open_ids={int(row.get("team_id") or 0) for row in profile.get("career_offers") or [] if row.get("status")=="open"}
            for opportunity in opportunities:
                if len([row for row in profile.get("career_offers") or [] if row.get("status")=="open"])>=2: break
                if int(opportunity["team_id"]) in open_ids or float(opportunity["suitability"])<76 or int(opportunity["manager_pressure"])<64: continue
                offer={**opportunity,"id":f"career-offer:{day.isoformat()}:{opportunity['team_id']}","kind":"direct_offer","reason":"El club valora tu trabajo actual y su banquillo está en revisión."}
                profile.setdefault("career_offers",[]).append(offer); open_ids.add(int(opportunity["team_id"]))
                event={"kind":"manager_interest","date":day.isoformat(),"team_id":int(opportunity["team_id"]),"team_name":opportunity["team_name"]}
                register_information_event(self.state,event,headline=f"{opportunity['team_name']} sigue tu situación",detail="El interés nace del rendimiento del club y de tu reputación, no de una noticia aleatoria.")
                publish_news(self.state,key=f"manager-interest:{day.isoformat()}:{opportunity['team_id']}",date=day.isoformat(),category="Tu carrera",importance=3,headline=f"{opportunity['team_name']} muestra interés",detail="Tu trabajo ha entrado en el mercado de banquillos. Puedes escuchar el proyecto sin abandonar tu club actual.",entity={"team_id":opportunity["team_id"]})
            profile["career_offers"]=profile.get("career_offers",[])[-40:]
        return [dict(row) for row in profile.get("available_jobs") or []]

    @staticmethod
    def _objective_title(expected: int, count: int) -> str:
        if expected<=2: return "Pelear por el título"
        if expected<=max(5,round(count*.30)): return "Zona alta"
        if expected>=max(12,round(count*.72)): return "Permanencia"
        return "Temporada competitiva"

    def _generate_user_job_offers(self, *, day: date) -> list[dict[str, Any]]:
        # Compatibility path for a dismissal: keep an immediate same-league
        # shortlist while NF9 also exposes the broader professional market.
        self._refresh_job_market(day=day,proactive=False)
        league_id=int(self.state["league_id"]); rows=[row for row in self.state["user_manager"].get("available_jobs") or [] if int(row.get("league_id") or 0)==league_id]
        if not rows:
            profile=self.state["user_manager"]; reputation=float(profile.get("reputation") or 50.0); table={int(row["team_id"]):row for row in self.standings()}
            fallback=[]
            league=self.universe.leagues_by_id.get(league_id) or {}; country=str(league.get("country") or ""); league_name=str(league.get("name") or f"Liga {league_id}")
            for team in self._teams_for_league(league_id):
                tid=int(team["source_id"]);
                if tid==int(self.state["team_id"]): continue
                score=float(club_status(self.state,tid).get("score") or 50); expected=self._expected_position_for_team(tid,league_id); position=int((table.get(tid) or {}).get("position") or expected)
                suitability=100-abs(score-reputation)*1.45
                fallback.append({"id":f"job:{day.isoformat()}:{tid}","date":day.isoformat(),"expires_on":(day+timedelta(days=21)).isoformat(),"team_id":tid,"team_name":self._team_name(tid),"league_id":league_id,"league_name":league_name,"country":country,"club_score":round(score,1),"position":position,"expected_position":expected,"manager_pressure":0,"suitability":round(suitability,1),"status":"open","reason":"proyecto_disponible_tras_destitucion"})
            fallback.sort(key=lambda row:(-row["suitability"],row["team_id"])); rows=fallback
        offers=[]
        for row in rows[:3]:
            offer={**row,"id":f"job:{day.isoformat()}:{int(row['team_id'])}","reason":"proyecto_disponible_tras_destitucion","status":"open"}
            offers.append(offer)
        set_job_offers(self.state,offers)
        return offers

    def apply_for_job(self, opportunity_id: str) -> dict[str, Any]:
        self._refresh_job_market(day=self.current_date,proactive=False)
        profile=self.state["user_manager"]
        opportunity=next((row for row in profile.get("available_jobs") or [] if str(row.get("id"))==str(opportunity_id) and row.get("status")=="open"),None)
        if opportunity is None: raise KeyError("vacante no encontrada o ya cerrada")
        result=application_interview(state=self.state,opportunity=opportunity,day=self.current_date)
        event={"kind":"manager_application","date":self.current_date.isoformat(),"team_id":int(opportunity["team_id"]),"application_id":result["application"]["id"]}
        thread=register_information_event(self.state,event,headline=f"Candidatura a {opportunity['team_name']}",detail="La candidatura y la entrevista nacen de una vacante real del mercado de banquillos.")
        if result["passed"]:
            offer={**opportunity,"id":f"application-offer:{result['application']['id']}","status":"open","kind":"application_offer","application_id":result["application"]["id"],"reason":"entrevista_superada"}
            profile.setdefault("career_offers",[]).append(offer); profile["career_offers"]=profile["career_offers"][-40:]
            if thread: add_reaction(self.state,thread_id=thread["id"],actor="Consejo",sentiment="positive",text="El consejo considera que tu perfil encaja y formaliza una oferta.",date_text=self.current_date.isoformat(),consequence={"kind":"job_offer","team_id":int(opportunity["team_id"])})
            publish_news(self.state,key=f"application-offer:{result['application']['id']}",date=self.current_date.isoformat(),category="Tu carrera",importance=4,headline=f"{opportunity['team_name']} te ofrece el banquillo",detail="La propuesta llega después de tu candidatura y entrevista. Puedes aceptarla o continuar con tu situación actual.",entity={"team_id":opportunity["team_id"]})
        else:
            if thread: add_reaction(self.state,thread_id=thread["id"],actor="Consejo",sentiment="negative",text="El club considera que el encaje del proyecto todavía no es suficiente.",date_text=self.current_date.isoformat(),consequence={"kind":"application_rejected","team_id":int(opportunity["team_id"])})
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {**result,"professional_career":self._professional_career_view()}

    def resign_club_job(self) -> dict[str, Any]:
        if self.state.get("job_status")!="active": raise ValueError("ya estás sin club")
        controlled=int(self.state["team_id"]); today=self.current_date
        close_role_promises_on_manager_exit(self.state,date_text=today.isoformat(),voluntary=True)
        close_current_tenure(self.state,date_text=today.isoformat(),team_name=self._team_name(controlled),reason="resigned",record_snapshot=records_snapshot(self.state))
        close_contract(self.state,date_text=today.isoformat(),reason="resigned")
        adjust_club_relationship(self.state,team_id=controlled,trust_delta=-14,respect_delta=-5,date_text=today.isoformat(),reason="dimisión con contrato vigente")
        replacement=choose_replacement(self.state,when=today,team_id=controlled,squad=self._career_players_by_team.get(controlled,[]),club_score=float(club_status(self.state,controlled).get("score") or 50),seed=int(self.state["seed"])^1771)
        events=[]
        if replacement:
            event=register_manager_change(self.state,when=today,team_id=controlled,old_manager_id=None,new_manager_id=int(replacement["source_id"]),reason="dimision_manager_usuario",pressure=0)
            event.update({"team_name":self._team_name(controlled),"from_manager_name":"Tú","to_manager_name":str(replacement.get("display_name") or self._manager_name(int(replacement["source_id"])))})
            events.append(event)
        self.state["job_status"]="dismissed"; self.state["user_dismissal_handled"]=f"resigned:{controlled}:{today.isoformat()}"
        offers=self._generate_user_job_offers(day=today)
        if events:
            self.state.setdefault("world_events",[]).extend(events); self.state["world_events"]=self.state["world_events"][-600:]; self._ingest_news(events)
        publish_news(self.state,key=f"manager-resign:{today.isoformat()}:{controlled}",date=today.isoformat(),category="Tu carrera",importance=5,headline=f"Dimites de {self._team_name(controlled)}",detail="Cierras voluntariamente la etapa. Tu reputación, relaciones e historial permanecen en el mundo.",entity={"team_id":controlled})
        register_manager_milestone(self.state,date_text=today.isoformat(),season=str(self.state["season"]),kind="resignation",team_id=controlled,team_name=self._team_name(controlled),summary=f"Cierras voluntariamente tu etapa en {self._team_name(controlled)}; el capítulo queda archivado con su fecha y motivo.")
        return {"offers":offers,"career":self.snapshot()}

    def _handle_user_dismissal(self) -> list[dict[str, Any]]:
        controlled=int(self.state["team_id"]); today=self.current_date
        stamp=f"{controlled}:{today.isoformat()}"
        if self.state.get("user_dismissal_handled")==stamp:
            return []
        close_role_promises_on_manager_exit(self.state,date_text=today.isoformat(),voluntary=False)
        close_current_tenure(self.state,date_text=today.isoformat(),team_name=self._team_name(controlled),reason="dismissed",record_snapshot=records_snapshot(self.state))
        close_contract(self.state,date_text=today.isoformat(),reason="dismissed")
        adjust_club_relationship(self.state,team_id=controlled,trust_delta=-8,respect_delta=-3,date_text=today.isoformat(),reason="destitución")
        events=[]
        replacement=choose_replacement(
            self.state,when=today,team_id=controlled,squad=self._career_players_by_team.get(controlled,[]),
            club_score=float(club_status(self.state,controlled).get("score") or 50),seed=int(self.state["seed"])^911,
        )
        if replacement:
            event=register_manager_change(self.state,when=today,team_id=controlled,old_manager_id=None,new_manager_id=int(replacement["source_id"]),reason="sustituye_al_manager_destituido",pressure=100)
            event.update({"team_name":self._team_name(controlled),"from_manager_name":"Tu etapa","to_manager_name":str(replacement.get("display_name") or self._manager_name(int(replacement["source_id"])))})
            events.append(event)
        offers=self._generate_user_job_offers(day=today)
        publish_news(
            self.state,key=f"manager-career-market:{stamp}",date=today.isoformat(),category="Tu carrera",importance=5,
            headline="Tu carrera continúa",detail=(f"{len(offers)} clubes de la liga han mostrado interés. Elige un nuevo proyecto para seguir." if offers else "Tu etapa ha terminado, pero tu historial como mánager permanece."),
            entity={"team_id":controlled},
        )
        if events:
            self.state.setdefault("world_events",[]).extend(events);self.state["world_events"]=self.state["world_events"][-600:];self._ingest_news(events)
        register_manager_milestone(self.state,date_text=today.isoformat(),season=str(self.state["season"]),kind="dismissal",team_id=controlled,team_name=self._team_name(controlled),summary=f"El consejo pone fin a tu etapa en {self._team_name(controlled)}. La destitución queda ligada a este proyecto y no borra la carrera previa.")
        self.state["user_dismissal_handled"]=stamp
        return events

    def _switch_controlled_league(self, new_league: int) -> None:
        old_league=int(self.state["league_id"]); new_league=int(new_league)
        if new_league==old_league: return
        world=self.state.setdefault("world_leagues",{})
        # The old controlled competition becomes a normal background league at
        # exactly its current point. The target background league becomes the
        # controlled one without replaying or deleting a single result.
        old_results=[]
        for row in self.state.get("results") or []:
            old_results.append({**row,"round":int(row.get("round") or row.get("matchday") or 0)})
        world[str(old_league)]={"completed_round":int(self.state.get("completed_matchday") or 0),"results":old_results,"simulation_model":"controlled_to_background_v1"}
        target=world.pop(str(new_league),{"completed_round":0,"results":[]})
        converted=[]
        for row in target.get("results") or []:
            round_number=int(row.get("matchday") or row.get("round") or 0)
            converted.append({**row,"matchday":round_number,"round":round_number})
        self.state["results"]=converted
        self.state["completed_matchday"]=int(target.get("completed_round") or max((int(r.get("matchday") or 0) for r in converted),default=0))
        self.state["league_id"]=new_league
        self._schedule_cache.clear(); self._team_league_cache.clear(); self._foreign_rule_cache.clear()
        self._ensure_world_leagues()
        profile = SPAIN_PRIMERA_SIMULATION_1993_94 if new_league == 1 else ERA_BASELINE_1993_94
        self.engine=FootballMatchEngine9394(profile=profile); self.live_engine=LiveMatchEngine9394(self.engine)

    def accept_job_offer(self, offer_id: str) -> dict[str, Any]:
        ensure_professional_state(self.state,team=self._team_api(int(self.state["team_id"])))
        profile=self.state["user_manager"]
        target=next((row for row in profile.get("career_offers") or [] if str(row.get("id"))==str(offer_id) and row.get("status")=="open"),None)
        legacy=False
        if target is None:
            target=next((row for row in profile.get("job_offers") or [] if str(row.get("id"))==str(offer_id) and row.get("status")=="open"),None); legacy=True
        if target is None: raise KeyError("oferta de trabajo no encontrada o ya cerrada")
        if self.state.get("job_status")=="active" and int(target.get("team_id") or 0)==int(self.state["team_id"]): raise ValueError("ya diriges ese club")
        old_team=int(self.state["team_id"]); new_team=int(target["team_id"]); new_league=int(target["league_id"]); today=self.current_date
        was_active=self.state.get("job_status")=="active"
        if was_active:
            close_role_promises_on_manager_exit(self.state,date_text=today.isoformat(),voluntary=True)
            close_current_tenure(self.state,date_text=today.isoformat(),team_name=self._team_name(old_team),reason="left_for_job",record_snapshot=records_snapshot(self.state))
            close_contract(self.state,date_text=today.isoformat(),reason="accepted_other_job")
            adjust_club_relationship(self.state,team_id=old_team,trust_delta=-6,respect_delta=1,date_text=today.isoformat(),reason="salida para aceptar otro proyecto")
            replacement=choose_replacement(self.state,when=today,team_id=old_team,squad=self._career_players_by_team.get(old_team,[]),club_score=float(club_status(self.state,old_team).get("score") or 50),seed=int(self.state["seed"])^new_team^733)
            if replacement:
                event=register_manager_change(self.state,when=today,team_id=old_team,old_manager_id=None,new_manager_id=int(replacement["source_id"]),reason="manager_usuario_acepta_otro_club",pressure=0)
                event.update({"team_name":self._team_name(old_team),"from_manager_name":"Tú","to_manager_name":str(replacement.get("display_name") or self._manager_name(int(replacement["source_id"])))})
                self.state.setdefault("world_events",[]).append(event); self._ingest_news([event])
        else:
            if legacy:
                for row in profile.get("job_offers") or []: row["status"]="accepted" if row is target else "declined"
            else:
                for row in profile.get("job_offers") or []:
                    if row.get("status")=="open": row["status"]="declined"
        for row in profile.get("career_offers") or []:
            if row.get("status")=="open": row["status"]="accepted" if row is target else "declined"
        predecessor=(self.state.get("manager_assignments") or {}).get(str(new_team))
        if not isinstance(predecessor,int): predecessor=(self.universe.team(new_team) or {}).get("manager_id")
        self.state["controlled_predecessor_manager_id"]=predecessor if isinstance(predecessor,int) else None
        for negotiation in (self.state.get("transfer_negotiations") or {}).values():
            if negotiation.get("status") in {"waiting","countered"} and int(negotiation.get("buyer_team_id") or 0)==old_team:
                negotiation["status"]="cancelled"; negotiation["reason"]="cambio_de_club_del_manager"
        self.state["transfer_listings"]={}
        for incoming in self.state.get("incoming_transfer_offers") or []:
            if incoming.get("status")=="open": incoming["status"]="withdrawn"; incoming["reason"]="cambio_de_club_del_manager"
        if isinstance(predecessor,int) and predecessor>1:
            unemployed={int(x) for x in self.state.get("manager_unemployed") or [] if str(x).lstrip('-').isdigit()}; unemployed.add(predecessor); self.state["manager_unemployed"]=sorted(unemployed)
        self.state.setdefault("manager_assignments",{})[str(new_team)]=-1
        manager_event={"kind":"manager_change","date":today.isoformat(),"team_id":new_team,"team_name":self._team_name(new_team),"from_manager_id":predecessor if isinstance(predecessor,int) else None,"to_manager_id":-1,"from_manager_name":self._manager_name(predecessor) if isinstance(predecessor,int) else "Anterior entrenador","to_manager_name":"Tú","reason":"contratacion_manager_usuario","pressure":0,"provenance":"user_manager_career"}
        self.state.setdefault("manager_history",[]).append(manager_event); self.state["manager_history"]=self.state["manager_history"][-300:]
        self.state.setdefault("world_events",[]).append(manager_event); self.state["world_events"]=self.state["world_events"][-600:]
        self._switch_controlled_league(new_league)
        self.state["team_id"]=new_team
        self.state["finances"]=self.state["club_finances"].setdefault(str(new_team),initial_club_finances(self.universe.team(new_team) or {},players=list(self.universe.players_by_team.get(new_team,()))))
        self.state["job_status"]="active"; self.state["board_warning_count"]=0; self.state["board_state"]={}; self.state["board_history"]=[]
        self.state["board_expectation"]={}; self.state["economy_ledger"]=[]; self.state["selection"]={}
        self.state["live_match"]=None; self.state["last_match_report"]=None; self.state["pending_world_match"]=None
        self._team_league_cache.clear(); self._foreign_rule_cache.clear(); self._rebuild_rosters()
        new_team_api=self._team_api(new_team) or self.universe.team(new_team) or {"source_id":new_team}
        ensure_club_staff_state(self.state,team=new_team_api,strength=self._team_strength(new_team),game_date=self.current_date)
        self.state["selection"]=self._safe_auto_selection(); self.state["board_expectation"]=self._board_expectation()
        open_new_tenure(self.state,date_text=today.isoformat(),team_id=new_team,team_name=self._team_name(new_team))
        adjust_club_relationship(self.state,team_id=new_team,trust_delta=8,respect_delta=5,date_text=today.isoformat(),reason="aceptación del proyecto")
        league=self.universe.leagues_by_id.get(new_league) or {}; country=str(league.get("country") or "")
        update_country_reputation(self.state,country=country,delta=1.5,date_text=today.isoformat(),reason="nuevo banquillo")
        contract=build_manager_contract(team_id=new_team,team_name=self._team_name(new_team),league_id=new_league,league_name=str(league.get("name") or target.get("league_name") or f"Liga {new_league}"),date_text=today.isoformat(),reputation=float(profile.get("reputation") or 50),club_score=float(club_status(self.state,new_team).get("score") or target.get("club_score") or 50),expected_position=int(self.state["board_expectation"].get("expected_position") or target.get("expected_position") or 1))
        register_contract(self.state,contract)
        self._ensure_nf9_nf12_layers(); self.board_snapshot(persist=True,trigger="new_job")
        self._ingest_news([manager_event])
        publish_news(self.state,key=f"new-job:{today.isoformat()}:{new_team}",date=today.isoformat(),category="Tu carrera",importance=5,headline=f"Aceptas el banquillo de {self._team_name(new_team)}",detail=f"Tu carrera continúa en {league.get('name') or target.get('league_name')}. Heredas su clasificación, calendario, plantilla, proyecto y situación financiera sin reiniciar el mundo.",entity={"team_id":new_team})
        prior_clubs={int(row.get("team_id") or 0) for row in profile.get("tenures") or []}
        move_kind="return" if new_team in prior_clubs else "job_change"
        register_manager_milestone(self.state,date_text=today.isoformat(),season=str(self.state["season"]),kind=move_kind,team_id=new_team,team_name=self._team_name(new_team),from_team_id=old_team if was_active else None,from_team_name=self._team_name(old_team) if was_active else None,summary=(f"Regresas a {self._team_name(new_team)} para abrir una nueva etapa." if move_kind=="return" else f"Tu carrera cambia de proyecto: {self._team_name(old_team) if was_active else 'sin club'} → {self._team_name(new_team)}."))
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return self.snapshot()

    def _refresh_storyline_state(self, *, dashboard: dict[str, Any] | None = None, squad_api: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        dashboard = dashboard or self.manager_dashboard()
        next_match = self.next_scheduled_fixture()
        controlled = int(self.state["team_id"])
        rival = None
        opponent_name = None
        if next_match:
            opponent_id = int(next_match.get("away_team_id") if int(next_match.get("home_team_id") or 0) == controlled else next_match.get("home_team_id") or 0)
            if opponent_id:
                rival = rivalry_between(self.state, controlled, opponent_id)
                opponent_name = self._team_name(opponent_id)
        squad_api = squad_api or [self._career_player_api(row) for row in self._career_players_by_team.get(controlled, [])]
        return refresh_storylines(
            self.state, date_text=self.current_date.isoformat(), controlled_team_id=controlled, standings=self.standings(),
            recent_form=list(dashboard.get("recent_form") or []), squad=squad_api,
            negotiations=list((self.state.get("transfer_negotiations") or {}).values()), next_match=next_match, rivalry=rival,
            team_name=self._team_name(controlled), opponent_name=opponent_name,
            manager_name_lookup=self._manager_name, player_name_lookup=self._player_name,
        )

    def _sheet(self, team_id: int, tactics: dict[str, Any] | None = None, *, foreign_rule=None, competition_kind: str | None = None) -> TeamSheet9394:
        controlled = int(team_id) == int(self.state["team_id"])
        tactical_payload = dict(tactics) if tactics is not None else None
        if controlled:
            tactical_payload = engine_tactics_payload(tactical_payload or {**_default_tactics(), **(self.state.get("tactics") or {})}, self.state)
        tactical = FootballTactics9394(**tactical_payload) if tactical_payload is not None else None
        coach_profile = None if controlled else self._coach_profile(int(team_id))
        eligible_rows = self._eligible_match_rows(int(team_id), competition_kind=competition_kind)
        universe_view = _CareerUniverseView(self, exclude_league_suspended=(competition_kind == "league"))
        emergency_universe_view = _CareerUniverseView(self, include_injured=True, exclude_league_suspended=(competition_kind == "league"))
        if tactical is None and not controlled:
            tactical = ai_tactics_for_squad(eligible_rows, coach_profile)
        if controlled and self.state.get("selection"):
            selected = self.selection_snapshot()
            if not selected["valid"]:
                raise ValueError("El once del mánager no es válido: " + " ".join(selected["issues"]))
            by_id = {int(row["source_id"]): row for row in eligible_rows}
            formation=(tactical or FootballTactics9394(**{**_default_tactics(), **(self.state.get("tactics") or {})})).formation
            assigned=assign_players_to_formation([by_id[pid] for pid in selected["starter_ids"]],formation)
            assigned_by_id={int(r["player_id"]):str(r["slot"]) for r in assigned}
            ordered=[int(r["player_id"]) for r in assigned]
            starters = tuple(self._apply_development_to_footballer(footballer_from_snapshot(by_id[pid],assigned_slot=assigned_by_id.get(pid))) for pid in ordered)
            bench = tuple(self._apply_development_to_footballer(footballer_from_snapshot(by_id[pid])) for pid in selected["bench_ids"])
            tactical_root = ensure_tactical_plan_state(self.state)
            sheet = TeamSheet9394(
                team_id=str(team_id), team_name=(self._team_api(team_id) or {}).get("name", str(team_id)), starters=starters, bench=bench,
                tactics=tactical or FootballTactics9394(**engine_tactics_payload({**_default_tactics(), **(self.state.get("tactics") or {})}, self.state)),
                tactical_familiarity=round(float((tactical_root.get("familiarity") or {}).get("overall") or 62.0)),
                individual_instructions=dict(tactical_root.get("individual_instructions") or {}),
                opposition_instructions=dict(tactical_root.get("opposition_instructions") or {}),
                set_piece_takers=dict(tactical_root.get("set_piece_takers") or {}),
            )
            sheet.validate(LAWS_1993_94)
            return sheet
        rule=foreign_rule or self._domestic_foreign_rule(int(team_id))
        predicate=(lambda row:is_foreign_player(
            row,home_country_id=rule.home_country_id,continental=bool(getattr(rule,"continental",False)),
            domestic_equivalent_country_ids=rule.domestic_equivalent_country_ids,
        )) if rule is not None else None
        try:
            sheet = build_snapshot_team_sheet(universe_view, team_id, tactics=tactical,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None),allow_emergency_outfield_goalkeeper=True,coach_profile=coach_profile)
            emergency_injury = False
        except ValueError as exc:
            # A senior squad can be numerically valid (>=18) while a temporary
            # injury makes an XI impossible under specialist-position + foreign
            # quotas.  World AI may risk one of its *real* injured players, with
            # a severe performance penalty, but it may never exceed the quota.
            message = str(exc)
            recoverable = (
                "futbolistas históricos disponibles" in message
                or "no se puede construir un once" in message
                or "plantilla histórica no contiene portero" in message
            )
            injured = any(
                int((self.state.get("player_development", {}).get(str(row.get("source_id")), {}) or {}).get("injury_days") or 0) > 0
                for row in self._career_players_by_team.get(int(team_id), [])
                if not row.get("retired")
            )
            if not recoverable or not injured:
                raise
            sheet = build_snapshot_team_sheet(emergency_universe_view, team_id, tactics=tactical,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None),allow_emergency_outfield_goalkeeper=True,coach_profile=coach_profile)
            emergency_injury = True

        starters=tuple(self._apply_development_to_footballer(p) for p in sheet.starters)
        bench=tuple(self._apply_development_to_footballer(p) for p in sheet.bench)
        if emergency_injury:
            starters=tuple(self._apply_ai_emergency_injury_penalty(p) for p in starters)
            bench=tuple(self._apply_ai_emergency_injury_penalty(p) for p in bench)
        if controlled:
            tactical_root = ensure_tactical_plan_state(self.state)
            return replace(
                sheet, starters=starters, bench=bench,
                tactical_familiarity=round(float((tactical_root.get("familiarity") or {}).get("overall") or 62.0)),
                individual_instructions=dict(tactical_root.get("individual_instructions") or {}),
                opposition_instructions=dict(tactical_root.get("opposition_instructions") or {}),
                set_piece_takers=dict(tactical_root.get("set_piece_takers") or {}),
            )
        return replace(sheet, starters=starters, bench=bench)

    def _apply_match_player_state(self, result, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, seed: int, *, competition: str = "Partido", record_performance: bool = True, counts_for_league_stats: bool = False) -> None:
        dev = self.state["player_development"]
        events = tuple(result.events)
        for side, sheet, goals_for, goals_against in (
            (str(result.home_team_id), home_sheet, result.home.goals, result.away.goals),
            (str(result.away_team_id), away_sheet, result.away.goals, result.home.goals),
        ):
            players = {p.id for p in sheet.starters}
            players.update(e.player_id for e in events if e.team_id == side and e.kind in {"substitution", "injury_substitution"} and e.player_id)
            goal_ids = [e.player_id for e in events if e.team_id == side and e.kind == "goal" and e.player_id]
            assist_ids = [e.player_id for e in events if e.team_id == side and e.kind == "assist" and e.player_id]
            injury_ids = [e.player_id for e in events if e.team_id == side and e.kind == "injury" and e.player_id]
            development_coach = None
            if side.isdigit() and int(side) != int(self.state.get("team_id") or 0):
                development_coach = self._coach_profile(int(side))
            starter_ids = {p.id for p in sheet.starters}
            apply_match_development(
                dev, player_ids=players, starter_ids=starter_ids, won=goals_for > goals_against, drew=goals_for == goals_against,
                goal_ids=goal_ids, assist_ids=assist_ids, injury_ids=injury_ids, seed=seed + int(side) if side.isdigit() else seed,
                coach_profile=development_coach, source_players=self._all_players_index(), game_date=self.current_date,
                age_reference_date=(CAREER_START_DATE_9394 if uses_frozen_age(self.state) else self.current_date),
                record_season_stats=counts_for_league_stats,
            )
            if counts_for_league_stats:
                # League-only 0-10 ratings are persisted for BOTH teams.  The
                # controlled club keeps the detailed match log; every player
                # in the playable league still accumulates comparable season
                # ratings so league awards are not biased toward the user.
                # A pending league ban is served by sitting out this fixture.
                # Consume it BEFORE registering cards from this match so a new
                # suspension cannot disappear on the same afternoon.
                if side.isdigit():
                    for roster_row in self._career_players_by_team.get(int(side), []):
                        discipline_row = dev.setdefault(str(int(roster_row["source_id"])), {})
                        pending_ban = int(discipline_row.get("league_suspension_matches") or 0)
                        if pending_ban > 0:
                            discipline_row["league_suspension_matches"] = max(0, pending_ban - 1)
                            if pending_ban == 1:
                                discipline_row["league_suspension_reason"] = None
                rating_rows = match_ratings_for_side(result=result, sheet=sheet, side_team_id=side)
                yellow_cycle = self._league_yellow_cycle(int(side)) if side.isdigit() else 5
                new_suspensions: list[tuple[int, str]] = []
                for player_id, facts in rating_rows.items():
                    rating_row = dev.setdefault(str(player_id), {})
                    rating_row["season_rating_total"] = round(float(rating_row.get("season_rating_total") or 0.0) + float(facts["rating"]), 2)
                    rating_row["season_rating_count"] = int(rating_row.get("season_rating_count") or 0) + 1
                    previous_yellows = int(rating_row.get("season_yellows") or 0)
                    new_yellows = previous_yellows + int(facts["yellow"])
                    rating_row["season_yellows"] = new_yellows
                    rating_row["season_reds"] = int(rating_row.get("season_reds") or 0) + (1 if facts["red"] else 0)
                    reason = None
                    if facts["red"]:
                        reason = "expulsión"
                    elif int(facts["yellow"]) > 0 and previous_yellows // yellow_cycle < new_yellows // yellow_cycle:
                        reason = f"ciclo de {yellow_cycle} amarillas"
                    if reason:
                        rating_row["league_suspension_matches"] = max(1, int(rating_row.get("league_suspension_matches") or 0))
                        rating_row["league_suspension_reason"] = reason
                        if side.isdigit() and int(side) == int(self.state.get("team_id") or 0):
                            new_suspensions.append((int(player_id), reason))
                for player_id, reason in new_suspensions:
                    publish_news(
                        self.state, key=f"suspension:{self.current_date.isoformat()}:{player_id}:{reason}",
                        date=self.current_date.isoformat(), category="Plantilla", importance=3,
                        headline=f"Sanción para {self._player_name(player_id)}",
                        detail=f"Cumplirá un partido de sanción en liga por {reason} y no podrá entrar en la próxima convocatoria liguera.",
                        entity={"player_id": player_id, "team_id": int(self.state["team_id"])},
                    )
            if side.isdigit():
                team_id = int(side)
                update_squad_dynamics_after_match(
                    self.state, players=self._career_players_by_team.get(team_id, ()), development=dev,
                    starter_ids=starter_ids, appeared_ids=players, won=goals_for > goals_against,
                    drew=goals_for == goals_against, game_date=self.current_date,
                )
                if team_id == int(self.state.get("team_id") or 0):
                    update_relationships_after_match(
                        self.state, date_text=self.current_date.isoformat(),
                        squad=self._career_players_by_team.get(team_id, ()), starter_ids=starter_ids, appeared_ids=players,
                        won=goals_for > goals_against, drew=goals_for == goals_against,
                    )
                    update_dressing_room_after_match(
                        self.state, date_text=self.current_date.isoformat(),
                        players=self._career_players_by_team.get(team_id, ()), starter_ids=starter_ids,
                        won=goals_for > goals_against, drew=goals_for == goals_against,
                    )
            if side.isdigit() and int(side)==int(self.state.get("team_id") or 0):
                for player_id in injury_ids:
                    if player_id is None or not str(player_id).isdigit(): continue
                    pid=int(player_id);dev_row=dev.get(str(pid),{});days=int(dev_row.get("injury_days") or 0)
                    current=(medical_api(dev_row).get("current_injury") or {})
                    injury_name=str(current.get("name") or "Problemas físicos")
                    detail=f"{injury_name}. El parte médico estima {days} días de baja." if days else "El futbolista ha tenido que abandonar el partido."
                    publish_news(self.state,key=f"injury:{self.current_date.isoformat()}:{pid}",date=self.current_date.isoformat(),category="Plantilla",importance=3,headline=f"Lesión de {self._player_name(pid)}",detail=detail,entity={"player_id":pid,"team_id":int(self.state["team_id"])})
                    register_important_injury(self.state,player_id=pid,days=days,players=self._career_players_by_team.get(int(self.state["team_id"]),()),date_text=self.current_date.isoformat())
        if record_performance:
            record_managed_match(self.state, result=result, home_sheet=home_sheet, away_sheet=away_sheet, competition=competition, match_date=self.state.get("current_date"), counts_for_league_stats=counts_for_league_stats)

    def _publish_controlled_result(
        self, *, competition: str, home_team_id: int, away_team_id: int, home_goals: int, away_goals: int,
        fixture_context: dict[str, Any] | None = None,
    ) -> None:
        controlled=int(self.state["team_id"])
        if controlled not in (int(home_team_id),int(away_team_id)): return
        publish_managed_match(self.state,date=self.current_date.isoformat(),competition=competition,
            home_name=self._team_name(int(home_team_id)),away_name=self._team_name(int(away_team_id)),
            home_goals=int(home_goals),away_goals=int(away_goals),controlled_team_id=controlled,
            home_team_id=int(home_team_id),away_team_id=int(away_team_id))
        rivalry_row=record_match_memory(
            self.state, self.universe, date_text=self.current_date.isoformat(), competition=competition,
            home_team_id=int(home_team_id), away_team_id=int(away_team_id),
            home_goals=int(home_goals), away_goals=int(away_goals),
        )
        if rivalry_row is not None and competition != "Pretemporada":
            own_home=int(home_team_id)==controlled
            opponent=int(away_team_id) if own_home else int(home_team_id)
            gf=int(home_goals) if own_home else int(away_goals); ga=int(away_goals) if own_home else int(home_goals)
            register_rivalry_result(
                self.state,date_text=self.current_date.isoformat(),season=str(self.state["season"]),
                controlled_team_id=controlled,controlled_team_name=self._team_name(controlled),
                opponent_team_id=opponent,opponent_team_name=self._team_name(opponent),competition_name=competition,
                goals_for=gf,goals_against=ga,heat=int(rivalry_row.get("heat") or 0),
            )
        if competition != "Pretemporada":
            home_controlled=int(home_team_id)==controlled
            mine=int(home_goals) if home_controlled else int(away_goals);theirs=int(away_goals) if home_controlled else int(home_goals)
            opponent=int(away_team_id) if home_controlled else int(home_team_id)
            record_managed_tactical_usage(
                self.state, date_text=self.current_date.isoformat(), opponent_team_id=opponent,
                tactics={**_default_tactics(), **(self.state.get("tactics") or {})},
                competition_context=fixture_context or {"competition_name": competition},
            )
            rep_change=update_reputation_after_match(
                self.state,date_text=self.current_date.isoformat(),won=mine>theirs,drew=mine==theirs,
                own_strength=self._team_strength(controlled),opponent_strength=self._team_strength(opponent),
                rivalry_heat=int((rivalry_row or {}).get("heat") or 0),
            )
            league=self.universe.leagues_by_id.get(int(self.state.get("league_id") or 0)) or {}
            update_country_reputation(self.state,country=str(league.get("country") or ""),delta=float(rep_change.get("delta") or 0)*.70,date_text=self.current_date.isoformat(),reason="resultado oficial")
            record_events = update_career_records_after_match(
                self.state, date_text=self.current_date.isoformat(), competition=competition, controlled_team_id=controlled,
                home_team_id=int(home_team_id), away_team_id=int(away_team_id),
                home_goals=int(home_goals), away_goals=int(away_goals),
                home_name=self._team_name(int(home_team_id)), away_name=self._team_name(int(away_team_id)),
            )
            if record_events:
                self.state.setdefault("world_events", []).extend(record_events)
                self.state["world_events"] = self.state["world_events"][-600:]
                self._ingest_news(record_events)
            process_familiarity_day(
                self.state, training_session="match_preparation",
                training_quality=int(self._responsibility_effect("first_team_training").get("quality") or 10), match_played=True,
            )
            reset_opposition_instructions(self.state)
            self.board_snapshot(persist=True,trigger="post_match")

    def _post_matchday_income(self, home_team_id: int, *, competition: str, reference: int | str) -> int:
        team = self.universe.team(int(home_team_id)) or {}
        if not team:
            return 0
        income = matchday_income(team)
        finances = self.state["club_finances"].setdefault(str(int(home_team_id)), initial_club_finances(team,players=self._career_players_by_team.get(int(home_team_id),[])))
        finances["cash"] = int(finances.get("cash") or 0) + income
        finances["matchday_income"] = int(finances.get("matchday_income") or 0) + income
        post_long_economy(self.state,team_id=int(home_team_id),season=str(self.state["season"]),category="gate_receipts",amount=income)
        if int(home_team_id) == int(self.state["team_id"]):
            self.state["finances"] = finances
            self.state["economy_ledger"].append({
                "date": self.state["current_date"], "kind": "matchday_income", "amount": income,
                "competition": competition, "reference": reference,
            })
        return income

    def _simulate_matchday(self, matchday: int) -> None:
        if int(matchday) <= int(self.state["completed_matchday"]):
            return
        league_id = int(self.state["league_id"])
        calendar = [row for row in self._league_schedule(league_id) if int(row["matchday"]) == int(matchday)]
        expected = len(self._teams_for_league(league_id)) // 2
        if len(calendar) != expected:
            raise ValueError(f"Liga {league_id}, jornada {matchday}: se esperaban {expected} partidos y hay {len(calendar)}")
        controlled = int(self.state["team_id"])
        tactics = dict(self.state.get("tactics") or _default_tactics())
        results = list(self.state.get("results") or [])
        season_seed = season_start_year(self.state) * 1_000_000
        controlled_result=None
        for fixture in calendar:
            home_id, away_id = int(fixture["home_team_id"]), int(fixture["away_team_id"])
            home_tactics = tactics if home_id == controlled else None
            away_tactics = tactics if away_id == controlled else None
            home_sheet, away_sheet = self._sheet(home_id, home_tactics, competition_kind="league"), self._sheet(away_id, away_tactics, competition_kind="league")
            match_seed = season_seed + int(self.state["seed"]) * 1000 + int(matchday) * 100 + int(fixture["id"])
            referee = referee_for_match(league_id, seed=match_seed)
            result = self.engine.simulate(home_sheet, away_sheet, seed=match_seed, referee=referee, venue=venue_for_team(self.universe, home_id))
            self._apply_match_player_state(result, home_sheet, away_sheet, match_seed, competition=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga", counts_for_league_stats=True)
            results.append(_league_match_payload(matchday, int(fixture["id"]), home_id, away_id, result.home.goals, result.away.goals, referee_id=result.referee_id, referee_name=result.referee_name, referee_source_confidence=result.referee_source_confidence))
            if controlled in (home_id,away_id): controlled_result=(home_id,away_id,int(result.home.goals),int(result.away.goals))
            self._post_matchday_income(home_id, competition=f"league:{league_id}", reference=int(matchday))
        self.state["results"] = results
        self.state["completed_matchday"] = int(matchday)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._rebuild_rosters()
        if controlled_result:
            league_name=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga"
            self._publish_controlled_result(
                competition=league_name, home_team_id=controlled_result[0], away_team_id=controlled_result[1],
                home_goals=controlled_result[2], away_goals=controlled_result[3],
                fixture_context={"fixture_type": "league", "competition_id": league_id, "competition_name": league_name, "matchday": int(matchday)},
            )

    def _bootstrap_background_world(self, through_round: int) -> None:
        """Fast deterministic backfill before the playable start date."""
        world = self.state.get("world_leagues") or {}
        for source_key, league_state in world.items():
            source_id = int(source_key)
            teams = self._teams_for_league(source_id)
            fixtures = self._league_schedule(source_id)
            max_round = min(int(through_round), max((int(f["round"]) for f in fixtures), default=0))
            previous_completed=int(league_state.get("completed_round") or 0)
            strength={int(team["source_id"]):self._team_strength(int(team["source_id"])) for team in teams}
            stored=[]
            for fixture in fixtures:
                round_number=int(fixture["round"])
                if round_number > max_round:
                    continue
                home, away = int(fixture["home_team_id"]), int(fixture["away_team_id"])
                rng = Random(season_start_year(self.state)*1_000_000 + int(self.state["seed"])*100000 + source_id*1000 + round_number*50 + home + away)
                edge=(strength.get(home,60)-strength.get(away,60))/18.0 + .18
                hg=max(0,round(rng.random()*2.4 + max(-.4,min(.8,edge))))
                ag=max(0,round(rng.random()*2.1 - max(-.5,min(.5,edge/2))))
                stored.append({"round":round_number,"home_team_id":home,"away_team_id":away,"home_goals":hg,"away_goals":ag,"bootstrap":True})
                if round_number>previous_completed:
                    self._post_matchday_income(home,competition=f"league:{source_id}",reference=round_number)
            league_state["results"]=stored
            league_state["completed_round"]=max_round
            league_state["bootstrap_model"]="fast_dynamic_strength_backfill"

    def _simulate_background_round(self, round_number: int, source_id: int | None = None) -> None:
        world = self.state.get("world_leagues") or {}
        target_keys = [str(int(source_id))] if source_id is not None else list(world)
        season_seed = season_start_year(self.state) * 1_000_000
        for source_key in target_keys:
            league_state = world.get(source_key)
            if league_state is None: continue
            lid = int(source_key)
            if int(league_state.get("completed_round") or 0) >= int(round_number): continue
            fixtures = [f for f in self._league_schedule(lid) if int(f["round"]) == int(round_number)]
            if not fixtures: continue
            stored = list(league_state.get("results") or [])
            for fixture in fixtures:
                home_id, away_id = int(fixture["home_team_id"]), int(fixture["away_team_id"])
                seed = season_seed + int(self.state["seed"]) * 10000 + lid * 100 + int(round_number) * 10 + int(fixture["id"])
                rng = Random(seed); edge = max(-1.5, min(1.5, (self._team_strength(home_id) - self._team_strength(away_id)) / 10.0))
                home_p = max(.12, min(.52, .30 + .07 * edge)); away_p = max(.10, min(.46, .24 - .055 * edge))
                hg = sum(1 for _ in range(5) if rng.random() < home_p); ag = sum(1 for _ in range(5) if rng.random() < away_p)
                if rng.random() < .035: hg += 1
                if rng.random() < .025: ag += 1
                stored.append({"round": int(round_number), "home_team_id": home_id, "away_team_id": away_id, "home_goals": hg, "away_goals": ag, "simulation_model": "fast_background_v1"})
                self._post_matchday_income(home_id, competition=f"league:{lid}", reference=int(round_number))
            league_state["results"] = stored; league_state["completed_round"] = int(round_number); league_state["simulation_model"] = "fast_background_v1"; league_state["data_repair_players"] = 0

    def _process_background_leagues_for_day(self, day: date) -> None:
        for source_key, league_state in list((self.state.get("world_leagues") or {}).items()):
            source_id=int(source_key)
            schedule=self._league_schedule(source_id)
            due=max((int(f["round"]) for f in schedule if date.fromisoformat(str(f["date"])) <= day), default=0)
            completed=int(league_state.get("completed_round") or 0)
            for round_number in range(completed+1,due+1):
                self._simulate_background_round(round_number, source_id=source_id)













    def _target_ai_squad_size(self, team_id: int) -> int:
        """Soft senior-squad target derived from evolving club stature.

        Eighteen remains the non-negotiable operational floor.  The target is
        intentionally not identical for every club: modest sides can run lean,
        while large clubs carry more rotation depth.
        """
        score=float(club_status(self.state,int(team_id)).get("score") or 50.0)
        if score >= 92: return 24
        if score >= 82: return 23
        if score >= 52: return 22
        if score >= 38: return 21
        return 20

    def _process_monthly_economy_and_ai(self, day: date) -> list[dict[str, Any]]:
        month_key = f"{day.year:04d}-{day.month:02d}"
        if day.day != 1 or month_key in self.state.get("processed_months", []):
            return []
        events: list[dict[str, Any]] = []
        active_ids = self._active_club_ids()
        for team_id in active_ids:
            team = self.universe.team(team_id) or {}
            finances = self.state["club_finances"].setdefault(str(team_id), initial_club_finances(team,players=self._career_players_by_team.get(team_id,[])))
            stature=float(club_status(self.state, int(team_id)).get("score") or 50.0)
            posting = apply_monthly_club_finances(
                team=team, finances=finances,
                players=self._career_players_by_team.get(team_id, []),
                development=self.state["player_development"], contract_overrides=self.state["contract_overrides"],
                stature_score=stature, month=day.month,
            )
            for category,key in (("memberships","membership_income"),("television","television_income"),("sponsorship","sponsorship_income")):
                post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category=category,amount=int(posting.get(key) or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="wages",amount=int(posting.get("wage_expense") or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="operations",amount=int(posting.get("operating_expense") or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="debt_interest",amount=int(posting.get("debt_interest") or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="debt_principal",amount=int(posting.get("debt_principal") or 0))
            if int(finances.get("cash") or 0)<0:
                draw=abs(int(finances.get("cash") or 0))+max(500_000,round((int(posting.get("wage_expense") or 0)+int(posting.get("operating_expense") or 0))*0.35))
                finances["debt"]=int(finances.get("debt") or 0)+draw; finances["cash"]=int(finances.get("cash") or 0)+draw
                finances["financing_draws"]=int(finances.get("financing_draws") or 0)+draw
                post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="financing_draws",amount=draw)
                event={"kind":"financial_restructuring","date":day.isoformat(),"team_id":team_id,"amount":draw,"debt":int(finances["debt"])}; events.append(event)
            if team_id == int(self.state["team_id"]):
                self.state["finances"] = finances
                self.state["economy_ledger"].append({"date": day.isoformat(), "kind": "monthly_operations", "amount":int(posting.get("net") or 0), **posting})
                if events and events[-1].get("kind")=="financial_restructuring" and int(events[-1].get("team_id") or 0)==team_id:
                    self.state["economy_ledger"].append({"date":day.isoformat(),"kind":"debt_draw","amount":int(events[-1]["amount"])})
        # Contract work is staggered across clubs.  A real football world does
        # not renew 400+ squads on the same monthly tick, and doing so made long
        # careers increasingly expensive/noisy.  Each AI club still receives
        # three renewal pulses between January and June; unresolved fringe
        # contracts are allowed to reach the summer market naturally.
        # Clubs resolve their retention plan in two coherent checkpoints rather
        # than dribbling hundreds of one-player renewals into every monthly tick.
        # January sets the plan; June catches squads changed by the market.
        renewal_ids=[tid for tid in active_ids if tid!=int(self.state["team_id"])] if day.month in (1,6) else []
        renewals = renew_ai_contracts(
            current_date=day, controlled_team_id=int(self.state["team_id"]),
            players_by_team=self._career_players_by_team, development=self.state["player_development"],
            contract_overrides=self.state["contract_overrides"], seed=int(self.state["seed"]),
            max_renewals=max(1, len(renewal_ids)*10) if renewal_ids else 0, eligible_team_ids=renewal_ids,
            club_finances=self.state["club_finances"],
        ) if renewal_ids else []
        if renewals:
            self.state["ai_contract_history"].extend(renewals)
            self.state["ai_contract_history"]=self.state["ai_contract_history"][-AI_CONTRACT_LOG_LIMIT:]
            # Detailed contract decisions remain queryable in their specialist
            # ledger; the general world/news stream receives one intelligible
            # cycle summary instead of thousands of low-value renewal events.
            events.append({
                "kind":"ai_contract_cycle","date":day.isoformat(),"count":len(renewals),
                "clubs":len({int(row.get("team_id") or 0) for row in renewals}),
            })
        activity=max((market_activity_budget(transfer_period_status(day,country_id=self._club_country_id(tid),season=str(self.state["season"]))) for tid in active_ids),default=0)
        plans=self.state.get("recruitment_plans") or {}
        refresh_all_plans=activity>0 and (day.month==7 or len(plans)<max(1,len(active_ids)-1))
        if refresh_all_plans:
            refresh_recruitment_plans(
                self.state,current_date=day,team_ids=active_ids,players_by_team=self._career_players_by_team,
                development=self.state["player_development"],contracts=self.state["contract_overrides"],club_finances=self.state["club_finances"],
                coach_profile_getter=lambda tid:self._coach_profile(int(tid)),
            )
        first_budget=(activity+1)//2
        transfers = run_ai_transfer_window(
            current_date=day, controlled_team_id=int(self.state["team_id"]), eligible_team_ids=active_ids,
            players_by_team=self._career_players_by_team, seller_team_ids=active_ids+self._market_container_ids(),
            seller_release_exempt_ids=set(self._market_container_ids()), development=self.state["player_development"],
            club_finances=self.state["club_finances"], player_team_overrides=self.state["player_team_overrides"],
            contract_overrides=self.state["contract_overrides"], seed=int(self.state["seed"]),
            max_deals=activity,
            signing_allowed=lambda buyer,player:self._signing_eligibility(int(buyer),player,day=day)[0],
            attraction_score=lambda buyer,seller,player:(float(club_status(self.state,int(buyer)).get("score") or 50)-float(club_status(self.state,int(seller)).get("score") or 50))/25.0,
            foreign_limit_getter=lambda tid:(self._domestic_foreign_rule(int(tid)).max_starting if self._domestic_foreign_rule(int(tid)) is not None else None),
            foreign_predicate=lambda tid,player:self._is_domestic_foreign(int(tid),player),
            coach_profile_getter=lambda tid: self._coach_profile(int(tid)),
            buyer_plans=self.state.get("recruitment_plans") or {},
        )
        if transfers and len(transfers)>first_budget:
            register_replacement_chain(self.state,day=day,first_deals=transfers[:first_budget],follow_up_deals=transfers[first_budget:])
        self.state["ai_transfer_history"].extend(transfers); events.extend(transfers)
        if transfers:
            self._rebuild_rosters()
            affected=sorted({int(tid) for deal in transfers for tid in (deal.get("from_team_id"),deal.get("to_team_id")) if int(tid or 0) in active_ids})
            if affected:
                refresh_recruitment_plans(self.state,current_date=day,team_ids=affected,players_by_team=self._career_players_by_team,development=self.state["player_development"],contracts=self.state["contract_overrides"],club_finances=self.state["club_finances"],coach_profile_getter=lambda tid:self._coach_profile(int(tid)))
        coverage=[]
        if day.month in (7,8):
            coverage=ensure_ai_squad_coverage(
                current_date=day,controlled_team_id=int(self.state["team_id"]),eligible_team_ids=active_ids,
                players_by_team=self._career_players_by_team,development=self.state["player_development"],club_finances=self.state["club_finances"],
                player_team_overrides=self.state["player_team_overrides"],contract_overrides=self.state["contract_overrides"],
                seed=int(self.state["seed"]),max_signings=max(500,len(active_ids)*MINIMUM_SENIOR_SQUAD_SIZE_9394),
                signing_allowed=lambda buyer,player:self._signing_eligibility(int(buyer),player,day=day)[0],
                foreign_limit_getter=lambda tid:(self._domestic_foreign_rule(int(tid)).max_starting if self._domestic_foreign_rule(int(tid)) is not None else None),
                foreign_predicate=lambda tid,player:self._is_domestic_foreign(int(tid),player),
                target_squad_size_getter=lambda tid:self._target_ai_squad_size(int(tid)),
                emergency_source_team_ids=active_ids+self._market_container_ids(),
            )
            if coverage:
                self.state["ai_transfer_history"].extend(coverage);events.extend(coverage);self._rebuild_rosters()
        if day.month==7:
            clubs=[]
            for team_id in active_ids:
                if team_id==int(self.state["team_id"]): continue
                audit=squad_audit(self._career_players_by_team.get(team_id,[]),self.state["player_development"])
                clubs.append({"team_id":team_id,"team_name":self._team_name(team_id),"squad_size":audit["squad_size"],"minimum_squad_size":audit["minimum_squad_size"],"depth_shortage":audit["depth_shortage"],"coverage_ok":audit["coverage_ok"],"primary_need":audit["primary_need"],"counts":audit["counts"]})
            self.state["ai_squad_audits"].append({"season":self.state.get("season"),"date":day.isoformat(),"clubs":clubs,"coverage_ok":sum(1 for row in clubs if row["coverage_ok"]),"club_count":len(clubs),"emergency_signings":len(coverage)})
            self.state["ai_squad_audits"]=self.state["ai_squad_audits"][-12:]
        self.state["processed_months"].append(month_key)
        self.board_snapshot(persist=True,trigger="monthly")
        return events

    def _process_contract_expirations(self, day: date) -> list[dict[str, Any]]:
        if not (day.month == 7 and day.day == 1):
            return []
        marker=f"expirations:{day.year}"
        if marker in self.state.get("processed_months", []):
            return []
        events=[]
        for player in self.universe.payload.get("players", []):
            pid=int(player["source_id"]); team_id=self._current_team_id(pid)
            if team_id == 0:
                continue
            overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or player.get("overall") or player.get("category") or 60)
            contract=effective_contract(player,overall=overall,override=self.state["contract_overrides"].get(str(pid)))
            if int(contract.get("end_year") or 9999) > day.year:
                continue
            self.state["player_team_overrides"][str(pid)] = 0
            event={"kind":"contract_expired","date":day.isoformat(),"player_id":pid,"from_team_id":team_id,"to_team_id":0}
            events.append(event);self.state["contract_history"].append(event)
        self.state["processed_months"].append(marker)
        if events:
            self._rebuild_rosters()
        return events

    def _repair_selection_after_roster_departures(self, events: list[dict[str, Any]]) -> None:
        controlled = int(self.state["team_id"])
        expired = any(e.get("kind") == "contract_expired" and int(e.get("from_team_id") or 0) == controlled for e in events)
        training_injury = any(e.get("kind") == "training_injury" for e in events)
        if not (expired or training_injury):
            return
        if self.selection_snapshot()["valid"]:
            return
        self.state["selection"] = self._safe_auto_selection()
        selection=self.selection_snapshot()
        if training_injury:
            detail=("El asistente ha rehecho una convocatoria legal tras la baja sufrida en el entrenamiento." if selection["valid"] else "La lesión deja al equipo sin once completo. Debes revisar la plantilla antes del próximo partido.")
            title="Convocatoria reajustada" if selection["valid"] else "Once incompleto"
        else:
            detail=("El asistente ha rehecho un once legal tras expiraciones de contrato." if selection["valid"] else "Las expiraciones han dejado al club sin once completo. Debes incorporar futbolistas antes del próximo partido.")
            title="Once reajustado" if selection["valid"] else "Plantilla incompleta"
        self.state.setdefault("world_events", []).append({"kind":"manager_note","date":self.state["current_date"],"title":title,"detail":detail})

    def _process_international_day(self, day: date) -> list[dict[str, Any]]:
        windows=generated_international_windows_9394(season_start_year(self.state))
        if day not in windows:
            return []
        index=windows.index(day)
        marker=f"{index}:{day.isoformat()}"
        if marker in self.state.get("processed_international_windows", []):
            return []
        job=international_manager_snapshot(self.state)
        selections={}
        if job.get("country_id") and job.get("selected_player_ids"):
            selections[int(job["country_id"])]=[int(pid) for pid in job.get("selected_player_ids") or []]
        raw=simulate_generated_friendlies(
            self.universe, development=self.state["player_development"], window_index=index,
            seed=int(self.state["seed"])*10000+index*100, selections=selections,
        )
        events=[]; called_up=set(); controlled_players={int(p["source_id"]) for p in self._career_players_by_team.get(int(self.state["team_id"]),[])}
        for match_index,row in enumerate(raw):
            result=row.pop("result");home_sheet=row.pop("home_sheet");away_sheet=row.pop("away_sheet")
            for player in (*home_sheet.starters,*home_sheet.bench,*away_sheet.starters,*away_sheet.bench):
                if str(player.id).isdigit() and int(player.id) in controlled_players: called_up.add(int(player.id))
            self._apply_match_player_state(result,home_sheet,away_sheet,int(self.state["seed"])*10000+index*100+match_index)
            record_international_player_match(self.state,result=result,home_sheet=home_sheet,away_sheet=away_sheet,date_text=day.isoformat(),competition="Amistoso internacional")
            stored={**row,"date":day.isoformat()}
            self.state["international_history"].append(stored);events.append(stored)
            managed_country=int((self.state.get("international_manager") or {}).get("country_id") or 0)
            if managed_country in {int(stored["home_country_id"]),int(stored["away_country_id"])}:
                own_home=managed_country==int(stored["home_country_id"]);gf=int(stored["home_goals"] if own_home else stored["away_goals"]);ga=int(stored["away_goals"] if own_home else stored["home_goals"])
                update_international_reputation(self.state,country_id=managed_country,goals_for=gf,goals_against=ga)
        if called_up:
            names=[self._player_name(pid) for pid in sorted(called_up)]
            detail=", ".join(names[:5]) + (f" y {len(names)-5} más" if len(names)>5 else "")
            publish_news(self.state,key=f"callups:{day.isoformat()}:{int(self.state['team_id'])}",date=day.isoformat(),category="Selecciones",importance=2,headline=f"{len(names)} futbolista{'s' if len(names)!=1 else ''} del club, convocado{'s' if len(names)!=1 else ''}",detail=detail,entity={"team_id":int(self.state["team_id"])})
        self.state["processed_international_windows"].append(marker)
        self._rebuild_rosters()
        return events

    def _process_international_tournament(self, day: date) -> list[dict[str, Any]]:
        if not (day.month==6 and day.day==17 and is_world_championship_summer(day.year)):
            return []
        marker=f"world-championship:{day.year}"
        if any(str(row.get("marker"))==marker for row in self.state.get("international_tournaments",[])):
            return []
        job=international_manager_snapshot(self.state);selections={}
        if job.get("country_id") and job.get("selected_player_ids"):
            selections[int(job["country_id"])]=[int(pid) for pid in job.get("selected_player_ids") or []]
        tournament=simulate_world_championship_24(self.universe,year=day.year,development=self.state["player_development"],seed=int(self.state["seed"])*100000+day.year,selections=selections,match_recorder=lambda result,home,away,stage: record_international_player_match(self.state,result=result,home_sheet=home,away_sheet=away,date_text=day.isoformat(),competition="Campeonato Mundial",tournament=True,stage=stage))
        tournament["marker"]=marker;self.state.setdefault("international_tournaments",[]).append(tournament);self.state["international_tournaments"]=self.state["international_tournaments"][-12:]
        managed=int(job.get("country_id") or 0)
        if managed:
            for row in tournament.get("matches") or []:
                if managed not in {int(row["home_country_id"]),int(row["away_country_id"])}: continue
                own_home=managed==int(row["home_country_id"]);gf=int(row["home_goals"] if own_home else row["away_goals"]);ga=int(row["away_goals"] if own_home else row["home_goals"])
                # Shootout advancement counts as a sporting win for reputation.
                if gf==ga and int(row.get("winner_country_id") or 0)==managed: gf+=1
                update_international_reputation(self.state,country_id=managed,goals_for=gf,goals_against=ga,tournament=True,stage=str(row.get("stage") or ""))
        event={"kind":"international_tournament_finished","date":day.isoformat(),"competition":"Campeonato Mundial","year":day.year,"champion_country_id":int(tournament["champion_country_id"]),"champion_name":tournament["champion_name"],"format":tournament["format"]}
        return [event]

    def international_manager_snapshot(self) -> dict[str,Any]:
        return international_manager_snapshot(self.state)

    def accept_national_job(self,offer_id:str) -> dict[str,Any]:
        event=accept_national_job_state(self.state,self.universe,str(offer_id),day=self.current_date,development=self.state["player_development"]);self.state.setdefault("world_events",[]).append(event);return event

    def resign_national_job(self) -> dict[str,Any]:
        event=resign_national_job_state(self.state,day=self.current_date);self.state.setdefault("world_events",[]).append(event);return event

    def auto_national_selection(self) -> list[int]:
        job=international_manager_snapshot(self.state);cid=int(job.get("country_id") or 0)
        if not cid: raise ValueError("no diriges ninguna selección")
        squad=select_national_squad(self.universe,cid,development=self.state["player_development"]);ids=[int(p["id"]) for p in squad]
        return set_national_selection_state(self.state,self.universe,ids,development=self.state["player_development"])

    def set_national_selection(self,player_ids:list[int]) -> list[int]:
        return set_national_selection_state(self.state,self.universe,[int(pid) for pid in player_ids],development=self.state["player_development"])

    def _process_daily_world(self, day: date) -> list[dict[str, Any]]:
        events=[]
        # Registration/contract state is resolved before any match played on the
        # same date.  This matters especially on 1 July: expirations and summer
        # squad repair must happen before summer leagues/cups try to build a legal
        # XI under their foreign-player and specialist-position rules.
        events.extend(self._process_user_loans(day))
        events.extend(self._process_contract_expirations(day))
        events.extend(self._process_user_negotiations(day))
        events.extend(self._process_user_listings(day))
        events.extend(self._process_monthly_economy_and_ai(day))
        events.extend(self._process_manager_market(day))
        if day.day == 1:
            self._refresh_job_market(day=day, proactive=True)
        cooled_information = process_information_day(self.state, day=day)
        if cooled_information:
            self.state.setdefault("world_events", []).extend(cooled_information)
            self.state["world_events"] = self.state["world_events"][-600:]
        events.extend(process_special_competitions(self, day, bootstrap=False))
        events.extend(process_daily_tournaments(self, day, bootstrap=False))
        events.extend(self._process_international_day(day))
        events.extend(self._process_international_tournament(day))
        if day.month==7 and day.day==1 and not (self.state.get("international_manager") or {}).get("country_id"):
            offers=generate_national_job_offers(self.state,self.universe,day=day,manager_reputation=float(manager_profile_snapshot(self.state).get("reputation") or 50),seed=int(self.state["seed"]))
            if offers: events.append({"kind":"national_job_offers","date":day.isoformat(),"count":len(offers)})
        for event in events:
            if event.get("kind") != "ai_transfer":
                continue
            buyer=int(event.get("to_team_id") or 0); seller=int(event.get("from_team_id") or 0); fee=int(event.get("fee") or 0)
            if fee > 0 and buyer:
                post_long_economy(self.state,team_id=buyer,season=str(self.state["season"]),category="transfer_spend",amount=fee)
            if fee > 0 and seller:
                post_long_economy(self.state,team_id=seller,season=str(self.state["season"]),category="transfer_income",amount=fee)
            pid=int(event.get("player_id") or 0); raw=self._player_source(pid) or {}
            overall=int(self.state.get("player_development",{}).get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
            record_transfer_memory(
                self.state,self.universe,date_text=str(event.get("date") or day.isoformat()),player_id=pid,
                from_team_id=int(event.get("from_team_id") or 0),to_team_id=int(event.get("to_team_id") or 0),
                fee=int(event.get("fee") or 0),player_overall=overall,
            )
        if events:
            self.state["world_events"].extend(events)
            # The save remains compact even after long careers; detailed history
            # lives in the specialised ledgers above.
            self.state["world_events"] = self.state["world_events"][-600:]
            self._ingest_news(events)
        return events

    def set_tactics(self, payload: dict[str, Any]) -> None:
        validated = FootballTactics9394(**{**_default_tactics(), **payload})
        self.state["tactics"] = {
            "formation": validated.formation, "mentality": validated.mentality,
            "tempo": validated.tempo, "pressing": validated.pressing,
            "directness": validated.directness, "defensive_line": validated.defensive_line,
            "width": validated.width, "offside_trap": validated.offside_trap, "marking": validated.marking,
            "build_up": validated.build_up, "final_third": validated.final_third, "transition": validated.transition,
        }
        update_tactical_plan_state(self.state, build_up=validated.build_up, final_third=validated.final_third, transition=validated.transition, game_date=self.current_date)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()

    def pending_world_fixture(self) -> dict[str, Any] | None:
        pending=self.state.get("pending_world_match")
        if not pending:
            return None
        home_id=int(pending["home_team_id"]);away_id=int(pending["away_team_id"])
        home=self.universe.team(home_id) or {};away=self.universe.team(away_id) or {}
        tournament=(self.state.get("daily_tournaments") or {}).get(str(int(pending["source_id"])),{})
        return {
            **pending,"fixture_type":"tournament","competition_name":tournament.get("name") or f"Torneo {pending['source_id']}",
            "home_team":home.get("name") or str(home_id),"away_team":away.get("name") or str(away_id),
        }

    def _process_controlled_league_byes(self, day: date) -> None:
        controlled=int(self.state["team_id"]); schedule=self._league_schedule()
        while int(self.state.get("completed_matchday") or 0) < self._controlled_total_rounds():
            round_number=int(self.state.get("completed_matchday") or 0)+1
            rows=[row for row in schedule if int(row["matchday"])==round_number]
            if not rows or date.fromisoformat(str(rows[0]["date"])) > day:
                break
            if any(controlled in (int(row["home_team_id"]),int(row["away_team_id"])) for row in rows):
                break
            self._simulate_matchday(round_number)

    def _club_country_id(self, team_id: int) -> int | None:
        lid=self._current_league_for_team(int(team_id))
        league=self.universe.leagues_by_id.get(int(lid)) if lid is not None else None
        try: return int((league or {}).get("country_id"))
        except (TypeError,ValueError): return None

    def transfer_period_snapshot(self, team_id: int | None = None, day: date | None = None) -> dict[str,Any]:
        tid=int(team_id if team_id is not None else self.state["team_id"])
        status=transfer_period_status(day or self.current_date,country_id=self._club_country_id(tid),season=str(self.state["season"]))
        return status.as_dict()

    def _domestic_foreign_rule(self, team_id: int | None = None):
        tid=int(team_id if team_id is not None else self.state["team_id"])
        lid=self._current_league_for_team(tid)
        if lid is None: return None
        cache=getattr(self,"_foreign_rule_cache",None)
        if cache is None:
            cache={};self._foreign_rule_cache=cache
        key=(int(lid),tid)
        if key not in cache:
            cache[key]=competition_foreign_rule(self.universe,kind="league",source_id=int(lid),team_id=tid)
        return cache[key]

    def _is_domestic_foreign(self, team_id: int, player: dict[str, Any]) -> bool:
        rule=self._domestic_foreign_rule(int(team_id))
        if rule is None: return False
        return is_foreign_player(
            player,home_country_id=rule.home_country_id,continental=False,
            domestic_equivalent_country_ids=rule.domestic_equivalent_country_ids,
        )

    def _signing_eligibility(self, team_id:int, player:dict[str,Any], *, day:date|None=None) -> tuple[bool,str]:
        day=day or self.current_date
        period=transfer_period_status(day,country_id=self._club_country_id(team_id),season=str(self.state["season"]))
        if not period.open: return False,period.label
        club_ok, club_reason = club_specific_signing_eligibility(int(team_id), player)
        if not club_ok: return False, club_reason
        rule=self._domestic_foreign_rule(team_id)
        if rule is None: return True,period.label
        ok,reason=can_register_foreign_signing(self._career_players_by_team.get(int(team_id),[]),player,rule)
        return ok,reason if not ok else period.label

    def _ensure_preseason_schedule(self) -> None:
        season=str(self.state.get("season") or "1993-94")
        existing=[r for r in (self.state.get("preseason_friendlies") or []) if str(r.get("season"))==season]
        if existing: return
        start=season_start_year(self.state);controlled=int(self.state["team_id"])
        candidates=[tid for tid in self._active_club_ids() if tid!=controlled and len(self._match_players_by_team.get(tid,[]))>=11]
        if not candidates: return
        own=self._team_strength(controlled)
        candidates.sort(key=lambda tid:(abs(self._team_strength(tid)-own),tid))
        # Mix comparable opposition with one slightly tougher test.  Fixtures are
        # generated career content, not claimed as historical real-life friendlies.
        picks=[]
        for idx in (0,3,8,14):
            if candidates: picks.append(candidates[min(idx,len(candidates)-1)])
        picks=list(dict.fromkeys(picks))[:4]
        while len(picks)<min(4,len(candidates)):
            nxt=next(t for t in candidates if t not in picks);picks.append(nxt)
        dates=[date(start,7,17),date(start,7,28),date(start,8,10),date(start,8,22)]
        rows=[]
        for i,(opp,day_) in enumerate(zip(picks,dates),1):
            home,away=(controlled,opp) if i%2 else (opp,controlled)
            rows.append({"id":-(start*100+i),"season":season,"date":day_.isoformat(),"home_team_id":home,"away_team_id":away,"fixture_type":"friendly","competition_name":"Pretemporada","played":False,"generated":True})
        self.state.setdefault("preseason_friendlies",[]).extend(rows)

    def next_preseason_fixture(self) -> dict[str,Any] | None:
        self._ensure_preseason_schedule();season=str(self.state["season"])
        rows=[r for r in self.state.get("preseason_friendlies") or [] if str(r.get("season"))==season and not r.get("played") and date.fromisoformat(str(r["date"]))>=self.current_date]
        if not rows: return None
        row=min(rows,key=lambda x:(str(x["date"]),int(x["id"])))
        home=self._team_api(int(row["home_team_id"]));away=self._team_api(int(row["away_team_id"]))
        return {**row,"home_team":home["name"] if home else str(row["home_team_id"]),"away_team":away["name"] if away else str(row["away_team_id"])}

    def next_scheduled_fixture(self) -> dict[str,Any] | None:
        if self.pending_world_fixture(): return self.pending_world_fixture()
        options=[x for x in (self.next_preseason_fixture(),self.next_fixture()) if x is not None]
        return min(options,key=lambda r:(str(r.get("date") or "9999-12-31"),0 if r.get("fixture_type")=="friendly" else 1)) if options else None

    def preseason_snapshot(self) -> dict[str,Any]:
        rows=[]
        for r in self.state.get("preseason_friendlies") or []:
            if str(r.get("season"))!=str(self.state["season"]): continue
            home=self._team_api(int(r["home_team_id"]));away=self._team_api(int(r["away_team_id"]))
            rows.append({**r,"home_team":home["name"] if home else str(r["home_team_id"]),"away_team":away["name"] if away else str(r["away_team_id"])})
        league=self.next_fixture();first_league=min((date.fromisoformat(str(r["date"])) for r in self._league_schedule()),default=date(season_start_year(self.state),9,1))
        active=self.current_date < first_league
        return {"active":active,"label":"Pretemporada" if active else "Temporada oficial","friendlies":rows,"next_friendly":self.next_preseason_fixture(),"first_league_match":first_league.isoformat(),"pace":"short" if active else "event_driven"}

    def club_status_snapshot(self, team_id:int|None=None) -> dict[str,Any]:
        tid=int(team_id if team_id is not None else self.state["team_id"]);row=club_status(self.state,tid)
        return {"team_id":tid,"team_name":self._team_name(tid),**row}

    def next_fixture(self) -> dict[str, Any] | None:
        next_matchday=int(self.state["completed_matchday"])+1
        if next_matchday > self._controlled_total_rounds():
            return None
        controlled=int(self.state["team_id"])
        fixture=next((row for row in self._league_schedule() if int(row["matchday"])==next_matchday and controlled in (int(row["home_team_id"]),int(row["away_team_id"]))),None)
        if fixture is None:
            # Odd-number leagues can give the controlled club a bye. Advance the
            # competition round internally until its next actual fixture.
            schedule=self._league_schedule()
            for round_number in range(next_matchday+1,self._controlled_total_rounds()+1):
                fixture=next((row for row in schedule if int(row["matchday"])==round_number and controlled in (int(row["home_team_id"]),int(row["away_team_id"]))),None)
                if fixture is not None: break
        if fixture is None: return None
        home_id,away_id=int(fixture["home_team_id"]),int(fixture["away_team_id"])
        home,away=self._team_api(home_id),self._team_api(away_id)
        return {**fixture,"home_team":home["name"] if home else str(home_id),"away_team":away["name"] if away else str(away_id),"fixture_type":"league","competition_id":int(self.state["league_id"])}

    def _foreign_rule_for_fixture(self, fixture:dict[str,Any], team_id:int|None=None):
        tid=int(team_id if team_id is not None else self.state["team_id"])
        if fixture.get("fixture_type")=="tournament":
            sid=int(fixture.get("source_id") or fixture.get("competition_id") or 0)
            return competition_foreign_rule(self.universe,kind="tournament",source_id=sid,team_id=tid)
        return self._domestic_foreign_rule(tid)

    def _validate_controlled_selection_for_fixture(self, fixture:dict[str,Any]) -> list[str]:
        selection=self.state.get("selection") or {};owned={int(p["source_id"]):p for p in self._career_players_by_team.get(int(self.state["team_id"]),[])}
        starters=[owned[pid] for pid in map(int,selection.get("starter_ids") or []) if pid in owned]
        bench=[owned[pid] for pid in map(int,selection.get("bench_ids") or []) if pid in owned]
        rule=self._foreign_rule_for_fixture(fixture)
        return validate_matchday_foreigners(starters,bench,rule) if rule is not None else []

    def _live_match_sheets(self) -> tuple[TeamSheet9394, TeamSheet9394]:
        live=self.state.get("live_match")
        if not live: raise ValueError("no hay partido en directo")
        home_id=int(live["home_team_id"]);away_id=int(live["away_team_id"]);controlled=int(self.state["team_id"])
        home_t=live.get("home_tactics") if home_id==controlled else None;away_t=live.get("away_tactics") if away_id==controlled else None
        fixture=live.get("fixture") or {}
        home_rule=self._foreign_rule_for_fixture(fixture,home_id) if fixture.get("fixture_type")=="tournament" else None
        away_rule=self._foreign_rule_for_fixture(fixture,away_id) if fixture.get("fixture_type")=="tournament" else None
        kind=str(fixture.get("fixture_type") or "league")
        home=self._sheet(home_id,home_t,foreign_rule=home_rule,competition_kind=kind);away=self._sheet(away_id,away_t,foreign_rule=away_rule,competition_kind=kind)
        return home,away

    def start_live_match(self) -> dict[str,Any]:
        if self.state.get("job_status")=="dismissed": raise ValueError("el consejo ha terminado tu etapa en el club")
        if self.state.get("live_match"):
            return self.live_match_snapshot()
        fixture=self.pending_world_fixture() or self.next_scheduled_fixture()
        if fixture is None: raise ValueError("no hay próximo partido")
        if bool(fixture.get("postponed")) or str(fixture.get("schedule_status") or "").lower()=="postponed":
            raise ValueError("el partido está aplazado; espera a que el calendario confirme una nueva fecha")
        controlled=int(self.state["team_id"]);home_id=int(fixture.get("home_team_id") or 0);away_id=int(fixture.get("away_team_id") or 0)
        opponent_id=away_id if home_id==controlled else home_id if away_id==controlled else 0
        if opponent_id<=0:
            raise ValueError("el rival todavía no está confirmado")
        foreign_issues=self._validate_controlled_selection_for_fixture(fixture)
        if foreign_issues: raise ValueError(" ".join(foreign_issues))
        match_date=date.fromisoformat(str(fixture.get("date") or self.current_date.isoformat()))
        if self.current_date<match_date: raise ValueError("todavía no es día de partido")
        tactics=dict(self.state.get("tactics") or _default_tactics())
        home_rule=self._foreign_rule_for_fixture(fixture,home_id) if fixture.get("fixture_type")=="tournament" else None
        away_rule=self._foreign_rule_for_fixture(fixture,away_id) if fixture.get("fixture_type")=="tournament" else None
        kind=str(fixture.get("fixture_type") or "league")
        home_sheet=self._sheet(home_id,tactics if home_id==controlled else None,foreign_rule=home_rule,competition_kind=kind)
        away_sheet=self._sheet(away_id,tactics if away_id==controlled else None,foreign_rule=away_rule,competition_kind=kind)

        # P5: the rival prepares against habits that have already been exposed
        # in prior matches. It does not read the user's last-second setup.
        ai_team_id=away_id if home_id==controlled else home_id
        ai_sheet=away_sheet if home_id==controlled else home_sheet
        coach=self._coach_profile(ai_team_id)
        tactical_context=tactical_context_for_fixture(fixture)
        expected=expected_managed_tactics(self.state,fallback=_default_tactics(),context=tactical_context)
        coach_id=(coach or {}).get("source_id") or (coach or {}).get("id")
        coach_id=int(coach_id) if str(coach_id or "").isdigit() else None
        learning=rival_learning_for_preparation(
            self.state, manager_id=coach_id, team_id=ai_team_id,
            expected_opponent_tactics=expected["tactics"],
        )
        preparation=prepare_tactics_for_opponent(
            ai_sheet.tactics, own_players=self._career_players_by_team.get(ai_team_id,()),
            opponent_players=self._career_players_by_team.get(controlled,()),
            expected_opponent_tactics=expected["tactics"], manager=coach,
            observed_sample=int(expected.get("sample_size") or 0),
            observed_predictability=int(expected.get("predictability") or 0),
            match_context=tactical_context, learning=learning,
        )
        ai_sheet=replace(ai_sheet,tactics=preparation["tactics"])
        if home_id==controlled: away_sheet=ai_sheet
        else: home_sheet=ai_sheet
        preparation_api={
            "adjustments":list(preparation.get("adjustments") or []),
            "threat_profile":dict(preparation.get("threat_profile") or {}),
            "confidence":int(preparation.get("confidence") or 0),
            "observed_sample":int(preparation.get("observed_sample") or 0),
            "observed_predictability":int(preparation.get("observed_predictability") or 0),
            "expected_opponent":dict(preparation.get("expected_opponent") or {}),
            "summary":str(preparation.get("summary") or ""),
            "prepared_tactics":dict(preparation.get("prepared_tactics") or {}),
            "context":dict(preparation.get("context") or {}),
            "phase_focus":str(preparation.get("phase_focus") or ""),
            "preparation_intensity":str(preparation.get("preparation_intensity") or ""),
            "learning":dict(preparation.get("learning") or {}),
            "learning_note":str(preparation.get("learning_note") or ""),
            "manager_id":coach_id,
            "team_id":ai_team_id,
        }
        if fixture.get("fixture_type")=="tournament": seed=int((self.state.get("pending_world_match") or {}).get("seed") or 1)
        elif fixture.get("fixture_type")=="friendly": seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+abs(int(fixture["id"]))
        else:
            seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+int(fixture["matchday"])*100+int(fixture["id"])
        referee = referee_for_match(int(self.state["league_id"]), seed=seed) if fixture.get("fixture_type") == "league" else None
        self.state["live_match"]=self.live_engine.start(home_sheet,away_sheet,seed=seed,controlled_team_id=controlled,fixture=fixture,referee=referee,venue=venue_for_team(self.universe, home_id))
        self.state["live_match"]["ai_preparation"]=preparation_api
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return self.live_match_snapshot()

    def cancel_live_preview(self) -> dict[str, Any]:
        """Discard an unstarted preview so the manager can revise XI/tactics.

        Once the clock has moved, the match is part of the world state and may
        no longer be cancelled.  This keeps the pre-match UX reversible without
        allowing a played match to be rerolled.
        """
        live=self.state.get("live_match")
        if not live: return self.snapshot()
        if int(live.get("minute") or 0) != 0 or str(live.get("status") or "") not in {"preview", "live"}:
            raise ValueError("el partido ya ha comenzado y no puede volver a la preparación")
        self.state["live_match"] = None
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.snapshot()

    def live_match_snapshot(self) -> dict[str,Any]|None:
        live=self.state.get("live_match")
        if not live: return None
        snap=self.live_engine.snapshot(live); home_sheet,away_sheet=self._live_match_sheets()
        player_map={int(p.id):p for p in (*home_sheet.starters,*home_sheet.bench,*away_sheet.starters,*away_sheet.bench) if str(p.id).isdigit()}
        controlled=int(self.state["team_id"]); own_home=int(snap["home_team_id"])==controlled
        on_pitch=snap["home_on_pitch_ids"] if own_home else snap["away_on_pitch_ids"]
        bench=snap["home_bench_ids"] if own_home else snap["away_bench_ids"]
        sent_off=snap["home_sent_off_ids"] if own_home else snap["away_sent_off_ids"]
        forced_off=snap["home_forced_off_ids"] if own_home else snap["away_forced_off_ids"]
        fatigue=snap["home_fatigue"] if own_home else snap["away_fatigue"]
        opponent_on_pitch=snap["away_on_pitch_ids"] if own_home else snap["home_on_pitch_ids"]
        opponent_bench=snap["away_bench_ids"] if own_home else snap["home_bench_ids"]
        opponent_fatigue=snap["away_fatigue"] if own_home else snap["home_fatigue"]
        def player_row(pid:int, fatigue_map:dict[str,Any])->dict[str,Any]:
            raw=self._player_source(int(pid)); api=self._career_player_api(raw) if raw else {"id":pid,"display_name":getattr(player_map.get(pid),"name",str(pid)),"position":getattr(player_map.get(pid),"position","")}
            api["match_fatigue"]=round(float(fatigue_map.get(str(pid),0.0)),1);api["match_condition"]=max(0,round(100-float(fatigue_map.get(str(pid),0.0))))
            return api
        snap["controlled_on_pitch"]=[player_row(pid,fatigue) for pid in on_pitch]
        snap["controlled_bench"]=[player_row(pid,fatigue) for pid in bench]
        snap["controlled_sent_off"]=[player_row(pid,fatigue) for pid in sent_off]
        snap["controlled_forced_off"]=[player_row(pid,fatigue) for pid in forced_off]
        snap["controlled_absences"]=self._controlled_absences_for_fixture(live.get("fixture") or {})
        controlled_stats=snap["home"] if own_home else snap["away"]
        snap["controlled_substitutions_used"]=int(controlled_stats.get("substitutions") or 0)
        snap["controlled_substitutions_remaining"]=max(0,LAWS_1993_94.max_used_substitutes-snap["controlled_substitutions_used"])
        # Once the official XI exists it is match information, not scouting omniscience.
        # Expose both confirmed elevens for the dedicated pre-match presentation.
        snap["opponent_on_pitch"]=[player_row(pid,opponent_fatigue) for pid in opponent_on_pitch]
        snap["opponent_bench"]=[player_row(pid,opponent_fatigue) for pid in opponent_bench]
        opponent_id = int(snap["away_team_id"] if own_home else snap["home_team_id"])
        opponent_players = [row for row in self._career_players_by_team.get(opponent_id, ()) if not row.get("retired")]
        def opponent_level(row: dict[str, Any]) -> int:
            pid = int(row.get("source_id") or 0)
            return int((self.state.get("player_development", {}).get(str(pid)) or {}).get("overall") or row.get("overall") or row.get("category") or 0)
        opponent_players = sorted(opponent_players, key=opponent_level, reverse=True)[:3]
        opponent_tactics = snap["away_tactics"] if own_home else snap["home_tactics"]
        report_effect = self._responsibility_effect("opposition_reports")
        report_quality = int(report_effect.get("quality") or 10)
        known_tactics = {"formation": (opponent_tactics or {}).get("formation")}
        if report_quality >= 11:
            known_tactics.update({"mentality": (opponent_tactics or {}).get("mentality"), "tempo": (opponent_tactics or {}).get("tempo")})
        if report_quality >= 14:
            known_tactics.update({"pressing": (opponent_tactics or {}).get("pressing"), "directness": (opponent_tactics or {}).get("directness")})
        if report_quality >= 17:
            known_tactics.update({"defensive_line": (opponent_tactics or {}).get("defensive_line"), "width": (opponent_tactics or {}).get("width"), "marking": (opponent_tactics or {}).get("marking")})
        key_count = 3 if report_quality >= 14 else 2 if report_quality >= 10 else 1
        key_rows=[]
        radius = 2 if report_quality >= 17 else 4 if report_quality >= 14 else 7 if report_quality >= 10 else 10
        for row in opponent_players[:key_count]:
            level=opponent_level(row)
            pid=int(row["source_id"])
            jitter_span=max(1,radius//2)
            jitter=0 if report_quality >= 18 else ((int(self.state.get("seed") or 9394) ^ (pid * 1009) ^ (report_quality * 313)) % (jitter_span * 2 + 1)) - jitter_span
            estimate=max(35,min(99,level+jitter))
            key_rows.append({
                "id": pid,
                "display_name": str(row.get("display_name") or row.get("name") or f"Jugador #{row['source_id']}"),
                "position": str(row.get("position") or row.get("broad_position") or "—"),
                "overall": level if report_quality >= 18 else estimate,
                "overall_is_exact": report_quality >= 18,
                "overall_range": [max(35,estimate-radius),min(99,estimate+radius)],
                "identity": player_archetype(row)[0] if report_quality >= 12 else "Amenaza a estudiar",
            })
        rivalry_row=rivalry_between(self.state,controlled,opponent_id)
        snap["opponent_context"] = {
            "team_id": opponent_id,
            "team_name": snap["away_team_name"] if own_home else snap["home_team_name"],
            "manager": self._coach_profile(opponent_id),
            "tactics": known_tactics,
            "preparation": dict(live.get("ai_preparation") or {}),
            "report": report_effect,
            "key_players": key_rows,
            "rivalry": dict(rivalry_row or {}),
            "history": contextual_milestones(self.state,team_id=controlled,opponent_team_id=opponent_id,limit=4),
            "reencounters": reencounters_for_opponent(self.state,opponent_players=self._career_players_by_team.get(opponent_id,())),
        }
        performance=live_player_performance(snap,controlled_team_id=controlled)
        names={int(row.get("id") or row.get("source_id") or 0):row.get("display_name") for row in snap.get("controlled_on_pitch") or []}
        snap["controlled_performance"]=[{**row,"name":names.get(int(row["player_id"])) or self._player_name(int(row["player_id"]))} for row in performance]
        assistant_quality=int(self._responsibility_effect("match_preparation").get("quality") or 10)
        snap["bench_advice"]=bench_advice(snap,controlled_team_id=controlled,staff_quality=assistant_quality)
        if str(snap.get("status") or live.get("status"))=="finished":
            familiarity=float((ensure_tactical_plan_state(self.state).get("familiarity") or {}).get("overall") or 62.0)
            snap["diagnosis"]=postmatch_diagnosis(snap,controlled_team_id=controlled,familiarity=familiarity)
        return snap

    def set_live_tactics(self,payload:dict[str,Any])->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        validated=FootballTactics9394(**{**_default_tactics(),**payload});self.set_tactics(payload);self.live_engine.set_controlled_tactics(self.state["live_match"],validated)
        return self.live_match_snapshot()

    def substitute_live_match(self,outgoing_id:int,incoming_id:int)->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        live=self.state["live_match"];snap=self.live_engine.snapshot(live);controlled=int(self.state["team_id"]);own_home=int(snap["home_team_id"])==controlled
        on_pitch=list(snap["home_on_pitch_ids"] if own_home else snap["away_on_pitch_ids"])
        forced_off=list(snap["home_forced_off_ids"] if own_home else snap["away_forced_off_ids"])
        replaceable=on_pitch+forced_off
        if int(outgoing_id) in replaceable:
            candidate=[int(incoming_id) if int(pid)==int(outgoing_id) else int(pid) for pid in replaceable]
            raw=[self._player_source(pid) for pid in candidate if self._player_source(pid) is not None]
            rule=self._foreign_rule_for_fixture(live.get("fixture") or {})
            if rule is not None:
                issues=validate_matchday_foreigners(raw,[],rule)
                if issues: raise ValueError(" ".join(issues))
        home,away=self._live_match_sheets();self.live_engine.substitute(live,home,away,outgoing_id=int(outgoing_id),incoming_id=int(incoming_id));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot()

    def advance_live_match(self,minutes:int=5)->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        home,away=self._live_match_sheets();self.live_engine.advance(self.state["live_match"],home,away,minutes=int(minutes));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot()

    def simulate_live_match(self)->dict[str,Any]:
        """Resolve the minute-zero preview through the same live engine.

        Instant Result must not be a second football model.  Both benches are
        delegated to the AI while the match is simulated so the controlled
        side receives the same fatigue/score-aware substitution behaviour as
        the opponent and the historical two-substitute cap remains enforced.
        """
        live=self.state.get("live_match")
        if not live: raise ValueError("no hay previa de partido preparada")
        if int(live.get("minute") or 0)!=0: raise ValueError("Resultado sólo está disponible antes de comenzar el partido")
        while str(live.get("status"))!="finished":
            home,away=self._live_match_sheets()
            self.live_engine.advance(live,home,away,minutes=45,auto_controlled=True)
        return self.finish_live_match()

    def _commit_preseason_friendly(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];fid=int(fixture["id"]);seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+abs(fid)
        self._apply_match_player_state(result,home_sheet,away_sheet,seed,competition="Pretemporada",record_performance=False)
        stored={"fixture_type":"friendly","id":fid,"season":self.state["season"],"date":fixture["date"],"home_team_id":int(fixture["home_team_id"]),"away_team_id":int(fixture["away_team_id"]),"home_goals":int(result.home.goals),"away_goals":int(result.away.goals)}
        for row in self.state.get("preseason_friendlies") or []:
            if int(row.get("id") or 0)==fid:
                row.update({"played":True,"home_goals":stored["home_goals"],"away_goals":stored["away_goals"]});break
        self.state.setdefault("preseason_history",[]).append(stored);self.state["preseason_history"]=self.state["preseason_history"][-80:]
        self._rebuild_rosters();return stored

    def league_matchday_summary(self, matchday: int | None = None, league_id: int | None = None) -> dict[str, Any]:
        """Return a UI-safe, persisted view of a complete league round.

        The controlled league is committed atomically: when the user's match is
        closed, every other fixture in that round is already resolved.  Keeping
        the round summary derived from those canonical results avoids a second
        score source in the UI and makes Instant Result/manual play equivalent.
        """
        lid=int(league_id if league_id is not None else self.state.get("league_id") or 0)
        round_number=int(matchday if matchday is not None else self.state.get("completed_matchday") or 0)
        league=self.universe.leagues_by_id.get(lid) or {}
        competition_name=str(league.get("name") or (self._team_api(int(self.state["team_id"])) or {}).get("league",{}).get("name") or "Liga")
        if round_number <= 0:
            return {"competition_id":lid,"competition_name":competition_name,"matchday":round_number,"label":"Sin jornada disputada","complete":False,"fixture_count":0,"result_count":0,"results":[]}
        fixtures=[row for row in self._league_schedule(lid) if int(row.get("matchday") or row.get("round") or 0)==round_number]
        if lid==int(self.state.get("league_id") or 0):
            stored=[row for row in self.state.get("results") or [] if int(row.get("matchday") or row.get("round") or 0)==round_number]
        else:
            stored=[row for row in self._league_result_rows(lid) if int(row.get("round") or row.get("matchday") or 0)==round_number]
        by_fixture={int(row.get("fixture_id") or -1):row for row in stored if row.get("fixture_id") is not None}
        fallback={(int(row.get("home_team_id") or 0),int(row.get("away_team_id") or 0)):row for row in stored}
        controlled=int(self.state.get("team_id") or 0)
        rows=[]
        for fixture in sorted(fixtures,key=lambda row:int(row.get("id") or 0)):
            home_id,away_id=int(fixture["home_team_id"]),int(fixture["away_team_id"])
            result=by_fixture.get(int(fixture.get("id") or -1)) or fallback.get((home_id,away_id))
            if result is None:
                continue
            home=self._team_api(home_id);away=self._team_api(away_id)
            hg,ag=int(result.get("home_goals") or 0),int(result.get("away_goals") or 0)
            own=controlled in (home_id,away_id)
            own_result=None
            if own:
                gf,ga=(hg,ag) if home_id==controlled else (ag,hg)
                own_result="W" if gf>ga else "D" if gf==ga else "L"
            rows.append({
                "fixture_id":int(fixture.get("id") or result.get("fixture_id") or 0),
                "date":str(fixture.get("date") or self.state.get("current_date") or ""),
                "home_team_id":home_id,"away_team_id":away_id,
                "home_team":home["name"] if home else str(home_id),"away_team":away["name"] if away else str(away_id),
                "home_goals":hg,"away_goals":ag,"controlled":own,"controlled_result":own_result,
            })
        return {
            "competition_id":lid,"competition_name":competition_name,"matchday":round_number,
            "label":f"Jornada {round_number}","complete":bool(fixtures) and len(rows)==len(fixtures),
            "fixture_count":len(fixtures),"result_count":len(rows),"results":rows,
        }

    def _commit_live_league(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];matchday=int(fixture["matchday"]);league_id=int(self.state["league_id"]);controlled=int(self.state["team_id"])
        if matchday<=int(self.state.get("completed_matchday") or 0): raise ValueError("la jornada del directo ya estaba cerrada")
        calendar=[row for row in self._league_schedule(league_id) if int(row["matchday"])==matchday];results=list(self.state.get("results") or []);season_seed=season_start_year(self.state)*1_000_000
        for fx in calendar:
            h,a=int(fx["home_team_id"]),int(fx["away_team_id"]);seed=season_seed+int(self.state["seed"])*1000+matchday*100+int(fx["id"])
            if int(fx["id"])==int(fixture["id"]):
                r=result;hs,as_=home_sheet,away_sheet
            else:
                hs,as_=self._sheet(h,competition_kind="league"),self._sheet(a,competition_kind="league");r=self.engine.simulate(hs,as_,seed=seed,referee=referee_for_match(league_id,seed=seed),venue=venue_for_team(self.universe,h))
            self._apply_match_player_state(r,hs,as_,seed,competition=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga",counts_for_league_stats=True)
            results.append(_league_match_payload(matchday,int(fx["id"]),h,a,r.home.goals,r.away.goals,referee_id=r.referee_id,referee_name=r.referee_name,referee_source_confidence=r.referee_source_confidence));self._post_matchday_income(h,competition=f"league:{league_id}",reference=matchday)
        self.state["results"]=results;self.state["completed_matchday"]=matchday;self._rebuild_rosters()
        raw=next(row for row in results if int(row.get("fixture_id") or -1)==int(fixture["id"]));return raw

    def finish_live_match(self)->dict[str,Any]:
        live=self.state.get("live_match")
        if not live: raise ValueError("no hay partido en directo")
        if live.get("status")!="finished": raise ValueError("el partido todavía no ha terminado")
        home,away=self._live_match_sheets();result=self.live_engine.result(live);live_report=self.live_match_snapshot();events=[]
        if live["fixture"].get("fixture_type")=="tournament":
            played,events=commit_pending_tournament_result(self,result,home,away)
        elif live["fixture"].get("fixture_type")=="friendly":
            played=self._commit_preseason_friendly(result,home,away,live)
        else:
            raw=self._commit_live_league(result,home,away,live);played={"fixture_type":"league",**raw}
        report={**live_report,"played_match":played,"committed":True,"individual_signatures":match_signature_report(result,home,away)}
        fixture_context=dict(live.get("fixture") or {})
        if fixture_context.get("fixture_type") != "friendly":
            controlled=int(self.state["team_id"]); own_home=int(live["home_team_id"])==controlled
            ai_team_id=int(live["away_team_id"] if own_home else live["home_team_id"])
            ai_goals=int(result.away.goals if own_home else result.home.goals)
            managed_goals=int(result.home.goals if own_home else result.away.goals)
            prep=dict(live.get("ai_preparation") or {})
            manager_id=prep.get("manager_id")
            record_rival_preparation_outcome(
                self.state, manager_id=(int(manager_id) if str(manager_id or "").isdigit() else None), team_id=ai_team_id,
                date_text=self.current_date.isoformat(), preparation=prep, goals_for=ai_goals, goals_against=managed_goals,
                competition_context=fixture_context,
            )
        self.state["live_match"]=None
        self._publish_controlled_result(
            competition=str(fixture_context.get("competition_name") or (self._team_api(int(self.state["team_id"])) or {}).get("league",{}).get("name") or "Partido"),
            home_team_id=int(live["home_team_id"]),away_team_id=int(live["away_team_id"]),home_goals=int(result.home.goals),away_goals=int(result.away.goals),
            fixture_context=fixture_context,
        )
        if events:
            self.state["world_events"].extend(events);self.state["world_events"]=self.state["world_events"][-600:];self._ingest_news(events)
        if fixture_context.get("fixture_type")=="league":
            report["round_summary"]=self.league_matchday_summary(int(fixture_context.get("matchday") or self.state.get("completed_matchday") or 0),int(fixture_context.get("competition_id") or self.state.get("league_id") or 0))
        next_fixture=self.next_scheduled_fixture()
        dashboard=self.manager_dashboard()
        own_row=next((row for row in self.standings() if int(row.get("team_id") or 0)==int(self.state["team_id"])),None)
        report["postmatch_context"]={
            "standings":dict(own_row or {}),
            "morale_average":int(dashboard.get("morale_average") or 0),
            "board_confidence":str(dashboard.get("board_confidence") or "A la espera"),
            "next_match":dict(next_fixture or {}),
            "next_match_absences":self._controlled_absences_for_fixture(next_fixture) if next_fixture else [],
        }
        self.state["last_match_report"]=report
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return {"match":report,"career":self.snapshot()}

    def advance_day(self) -> dict[str, Any]:
        if self.state.get("job_status")=="dismissed":
            return {"advanced":False,"career_over":False,"requires_job_decision":True,"reason":"job_decision","date":self.current_date.isoformat(),"job_offers":manager_profile_snapshot(self.state).get("job_offers") or []}
        if self.state.get("live_match"):
            return {"advanced":False,"requires_match":True,"live_match":self.live_match_snapshot(),"date":self.current_date.isoformat()}
        pending=self.pending_world_fixture()
        if pending:
            return {"advanced":False,"requires_match":True,"next_match":pending,"date":self.current_date.isoformat()}
        fixture=self.next_scheduled_fixture()
        if fixture and self.current_date >= date.fromisoformat(fixture["date"]):
            return {"advanced":False,"requires_match":True,"next_match":fixture,"date":self.current_date.isoformat()}
        tomorrow=self.current_date+timedelta(days=1)
        self.state["current_date"]=tomorrow.isoformat()
        controlled_players=list(self._career_players_by_team.get(int(self.state["team_id"]),()))
        injured_before={int(p["source_id"]) for p in controlled_players if int((self.state.get("player_development") or {}).get(str(int(p["source_id"])),{}).get("injury_days") or 0)>0}
        if recover_one_day(self.state["player_development"], game_date=tomorrow):
            recovered=[pid for pid in injured_before if int((self.state.get("player_development") or {}).get(str(pid),{}).get("injury_days") or 0)==0]
            for pid in recovered:
                register_return_from_injury(self.state,player_id=pid,players=controlled_players,date_text=tomorrow.isoformat())
            self._rebuild_rosters()
        training_fixture = self.next_scheduled_fixture()
        training_next_date = date.fromisoformat(str(training_fixture["date"])) if training_fixture and training_fixture.get("date") else None
        training_events = process_training_day(
            self.state, game_date=tomorrow, players=controlled_players, development=self.state["player_development"],
            effectiveness=self._responsibility_effect("first_team_training"), seed=int(self.state.get("seed") or 9394),
            next_match_date=training_next_date,
        )
        familiarity_session = session_for_date(self.state, game_date=tomorrow, next_match_date=training_next_date)
        if familiarity_session == "match_preparation":
            prep_focus = str((self.state.get("training") or {}).get("match_preparation_focus") or "balanced")
            familiarity_session = {"opponent": "tactical", "attacking": "attack", "defensive": "defence", "set_pieces": "set_pieces"}.get(prep_focus, "match_preparation")
        process_familiarity_day(
            self.state, training_session=familiarity_session,
            training_quality=int(self._responsibility_effect("first_team_training").get("quality") or 10),
        )
        if training_events:
            for event in training_events:
                register_important_injury(self.state, player_id=int(event["player_id"]), days=int(event.get("expected_days") or 0), players=controlled_players, date_text=tomorrow.isoformat())
            self._rebuild_rosters()
            self._ingest_news(training_events)
        # Every background league progresses by its own dated calendar.
        self._process_background_leagues_for_day(tomorrow)
        self._process_controlled_league_byes(tomorrow)
        world_events=list(training_events)
        scout_events = process_scouting_day(
            self.state, game_date=tomorrow, effectiveness=self._responsibility_effect("recruitment_search"),
            player_lookup=self._player_source,
        )
        world_events.extend(scout_events)
        if scout_events:
            self._ingest_news(scout_events)
        summer_from_season=None;summer_started=None
        if tomorrow.month==7 and tomorrow.day==1:
            summer_from_season=str(self.state.get("season") or "")
            summer_started=perf_counter()
            rollover_events=self._rollover_season(tomorrow);world_events.extend(rollover_events)
            if rollover_events:
                self.state["world_events"].extend(rollover_events);self.state["world_events"]=self.state["world_events"][-600:];self._ingest_news(rollover_events)
        world_events.extend(self._process_daily_world(tomorrow))
        if summer_from_season is not None:
            elapsed_ms=round((perf_counter()-(summer_started or perf_counter()))*1000)
            transition=finalize_summer_transition(self,from_season=summer_from_season,date_text=tomorrow.isoformat(),transition_ms=elapsed_ms)
            world_events.append({"kind":"longitudinal_health","date":tomorrow.isoformat(),"season":self.state.get("season"),"status":transition["health"]["status"],"save_megabytes":transition["health"]["save_megabytes"],"transition_ms":elapsed_ms})
        self._repair_selection_after_roster_departures(world_events)
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        pending=self.pending_world_fixture()
        if pending:
            return {"advanced":True,"requires_match":True,"next_match":pending,"date":tomorrow.isoformat(),"world_events":world_events}
        fixture=self.next_scheduled_fixture(); requires=bool(fixture and tomorrow>=date.fromisoformat(fixture["date"]))
        return {"advanced":True,"requires_match":requires,"next_match":fixture,"date":tomorrow.isoformat(),"world_events":world_events}

    def advance_until_event(self, max_days: int = 14) -> dict[str, Any]:
        max_days=max(1,min(62,int(max_days)))
        if self.preseason_snapshot().get("active"): max_days=min(max_days,3)
        dashboard=self.manager_dashboard()
        blocking=list(dashboard.get("blocking_decisions") or [])
        if blocking:
            first=blocking[0]
            return {
                "advanced_days":0,"date":self.current_date.isoformat(),"requires_match":bool(first.get("kind")=="live_match"),
                "requires_job_decision":False,"requires_decision":True,"decision":first,"next_match":self.next_scheduled_fixture(),
                "world_events":[],"career_over":False,"reason":"decision_required","pace":self.preseason_snapshot().get("pace"),
            }
        events=[];days=0;last=None
        for _ in range(max_days):
            last=self.advance_day();events.extend(last.get("world_events") or [])
            if last.get("advanced"): days+=1
            if last.get("career_over") or last.get("requires_match") or not last.get("advanced",False): break
            if any(e.get("kind")=="season_rollover" for e in last.get("world_events") or []): break
            urgent=[d for d in self.manager_dashboard().get("pending_decisions") or [] if d.get("blocking")]
            if urgent: break
        return {"advanced_days":days,"date":self.current_date.isoformat(),"requires_match":bool((last or {}).get("requires_match")),"requires_job_decision":bool((last or {}).get("requires_job_decision")),"requires_decision":False,"decision":None,"next_match":self.next_scheduled_fixture(),"world_events":events,"career_over":bool((last or {}).get("career_over")),"reason":((last or {}).get("reason")),"pace":self.preseason_snapshot().get("pace")}

    def play_next_matchday(self) -> dict[str, Any]:
        if self.state.get("job_status")=="dismissed": raise ValueError("el consejo ha terminado tu etapa en el club")
        if self.state.get("live_match"):
            raise ValueError("hay un partido en directo: termínalo o abandónalo antes de usar resultado instantáneo")
        if self.state.get("pending_world_match"):
            row,events=play_pending_tournament_match(self)
            self._publish_controlled_result(
                competition=str(row.get("competition_name") or "Copa"), home_team_id=int(row["home_team_id"]), away_team_id=int(row["away_team_id"]),
                home_goals=int(row["home_goals"]), away_goals=int(row["away_goals"]), fixture_context={"fixture_type": "tournament", **row},
            )
            if events:
                self.state["world_events"].extend(events)
                self.state["world_events"]=self.state["world_events"][-600:]
                self._ingest_news(events)
            self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
            snapshot=self.snapshot()
            snapshot["played_match"]={"fixture_type":"tournament",**row}
            return snapshot
        scheduled=self.next_scheduled_fixture()
        if scheduled and scheduled.get("fixture_type")=="friendly":
            match_date=date.fromisoformat(str(scheduled["date"]))
            if self.current_date<match_date: self.state["current_date"]=match_date.isoformat()
            issues=self._validate_controlled_selection_for_fixture(scheduled)
            if issues: raise ValueError(" ".join(issues))
            home=self._sheet(int(scheduled["home_team_id"]));away=self._sheet(int(scheduled["away_team_id"]));seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+abs(int(scheduled["id"]))
            result=self.engine.simulate(home,away,seed=seed,venue=venue_for_team(self.universe,int(scheduled["home_team_id"])))
            played=self._commit_preseason_friendly(result,home,away,{"fixture":scheduled})
            self._publish_controlled_result(
                competition="Pretemporada", home_team_id=int(scheduled["home_team_id"]), away_team_id=int(scheduled["away_team_id"]),
                home_goals=int(result.home.goals), away_goals=int(result.away.goals), fixture_context={"fixture_type": "friendly", **scheduled},
            )
            snapshot=self.snapshot();snapshot["played_match"]=played;return snapshot
        fixture = self.next_fixture()
        if fixture is None:
            raise ValueError("la liga ya no tiene jornadas pendientes")
        match_date = date.fromisoformat(fixture["date"])
        if self.current_date < match_date:
            self.state["current_date"] = match_date.isoformat()
        for round_number in range(int(self.state.get("completed_matchday") or 0)+1,int(fixture["matchday"])+1):
            self._simulate_matchday(round_number)
        return self.snapshot()

    def _career_player_api(self, row: dict[str, Any]) -> dict[str, Any]:
        pid = int(row["source_id"])
        api = self.universe.player_api(row, game_date=self.current_date)
        team_id = self._current_team_id(pid)
        team = self.universe.team(team_id)
        api["team_id"] = team_id
        api["team_name"] = team["name"] if team else None
        d = self.state["player_development"].get(str(pid), {})
        api["overall"] = d.get("overall", api.get("overall"))
        base_overall = int(row.get("overall") or row.get("category") or 60)
        overall_delta = int(api["overall"] or base_overall) - base_overall
        physical_delta = int(d.get("physical_delta") or 0)
        technical_delta = int(d.get("technical_delta") or 0)
        specific = dict(d.get("attribute_deltas") or {})
        physical_keys = {"pace","acceleration","stamina","strength","jumping"}
        technical_keys = {"technique","short_pass","long_pass","vision","dribbling","finishing","heading","shot_power","free_kicks","penalties"}
        effective_attrs = {}
        for key, value in dict(api.get("attributes") or {}).items():
            try:
                extra = physical_delta if key in physical_keys else technical_delta if key in technical_keys else 0
                effective_attrs[key] = max(1, min(100, int(value) + overall_delta + extra + int(specific.get(key) or 0)))
            except (TypeError, ValueError):
                effective_attrs[key] = value
        api["attributes"] = effective_attrs
        api["attribute_deltas"] = specific
        api["form"] = d.get("form")
        api["morale"] = d.get("morale")
        api["condition"] = d.get("condition")
        if uses_frozen_age(self.state):
            # Keep the age shown at the historical anchor forever. Birth date is
            # retained for provenance; only the career-facing age is frozen.
            api["age"] = self.universe.player_api(row, game_date=CAREER_START_DATE_9394).get("age")
            api["age_frozen"] = True
        else:
            api["age_frozen"] = False
        api["generated"] = bool(row.get("generated"))
        api["provenance"] = row.get("provenance") or "mdb_source"
        archetype, archetype_detail = player_archetype(row)
        api["identity"] = {"archetype": archetype, "description": archetype_detail, "traits": gameplay_traits(row)}
        plan = FootballTactics9394(**{**_default_tactics(), **(self.state.get("tactics") or {})})
        api["tactical_fit"] = tactical_fit(row, plan)
        api["squad_dynamics"] = dynamics_api(self.state, pid)
        api["manager_relationship"] = relationship_api(self.state, pid) if team_id == int(self.state.get("team_id") or 0) else None
        api["role_promise"] = role_promise_api(self.state, pid) if team_id == int(self.state.get("team_id") or 0) else None
        api["injury_days"] = int(d.get("injury_days") or 0)
        if team_id == int(self.state.get("team_id") or 0):
            api["medical"] = medical_staff_report(
                d, effectiveness=self._responsibility_effect("medical_assessment"),
                game_date=self.current_date, seed=int(self.state.get("seed") or 9394), player_id=pid,
            )
            api["scout"] = {
                "knowledge": "Conocimiento interno", "confidence": "100%",
                "summary": "La evaluación pertenece al cuerpo técnico del club; no consume capacidad de ojeadores.",
                "recommended_role": (api.get("identity") or {}).get("archetype"),
                "tactical_fit": (api.get("tactical_fit") or {}).get("label"),
            }
        else:
            api["medical"] = medical_api(d)
        api["league_suspension_matches"] = int(d.get("league_suspension_matches") or 0)
        api["league_suspension_reason"] = d.get("league_suspension_reason")
        api["league_suspension_active_for_next_match"] = bool(api["league_suspension_matches"] > 0 and self._selection_fixture_kind() == "league")
        if api["injury_days"] > 0:
            injury_name = str((api["medical"].get("current_injury") or {}).get("name") or "Lesión")
            api["status"] = f"{injury_name} · {api['injury_days']} d"
        elif api["league_suspension_active_for_next_match"]:
            api["status"] = f"Sancionado (liga) · {api['league_suspension_matches']} partido" + ("s" if api["league_suspension_matches"] != 1 else "")
        rating_count = int(d.get("season_rating_count") or 0)
        average_rating = round(float(d.get("season_rating_total") or 0.0) / rating_count, 2) if rating_count else None
        api["season_stats"] = {
            "appearances": int(d.get("season_appearances") or 0), "starts": int(d.get("season_starts") or 0), "minutes": int(d.get("season_minutes") or 0),
            "goals": int(d.get("season_goals") or 0), "assists": int(d.get("season_assists") or 0),
            "yellow_cards": int(d.get("season_yellows") or 0), "red_cards": int(d.get("season_reds") or 0),
            "average_rating": average_rating,
        }
        api["match_history"] = list((self.state.get("player_match_history") or {}).get(str(pid), []))[-12:]
        api["career_seasons"] = list((self.state.get("player_season_archive") or {}).get(str(pid), []))
        intl=dict((self.state.get("international_player_stats") or {}).get(str(pid)) or {})
        api["international_stats"]={**intl,"history":list(intl.get("history") or [])[-20:]} if intl else {"caps":0,"starts":0,"goals":0,"assists":0,"tournament_caps":0,"tournament_goals":0,"history":[]}
        contract_override = self.state.get("contract_overrides", {}).get(str(pid))
        api["contract"] = effective_contract(row, overall=int(api["overall"] or 60), override=contract_override)
        api["estimated_transfer_value"] = estimated_transfer_value(row, overall=int(api["overall"] or 60))
        dyn = api["squad_dynamics"]
        api["market"] = market_flags(row, overall=int(api["overall"] or 60), team_id=team_id, contract=api["contract"], current_year=self.current_date.year, wants_move=bool(dyn.get("wants_move")), satisfaction=int(dyn.get("satisfaction") or 70))
        api["watched"] = pid in {int(x) for x in (self.state.get("watchlist") or [])}
        api["transfer_listed"] = str(pid) in (self.state.get("transfer_listings") or {})
        return api

    def _external_player_api(self, row: dict[str, Any]) -> dict[str, Any]:
        pid = int(row["source_id"])
        return external_player_view(
            self.state, api=self._career_player_api(row), player_id=pid, game_date=self.current_date,
            effectiveness=self._responsibility_effect("recruitment_search"),
        )

    def player_detail(self, player_id:int) -> dict[str,Any]:
        pid=int(player_id);row=self._player_source(pid)
        if row is None: raise KeyError(f"jugador {pid} no existe")
        return self._career_player_api(row) if self._current_team_id(pid)==int(self.state["team_id"]) else self._external_player_api(row)

    def team_detail(self, team_id:int) -> dict[str,Any]:
        """Career-aware club card used by cross-entity navigation.

        The static MDB identity is preserved, while league membership, manager,
        squad and table position come from the current career.  External player
        quality is passed through ``player_detail`` so opening another club never
        bypasses the scouting/knowledge model.
        """
        tid=int(team_id);team=self._team_api(tid)
        if team is None: raise KeyError(f"equipo {tid} no existe")
        league_id=self._current_league_for_team(tid)
        standing=None
        if league_id is not None:
            standing=next((row for row in self.league_standings(int(league_id)) if int(row.get("team_id") or 0)==tid),None)
        assignment=(self.state.get("manager_assignments") or {}).get(str(tid))
        if tid==int(self.state.get("team_id") or 0) and str(self.state.get("job_status") or "active")=="active":
            manager={"id":-1,"name":"Tú","user_managed":True}
        else:
            coach=self._coach_profile(tid) or {}
            manager_id=int(assignment) if isinstance(assignment,int) else int(coach.get("source_id") or 0) or None
            manager={
                "id":manager_id,
                "name":str(coach.get("display_name") or (self._manager_name(manager_id) if manager_id is not None else "Sin entrenador")),
                "user_managed":False,
                "profile":coach or None,
            }
        squad=[]
        for raw in self._career_players_by_team.get(tid,[]):
            if raw.get("retired"): continue
            api=self.player_detail(int(raw.get("source_id") or 0))
            squad.append({
                "id":api.get("id"),"display_name":api.get("display_name"),"shirt_number":api.get("shirt_number"),
                "team_id":tid,"team_name":team.get("name"),"position":api.get("position"),"nationality":api.get("nationality"),"status":api.get("status"),
                "overall":api.get("overall"),"overall_range":api.get("overall_range"),"overall_is_exact":api.get("overall_is_exact",True),
            })
        squad.sort(key=lambda row:(row.get("shirt_number") is None,row.get("shirt_number") or 999,row.get("display_name") or ""))
        venue=venue_for_team(self.universe,tid)
        main_rival=self._team_api(int(team.get("main_rival_id") or 0)) if team.get("main_rival_id") else None
        regional_rival=self._team_api(int(team.get("regional_rival_id") or 0)) if team.get("regional_rival_id") else None
        return {
            "team":team,
            "club_status":club_status(self.state,tid),
            "manager":manager,
            "standing":standing,
            "venue":asdict(venue) if venue is not None else None,
            "main_rival":({"id":main_rival.get("source_id"),"name":main_rival.get("name"),"long_name":main_rival.get("long_name")} if main_rival else None),
            "regional_rival":({"id":regional_rival.get("source_id"),"name":regional_rival.get("name"),"long_name":regional_rival.get("long_name")} if regional_rival else None),
            "squad":squad,
            "squad_size":len(squad),
            "controlled":tid==int(self.state.get("team_id") or 0),
            "season":str(self.state.get("season") or "1993-94"),
        }

    def squad(self, team_id: int | None = None) -> list[dict[str, Any]]:
        tid = int(team_id if team_id is not None else self.state["team_id"])
        rows = self._career_players_by_team.get(tid, [])
        return sorted((self._career_player_api(row) for row in rows), key=lambda p: (p.get("shirt_number") is None, p.get("shirt_number") or 999, p.get("display_name") or ""))
























    def standings(self) -> list[dict[str, Any]]:
        matches=[LeagueMatch9394(str(r["home_team_id"]),str(r["away_team_id"]),int(r["home_goals"]),int(r["away_goals"])) for r in self.state.get("results") or []]
        league_id=int(self.state["league_id"]); ids=[str(team["source_id"]) for team in self._teams_for_league(league_id)]
        table=build_league_table(ids,matches,self._league_rules(league_id))
        out=[]
        for row in table:
            team=self._team_api(int(row.team_id))
            out.append({"team_id":int(row.team_id),"team_name":team["name"] if team else row.team_id,
                "position":row.position,"played":row.played,"wins":row.wins,"draws":row.draws,"losses":row.losses,
                "goals_for":row.goals_for,"goals_against":row.goals_against,"goal_difference":row.goal_difference,"points":row.points})
        return out

    def career_calendar(self) -> list[dict[str,Any]]:
        """Calendar of the controlled club, including generated preseason.

        Friendlies are deliberately marked as generated career content.  This
        makes the slower summer rhythm visible without presenting those matches
        as historical real-world fixtures.
        """
        controlled=int(self.state["team_id"]);results_by_fixture={int(r["fixture_id"]):r for r in self.state.get("results") or [] if r.get("fixture_id") is not None}
        out=[]
        for row in self.state.get("preseason_friendlies") or []:
            if str(row.get("season"))!=str(self.state["season"]): continue
            if controlled not in (int(row["home_team_id"]),int(row["away_team_id"])): continue
            home_id,away_id=int(row["home_team_id"]),int(row["away_team_id"])
            out.append({**row,"home_team":(self._team_api(home_id) or {}).get("name",str(home_id)),"away_team":(self._team_api(away_id) or {}).get("name",str(away_id)),
                "competition_name":"Pretemporada","matchday":0,"played":bool(row.get("played")),"home_goals":row.get("home_goals"),"away_goals":row.get("away_goals")})
        league_name=(self.universe.leagues_by_id.get(int(self.state["league_id"])) or {}).get("name") or "Liga"
        for fixture in self._league_schedule():
            if controlled not in (int(fixture["home_team_id"]),int(fixture["away_team_id"])): continue
            home_id,away_id=int(fixture["home_team_id"]),int(fixture["away_team_id"]);result=results_by_fixture.get(int(fixture["id"]))
            out.append({**fixture,"fixture_type":"league","competition_name":league_name,"home_team":(self._team_api(home_id) or {}).get("name",str(home_id)),"away_team":(self._team_api(away_id) or {}).get("name",str(away_id)),
                "played":result is not None,"home_goals":result.get("home_goals") if result else None,"away_goals":result.get("away_goals") if result else None})
        next_fixture=self.next_scheduled_fixture(); next_id=int((next_fixture or {}).get("id") or 0); availability=self._controlled_absences_for_fixture(next_fixture) if next_fixture else []
        if next_id:
            for row in out:
                if int(row.get("id") or 0)==next_id and not row.get("played"):
                    row["availability_count"]=len(availability); row["availability"]=availability
        out.sort(key=lambda row:(str(row.get("date") or "9999-12-31"),int(row.get("id") or 0)))
        return out

    def snapshot(self) -> dict[str, Any]:
        team_id=int(self.state["team_id"]); completed=int(self.state.get("completed_matchday") or 0); last_result=None
        squad_api=self.squad(team_id)
        dashboard=self.manager_dashboard()
        stories=self._refresh_storyline_state(dashboard=dashboard,squad_api=squad_api)
        rivalries=rivalry_snapshot(self.state,self.universe,team_id,limit=8)
        next_fixture=self.next_scheduled_fixture()
        opponent_id=None
        if next_fixture:
            h,a=int(next_fixture.get("home_team_id") or 0),int(next_fixture.get("away_team_id") or 0)
            opponent_id=a if h==team_id else h if a==team_id else None
        reencounters=reencounters_for_opponent(self.state,opponent_players=self._career_players_by_team.get(int(opponent_id or 0),())) if opponent_id else []
        dressing=dressing_room_snapshot(self.state,players=self._career_players_by_team.get(team_id,()),game_date=self.current_date)
        if completed:
            raw=next((r for r in reversed(self.state.get("results") or []) if int(r["matchday"])==completed and team_id in (int(r["home_team_id"]),int(r["away_team_id"]))),None)
            if raw:
                home=self._team_api(int(raw["home_team_id"])); away=self._team_api(int(raw["away_team_id"]))
                last_result={**raw,"home_team":home["name"] if home else str(raw["home_team_id"]),"away_team":away["name"] if away else str(raw["away_team_id"])}
        return {
            "career_id":self.state["career_id"],"season":self.state["season"],"league_id":int(self.state["league_id"]),
            "game_date":self.state["current_date"],"completed_matchday":self.state["completed_matchday"],"total_matchdays":self._controlled_total_rounds(),
            "age_policy":self.state.get("age_policy"),"rules_policy":self.state.get("rules_policy"),"regulatory_integrity":regulatory_integrity_report(self.universe,season=str(self.state.get("season") or "1993-94")),"team":self._team_api(team_id),"squad":squad_api,
            "source_manager":(source_coach_for_team(self.universe,team_id,manager_id=int(self.state.get("controlled_predecessor_manager_id"))) if isinstance(self.state.get("controlled_predecessor_manager_id"),int) and int(self.state.get("controlled_predecessor_manager_id"))>0 else None),
            "venue":default_source_catalog().venue_context((self._team_api(team_id, resolve_league=False) or {}).get("stadium_id")),
            "standings":self.standings(),"next_match":next_fixture,
            "tactics":dict(self.state.get("tactics") or {}),"tactical_identity":tactical_identity_9394(FootballTactics9394(**{**_default_tactics(),**(self.state.get("tactics") or {})})),"selection":self.selection_snapshot(),"manager_dashboard":dashboard,"finances":dict(self.state.get("finances") or {}),"economy":self.economy_snapshot(),
            "transfer_history":list(self.state.get("transfer_history") or []),"ai_transfer_history":list(self.state.get("ai_transfer_history") or [])[-50:],
            "contract_history":list(self.state.get("contract_history") or [])[-50:],"international_history":list(self.state.get("international_history") or [])[-50:],"international_manager":international_manager_snapshot(self.state),"international_tournaments":list(self.state.get("international_tournaments") or [])[-6:],
            "world_progress":{key:{"completed_round":int(value.get("completed_round") or 0),"result_count":len(value.get("results") or [])} for key,value in (self.state.get("world_leagues") or {}).items()},
            "special_progress":special_competition_snapshot(self),"tournament_progress":tournament_snapshot(self),
            "season_archive":list(self.state.get("season_archive") or []),"season_dossiers":list(self.state.get("season_dossiers") or []),"honours":list(self.state.get("honours") or []),
            "club_honours":list((self.state.get("club_honours") or {}).get(str(team_id),[])),"continental_qualifiers":dict(self.state.get("continental_qualifiers") or {}),
            "season_transition_log":list(self.state.get("season_transition_log") or []),"recent_world_events":list(self.state.get("world_events") or [])[-30:],
            "board":self.board_snapshot(persist=False),"news_feed":self.news_snapshot(limit=30),"season_recaps":list(self.state.get("season_recaps") or []),
            "latest_ai_squad_audit":((self.state.get("ai_squad_audits") or [])[-1] if self.state.get("ai_squad_audits") else None),"job_status":self.state.get("job_status") or "active",
            "preseason":self.preseason_snapshot(),"market_period":self.transfer_period_snapshot(),"club_status":self.club_status_snapshot(),"summer_briefing":dict(self.state.get("summer_briefing") or {}),"longitudinal_health":list(self.state.get("longitudinal_health") or [])[-10:],
            "market_flow":self.market_snapshot(),"live_match":self.live_match_snapshot(),"last_match_report":self.state.get("last_match_report"),
            "storylines":stories,
            "storyline_archive":[dict(row) for row in (self.state.get("storylines") or []) if row.get("status")=="resolved"][-40:],
            "rivalries":rivalries,"dressing_room":dressing,"reencounters":reencounters,"career_milestones":milestone_snapshot(self.state,limit=120),"next_match_memory":contextual_milestones(self.state,team_id=team_id,opponent_team_id=opponent_id,limit=5) if opponent_id else contextual_milestones(self.state,team_id=team_id,limit=5),"staff":self.staff_snapshot(),"staff_reports":self.staff_reports_snapshot(),"scouting":self.scouting_snapshot(),"squad_plan":self.squad_plan_snapshot(),"training":self.training_snapshot(),"tactical_plan":self.tactical_plan_snapshot(),"match_briefing":self.match_briefing_snapshot(),"career_records":records_snapshot(self.state),"user_manager":manager_profile_snapshot(self.state),
            "professional_career":self._professional_career_view(),"board_project":project_snapshot(self.state,team_id),"information_world":information_snapshot(self.state,limit=60),
            "manager_world":{"history":list(self.state.get("manager_history") or [])[-40:],"pressure":dict(self.state.get("manager_pressure") or {}),"unemployed_count":len(self.state.get("manager_unemployed") or [])},
            "result_count":len(self.state.get("results") or []),"last_controlled_result":last_result,
        }

