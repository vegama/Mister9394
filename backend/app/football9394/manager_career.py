from __future__ import annotations

"""Persistent playable career loop for Míster 93/94.

The controlled career is intentionally simple on the surface but stateful under
it: results are written once, player form/ability can evolve while age is
frozen, injuries recover day by day, transfers alter actual squads and the
club's source-scale cash balance moves with matches and deals.
"""

from dataclasses import dataclass, replace
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
from .career_ai import renew_ai_contracts, run_ai_transfer_window
from .career_international import generated_international_windows_9394, simulate_generated_friendlies
from .calendar_cycle import generated_round_dates, season_label, season_start_year
from .career_special_world import ensure_special_competitions, process_special_competitions, special_competition_snapshot
from .career_tournaments import ensure_tournament_state, play_pending_tournament_match, process_daily_tournaments, tournament_snapshot
from .league_engine import LeagueSeason9394
from .laws import LAWS_1993_94
from .registry import default_registry_9394
from .development import apply_match_development, initial_player_development, recover_one_day, season_rollover as rollover_player_development
from .match_engine import ERA_BASELINE_1993_94, FootballMatchEngine9394, FootballTactics9394, Footballer9394, SPAIN_PRIMERA_SIMULATION_1993_94, TeamSheet9394
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

CAREER_SCHEMA_9394 = 5
CAREER_START_DATE_9394 = date(1993, 10, 23)
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
                 "position": player.get("broad_position") or player.get("position"),
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


def _league_match_payload(matchday: int, fixture_id: int, home_id: int, away_id: int, goals_home: int, goals_away: int) -> dict[str, Any]:
    return {
        "matchday": int(matchday), "fixture_id": int(fixture_id),
        "home_team_id": int(home_id), "away_team_id": int(away_id),
        "home_goals": int(goals_home), "away_goals": int(goals_away),
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
        if schema not in (1, 2, 3, 4, CAREER_SCHEMA_9394):
            raise ValueError("save de carrera Míster 93/94 incompatible")
        return payload


class _CareerUniverseView:
    """Tiny adapter consumed by `build_snapshot_team_sheet`."""
    def __init__(self, runtime: "ManagerCareerRuntime9394"):
        self.runtime = runtime
        self.players_by_team = runtime._match_players_by_team

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
        self._schedule_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        self._strength_cache: dict[int, float] = {}
        self._rebuild_rosters()
        self._ensure_manager_layer()
        self._ensure_world_leagues()
        ensure_special_competitions(self.state)
        ensure_tournament_state(self.state, self.universe)

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
        self.state.setdefault("age_policy", "frozen_at_1993_10_23")
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
        for source_id, ids in (self.state.get("league_memberships") or {}).items():
            if team_id in {int(value) for value in ids}:
                return int(source_id)
        team = self.universe.team(team_id) or {}
        league = team.get("league") or {}
        return int(league["source_id"]) if league.get("source_id") is not None else None

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
               universe: FootballUniverseSnapshot9394 | None = None) -> "ManagerCareerRuntime9394":
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
        playable_date=date(1993,9,4) if through_requested==0 else CAREER_START_DATE_9394
        state = {
            "schema": CAREER_SCHEMA_9394,
            "career_id": str(uuid4()), "season": "1993-94", "seed": int(seed),
            "team_id": int(team_id), "league_id": selected_league,
            "current_date": playable_date.isoformat(),
            "completed_matchday": 0, "results": [], "tactics": _default_tactics(),
            "player_development": initial_player_development(universe.payload.get("players", [])),
            "player_team_overrides": {}, "contract_overrides": {}, "transfer_history": [],
            "finances": initial_finances(team), "economy_ledger": [],
            "age_policy": "frozen_at_1993_10_23",
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
        return runtime

    @property
    def current_date(self) -> date:
        return date.fromisoformat(str(self.state["current_date"]))

    def _current_team_id(self, player_id: int) -> int:
        override = self.state.get("player_team_overrides", {}).get(str(int(player_id)))
        if override is not None:
            return int(override)
        row = self.universe.players_by_id[int(player_id)]
        return int(row["team_id"])

    def _rebuild_rosters(self) -> None:
        all_by_team: dict[int, list[dict[str, Any]]] = {}
        match_by_team: dict[int, list[dict[str, Any]]] = {}
        dev = self.state.get("player_development") or {}
        for base in self.universe.payload.get("players", []):
            pid = int(base["source_id"])
            team_id = self._current_team_id(pid)
            row = dict(base)
            row["team_id"] = team_id
            d = dev.get(str(pid), {})
            if d.get("overall") is not None:
                row["overall"] = int(d["overall"])
            all_by_team.setdefault(team_id, []).append(row)
            if int(d.get("injury_days") or 0) <= 0 and not row.get("retired"):
                match_by_team.setdefault(team_id, []).append(row)
        self._career_players_by_team = all_by_team
        self._match_players_by_team = match_by_team
        self._career_universe = _CareerUniverseView(self)
        if hasattr(self, "_strength_cache"):
            self._strength_cache.clear()

    def _apply_development_to_footballer(self, player: Footballer9394) -> Footballer9394:
        d = self.state.get("player_development", {}).get(str(player.id))
        if not d:
            return player
        target = int(d.get("overall") or player.overall)
        delta = target - int(player.overall)
        def c(v: int) -> int: return max(1, min(100, int(v) + delta))
        return replace(
            player, overall=target, pace=c(player.pace), stamina=c(player.stamina), technique=c(player.technique),
            short_pass=c(player.short_pass), long_pass=c(player.long_pass), creativity=c(player.creativity),
            finishing=c(player.finishing), heading=c(player.heading), tackling=c(player.tackling),
            marking=c(player.marking), positioning=c(player.positioning),
            goalkeeping=(c(player.goalkeeping) if player.position.upper() == "GK" else player.goalkeeping),
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
        sheet = build_snapshot_team_sheet(self._career_universe, int(self.state["team_id"]), tactics=tactics)
        return {"starter_ids": [int(p.id) for p in sheet.starters], "bench_ids": [int(p.id) for p in sheet.bench]}

    def _board_expectation(self) -> dict[str, Any]:
        league_id = int(self.state["league_id"])
        teams = sorted(self._teams_for_league(league_id), key=lambda team: -self._team_strength(int(team["source_id"])))
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
            self.state["selection"] = self._auto_selection()
        if not self.state.get("board_expectation"):
            self.state["board_expectation"] = self._board_expectation()

    def selection_snapshot(self) -> dict[str, Any]:
        controlled = int(self.state["team_id"]); raw = self.state.get("selection") or {}
        starter_ids = [int(x) for x in raw.get("starter_ids") or []]
        bench_ids = [int(x) for x in raw.get("bench_ids") or []]
        available = {int(p["source_id"]): p for p in self._match_players_by_team.get(controlled, [])}
        owned = {int(p["source_id"]): p for p in self._career_players_by_team.get(controlled, [])}
        issues: list[str] = []
        if len(starter_ids) != LAWS_1993_94.players_per_team: issues.append("El once debe tener exactamente 11 jugadores.")
        if len(starter_ids) != len(set(starter_ids)): issues.append("Hay jugadores repetidos en el once.")
        if any(pid not in owned for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador que no pertenece al club.")
        if any(pid not in available for pid in starter_ids + bench_ids): issues.append("La convocatoria contiene un jugador lesionado o no disponible.")
        if len(bench_ids) > LAWS_1993_94.max_named_substitutes: issues.append(f"Sólo se pueden nombrar {LAWS_1993_94.max_named_substitutes} suplentes.")
        if len(set(starter_ids + bench_ids)) != len(starter_ids + bench_ids): issues.append("Un jugador no puede ser titular y suplente a la vez.")
        if starter_ids and not any(str(owned.get(pid, {}).get("broad_position") or "").upper() == "POR" for pid in starter_ids): issues.append("El once necesita portero.")
        def api(pid: int): return self._career_player_api(owned[pid]) if pid in owned else {"id": pid}
        return {"starter_ids": starter_ids, "bench_ids": bench_ids, "starters": [api(pid) for pid in starter_ids], "bench": [api(pid) for pid in bench_ids], "valid": not issues, "issues": issues}

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
        expectation = self.state.get("board_expectation") or self._board_expectation(); actual = int(own.get("position") or expectation["expected_position"]); delta = int(expectation["expected_position"]) - actual
        confidence = "A la espera" if not recent else "Muy alta" if delta >= 3 else "Alta" if delta >= 0 else "Estable" if delta >= -3 else "Bajo presión"
        pending = []
        selection = self.selection_snapshot()
        if not selection["valid"]: pending.append({"priority":"high","kind":"lineup","title":"El once necesita atención","detail":" ".join(selection["issues"]),"action":"squad"})
        expiring = [p for p in squad if p.get("contract",{}).get("end_year") and int(p["contract"]["end_year"]) <= self.current_date.year + (1 if self.current_date.month >= 1 else 0)]
        if expiring: pending.append({"priority":"medium","kind":"contracts","title":f"{len(expiring)} contratos próximos a expirar","detail":"Revisa las renovaciones antes de perder jugadores.","action":"squad"})
        if unavailable: pending.append({"priority":"medium","kind":"availability","title":f"{len(unavailable)} futbolistas no disponibles","detail":"Revisa el once y la convocatoria.","action":"squad"})
        return {"position": own.get("position"), "team_count": len(table), "points": own.get("points", 0), "recent_form": recent, "form_label": form_label, "morale_average": morale, "unavailable_count": len(unavailable), "board_expectation": expectation, "board_confidence": confidence, "pending_decisions": pending, "next_match": self.pending_world_fixture() or self.next_fixture()}

    def _sheet(self, team_id: int, tactics: dict[str, Any] | None = None) -> TeamSheet9394:
        tactical = FootballTactics9394(**tactics) if tactics is not None else None
        if int(team_id) == int(self.state["team_id"]) and self.state.get("selection"):
            selected = self.selection_snapshot()
            if not selected["valid"]:
                raise ValueError("El once del mánager no es válido: " + " ".join(selected["issues"]))
            by_id = {int(row["source_id"]): row for row in self._match_players_by_team.get(int(team_id), [])}
            starters = tuple(self._apply_development_to_footballer(footballer_from_snapshot(by_id[pid])) for pid in selected["starter_ids"])
            bench = tuple(self._apply_development_to_footballer(footballer_from_snapshot(by_id[pid])) for pid in selected["bench_ids"])
            sheet = TeamSheet9394(team_id=str(team_id), team_name=(self._team_api(team_id) or {}).get("name", str(team_id)), starters=starters, bench=bench, tactics=tactical or FootballTactics9394(**{**_default_tactics(), **(self.state.get("tactics") or {})}))
            sheet.validate(LAWS_1993_94)
            return sheet
        sheet = build_snapshot_team_sheet(self._career_universe, team_id, tactics=tactical)
        return replace(sheet, starters=tuple(self._apply_development_to_footballer(p) for p in sheet.starters), bench=tuple(self._apply_development_to_footballer(p) for p in sheet.bench))

    def _apply_match_player_state(self, result, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, seed: int) -> None:
        dev = self.state["player_development"]
        events = tuple(result.events)
        for side, sheet, goals_for, goals_against in (
            (str(result.home_team_id), home_sheet, result.home.goals, result.away.goals),
            (str(result.away_team_id), away_sheet, result.away.goals, result.home.goals),
        ):
            players = {p.id for p in sheet.starters}
            players.update(e.player_id for e in events if e.team_id == side and e.kind in {"substitution", "injury_substitution"} and e.player_id)
            goal_ids = [e.player_id for e in events if e.team_id == side and e.kind == "goal" and e.player_id]
            injury_ids = [e.player_id for e in events if e.team_id == side and e.kind == "injury" and e.player_id]
            apply_match_development(
                dev, player_ids=players, won=goals_for > goals_against, drew=goals_for == goals_against,
                goal_ids=goal_ids, injury_ids=injury_ids, seed=seed + int(side) if side.isdigit() else seed,
            )

    def _post_matchday_income(self, home_team_id: int, *, competition: str, reference: int | str) -> int:
        team = self.universe.team(int(home_team_id)) or {}
        if not team:
            return 0
        income = matchday_income(team)
        finances = self.state["club_finances"].setdefault(str(int(home_team_id)), initial_club_finances(team))
        finances["cash"] = int(finances.get("cash") or 0) + income
        finances["matchday_income"] = int(finances.get("matchday_income") or 0) + income
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
        for fixture in calendar:
            home_id, away_id = int(fixture["home_team_id"]), int(fixture["away_team_id"])
            home_tactics = tactics if home_id == controlled else None
            away_tactics = tactics if away_id == controlled else None
            home_sheet, away_sheet = self._sheet(home_id, home_tactics), self._sheet(away_id, away_tactics)
            match_seed = season_seed + int(self.state["seed"]) * 1000 + int(matchday) * 100 + int(fixture["id"])
            result = self.engine.simulate(home_sheet, away_sheet, seed=match_seed)
            self._apply_match_player_state(result, home_sheet, away_sheet, match_seed)
            results.append(_league_match_payload(matchday, int(fixture["id"]), home_id, away_id, result.home.goals, result.away.goals))
            self._post_matchday_income(home_id, competition=f"league:{league_id}", reference=int(matchday))
        self.state["results"] = results
        self.state["completed_matchday"] = int(matchday)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._rebuild_rosters()

    def _bootstrap_background_world(self, through_round: int) -> None:
        """Fast deterministic backfill before the playable start date."""
        world = self.state.get("world_leagues") or {}
        for source_key, league_state in world.items():
            source_id = int(source_key)
            teams = self._teams_for_league(source_id)
            fixtures = self._league_schedule(source_id)
            max_round = min(int(through_round), max((int(f["round"]) for f in fixtures), default=0))
            strength: dict[int, float] = {}
            for team in teams:
                tid = int(team["source_id"])
                vals = sorted((int(p.get("overall") or p.get("category") or 60) for p in self.universe.players_by_team.get(tid, [])), reverse=True)[:11]
                strength[tid] = (sum(vals) / len(vals)) if vals else 60.0
            stored=[]
            for fixture in fixtures:
                if int(fixture["round"]) > max_round:
                    continue
                home, away = int(fixture["home_team_id"]), int(fixture["away_team_id"])
                rng = Random(season_start_year(self.state)*1_000_000 + int(self.state["seed"])*100000 + source_id*1000 + int(fixture["round"])*50 + home + away)
                edge=(strength.get(home,60)-strength.get(away,60))/18.0 + .18
                hg=max(0,round(rng.random()*2.4 + max(-.4,min(.8,edge))))
                ag=max(0,round(rng.random()*2.1 - max(-.5,min(.5,edge/2))))
                stored.append({"round":int(fixture["round"]),"home_team_id":home,"away_team_id":away,"home_goals":hg,"away_goals":ag,"bootstrap":True})
            league_state["results"]=stored
            league_state["completed_round"]=max_round
            league_state["bootstrap_model"]="fast_strength_backfill_no_player_development"

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

    def _rollover_season(self, day: date) -> list[dict[str,Any]]:
        old_season=str(self.state["season"])
        tables={lid:self.league_standings(lid) for lid in self._simple_world_league_ids()}
        honours=self._archive_honours(tables)
        qualifiers=self._continental_qualifiers(tables)
        movements=[]
        movements.extend(self._spain_rollover(tables)); movements.extend(self._italy_rollover(tables)); movements.extend(self._netherlands_rollover(tables))
        archive={
            "season":old_season,"closed_on":day.isoformat(),"honours":honours,"movements":movements,
            "continental_qualifiers":qualifiers,
            "league_tables":{str(lid):table for lid,table in tables.items()},
        }
        self.state["season_archive"].append(archive)
        old_start=season_start_year(self.state)
        self.state["season"]=season_label(old_start+1)
        self.state["continental_qualifiers"]=qualifiers
        self.state["league_id"]=int(self._current_league_for_team(int(self.state["team_id"])) or self.state["league_id"])
        self.state["completed_matchday"]=0; self.state["results"]=[]; self.state["world_leagues"]={}
        self.state["special_competitions"]={}; self.state["daily_tournaments"]={}; self.state["pending_world_match"]=None
        self.state["processed_international_windows"]=[]
        rollover_player_development(self.state["player_development"])
        self._schedule_cache.clear(); self._rebuild_rosters()
        self.state["selection"] = self._auto_selection(); self.state["board_expectation"] = self._board_expectation()
        self._ensure_world_leagues(); ensure_special_competitions(self.state); ensure_tournament_state(self.state,self.universe)
        self.engine=FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94 if int(self.state["league_id"])==1 else ERA_BASELINE_1993_94)
        event={"kind":"season_rollover","date":day.isoformat(),"from_season":old_season,"to_season":self.state["season"],"movement_count":len(movements),"honour_count":len(honours)}
        self.state["season_transition_log"].append(event)
        return [event]

    def _process_monthly_economy_and_ai(self, day: date) -> list[dict[str, Any]]:
        month_key = f"{day.year:04d}-{day.month:02d}"
        if day.day != 1 or month_key in self.state.get("processed_months", []):
            return []
        events: list[dict[str, Any]] = []
        active_ids = self._active_club_ids()
        for team_id in active_ids:
            team = self.universe.team(team_id) or {}
            finances = self.state["club_finances"].setdefault(str(team_id), initial_club_finances(team))
            posting = apply_monthly_club_finances(
                team=team, finances=finances,
                players=self._career_players_by_team.get(team_id, []),
                development=self.state["player_development"], contract_overrides=self.state["contract_overrides"],
            )
            if team_id == int(self.state["team_id"]):
                self.state["finances"] = finances
                self.state["economy_ledger"].append({"date": day.isoformat(), "kind": "monthly_operations", **posting})
        renewals = renew_ai_contracts(
            current_date=day, controlled_team_id=int(self.state["team_id"]),
            players_by_team=self._career_players_by_team, development=self.state["player_development"],
            contract_overrides=self.state["contract_overrides"], seed=int(self.state["seed"]),
            max_renewals=max(1, len(active_ids)),
        )
        self.state["ai_contract_history"].extend(renewals); events.extend(renewals)
        transfers = run_ai_transfer_window(
            current_date=day, controlled_team_id=int(self.state["team_id"]), eligible_team_ids=active_ids,
            players_by_team=self._career_players_by_team, development=self.state["player_development"],
            club_finances=self.state["club_finances"], player_team_overrides=self.state["player_team_overrides"],
            contract_overrides=self.state["contract_overrides"], seed=int(self.state["seed"]),
            max_deals=(6 if day.month in (7, 8) else 2),
        )
        self.state["ai_transfer_history"].extend(transfers); events.extend(transfers)
        self.state["processed_months"].append(month_key)
        if transfers:
            self._rebuild_rosters()
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
        if not any(e.get("kind") == "contract_expired" and int(e.get("from_team_id") or 0) == controlled for e in events):
            return
        if self.selection_snapshot()["valid"]: return
        self.state["selection"] = self._auto_selection()
        self.state.setdefault("world_events", []).append({"kind":"manager_note","date":self.state["current_date"],"title":"Once reajustado","detail":"El asistente ha rehecho un once legal tras expiraciones de contrato."})

    def _process_international_day(self, day: date) -> list[dict[str, Any]]:
        windows=generated_international_windows_9394(season_start_year(self.state))
        if day not in windows:
            return []
        index=windows.index(day)
        marker=f"{index}:{day.isoformat()}"
        if marker in self.state.get("processed_international_windows", []):
            return []
        raw=simulate_generated_friendlies(
            self.universe, development=self.state["player_development"], window_index=index,
            seed=int(self.state["seed"])*10000+index*100,
        )
        events=[]
        for match_index,row in enumerate(raw):
            result=row.pop("result");home_sheet=row.pop("home_sheet");away_sheet=row.pop("away_sheet")
            self._apply_match_player_state(result,home_sheet,away_sheet,int(self.state["seed"])*10000+index*100+match_index)
            stored={**row,"date":day.isoformat()}
            self.state["international_history"].append(stored);events.append(stored)
        self.state["processed_international_windows"].append(marker)
        self._rebuild_rosters()
        return events

    def _process_daily_world(self, day: date) -> list[dict[str, Any]]:
        events=[]
        events.extend(process_special_competitions(self, day, bootstrap=False))
        events.extend(process_daily_tournaments(self, day, bootstrap=False))
        events.extend(self._process_international_day(day))
        events.extend(self._process_contract_expirations(day))
        events.extend(self._process_monthly_economy_and_ai(day))
        if events:
            self.state["world_events"].extend(events)
            # The save remains compact even after long careers; detailed history
            # lives in the specialised ledgers above.
            self.state["world_events"] = self.state["world_events"][-600:]
        return events

    def set_tactics(self, payload: dict[str, Any]) -> None:
        validated = FootballTactics9394(**{**_default_tactics(), **payload})
        self.state["tactics"] = {
            "formation": validated.formation, "mentality": validated.mentality,
            "tempo": validated.tempo, "pressing": validated.pressing,
            "directness": validated.directness, "defensive_line": validated.defensive_line,
            "width": validated.width, "offside_trap": validated.offside_trap, "marking": validated.marking,
        }
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

    def advance_day(self) -> dict[str, Any]:
        pending=self.pending_world_fixture()
        if pending:
            return {"advanced":False,"requires_match":True,"next_match":pending,"date":self.current_date.isoformat()}
        fixture=self.next_fixture()
        if fixture and self.current_date >= date.fromisoformat(fixture["date"]):
            return {"advanced":False,"requires_match":True,"next_match":fixture,"date":self.current_date.isoformat()}
        tomorrow=self.current_date+timedelta(days=1)
        self.state["current_date"]=tomorrow.isoformat()
        if recover_one_day(self.state["player_development"]):
            self._rebuild_rosters()
        # Every background league progresses by its own dated calendar.
        self._process_background_leagues_for_day(tomorrow)
        self._process_controlled_league_byes(tomorrow)
        world_events=[]
        if tomorrow.month==7 and tomorrow.day==1:
            world_events.extend(self._rollover_season(tomorrow))
        world_events.extend(self._process_daily_world(tomorrow))
        self._repair_selection_after_roster_departures(world_events)
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        pending=self.pending_world_fixture()
        if pending:
            return {"advanced":True,"requires_match":True,"next_match":pending,"date":tomorrow.isoformat(),"world_events":world_events}
        fixture=self.next_fixture(); requires=bool(fixture and tomorrow>=date.fromisoformat(fixture["date"]))
        return {"advanced":True,"requires_match":requires,"next_match":fixture,"date":tomorrow.isoformat(),"world_events":world_events}

    def play_next_matchday(self) -> dict[str, Any]:
        if self.state.get("pending_world_match"):
            row,events=play_pending_tournament_match(self)
            if events:
                self.state["world_events"].extend(events)
                self.state["world_events"]=self.state["world_events"][-600:]
            self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
            snapshot=self.snapshot()
            snapshot["played_match"]={"fixture_type":"tournament",**row}
            return snapshot
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
        api = self.universe.player_api(row, game_date=DEFAULT_GAME_DATE)  # explicit frozen-age policy
        team_id = self._current_team_id(pid)
        team = self.universe.team(team_id)
        api["team_id"] = team_id
        api["team_name"] = team["name"] if team else None
        d = self.state["player_development"].get(str(pid), {})
        api["overall"] = d.get("overall", api.get("overall"))
        api["form"] = d.get("form")
        api["morale"] = d.get("morale")
        api["condition"] = d.get("condition")
        api["age_frozen"] = True
        api["injury_days"] = int(d.get("injury_days") or 0)
        if api["injury_days"] > 0:
            api["status"] = f"Lesionado · {api['injury_days']} d"
            api["medical"] = {"status": "Lesionado", "current_injury": {"name": "Problemas físicos", "expected_days": api["injury_days"]}, "history": []}
        api["season_stats"] = {
            "appearances": int(d.get("season_appearances") or 0), "minutes": int(d.get("season_minutes") or 0),
            "goals": int(d.get("season_goals") or 0), "assists": int(d.get("season_assists") or 0),
        }
        contract_override = self.state.get("contract_overrides", {}).get(str(pid))
        api["contract"] = effective_contract(row, overall=int(api["overall"] or 60), override=contract_override)
        api["estimated_transfer_value"] = estimated_transfer_value(row, overall=int(api["overall"] or 60))
        return api

    def squad(self, team_id: int | None = None) -> list[dict[str, Any]]:
        tid = int(team_id if team_id is not None else self.state["team_id"])
        rows = self._career_players_by_team.get(tid, [])
        return sorted((self._career_player_api(row) for row in rows), key=lambda p: (p.get("shirt_number") is None, p.get("shirt_number") or 999, p.get("display_name") or ""))

    def search_market(self, query: str = "", *, limit: int = 20) -> list[dict[str, Any]]:
        q = " ".join(query.casefold().split())
        controlled = int(self.state["team_id"])
        rows = []
        for row in self.universe.payload.get("players", []):
            if self._current_team_id(int(row["source_id"])) == controlled or row.get("retired"):
                continue
            if q and q not in str(row.get("display_name") or "").casefold():
                continue
            rows.append(row)
        rows.sort(key=lambda p: -int(self.state["player_development"].get(str(p["source_id"]), {}).get("overall") or p.get("overall") or p.get("category") or 0))
        return [self._career_player_api(row) for row in rows[:max(1, min(int(limit), 100))]]

    def negotiate_player(self, player_id: int, *, fee_offer: int, salary_offer: int = 0, contract_years: int = 3) -> dict[str, Any]:
        pid = int(player_id)
        if pid not in self.universe.players_by_id:
            raise KeyError(f"jugador {pid} no existe")
        controlled = int(self.state["team_id"])
        seller = self._current_team_id(pid)
        if seller == controlled:
            raise ValueError("el jugador ya pertenece a tu club")
        raw = self.universe.players_by_id[pid]
        current_overall = int(self.state["player_development"].get(str(pid), {}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        decision = negotiate_transfer(
            player=self._career_player_api(raw), current_overall=current_overall,
            buyer_cash=int(self.state["finances"]["cash"]), fee_offer=int(fee_offer),
            salary_offer=int(salary_offer), contract_years=int(contract_years),
        )
        salary_minimum = round(inferred_annual_salary(raw, overall=current_overall) * 0.90)
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
            self._rebuild_rosters()
        self.state["transfer_history"].append(record)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return record

    def renew_player_contract(self, player_id: int, *, years: int = 3, salary_offer: int | None = None) -> dict[str, Any]:
        pid=int(player_id); controlled=int(self.state["team_id"])
        if pid not in self.universe.players_by_id:
            raise KeyError(f"jugador {pid} no existe")
        if self._current_team_id(pid) != controlled:
            raise ValueError("sólo puedes renovar futbolistas de tu club")
        if not 1 <= int(years) <= 6:
            raise ValueError("la renovación debe durar entre 1 y 6 años")
        raw=self.universe.players_by_id[pid]
        overall=int(self.state["player_development"].get(str(pid),{}).get("overall") or raw.get("overall") or raw.get("category") or 60)
        current=effective_contract(raw,overall=overall,override=self.state["contract_overrides"].get(str(pid)))
        minimum=round(max(inferred_annual_salary(raw,overall=overall),int(current.get("salary") or 0))*.96)
        offered=minimum if salary_offer is None else int(salary_offer)
        accepted=offered>=minimum
        record={"kind":"user_renewal","date":self.state["current_date"],"player_id":pid,"years":int(years),"salary_offer":offered,"minimum_salary":minimum,"accepted":accepted}
        if accepted:
            year=self.current_date.year
            self.state["contract_overrides"][str(pid)]={**current,"start":str(year),"end":str(year+int(years)),"end_year":year+int(years),"salary":offered,"salary_display":f"{offered:,} ptas.".replace(",","."),"career_inferred":True,"renewed_by_user":True}
        else:
            record["counter_salary"]=minimum
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
        controlled=int(self.state["team_id"]); results_by_fixture={int(r["fixture_id"]):r for r in self.state.get("results") or [] if r.get("fixture_id") is not None}
        out=[]
        for fixture in self._league_schedule():
            if controlled not in (int(fixture["home_team_id"]),int(fixture["away_team_id"])): continue
            home_id,away_id=int(fixture["home_team_id"]),int(fixture["away_team_id"]); result=results_by_fixture.get(int(fixture["id"]))
            out.append({**fixture,"home_team":(self._team_api(home_id) or {}).get("name",str(home_id)),"away_team":(self._team_api(away_id) or {}).get("name",str(away_id)),
                "played":result is not None,"home_goals":result.get("home_goals") if result else None,"away_goals":result.get("away_goals") if result else None})
        return out

    def snapshot(self) -> dict[str, Any]:
        team_id=int(self.state["team_id"]); completed=int(self.state.get("completed_matchday") or 0); last_result=None
        if completed:
            raw=next((r for r in reversed(self.state.get("results") or []) if int(r["matchday"])==completed and team_id in (int(r["home_team_id"]),int(r["away_team_id"]))),None)
            if raw:
                home=self._team_api(int(raw["home_team_id"])); away=self._team_api(int(raw["away_team_id"]))
                last_result={**raw,"home_team":home["name"] if home else str(raw["home_team_id"]),"away_team":away["name"] if away else str(raw["away_team_id"])}
        return {
            "career_id":self.state["career_id"],"season":self.state["season"],"league_id":int(self.state["league_id"]),
            "game_date":self.state["current_date"],"completed_matchday":self.state["completed_matchday"],"total_matchdays":self._controlled_total_rounds(),
            "age_policy":self.state.get("age_policy"),"team":self._team_api(team_id),"squad":self.squad(team_id),
            "standings":self.standings(),"next_match":self.pending_world_fixture() or self.next_fixture(),
            "tactics":dict(self.state.get("tactics") or {}),"selection":self.selection_snapshot(),"manager_dashboard":self.manager_dashboard(),"finances":dict(self.state.get("finances") or {}),
            "transfer_history":list(self.state.get("transfer_history") or []),"ai_transfer_history":list(self.state.get("ai_transfer_history") or [])[-50:],
            "contract_history":list(self.state.get("contract_history") or [])[-50:],"international_history":list(self.state.get("international_history") or [])[-50:],
            "world_progress":{key:{"completed_round":int(value.get("completed_round") or 0),"result_count":len(value.get("results") or [])} for key,value in (self.state.get("world_leagues") or {}).items()},
            "special_progress":special_competition_snapshot(self),"tournament_progress":tournament_snapshot(self),
            "season_archive":list(self.state.get("season_archive") or []),"honours":list(self.state.get("honours") or []),
            "club_honours":list((self.state.get("club_honours") or {}).get(str(team_id),[])),"continental_qualifiers":dict(self.state.get("continental_qualifiers") or {}),
            "season_transition_log":list(self.state.get("season_transition_log") or []),"recent_world_events":list(self.state.get("world_events") or [])[-30:],
            "result_count":len(self.state.get("results") or []),"last_controlled_result":last_result,
        }

