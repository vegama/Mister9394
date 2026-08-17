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
from typing import Any
from uuid import uuid4

from .career_market import estimated_transfer_value, initial_finances, matchday_income, negotiate_transfer
from .career_economy import (
    apply_monthly_club_finances,
    effective_contract,
    inferred_annual_salary,
    initial_club_finances,
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
from .career_performance import ensure_performance_state, record_managed_match, archive_managed_season
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
from .user_manager_career import ensure_user_manager_state, manager_profile_snapshot, update_reputation_after_match, close_current_tenure, open_new_tenure, set_job_offers, accept_offer as accept_user_manager_offer
from .career_professional import (
    ensure_professional_state, professional_snapshot, update_country_reputation, adjust_club_relationship,
    build_manager_contract, register_contract, close_contract, job_suitability, application_interview, expire_job_market,
)
from .board_project import ensure_board_project, update_board_project, submit_board_request, project_snapshot, register_sale_income
from .information_world import ensure_information_state, register_information_event, process_information_day, information_snapshot, add_reaction
from .economy_longitudinal import ensure_longitudinal_economy, monthly_revenue_mix, post as post_long_economy, season_prize_money, financial_health, longitudinal_snapshot, register_structural_event
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

CAREER_SCHEMA_9394 = 22
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
        return {
            "source_id": tid, "name": team.get("name"), "long_name": team.get("long_name"),
            "initials": team.get("initials"), "squad_size": len(players), "average_top_11": average,
            "members": team.get("members"), "budget": team.get("budget"), "debt": team.get("debt"),
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

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def path_for(self, career_id: str) -> Path:
        safe = "".join(ch for ch in str(career_id) if ch.isalnum() or ch in "-_")
        if not safe:
            raise ValueError("career_id inválido")
        return self.root / f"{safe}.json"

    def save(self, state: dict[str, Any]) -> Path:
        state["schema"] = CAREER_SCHEMA_9394
        path = self.path_for(str(state.get("career_id") or ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return path

    def load(self, career_id: str) -> dict[str, Any]:
        payload = json.loads(self.path_for(career_id).read_text(encoding="utf-8"))
        schema = int(payload.get("schema") or 0)
        if schema < 1 or schema > CAREER_SCHEMA_9394:
            raise ValueError("save de carrera Míster 93/94 incompatible")
        return payload


class _CareerUniverseView:
    """Tiny adapter consumed by `build_snapshot_team_sheet`.

    Matchday views normally expose only available footballers.  The all-roster
    variant exists solely for AI emergency selection: if temporary injuries
    make a quota-legal XI impossible, an AI club may risk one of its own
    injured players rather than violate competition rules or crash the world.
    """
    def __init__(self, runtime: "ManagerCareerRuntime9394", *, include_injured: bool = False):
        self.runtime = runtime
        self.players_by_team = runtime._career_players_by_team if include_injured else runtime._match_players_by_team

    def team(self, team_id: int):
        return self.runtime._team_api(team_id)

    def teams(self, *, league_id: int | None = None):
        return self.runtime._teams_for_league(league_id) if league_id is not None else [self.runtime._team_api(int(t["source_id"])) for t in self.runtime.universe.payload.get("teams", [])]


class ManagerCareerRuntime9394:
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
        self.state.setdefault("finances", initial_finances(team))
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
        ensure_professional_state(self.state, team=team)
        ensure_information_state(self.state)
        ensure_longitudinal_economy(self.state)
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
            tid = str(int(club["source_id"]))
            baseline = initial_club_finances(club)
            existing = club_finances.get(tid)
            club_finances[tid] = {**baseline, **(existing or {})}
        controlled_key = str(int(self.state["team_id"]))
        # Migrate v1/v2 saves: the user's richer ledger remains authoritative.
        club_finances[controlled_key] = {**club_finances.get(controlled_key, {}), **(self.state.get("finances") or {})}
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
            "finances": initial_finances(team), "economy_ledger": [],
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

    def _auto_selection(self) -> dict[str, list[int]]:
        tactics = FootballTactics9394(**{**_default_tactics(), **(self.state.get("tactics") or {})})
        controlled=int(self.state["team_id"]);rule=self._domestic_foreign_rule(controlled)
        predicate=(lambda row:is_foreign_player(
            row,home_country_id=rule.home_country_id,continental=False,
            domestic_equivalent_country_ids=rule.domestic_equivalent_country_ids,
        )) if rule is not None else None
        sheet = build_snapshot_team_sheet(self._career_universe, controlled, tactics=tactics,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None))
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
            players=sorted(self._match_players_by_team.get(int(self.state["team_id"]), []), key=lambda p:(-int(p.get("overall") or p.get("category") or 0),int(p.get("source_id") or 0)))
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
        issues: list[str] = []; warnings: list[str] = []
        if len(starter_ids) != LAWS_1993_94.players_per_team: issues.append("El once debe tener exactamente 11 jugadores.")
        if len(starter_ids) != len(set(starter_ids)): issues.append("Hay jugadores repetidos en el once.")
        if any(pid not in owned for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador que no pertenece al club.")
        if any(pid not in available for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador lesionado o no disponible.")
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
            candidates = [int(p["source_id"]) for p in sorted(self._match_players_by_team.get(int(self.state["team_id"]), []), key=lambda p: -int(p.get("overall") or p.get("category") or 0)) if int(p["source_id"]) not in set(starters)]
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
            amount=int(request.get("amount") or 0); self.state["finances"]["cash"]=int(self.state["finances"].get("cash") or 0)+amount; self.state["club_finances"][str(team_id)]=self.state["finances"]
            self.state["economy_ledger"].append({"date":self.current_date.isoformat(),"kind":"board_injection","amount":amount})
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="board_injections",amount=amount)
        publish_news(self.state,key=f"board-request:{request['id']}",date=self.current_date.isoformat(),category="Club",importance=3 if request.get("status")=="accepted" else 2,headline=("El consejo respalda tu petición" if request.get("status")=="accepted" else "El consejo rechaza tu petición"),detail=str(request.get("reason") or ""),entity={"team_id":team_id})
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return {"request":request,"project":self.board_project_snapshot(),"economy":self.economy_snapshot()}

    def staff_snapshot(self) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id, "name": self._team_name(team_id)}
        return club_staff_snapshot(
            self.state, team=team, strength=self._team_strength(team_id), game_date=self.current_date,
        )

    def set_staff_responsibility(self, responsibility_key: str, assignee: str) -> dict[str, Any]:
        team_id = int(self.state["team_id"])
        team = self._team_api(team_id) or self.universe.team(team_id) or {"source_id": team_id, "name": self._team_name(team_id)}
        return assign_staff_responsibility(
            self.state, team=team, strength=self._team_strength(team_id),
            responsibility_key=responsibility_key, assignee=assignee, game_date=self.current_date,
        )

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
        return build_training_snapshot(
            self.state, players=list(self._career_players_by_team.get(controlled, [])),
            development=self.state["player_development"], effectiveness=self._responsibility_effect("first_team_training"),
            game_date=self.current_date, next_match_date=next_date,
        )

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
        return {"fixture":dict(fixture),"opponent":{"team_id":opponent,"team_name":self._team_name(opponent),"manager":self._coach_profile(opponent)},"report":report,"known_tactics":tactics,"threats":threats,"absences":absences[:8],"own_risk":own_risk[:6],"tactical_familiarity":tactical.get("familiarity"),"preparation_focus":prep_focus,"recommendation":recommendation}

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
            if row.get("kind")=="competition_completed" and not row.get("competition_name"):
                sid=int(row.get("source_id") or 0)
                comp=next((c for c in self.universe.career_competitions() if int(c.get("source_id") or -1)==sid and c.get("kind")=="tournament"),None)
                if comp: row["competition_name"]=comp.get("name")
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
        unavailable = [p for p in squad if int(p.get("injury_days") or 0) > 0 or p.get("status") == "Retirado"]
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
        return {"position": own.get("position"), "team_count": len(table), "points": own.get("points", 0), "recent_form": recent, "form_label": form_label, "morale_average": morale, "unavailable_count": len(unavailable), "board_expectation": expectation, "board_confidence": confidence, "board":board, "pending_decisions": pending, "next_match": self.next_scheduled_fixture(), "preseason":self.preseason_snapshot(), "market_period":self.transfer_period_snapshot(), "club_status":self.club_status_snapshot()}

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
        points = 0
        for row in rows[-max(1, int(limit)):]:
            home = int(row.get("home_team_id") or 0) == int(team_id)
            mine = int(row.get("home_goals") or 0) if home else int(row.get("away_goals") or 0)
            theirs = int(row.get("away_goals") or 0) if home else int(row.get("home_goals") or 0)
            points += 3 if mine > theirs else 1 if mine == theirs else 0
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
        self.state["finances"]=self.state["club_finances"].setdefault(str(new_team),initial_club_finances(self.universe.team(new_team) or {}))
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

    def _sheet(self, team_id: int, tactics: dict[str, Any] | None = None, *, foreign_rule=None) -> TeamSheet9394:
        controlled = int(team_id) == int(self.state["team_id"])
        tactical_payload = dict(tactics) if tactics is not None else None
        if controlled:
            tactical_payload = engine_tactics_payload(tactical_payload or {**_default_tactics(), **(self.state.get("tactics") or {})}, self.state)
        tactical = FootballTactics9394(**tactical_payload) if tactical_payload is not None else None
        coach_profile = None if controlled else self._coach_profile(int(team_id))
        if tactical is None and not controlled:
            tactical = ai_tactics_for_squad(self._match_players_by_team.get(int(team_id), ()), coach_profile)
        if controlled and self.state.get("selection"):
            selected = self.selection_snapshot()
            if not selected["valid"]:
                raise ValueError("El once del mánager no es válido: " + " ".join(selected["issues"]))
            by_id = {int(row["source_id"]): row for row in self._match_players_by_team.get(int(team_id), [])}
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
            sheet = build_snapshot_team_sheet(self._career_universe, team_id, tactics=tactical,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None),allow_emergency_outfield_goalkeeper=True,coach_profile=coach_profile)
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
            sheet = build_snapshot_team_sheet(self._all_career_universe, team_id, tactics=tactical,foreign_predicate=predicate,max_foreign_starters=(rule.max_starting if rule else None),max_foreign_squad=(rule.max_squad if rule else None),allow_emergency_outfield_goalkeeper=True,coach_profile=coach_profile)
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

    def _apply_match_player_state(self, result, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, seed: int, *, competition: str = "Partido", record_performance: bool = True) -> None:
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
            record_managed_match(self.state, result=result, home_sheet=home_sheet, away_sheet=away_sheet, competition=competition, match_date=self.state.get("current_date"))

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
        finances = self.state["club_finances"].setdefault(str(int(home_team_id)), initial_club_finances(team))
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
            home_sheet, away_sheet = self._sheet(home_id, home_tactics), self._sheet(away_id, away_tactics)
            match_seed = season_seed + int(self.state["seed"]) * 1000 + int(matchday) * 100 + int(fixture["id"])
            referee = referee_for_match(league_id, seed=match_seed)
            result = self.engine.simulate(home_sheet, away_sheet, seed=match_seed, referee=referee, venue=venue_for_team(self.universe, home_id))
            self._apply_match_player_state(result, home_sheet, away_sheet, match_seed, competition=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga")
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
        team=self._team_api(int(champion_team_id)) or self.universe.team(int(champion_team_id)) or {}
        return {
            "season": str(self.state["season"]), "competition_kind": competition_kind,
            "source_id": int(source_id), "competition_name": name,
            "team_id": int(champion_team_id), "team_name": team.get("name") or str(champion_team_id),
            "honour": "Campeón",
        }

    def _archive_honours(self, tables: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        honours: list[dict[str, Any]]=[]
        for source_id,table in tables.items():
            if not table:
                continue
            comp=self.universe.leagues_by_id.get(int(source_id)) or {}
            honours.append(self._honour(competition_kind="league",source_id=source_id,name=str(comp.get("name") or f"Liga {source_id}"),champion_team_id=int(table[0]["team_id"])))
        for key,special in (self.state.get("special_competitions") or {}).items():
            champion=special.get("champion_team_id")
            if champion:
                honours.append(self._honour(competition_kind="league",source_id=int(key),name=str(special.get("name") or f"Liga {key}"),champion_team_id=int(champion)))
        for key,tournament in (self.state.get("daily_tournaments") or {}).items():
            champion=tournament.get("champion_team_id")
            if champion:
                honours.append(self._honour(competition_kind="tournament",source_id=int(key),name=str(tournament.get("name") or f"Torneo {key}"),champion_team_id=int(champion)))
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
        european=(14,31,13,4,5,32,1,38)
        champions=[]; uefa=[]
        for lid in european:
            table=tables.get(lid) or []
            if table:
                champions.append(int(table[0]["team_id"])); uefa.extend(int(row["team_id"]) for row in table[1:3])
        if len(champions)!=8 or len(uefa)!=16:
            raise ValueError("no se pudieron reconstruir las plazas europeas para la nueva temporada")
        cwc=[int(x) for x in self.universe.payload.get("tournament_participants",{}).get("90",())]
        copa=((self.state.get("daily_tournaments") or {}).get("3") or {}).get("champion_team_id")
        if copa:
            spanish=[tid for tid in cwc if ((self.universe.team(int(tid)) or {}).get("league") or {}).get("country") == "España"]
            if spanish:
                cwc=[int(copa) if tid==spanish[0] else tid for tid in cwc]
            elif int(copa) not in cwc:
                cwc[-1]=int(copa)
        return {"1":champions,"2":uefa,"90":list(dict.fromkeys(cwc))}

    def _build_season_recap(self, *, season: str, tables: dict[int,list[dict[str,Any]]], honours: list[dict[str,Any]], movements: list[dict[str,Any]], qualifiers: dict[str,list[int]]) -> dict[str,Any]:
        controlled=int(self.state["team_id"]);league_id=int(self.state["league_id"]);table=tables.get(league_id) or self.standings()
        row=next((r for r in table if int(r.get("team_id") or 0)==controlled),{})
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
                finances=self.state["club_finances"].setdefault(str(tid),initial_club_finances(self.universe.team(tid) or {}))
                finances["cash"]=int(finances.get("cash") or 0)+prize
                finances["prize_income"]=int(finances.get("prize_income") or 0)+prize
                post_long_economy(self.state,team_id=tid,season=old_season,category="prize_money",amount=prize)
                if tid==controlled:
                    self.state["finances"]=finances
                    self.state["economy_ledger"].append({"date":day.isoformat(),"kind":"prize_money","amount":prize,"league_id":int(lid),"position":int(row.get("position") or 0)})
        recap=self._build_season_recap(season=old_season,tables=tables,honours=honours,movements=movements,qualifiers=qualifiers)
        archive={
            "season":old_season,"closed_on":day.isoformat(),"honours":honours,"movements":movements,
            "continental_qualifiers":qualifiers,"managed_club":recap,"club_status_changes":status_changes,
            "league_tables":{str(lid):table for lid,table in tables.items()},
        }
        self.state["season_archive"].append(archive);self.state["season_recaps"].append(recap);self.state["season_recaps"]=self.state["season_recaps"][-20:]
        for honour in honours:
            publish_news(self.state,key=f"honour:{old_season}:{honour['competition_kind']}:{honour['source_id']}",date=day.isoformat(),category="Competiciones",importance=5,headline=f"{honour['team_name']} campeón de {honour['competition_name']}",detail=f"Palmarés de la temporada {old_season}.",entity={"team_id":honour["team_id"],"competition_id":honour["source_id"]})
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
                entity={"team_id":tid,"competition_id":to_lid},
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
            finances = self.state["club_finances"].setdefault(str(team_id), initial_club_finances(team))
            stature=float(club_status(self.state, int(team_id)).get("score") or 50.0)
            posting = apply_monthly_club_finances(
                team=team, finances=finances,
                players=self._career_players_by_team.get(team_id, []),
                development=self.state["player_development"], contract_overrides=self.state["contract_overrides"],
                stature_score=stature,
            )
            mix=monthly_revenue_mix(team=team,club_score=stature,month=day.month); weight=max(1,sum(mix.values())); commercial=int(posting.get("commercial_income") or 0)
            allocated={key:round(commercial*value/weight) for key,value in mix.items()}
            drift=commercial-sum(allocated.values()); allocated["sponsorship"]=int(allocated.get("sponsorship") or 0)+drift
            for category,amount in allocated.items(): post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category=category,amount=int(amount))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="wages",amount=int(posting.get("wage_expense") or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="operations",amount=int(posting.get("operating_expense") or 0))
            post_long_economy(self.state,team_id=team_id,season=str(self.state["season"]),category="debt_service",amount=int(posting.get("debt_service") or 0))
            if int(finances.get("cash") or 0)<0:
                draw=abs(int(finances.get("cash") or 0))+max(500_000,round((int(posting.get("wage_expense") or 0)+int(posting.get("operating_expense") or 0))*0.35))
                finances["debt"]=int(finances.get("debt") or 0)+draw; finances["cash"]=int(finances.get("cash") or 0)+draw
                event={"kind":"financial_restructuring","date":day.isoformat(),"team_id":team_id,"amount":draw,"debt":int(finances["debt"])}; events.append(event)
            if team_id == int(self.state["team_id"]):
                self.state["finances"] = finances
                self.state["economy_ledger"].append({"date": day.isoformat(), "kind": "monthly_operations", "amount":int(posting.get("net") or 0), **posting})
                if events and events[-1].get("kind")=="financial_restructuring" and int(events[-1].get("team_id") or 0)==team_id:
                    self.state["economy_ledger"].append({"date":day.isoformat(),"kind":"debt_draw","amount":int(events[-1]["amount"])})
        renewals = renew_ai_contracts(
            current_date=day, controlled_team_id=int(self.state["team_id"]),
            players_by_team=self._career_players_by_team, development=self.state["player_development"],
            contract_overrides=self.state["contract_overrides"], seed=int(self.state["seed"]),
            max_renewals=max(1, len(active_ids)), eligible_team_ids=active_ids,
        )
        self.state["ai_contract_history"].extend(renewals); events.extend(renewals)
        activity=max((market_activity_budget(transfer_period_status(day,country_id=self._club_country_id(tid),season=str(self.state["season"]))) for tid in active_ids),default=0)
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
            max_deals=first_budget,
            signing_allowed=lambda buyer,player:self._signing_eligibility(int(buyer),player,day=day)[0],
            attraction_score=lambda buyer,seller,player:(float(club_status(self.state,int(buyer)).get("score") or 50)-float(club_status(self.state,int(seller)).get("score") or 50))/25.0,
            foreign_limit_getter=lambda tid:(self._domestic_foreign_rule(int(tid)).max_starting if self._domestic_foreign_rule(int(tid)) is not None else None),
            foreign_predicate=lambda tid,player:self._is_domestic_foreign(int(tid),player),
            coach_profile_getter=lambda tid: self._coach_profile(int(tid)),
        )
        follow_up=[]
        if transfers and activity>first_budget:
            # Recompute after the first deals.  A seller that has just lost a
            # useful footballer can now become a buyer in the same market pulse.
            follow_up=run_ai_transfer_window(
                current_date=day,controlled_team_id=int(self.state["team_id"]),eligible_team_ids=active_ids,
                players_by_team=self._career_players_by_team,seller_team_ids=active_ids+self._market_container_ids(),
                seller_release_exempt_ids=set(self._market_container_ids()),development=self.state["player_development"],club_finances=self.state["club_finances"],
                player_team_overrides=self.state["player_team_overrides"],contract_overrides=self.state["contract_overrides"],seed=int(self.state["seed"])^0x717,
                max_deals=activity-first_budget,signing_allowed=lambda buyer,player:self._signing_eligibility(int(buyer),player,day=day)[0],
                attraction_score=lambda buyer,seller,player:(float(club_status(self.state,int(buyer)).get("score") or 50)-float(club_status(self.state,int(seller)).get("score") or 50))/25.0,
                foreign_limit_getter=lambda tid:(self._domestic_foreign_rule(int(tid)).max_starting if self._domestic_foreign_rule(int(tid)) is not None else None),
                foreign_predicate=lambda tid,player:self._is_domestic_foreign(int(tid),player),
                coach_profile_getter=lambda tid:self._coach_profile(int(tid)),
            )
            register_replacement_chain(self.state,day=day,first_deals=transfers,follow_up_deals=follow_up)
        transfers.extend(follow_up)
        self.state["ai_transfer_history"].extend(transfers); events.extend(transfers)
        if transfers:
            self._rebuild_rosters()
            refresh_recruitment_plans(self.state,current_date=day,team_ids=active_ids,players_by_team=self._career_players_by_team,development=self.state["player_development"],contracts=self.state["contract_overrides"],club_finances=self.state["club_finances"],coach_profile_getter=lambda tid:self._coach_profile(int(tid)))
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
        home=self._sheet(home_id,home_t,foreign_rule=home_rule);away=self._sheet(away_id,away_t,foreign_rule=away_rule)
        return home,away

    def start_live_match(self) -> dict[str,Any]:
        if self.state.get("job_status")=="dismissed": raise ValueError("el consejo ha terminado tu etapa en el club")
        if self.state.get("live_match"):
            return self.live_match_snapshot()
        fixture=self.pending_world_fixture() or self.next_scheduled_fixture()
        if fixture is None: raise ValueError("no hay próximo partido")
        foreign_issues=self._validate_controlled_selection_for_fixture(fixture)
        if foreign_issues: raise ValueError(" ".join(foreign_issues))
        match_date=date.fromisoformat(str(fixture.get("date") or self.current_date.isoformat()))
        if self.current_date<match_date: raise ValueError("todavía no es día de partido")
        controlled=int(self.state["team_id"]);home_id=int(fixture["home_team_id"]);away_id=int(fixture["away_team_id"])
        tactics=dict(self.state.get("tactics") or _default_tactics())
        home_rule=self._foreign_rule_for_fixture(fixture,home_id) if fixture.get("fixture_type")=="tournament" else None
        away_rule=self._foreign_rule_for_fixture(fixture,away_id) if fixture.get("fixture_type")=="tournament" else None
        home_sheet=self._sheet(home_id,tactics if home_id==controlled else None,foreign_rule=home_rule)
        away_sheet=self._sheet(away_id,tactics if away_id==controlled else None,foreign_rule=away_rule)

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

    def live_match_snapshot(self) -> dict[str,Any]|None:
        live=self.state.get("live_match")
        if not live: return None
        snap=self.live_engine.snapshot(live); home_sheet,away_sheet=self._live_match_sheets()
        player_map={int(p.id):p for p in (*home_sheet.starters,*home_sheet.bench,*away_sheet.starters,*away_sheet.bench) if str(p.id).isdigit()}
        controlled=int(self.state["team_id"]); own_home=int(snap["home_team_id"])==controlled
        on_pitch=snap["home_on_pitch_ids"] if own_home else snap["away_on_pitch_ids"];bench=snap["home_bench_ids"] if own_home else snap["away_bench_ids"];fatigue=snap["home_fatigue"] if own_home else snap["away_fatigue"]
        def player_row(pid:int)->dict[str,Any]:
            raw=self._player_source(int(pid)); api=self._career_player_api(raw) if raw else {"id":pid,"display_name":getattr(player_map.get(pid),"name",str(pid)),"position":getattr(player_map.get(pid),"position","")}
            api["match_fatigue"]=round(float(fatigue.get(str(pid),0.0)),1);api["match_condition"]=max(0,round(100-float(fatigue.get(str(pid),0.0))))
            return api
        snap["controlled_on_pitch"]=[player_row(pid) for pid in on_pitch];snap["controlled_bench"]=[player_row(pid) for pid in bench]
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
        snap["opponent_context"] = {
            "team_id": opponent_id,
            "team_name": snap["away_team_name"] if own_home else snap["home_team_name"],
            "manager": self._coach_profile(opponent_id),
            "tactics": known_tactics,
            "preparation": dict(live.get("ai_preparation") or {}),
            "report": report_effect,
            "key_players": key_rows,
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
        if int(outgoing_id) in on_pitch:
            candidate=[int(incoming_id) if int(pid)==int(outgoing_id) else int(pid) for pid in on_pitch]
            raw=[self._player_source(pid) for pid in candidate if self._player_source(pid) is not None]
            rule=self._foreign_rule_for_fixture(live.get("fixture") or {})
            if rule is not None:
                issues=validate_matchday_foreigners(raw,[],rule)
                if issues: raise ValueError(" ".join(issues))
        home,away=self._live_match_sheets();self.live_engine.substitute(live,home,away,outgoing_id=int(outgoing_id),incoming_id=int(incoming_id));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot()

    def advance_live_match(self,minutes:int=5)->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        home,away=self._live_match_sheets();self.live_engine.advance(self.state["live_match"],home,away,minutes=int(minutes));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot()

    def _commit_preseason_friendly(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];fid=int(fixture["id"]);seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+abs(fid)
        self._apply_match_player_state(result,home_sheet,away_sheet,seed,competition="Pretemporada",record_performance=False)
        stored={"fixture_type":"friendly","id":fid,"season":self.state["season"],"date":fixture["date"],"home_team_id":int(fixture["home_team_id"]),"away_team_id":int(fixture["away_team_id"]),"home_goals":int(result.home.goals),"away_goals":int(result.away.goals)}
        for row in self.state.get("preseason_friendlies") or []:
            if int(row.get("id") or 0)==fid:
                row.update({"played":True,"home_goals":stored["home_goals"],"away_goals":stored["away_goals"]});break
        self.state.setdefault("preseason_history",[]).append(stored);self.state["preseason_history"]=self.state["preseason_history"][-80:]
        self._rebuild_rosters();return stored

    def _commit_live_league(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];matchday=int(fixture["matchday"]);league_id=int(self.state["league_id"]);controlled=int(self.state["team_id"])
        if matchday<=int(self.state.get("completed_matchday") or 0): raise ValueError("la jornada del directo ya estaba cerrada")
        calendar=[row for row in self._league_schedule(league_id) if int(row["matchday"])==matchday];results=list(self.state.get("results") or []);season_seed=season_start_year(self.state)*1_000_000
        for fx in calendar:
            h,a=int(fx["home_team_id"]),int(fx["away_team_id"]);seed=season_seed+int(self.state["seed"])*1000+matchday*100+int(fx["id"])
            if int(fx["id"])==int(fixture["id"]):
                r=result;hs,as_=home_sheet,away_sheet
            else:
                hs,as_=self._sheet(h),self._sheet(a);r=self.engine.simulate(hs,as_,seed=seed,referee=referee_for_match(league_id,seed=seed),venue=venue_for_team(self.universe,h))
            self._apply_match_player_state(r,hs,as_,seed,competition=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga")
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
        report={**live_report,"played_match":played,"committed":True,"individual_signatures":match_signature_report(result,home,away)};self.state["last_match_report"]=report
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
        if tomorrow.month==7 and tomorrow.day==1:
            rollover_events=self._rollover_season(tomorrow);world_events.extend(rollover_events)
            if rollover_events:
                self.state["world_events"].extend(rollover_events);self.state["world_events"]=self.state["world_events"][-600:];self._ingest_news(rollover_events)
        world_events.extend(self._process_daily_world(tomorrow))
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
        events=[];days=0;last=None
        for _ in range(max_days):
            last=self.advance_day();events.extend(last.get("world_events") or [])
            if last.get("advanced"): days+=1
            if last.get("career_over") or last.get("requires_match") or not last.get("advanced",False): break
            if any(e.get("kind")=="season_rollover" for e in last.get("world_events") or []): break
            urgent=[d for d in self.manager_dashboard().get("pending_decisions") or [] if d.get("priority")=="high" and d.get("kind") in {"transfer_counters","incoming_offers","live_match","squad_depth"}]
            if urgent: break
        return {"advanced_days":days,"date":self.current_date.isoformat(),"requires_match":bool((last or {}).get("requires_match")),"requires_job_decision":bool((last or {}).get("requires_job_decision")),"next_match":self.next_scheduled_fixture(),"world_events":events,"career_over":bool((last or {}).get("career_over")),"reason":((last or {}).get("reason")),"pace":self.preseason_snapshot().get("pace")}

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
        if api["injury_days"] > 0:
            injury_name = str((api["medical"].get("current_injury") or {}).get("name") or "Lesión")
            api["status"] = f"{injury_name} · {api['injury_days']} d"
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

    def squad(self, team_id: int | None = None) -> list[dict[str, Any]]:
        tid = int(team_id if team_id is not None else self.state["team_id"])
        rows = self._career_players_by_team.get(tid, [])
        return sorted((self._career_player_api(row) for row in rows), key=lambda p: (p.get("shirt_number") is None, p.get("shirt_number") or 999, p.get("display_name") or ""))

    def search_market(self, query: str = "", *, limit: int = 20, position: str = "", free_agents: bool = False, watched: bool = False) -> list[dict[str, Any]]:
        q = " ".join(query.casefold().split()); pos = str(position or "").upper()
        controlled = int(self.state["team_id"]); watched_ids = {int(x) for x in (self.state.get("watchlist") or [])}
        rows = []
        for row in self._all_player_rows():
            pid=int(row["source_id"]); team_id=self._current_team_id(pid)
            if team_id == controlled or row.get("retired") or bool((self.state.get("player_development", {}).get(str(pid)) or {}).get("retired")):
                continue
            if q and q not in str(row.get("display_name") or "").casefold():
                continue
            role=role_for_player(row)
            if pos and pos not in {str(row.get("broad_position") or "").upper(), str(row.get("position") or "").upper(),role.code.upper(),role.name.upper(),role.squad_slot.upper()}:
                continue
            if free_agents and team_id != 0:
                continue
            if watched and pid not in watched_ids:
                continue
            rows.append(row)
        cash=max(0, int((self.state.get("finances") or {}).get("cash") or 0))
        def market_order(player: dict[str, Any]) -> tuple[int, int, int, int]:
            pid=int(player["source_id"])
            overall=int(self.state["player_development"].get(str(pid), {}).get("overall") or player.get("overall") or player.get("category") or 0)
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
        rows.sort(key=market_order)
        return [self._external_player_api(row) for row in rows[:max(1, min(int(limit), 100))]]

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
            buyer_cash=int(self.state["finances"]["cash"]), fee_offer=int(fee_offer),
            salary_offer=int(salary_offer), contract_years=int(contract_years),
        )
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
            buyer_fin["cash"] -= int(decision["fee"])
            buyer_fin["transfer_spend"] = int(buyer_fin.get("transfer_spend") or 0) + int(decision["fee"])
            if seller and str(seller) in self.state["club_finances"]:
                seller_fin = self.state["club_finances"][str(seller)]
                seller_fin["cash"] += int(decision["fee"])
                seller_fin["transfer_income"] = int(seller_fin.get("transfer_income") or 0) + int(decision["fee"])
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
        if total_cost>int(buyer_fin.get("cash") or 0): raise ValueError("ya no hay caja suficiente para completar el fichaje")
        self.state["player_team_overrides"][str(pid)]=controlled
        buyer_fin["cash"]-=total_cost; buyer_fin["transfer_spend"]=int(buyer_fin.get("transfer_spend") or 0)+int(fee)
        if seller and str(seller) in self.state["club_finances"]:
            seller_fin=self.state["club_finances"][str(seller)]; seller_fin["cash"]+=int(fee); seller_fin["transfer_income"]=int(seller_fin.get("transfer_income") or 0)+int(fee)
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
        if int(loan_fee)>int(buyer_fin.get("cash") or 0): raise ValueError("no hay caja suficiente para completar la cesión")
        raw=self._player_source(pid) or {}
        overall=int(self.state.get("player_development",{}).get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        previous_override=(self.state.get("contract_overrides") or {}).get(str(pid))
        current_contract=effective_contract(raw,overall=overall,override=previous_override)
        previous_team_override=(self.state.get("player_team_overrides") or {}).get(str(pid))
        end_year=self.current_date.year+1 if self.current_date.month>=7 else self.current_date.year
        ends_on=date(end_year,6,30)
        buyer_fin["cash"]-=int(loan_fee); buyer_fin["transfer_spend"]=int(buyer_fin.get("transfer_spend") or 0)+int(loan_fee)
        if str(seller) in self.state.get("club_finances",{}):
            seller_fin=self.state["club_finances"][str(seller)]; seller_fin["cash"]+=int(loan_fee); seller_fin["transfer_income"]=int(seller_fin.get("transfer_income") or 0)+int(loan_fee)
        borrower_salary=round(int(current_contract.get("salary") or inferred_annual_salary(raw,overall=overall))*max(0,min(100,int(wage_share)))/100)
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
        if int(fee_offer)+int(signing_bonus)>int(self.state.get("finances",{}).get("cash") or 0): raise ValueError("la oferta y la prima superan la caja disponible")
        raw=self._player_source(pid) or {}
        value=estimated_transfer_value(raw,overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60))
        slot=role_for_player(raw).squad_slot
        competitors=[]
        for tid in self._active_club_ids():
            if tid in {controlled,seller}: continue
            fin=int((self.state.get("club_finances",{}).get(str(tid)) or {}).get("cash") or 0)
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
                fee_decision=negotiate_transfer(player=self._career_player_api(raw),current_overall=overall,buyer_cash=int(self.state["finances"].get("cash") or 0),fee_offer=fee_offer,salary_offer=salary_offer,contract_years=years)
            # A concrete rival can close the deal if the user drags a contested
            # negotiation through multiple rounds with a clearly weaker package.
            if row.get("rival_interest") and seller and int(row.get("round") or 1)>=2 and row.get("rival_team_id"):
                rival_tid=int(row["rival_team_id"]);rival_fee=int(row.get("rival_fee") or 0);rival_salary=int(row.get("rival_salary") or 0)
                rival_fin=self.state.get("club_finances",{}).get(str(rival_tid)) or {}
                rival_ok,_=self._signing_eligibility(rival_tid,raw,day=day)
                if rival_ok and int(rival_fin.get("cash") or 0)>=rival_fee and (fee_offer<rival_fee or salary_offer<round(rival_salary*.95)):
                    rival_fin["cash"]-=rival_fee;rival_fin["transfer_spend"]=int(rival_fin.get("transfer_spend") or 0)+rival_fee
                    if str(seller) in self.state.get("club_finances",{}):
                        sf=self.state["club_finances"][str(seller)];sf["cash"]+=rival_fee;sf["transfer_income"]=int(sf.get("transfer_income") or 0)+rival_fee
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
            if fee_decision.get("accepted") and salary_offer>=salary_min:
                transfer=self._complete_user_transfer(player_id=pid,seller=seller,fee=int(fee_decision.get("fee") or 0),salary=salary_offer,years=years,date_text=day.isoformat(),source="negotiation",signing_bonus=int(row.get("signing_bonus") or 0),release_clause=row.get("release_clause"),squad_role=str(row.get("squad_role") or "rotation"))
                row.update({"status":"completed","completed_on":day.isoformat(),"fee":transfer["fee"],"salary":salary_offer}); row.setdefault("history",[]).append({"date":day.isoformat(),"kind":"accepted","fee":transfer["fee"],"salary":salary_offer})
                events.append({"kind":"user_transfer_completed","date":day.isoformat(),"player_id":pid,"fee":transfer["fee"]})
            else:
                counter_fee=int(fee_decision.get("counter_fee") or fee_offer)
                if str(fee_decision.get("reason") or "") == "oferta_insuficiente":
                    counter_fee=max(fee_offer,round(counter_fee*negotiation_multiplier))
                counter_salary=max(salary_min,int(row.get("salary_offer") or 0))
                reason="salario_insuficiente" if fee_decision.get("accepted") and salary_offer<salary_min else str(fee_decision.get("reason") or "oferta_insuficiente")
                row.update({"status":"countered","reason":reason,"counter_fee":counter_fee,"counter_salary":counter_salary})
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
                fin=self.state["club_finances"].get(str(tid),{}); cash=int(fin.get("cash") or 0)
                if cash<value*.75: continue
                squad=self._career_players_by_team.get(tid,[]); audit=squad_audit(squad,self.state["player_development"]); target_need=next((n for n in audit["needs"] if n["slot"]==target_slot),{"shortage":0})
                need=int(target_need["shortage"])*3+max(0,20-len(squad))+float(club_status(self.state,tid).get("score") or 50)/100
                candidates.append((need+rng.random(),tid,cash))
            if not candidates: continue
            candidates.sort(reverse=True); buyer=candidates[0][1]; fee=round(value*(.82+rng.random()*.20)); fee=min(fee,int(self.state["club_finances"][str(buyer)].get("cash") or 0))
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
        if int(buyer_fin.get("cash") or 0)<fee: offer["status"]="withdrawn";raise ValueError("el comprador ya no dispone de fondos")
        seller_fin=self.state["club_finances"][str(controlled)]; buyer_fin["cash"]-=fee;buyer_fin["transfer_spend"]=int(buyer_fin.get("transfer_spend") or 0)+fee; seller_fin["cash"]+=fee;seller_fin["transfer_income"]=int(seller_fin.get("transfer_income") or 0)+fee
        raw=self._player_source(pid);overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60); salary=round(inferred_annual_salary(raw,overall=overall)*1.04); years=3
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
        ensure_market_flow_state(self.state);period=self.transfer_period_snapshot();rule=self._domestic_foreign_rule();squad=self._career_players_by_team.get(int(self.state["team_id"]),[])
        return {"watchlist":list(self.state["watchlist"]),"negotiations":list(self.state["transfer_negotiations"].values()),"inquiries":list(self.state.get("market_inquiries") or [])[-30:],"loans":list(self.state.get("loan_deals") or [])[-40:],"listings":list(self.state["transfer_listings"].values()),"incoming_offers":list(self.state["incoming_transfer_offers"])[-30:],
            "period":period,"foreign_rule":rule.as_dict() if rule else None,"foreign_count":foreign_count(squad,rule) if rule else 0,"club_status":self.club_status_snapshot(),
            "recruitment_plan":dict((self.state.get("recruitment_plans") or {}).get(str(int(self.state["team_id"]))) or {}),"market_storylines":list(self.state.get("market_storylines") or [])[-30:],
            "scouting":self.scouting_snapshot(),"squad_plan":self.squad_plan_snapshot(),
            "squad_size":len(squad),"minimum_squad_size":MINIMUM_SENIOR_SQUAD_SIZE_9394,"target_squad_size":TARGET_SENIOR_SQUAD_SIZE_9394}

    def economy_snapshot(self) -> dict[str,Any]:
        team_id=int(self.state["team_id"]); team=self.universe.team(team_id) or {}; players=self._career_players_by_team.get(team_id,[])
        base=economy_snapshot(team=team,finances=self.state["finances"],players=players,development=self.state["player_development"],contract_overrides=self.state["contract_overrides"],ledger=self.state["economy_ledger"],stature_score=float(club_status(self.state,team_id).get("score") or 50.0))
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
        accepted=offered>=minimum
        record={"kind":"user_renewal","date":self.state["current_date"],"player_id":pid,"years":int(years),"salary_offer":offered,"minimum_salary":minimum,"accepted":accepted,"relationship_trust":trust,"relationship_multiplier":round(trust_multiplier,3),"wants_move":wants_move}
        if accepted:
            year=self.current_date.year
            self.state["contract_overrides"][str(pid)]={**current,"start":str(year),"end":str(year+int(years)),"end_year":year+int(years),"salary":offered,"salary_display":f"{offered:,} ptas.".replace(",","."),"career_inferred":True,"renewed_by_user":True}
            adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=7,reason="renovación acordada")
        else:
            record["counter_salary"]=minimum
            adjust_player_manager_relationship(self.state,player_id=pid,date_text=self.current_date.isoformat(),delta=-2,reason="oferta de renovación insuficiente")
        register_contract_decision(self.state, player_id=pid, accepted=accepted, date_text=self.current_date.isoformat())
        self.state["contract_history"].append(record)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return record

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
            "season_archive":list(self.state.get("season_archive") or []),"honours":list(self.state.get("honours") or []),
            "club_honours":list((self.state.get("club_honours") or {}).get(str(team_id),[])),"continental_qualifiers":dict(self.state.get("continental_qualifiers") or {}),
            "season_transition_log":list(self.state.get("season_transition_log") or []),"recent_world_events":list(self.state.get("world_events") or [])[-30:],
            "board":self.board_snapshot(persist=False),"news_feed":self.news_snapshot(limit=30),"season_recaps":list(self.state.get("season_recaps") or []),
            "latest_ai_squad_audit":((self.state.get("ai_squad_audits") or [])[-1] if self.state.get("ai_squad_audits") else None),"job_status":self.state.get("job_status") or "active",
            "preseason":self.preseason_snapshot(),"market_period":self.transfer_period_snapshot(),"club_status":self.club_status_snapshot(),
            "market_flow":self.market_snapshot(),"live_match":self.live_match_snapshot(),"last_match_report":self.state.get("last_match_report"),
            "storylines":stories,
            "storyline_archive":[dict(row) for row in (self.state.get("storylines") or []) if row.get("status")=="resolved"][-40:],
            "rivalries":rivalries,"dressing_room":dressing,"reencounters":reencounters,"staff":self.staff_snapshot(),"staff_reports":self.staff_reports_snapshot(),"scouting":self.scouting_snapshot(),"squad_plan":self.squad_plan_snapshot(),"training":self.training_snapshot(),"tactical_plan":self.tactical_plan_snapshot(),"match_briefing":self.match_briefing_snapshot(),"career_records":records_snapshot(self.state),"user_manager":manager_profile_snapshot(self.state),
            "professional_career":self._professional_career_view(),"board_project":project_snapshot(self.state,team_id),"information_world":information_snapshot(self.state,limit=60),
            "manager_world":{"history":list(self.state.get("manager_history") or [])[-40:],"pressure":dict(self.state.get("manager_pressure") or {}),"unemployed_count":len(self.state.get("manager_unemployed") or [])},
            "result_count":len(self.state.get("results") or []),"last_controlled_result":last_result,
        }

