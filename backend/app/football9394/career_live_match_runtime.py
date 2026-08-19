from __future__ import annotations

"""Dirección del partido en directo: previa, minutos, cambios y cierre del acta.

Extraído de ``manager_career.py``, que había vuelto a superar el presupuesto de
tamaño vigilado por ``test_m_source_roots_are_materially_smaller_and_have_real_seams``.
El partido es la costura más natural del runtime: se entra por la previa, se
avanza el reloj, se admiten cambios y órdenes, y se cierra publicando el acta.

Sigue el patrón ya establecido por ``CareerMarketRuntimeMixin`` y
``CareerHistoryRuntimeMixin``: un mixin sin estado propio que compone
``ManagerCareerRuntime9394``.
"""

from dataclasses import replace
from datetime import date, datetime, timezone
from typing import Any

from .calendar_cycle import season_start_year
from .career_memory import rivalry_between
from .career_milestones import contextual_milestones
from .career_tournaments import commit_pending_tournament_result
from .dressing_room import reencounters_for_opponent
from .foreign_rules import validate_matchday_foreigners
from .laws import LAWS_1993_94
from .match_analysis import bench_advice, live_player_performance, postmatch_diagnosis
from .match_engine import FootballTactics9394, TeamSheet9394
from .match_signatures import match_signature_report
from .player_identity import player_archetype
from .refereeing import referee_for_match
from .tactical_ai import expected_managed_tactics, prepare_tactics_for_opponent, record_rival_preparation_outcome, rival_learning_for_preparation, tactical_context_for_fixture
from .tactical_plan import ensure_tactical_plan_state
from .venue import venue_for_team


def _default_tactics() -> dict[str, Any]:
    return {
        "formation": "4-4-2", "mentality": "balanced", "tempo": "normal",
        "pressing": "medium", "directness": "mixed", "defensive_line": "medium",
        "width": "normal", "offside_trap": False, "marking": "zonal",
        "build_up": "balanced", "final_third": "mixed", "transition": "balanced",
    }


def _league_match_payload(matchday: int, fixture_id: int, home_id: int, away_id: int, goals_home: int, goals_away: int, *, referee_id: str | None = None, referee_name: str | None = None, referee_source_confidence: str | None = None) -> dict[str, Any]:
    return {
        "matchday": int(matchday), "fixture_id": int(fixture_id),
        "home_team_id": int(home_id), "away_team_id": int(away_id),
        "home_goals": int(goals_home), "away_goals": int(goals_away),
        "referee_id": referee_id, "referee_name": referee_name,
        "referee_source_confidence": referee_source_confidence,
    }


class CareerLiveMatchRuntimeMixin:
    def _live_match_sheets(self) -> tuple[TeamSheet9394, TeamSheet9394]:
        live=self.state.get("live_match")
        if not live: raise ValueError("no hay partido en directo")
        cached = getattr(self, "_live_sheets_cache", None)
        if cached is not None and cached[0] == id(live):
            return cached[1], cached[2]
        home_id=int(live["home_team_id"]);away_id=int(live["away_team_id"]);controlled=int(self.state["team_id"])
        home_t=live.get("home_tactics") if home_id==controlled else None;away_t=live.get("away_tactics") if away_id==controlled else None
        fixture=live.get("fixture") or {}
        home_rule=self._foreign_rule_for_fixture(fixture,home_id) if fixture.get("fixture_type")=="tournament" else None
        away_rule=self._foreign_rule_for_fixture(fixture,away_id) if fixture.get("fixture_type")=="tournament" else None
        kind=str(fixture.get("fixture_type") or "league")
        home=self._sheet(home_id,home_t,foreign_rule=home_rule,competition_kind=kind);away=self._sheet(away_id,away_t,foreign_rule=away_rule,competition_kind=kind)
        self._live_sheets_cache = (id(live), home, away)
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
        self._live_sheets_cache = (id(self.state["live_match"]), home_sheet, away_sheet)
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return self.live_match_snapshot(sheets=(home_sheet, away_sheet))

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
        self._live_sheets_cache = None
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.snapshot()

    def live_match_snapshot(self, *, sheets: tuple[TeamSheet9394, TeamSheet9394] | None = None) -> dict[str,Any]|None:
        live=self.state.get("live_match")
        if not live: return None
        snap=self.live_engine.snapshot(live); home_sheet,away_sheet=sheets or self._live_match_sheets()
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
            # Live-match payloads are hot-path UI data.  Do not embed the full
            # career player dossier (history, medical, scouting, relationships,
            # contracts...) for every footballer on every minute tick.  The live
            # screen only needs stable identity/position/number plus match state.
            # Full dossiers remain available through the dedicated player route.
            raw=self._player_source(int(pid)) or {}
            sheet_player=player_map.get(int(pid))
            fatigue_value=float(fatigue_map.get(str(pid),0.0))
            display_name=str(raw.get("display_name") or raw.get("name") or getattr(sheet_player,"name",str(pid)))
            position=str(raw.get("position") or raw.get("broad_position") or getattr(sheet_player,"position","") or "—")
            shirt_number=raw.get("shirt_number")
            if shirt_number in (None,0,""):
                shirt_number=getattr(sheet_player,"number",None)
            return {
                "id":int(pid),
                "source_id":int(pid),
                "display_name":display_name,
                "position":position,
                "shirt_number":shirt_number,
                "match_fatigue":round(fatigue_value,1),
                "match_condition":max(0,round(100-fatigue_value)),
            }
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
        if str(snap.get("status") or "")=="finished":
            raise ValueError("el partido ya ha terminado")
        controlled_state=live["home"] if own_home else live["away"]
        if int(controlled_state.get("substitutions") or 0)>=LAWS_1993_94.max_used_substitutes:
            raise ValueError("ya has utilizado los dos cambios permitidos en 1993-94")
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
        home,away=self._live_match_sheets();self.live_engine.substitute(live,home,away,outgoing_id=int(outgoing_id),incoming_id=int(incoming_id));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot(sheets=(home,away))

    def advance_live_match(self,minutes:int=5)->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        home,away=self._live_match_sheets();self.live_engine.advance(self.state["live_match"],home,away,minutes=int(minutes),substitution_validator=self._substitution_validator_for_fixture(self.state["live_match"].get("fixture") or {}));self.state["updated_at"]=datetime.now(timezone.utc).isoformat();return self.live_match_snapshot(sheets=(home,away))

    def advance_live_match_until_event(self,max_minutes:int=20)->dict[str,Any]:
        if not self.state.get("live_match"): raise ValueError("no hay partido en directo")
        live=self.state["live_match"]
        notable={"shot_off","save","goal","corner","yellow","red","second_yellow_red","injury","injury_forced_off","halftime","fulltime","penalty","penalty_saved","free_kick","free_kick_chance","set_piece_chance","defensive_error","tactical_adjustment"}
        limit=max(1,min(45,int(max_minutes)))
        home,away=self._live_match_sheets()
        validator=self._substitution_validator_for_fixture(live.get("fixture") or {})
        for _ in range(limit):
            before=len(live.get("events") or [])
            self.live_engine.advance(live,home,away,minutes=1,substitution_validator=validator)
            fresh=(live.get("events") or [])[before:]
            if any(str(event.get("kind") or "") in notable for event in fresh) or str(live.get("status") or "") not in {"live","preview"}:
                break
        self.state["updated_at"]=datetime.now(timezone.utc).isoformat()
        return self.live_match_snapshot(sheets=(home,away))

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
        home,away=self._live_match_sheets()
        validator=self._substitution_validator_for_fixture(live.get("fixture") or {})
        while str(live.get("status"))!="finished":
            self.live_engine.advance(live,home,away,minutes=45,auto_controlled=True,substitution_validator=validator)
        return self.finish_live_match()

    def _commit_preseason_friendly(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];fid=int(fixture["id"]);seed=season_start_year(self.state)*1_000_000+int(self.state["seed"])*1000+abs(fid)
        self._apply_match_player_state(result,home_sheet,away_sheet,seed,competition="Pretemporada",record_performance=False)
        stored={"fixture_type":"friendly","id":fid,"season":self.state["season"],"date":fixture["date"],"home_team_id":int(fixture["home_team_id"]),"away_team_id":int(fixture["away_team_id"]),"home_goals":int(result.home.goals),"away_goals":int(result.away.goals)}
        for row in self.state.get("preseason_friendlies") or []:
            if int(row.get("id") or 0)==fid:
                row.update({"played":True,"home_goals":stored["home_goals"],"away_goals":stored["away_goals"]});break
        self.state.setdefault("preseason_history",[]).append(stored);self.state["preseason_history"]=self.state["preseason_history"][-80:]
        self._rebuild_rosters(sync_dynamics=False);return stored

    def _commit_live_league(self,result,home_sheet:TeamSheet9394,away_sheet:TeamSheet9394,live:dict[str,Any])->dict[str,Any]:
        fixture=live["fixture"];matchday=int(fixture["matchday"]);league_id=int(self.state["league_id"]);controlled=int(self.state["team_id"])
        if matchday<=int(self.state.get("completed_matchday") or 0): raise ValueError("la jornada del directo ya estaba cerrada")
        calendar=[row for row in self._league_schedule(league_id) if int(row["matchday"])==matchday];results=list(self.state.get("results") or []);season_seed=season_start_year(self.state)*1_000_000
        for fx in calendar:
            h,a=int(fx["home_team_id"]),int(fx["away_team_id"]);seed=season_seed+int(self.state["seed"])*1000+matchday*100+int(fx["id"])
            if int(fx["id"])==int(fixture["id"]):
                r=result;hs,as_=home_sheet,away_sheet
            else:
                hs,as_=self._sheet(h,competition_kind="league"),self._sheet(a,competition_kind="league");r=self.engine.simulate(hs,as_,seed=seed,referee=referee_for_match(league_id,seed=seed),venue=venue_for_team(self.universe,h),substitution_validator=self._substitution_validator_for_fixture({"fixture_type":"league","competition_id":league_id}))
            self._apply_match_player_state(r,hs,as_,seed,competition=(self._team_api(controlled) or {}).get("league",{}).get("name") or "Liga",counts_for_league_stats=True)
            results.append(_league_match_payload(matchday,int(fx["id"]),h,a,r.home.goals,r.away.goals,referee_id=r.referee_id,referee_name=r.referee_name,referee_source_confidence=r.referee_source_confidence));self._post_matchday_income(h,competition=f"league:{league_id}",reference=matchday)
        self.state["results"]=results;self.state["completed_matchday"]=matchday;self._rebuild_rosters()
        raw=next(row for row in results if int(row.get("fixture_id") or -1)==int(fixture["id"]));return raw

    def finish_live_match(self)->dict[str,Any]:
        live=self.state.get("live_match")
        if not live: raise ValueError("no hay partido en directo")
        if live.get("status")!="finished": raise ValueError("el partido todavía no ha terminado")
        home,away=self._live_match_sheets();result=self.live_engine.result(live);live_report=self.live_match_snapshot(sheets=(home,away));events=[]
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
        self._live_sheets_cache = None
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
