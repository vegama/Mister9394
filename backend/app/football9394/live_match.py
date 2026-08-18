from __future__ import annotations

"""Serializable minute-by-minute match layer for the controlled manager game.

The full match engine remains the single football model.  This adapter stores
its mutable side state as JSON so a live match can survive refresh/save and can
be advanced in small chunks while tactics/substitutions change during play.
"""

from dataclasses import asdict, replace
from random import Random
from typing import Any

from .laws import LAWS_1993_94
from .match_engine import (
    FootballMatchEngine9394, FootballTactics9394, MatchEvent9394, MatchResult9394, MatchVenue9394, RefereeProfile9394,
    TeamMatchStats9394, TeamSheet9394, _SideState, _clamp,
)


def _event_dict(event: MatchEvent9394) -> dict[str, Any]:
    return asdict(event)


def _serialize_side(side: _SideState) -> dict[str, Any]:
    return {
        "on_pitch_ids": [str(p.id) for p in side.on_pitch],
        "bench_ids": [str(p.id) for p in side.bench],
        "fatigue": {str(k): round(float(v), 4) for k, v in side.fatigue.items()},
        "yellow_by_player": {str(k): int(v) for k, v in side.yellow_by_player.items()},
        "sent_off": sorted(str(x) for x in side.sent_off),
        "forced_off": sorted(str(x) for x in side.forced_off),
        "goals": side.goals, "shots": side.shots, "shots_on_target": side.shots_on_target,
        "corners": side.corners, "offsides": side.offsides, "fouls": side.fouls,
        "yellows": side.yellows, "reds": side.reds, "possession_ticks": side.possession_ticks,
        "substitutions": side.substitutions,
    }


def _restore_side(sheet: TeamSheet9394, raw: dict[str, Any]) -> _SideState:
    side = _SideState.from_sheet(sheet)
    players = {str(p.id): p for p in (*sheet.starters, *sheet.bench)}
    side.on_pitch = [players[pid] for pid in raw.get("on_pitch_ids", []) if pid in players]
    side.bench = [players[pid] for pid in raw.get("bench_ids", []) if pid in players]
    side.fatigue = {str(k): float(v) for k, v in (raw.get("fatigue") or {}).items()}
    side.yellow_by_player = {str(k): int(v) for k, v in (raw.get("yellow_by_player") or {}).items()}
    side.sent_off = {str(x) for x in raw.get("sent_off", [])}
    side.forced_off = {str(x) for x in raw.get("forced_off", [])}
    for name in ("goals", "shots", "shots_on_target", "corners", "offsides", "fouls", "yellows", "reds", "possession_ticks", "substitutions"):
        setattr(side, name, int(raw.get(name) or 0))
    return side


def _stats(side: dict[str, Any], possession: int) -> dict[str, int]:
    return {
        "goals": int(side.get("goals") or 0), "shots": int(side.get("shots") or 0),
        "shots_on_target": int(side.get("shots_on_target") or 0), "corners": int(side.get("corners") or 0),
        "offsides": int(side.get("offsides") or 0), "fouls": int(side.get("fouls") or 0),
        "yellow_cards": int(side.get("yellows") or 0), "red_cards": int(side.get("reds") or 0),
        "possession": int(possession), "substitutions": int(side.get("substitutions") or 0),
    }


class LiveMatchEngine9394:
    def __init__(self, engine: FootballMatchEngine9394):
        self.engine = engine

    def start(self, home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, *, seed: int, controlled_team_id: int,
              fixture: dict[str, Any], referee: RefereeProfile9394 | None = None, venue: MatchVenue9394 | None = None) -> dict[str, Any]:
        home_sheet.validate(LAWS_1993_94); away_sheet.validate(LAWS_1993_94)
        clock_rng = Random(int(seed) ^ 0x9394F)
        stoppage_first = clock_rng.randint(0, 2)
        stoppage_second = clock_rng.randint(1, 4)
        home = _SideState.from_sheet(home_sheet); away = _SideState.from_sheet(away_sheet)
        return {
            "schema": 1, "status": "live", "minute": 0, "played_minutes": 90 + stoppage_second,
            "stoppage_first": stoppage_first, "stoppage_second": stoppage_second,
            "seed": int(seed), "controlled_team_id": int(controlled_team_id), "fixture": dict(fixture),
            "home_team_id": str(home_sheet.team_id), "away_team_id": str(away_sheet.team_id),
            "home_team_name": home_sheet.team_name, "away_team_name": away_sheet.team_name,
            "home_tactics": asdict(home_sheet.tactics), "away_tactics": asdict(away_sheet.tactics),
            "referee": (asdict(referee) if referee else None),
            "venue": (asdict(venue) if venue else None),
            "home": _serialize_side(home), "away": _serialize_side(away),
            "events": [_event_dict(MatchEvent9394(0, "kickoff", detail="Comienza el partido"))],
            "last_event_index": 0,
        }

    def _sheets(self, state: dict[str, Any], home_sheet: TeamSheet9394, away_sheet: TeamSheet9394) -> tuple[TeamSheet9394, TeamSheet9394]:
        home_t = FootballTactics9394(**state.get("home_tactics", {}))
        away_t = FootballTactics9394(**state.get("away_tactics", {}))
        return replace(home_sheet, tactics=home_t), replace(away_sheet, tactics=away_t)

    def _injury(self, side: _SideState, minute: int, rng: Random, events: list[MatchEvent9394], *, auto_sub: bool) -> None:
        if rng.random() > 0.00125:
            return
        players = side.available_players()
        if not players:
            return
        player = rng.choice(players)
        events.append(MatchEvent9394(minute, "injury", side.sheet.team_id, player.id, player.name, "Problemas físicos"))
        forced_off = rng.random() < 0.58
        if not forced_off:
            return
        if auto_sub and side.substitutions < LAWS_1993_94.max_used_substitutes and side.bench:
            replacement = max(side.bench, key=lambda p: self.engine._replacement_fit(p, player))
            idx = side.on_pitch.index(player); side.on_pitch[idx] = replacement; side.bench.remove(replacement)
            side.substitutions += 1
            events.append(MatchEvent9394(minute, "injury_substitution", side.sheet.team_id, replacement.id, replacement.name,
                                         f"Entra {replacement.name}; sale lesionado {player.name}", player.id, player.name))
            return
        side.forced_off.add(player.id)
        detail = f"{player.name} no puede continuar"
        if side.substitutions >= LAWS_1993_94.max_used_substitutes or not side.bench:
            detail += " y no quedan cambios"
        else:
            detail += "; necesita sustitución"
        events.append(MatchEvent9394(minute, "injury_forced_off", side.sheet.team_id, player.id, player.name, detail))

    def advance(self, state: dict[str, Any], home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, *, minutes: int = 5, auto_controlled: bool = False) -> dict[str, Any]:
        if state.get("status") == "finished":
            return state
        if state.get("status") == "halftime":
            state["status"] = "live"
        home_sheet, away_sheet = self._sheets(state, home_sheet, away_sheet)
        referee = RefereeProfile9394(**state["referee"]) if state.get("referee") else None
        venue = MatchVenue9394(**state["venue"]) if state.get("venue") else None
        home = _restore_side(home_sheet, state["home"]); away = _restore_side(away_sheet, state["away"])
        current = int(state.get("minute") or 0)
        target = min(int(state["played_minutes"]), current + max(1, min(int(minutes), 45)))
        events: list[MatchEvent9394] = []
        controlled = str(int(state["controlled_team_id"]))
        for minute in range(current + 1, target + 1):
            if minute == 45 and int(state.get("stoppage_first") or 0):
                events.append(MatchEvent9394(45, "stoppage_time", detail=f"{state['stoppage_first']} min de añadido"))
            if minute == 45:
                events.append(MatchEvent9394(45, "halftime", detail="Descanso"))
            if minute == 46:
                events.append(MatchEvent9394(46, "second_half", detail="Comienza la segunda parte"))
            if minute == 90 and int(state.get("stoppage_second") or 0):
                events.append(MatchEvent9394(90, "stoppage_time", detail=f"{state['stoppage_second']} min de añadido"))

            self.engine._accumulate_fatigue(home, minute, venue=venue); self.engine._accumulate_fatigue(away, minute, venue=venue)
            rng = Random(int(state["seed"]) * 100003 + minute * 7919 + 17)
            if minute in (58, 70, 78):
                if auto_controlled or str(home.sheet.team_id) != controlled:
                    self.engine._maybe_manager_adjustment(home, away, minute, events)
                    self.engine._maybe_substitute(home, minute, rng, events, opponent=away)
                if auto_controlled or str(away.sheet.team_id) != controlled:
                    self.engine._maybe_manager_adjustment(away, home, minute, events)
                    self.engine._maybe_substitute(away, minute, rng, events, opponent=home)
            activity = (self.engine._activity(home.sheet.tactics, venue=venue) + self.engine._activity(away.sheet.tactics, venue=venue)) / 2
            activity = _clamp(activity * self.engine.profile.notable_attack_multiplier, 0.20, 0.88)
            if rng.random() <= activity:
                home_possession = self.engine._possession_probability(home, away, venue=venue)
                attack, defend = (home, away) if rng.random() < home_possession else (away, home)
                attack.possession_ticks += 1
                self.engine._resolve_attack(attack, defend, minute, rng, events, referee=referee, venue=venue)
                self._injury(attack, minute, rng, events, auto_sub=auto_controlled or str(attack.sheet.team_id) != controlled)
                self._injury(defend, minute, rng, events, auto_sub=auto_controlled or str(defend.sheet.team_id) != controlled)
            state["minute"] = minute
            if minute == 45:
                state["status"] = "halftime"
                break

        state["home"] = _serialize_side(home); state["away"] = _serialize_side(away)
        # Persist AI coaching adjustments made inside the minute loop.
        state["home_tactics"] = asdict(home.sheet.tactics)
        state["away_tactics"] = asdict(away.sheet.tactics)
        state["events"].extend(_event_dict(e) for e in events)
        if int(state["minute"]) >= int(state["played_minutes"]):
            state["status"] = "finished"
            if not state["events"] or state["events"][-1].get("kind") != "fulltime":
                state["events"].append(_event_dict(MatchEvent9394(int(state["played_minutes"]), "fulltime", detail="Final del partido")))
        return state

    def set_controlled_tactics(self, state: dict[str, Any], tactics: FootballTactics9394) -> None:
        key = "home_tactics" if str(state["home_team_id"]) == str(state["controlled_team_id"]) else "away_tactics"
        state[key] = asdict(tactics)

    def substitute(self, state: dict[str, Any], home_sheet: TeamSheet9394, away_sheet: TeamSheet9394, *, outgoing_id: int, incoming_id: int) -> dict[str, Any]:
        if state.get("status") == "finished":
            raise ValueError("el partido ya ha terminado")
        home_sheet, away_sheet = self._sheets(state, home_sheet, away_sheet)
        home = _restore_side(home_sheet, state["home"]); away = _restore_side(away_sheet, state["away"])
        side = home if str(home.sheet.team_id) == str(state["controlled_team_id"]) else away
        if side.substitutions >= LAWS_1993_94.max_used_substitutes:
            raise ValueError("ya has utilizado los dos cambios permitidos en 1993-94")
        outgoing = next((p for p in side.on_pitch if p.id not in side.sent_off and str(p.id) == str(int(outgoing_id))), None)
        incoming = next((p for p in side.bench if str(p.id) == str(int(incoming_id))), None)
        if str(int(outgoing_id)) in {str(x) for x in side.sent_off}:
            raise ValueError("un jugador expulsado ya no puede ser sustituido")
        if outgoing is None: raise ValueError("el jugador que sale no está en el campo")
        if incoming is None: raise ValueError("el jugador que entra no está en el banquillo")
        idx = side.on_pitch.index(outgoing); side.on_pitch[idx] = incoming; side.bench.remove(incoming)
        side.forced_off.discard(outgoing.id)
        side.substitutions += 1
        event = MatchEvent9394(int(state.get("minute") or 0), "substitution", side.sheet.team_id, incoming.id, incoming.name,
                               f"Entra {incoming.name}; sale {outgoing.name}", outgoing.id, outgoing.name)
        state["events"].append(_event_dict(event))
        state["home"] = _serialize_side(home); state["away"] = _serialize_side(away)
        return state

    def snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        total = int(state["home"].get("possession_ticks") or 0) + int(state["away"].get("possession_ticks") or 0)
        home_poss = round(100 * int(state["home"].get("possession_ticks") or 0) / total) if total else 50
        away_poss = 100 - home_poss
        return {
            "status": state["status"], "minute": int(state["minute"]), "played_minutes": int(state["played_minutes"]),
            "home_team_id": int(state["home_team_id"]), "away_team_id": int(state["away_team_id"]),
            "home_team_name": state["home_team_name"], "away_team_name": state["away_team_name"],
            "home": _stats(state["home"], home_poss), "away": _stats(state["away"], away_poss),
            "events": list(state.get("events") or []), "fixture": dict(state.get("fixture") or {}),
            "controlled_team_id": int(state["controlled_team_id"]),
            # Sent-off and forced-injury footballers keep their historical slot
            # in serialization, but neither continues participating in play.
            "home_on_pitch_ids": [int(x) for x in state["home"].get("on_pitch_ids", []) if str(x).isdigit() and str(x) not in {str(v) for v in state["home"].get("sent_off", [])} and str(x) not in {str(v) for v in state["home"].get("forced_off", [])}],
            "away_on_pitch_ids": [int(x) for x in state["away"].get("on_pitch_ids", []) if str(x).isdigit() and str(x) not in {str(v) for v in state["away"].get("sent_off", [])} and str(x) not in {str(v) for v in state["away"].get("forced_off", [])}],
            "home_sent_off_ids": [int(x) for x in state["home"].get("sent_off", []) if str(x).isdigit()],
            "away_sent_off_ids": [int(x) for x in state["away"].get("sent_off", []) if str(x).isdigit()],
            "home_forced_off_ids": [int(x) for x in state["home"].get("forced_off", []) if str(x).isdigit()],
            "away_forced_off_ids": [int(x) for x in state["away"].get("forced_off", []) if str(x).isdigit()],
            "home_bench_ids": [int(x) for x in state["home"].get("bench_ids", []) if str(x).isdigit()],
            "away_bench_ids": [int(x) for x in state["away"].get("bench_ids", []) if str(x).isdigit()],
            "home_fatigue": dict(state["home"].get("fatigue") or {}), "away_fatigue": dict(state["away"].get("fatigue") or {}),
            "home_tactics": dict(state.get("home_tactics") or {}), "away_tactics": dict(state.get("away_tactics") or {}),
            "referee": dict(state.get("referee") or {}) if state.get("referee") else None,
            "venue": dict(state.get("venue") or {}) if state.get("venue") else None,
        }

    def result(self, state: dict[str, Any]) -> MatchResult9394:
        if state.get("status") != "finished":
            raise ValueError("el partido todavía no ha terminado")
        snap = self.snapshot(state)
        events = tuple(MatchEvent9394(**row) for row in state.get("events") or [])
        return MatchResult9394(
            home_team_id=str(state["home_team_id"]), away_team_id=str(state["away_team_id"]),
            home=TeamMatchStats9394(**snap["home"]), away=TeamMatchStats9394(**snap["away"]),
            events=events, played_minutes=int(state["played_minutes"]),
            referee_id=(str(state["referee"]["source_id"]) if state.get("referee") else None),
            referee_name=(str(state["referee"]["name"]) if state.get("referee") else None),
            referee_source_confidence=(state["referee"].get("temporal_confidence") if state.get("referee") else None),
            venue_id=(str(state["venue"]["source_id"]) if state.get("venue") else None),
            venue_name=(str(state["venue"]["name"]) if state.get("venue") else None),
            venue_city=((state["venue"].get("city_name")) if state.get("venue") else None),
            venue_source_confidence=(state["venue"].get("temporal_confidence") if state.get("venue") else None),
        )
