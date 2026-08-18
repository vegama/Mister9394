from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.app.football9394.live_match import _restore_side, _serialize_side
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _matchday(seed: int) -> ManagerCareerRuntime9394:
    career = ManagerCareerRuntime9394.create(team_id=16, seed=seed, through_matchday=7)
    step = career.advance_day()
    assert step["requires_match"] is True
    return career


def _natural_change(snapshot: dict, *, avoid: set[int] | None = None) -> tuple[int, int]:
    avoid = avoid or set()
    starters = [p for p in snapshot["controlled_on_pitch"] if int(p["id"]) not in avoid]
    bench = [p for p in snapshot["controlled_bench"] if int(p["id"]) not in avoid]
    pair = next(
        (
            (int(starter["id"]), int(substitute["id"]))
            for starter in starters
            for substitute in bench
            if starter.get("position") == substitute.get("position")
            and str(starter.get("position") or "").lower() not in {"portero", "por", "gk"}
        ),
        None,
    )
    if pair is None:
        pair = next(
            (
                (int(starter["id"]), int(substitute["id"]))
                for starter in starters
                for substitute in bench
                if str(starter.get("position") or "").lower() not in {"portero", "por", "gk"}
                and str(substitute.get("position") or "").lower() not in {"portero", "por", "gk"}
            ),
            None,
        )
    assert pair is not None
    return pair


def test_v100_second_yellow_is_both_second_caution_and_red_and_reaches_next_match():
    career = _matchday(12001)
    snap = career.start_live_match()
    player = next(p for p in snap["controlled_on_pitch"] if str(p.get("position") or "").lower() not in {"portero", "por", "gk"})
    pid = int(player["id"])
    before_yellows = int(career.state["player_development"][str(pid)].get("season_yellows") or 0)

    live = career.state["live_match"]
    side_key = "home" if int(live["home_team_id"]) == int(career.state["team_id"]) else "away"
    side = live[side_key]
    side.setdefault("yellow_by_player", {})[str(pid)] = 2
    side.setdefault("sent_off", []).append(str(pid))
    side["yellows"] = int(side.get("yellows") or 0) + 2
    side["reds"] = int(side.get("reds") or 0) + 1
    live["events"].extend([
        {"minute": 18, "kind": "yellow", "team_id": str(career.state["team_id"]), "player_id": str(pid), "player_name": player["display_name"], "detail": "Tarjeta amarilla", "secondary_player_id": None, "secondary_player_name": None},
        {"minute": 54, "kind": "second_yellow_red", "team_id": str(career.state["team_id"]), "player_id": str(pid), "player_name": player["display_name"], "detail": "Segunda amarilla y expulsión", "secondary_player_id": None, "secondary_player_name": None},
    ])

    in_play = career.live_match_snapshot()
    assert pid not in {int(p["id"]) for p in in_play["controlled_on_pitch"]}
    assert pid in {int(p["id"]) for p in in_play["controlled_sent_off"]}
    result = career.simulate_live_match()
    assert result["match"]["committed"] is True

    dev = career.state["player_development"][str(pid)]
    assert int(dev.get("season_yellows") or 0) == before_yellows + 2
    assert int(dev.get("season_reds") or 0) >= 1
    assert int(dev.get("league_suspension_matches") or 0) == 1
    assert "expuls" in str(dev.get("league_suspension_reason") or "").lower()

    detail = career.player_detail(pid)
    assert detail["league_suspension_active_for_next_match"] is True
    assert "Sancionado" in str(detail.get("status") or "")
    briefing = career.match_briefing_snapshot()
    assert any(int(row["player_id"]) == pid and row["kind"] == "suspension" for row in briefing["own_absences"])
    dashboard = career.manager_dashboard()
    assert any(int(row["player_id"]) == pid and row["kind"] == "suspension" for row in dashboard["unavailable_players"])
    calendar = career.career_calendar()
    next_rows = [row for row in calendar if not row.get("played") and int(row.get("availability_count") or 0) > 0]
    assert any(any(int(a["player_id"]) == pid and a["kind"] == "suspension" for a in row.get("availability") or []) for row in next_rows)
    assert any("Sanción para" in str(row.get("headline") or "") and int((row.get("entity") or {}).get("player_id") or 0) == pid for row in career.news_snapshot())


def test_v100_forced_injury_after_two_changes_really_leaves_team_short():
    career = _matchday(12002)
    snap = career.start_live_match()
    first_out, first_in = _natural_change(snap)
    snap = career.substitute_live_match(first_out, first_in)
    second_out, second_in = _natural_change(snap, avoid={first_in})
    snap = career.substitute_live_match(second_out, second_in)
    assert snap["controlled_substitutions_remaining"] == 0

    live = career.state["live_match"]
    own_home = int(live["home_team_id"]) == int(career.state["team_id"])
    side_key = "home" if own_home else "away"
    home_sheet, away_sheet = career._live_match_sheets()
    side = _restore_side(home_sheet if own_home else away_sheet, live[side_key])
    target = next(p for p in side.available_players() if str(p.id) not in {str(first_in), str(second_in)})

    class ForcedInjuryRng:
        def __init__(self): self.values = iter((0.0, 0.0))
        def random(self): return next(self.values)
        def choice(self, rows):
            assert target in rows
            return target

    events = []
    career.live_engine._injury(side, 77, ForcedInjuryRng(), events, auto_sub=False)
    live[side_key] = _serialize_side(side)
    live["events"].extend(asdict(event) for event in events)
    after = career.live_match_snapshot()

    assert any(event.kind == "injury_forced_off" for event in events)
    assert str(target.id) in {str(x) for x in side.forced_off}
    assert len(after["controlled_on_pitch"]) == 10
    assert int(target.id) in {int(p["id"]) for p in after["controlled_forced_off"]}
    assert after["controlled_substitutions_remaining"] == 0
    with pytest.raises(ValueError, match="dos cambios permitidos"):
        career.substitute_live_match(int(target.id), int(after["controlled_bench"][0]["id"]))


def test_v100_halftime_tactical_change_survives_resume():
    career = _matchday(12003)
    career.start_live_match()
    half = career.advance_live_match(45)
    assert half["status"] == "halftime"

    current = dict(career.state.get("tactics") or {})
    current.update({"mentality": "attacking", "tempo": "high", "pressing": "high"})
    adjusted = career.set_live_tactics(current)
    own_home = int(adjusted["home_team_id"]) == int(career.state["team_id"])
    live_tactics = adjusted["home_tactics"] if own_home else adjusted["away_tactics"]
    assert adjusted["status"] == "halftime"
    assert live_tactics["mentality"] == "attacking"
    assert live_tactics["tempo"] == "high"

    resumed = career.advance_live_match(1)
    live_tactics = resumed["home_tactics"] if own_home else resumed["away_tactics"]
    assert resumed["status"] == "live"
    assert resumed["minute"] >= 46
    assert live_tactics["mentality"] == "attacking"
    assert live_tactics["pressing"] == "high"


def test_v100_calendar_context_handles_postponed_and_unknown_opponent_without_guessing(monkeypatch):
    career = ManagerCareerRuntime9394.create(team_id=16, seed=12004, through_matchday=7)
    controlled = int(career.state["team_id"])
    postponed_fixture = {"id": 9001, "date": career.current_date.isoformat(), "home_team_id": controlled, "away_team_id": 999999, "fixture_type": "league", "postponed": True}
    postponed = career.calendar_context_snapshot(postponed_fixture)
    assert postponed["state"] == "postponed"
    assert postponed["label"] == "Partido aplazado"
    monkeypatch.setattr(career, "next_scheduled_fixture", lambda: postponed_fixture)
    with pytest.raises(ValueError, match="aplazado"):
        career.start_live_match()

    pending_fixture = {"id": 9002, "date": career.current_date.isoformat(), "home_team_id": controlled, "away_team_id": 0, "fixture_type": "league"}
    pending = career.calendar_context_snapshot(pending_fixture)
    assert pending["state"] == "opponent_pending"
    assert pending["label"] == "Rival por confirmar"
    assert pending.get("opponent_name") is None
    monkeypatch.setattr(career, "next_scheduled_fixture", lambda: pending_fixture)
    with pytest.raises(ValueError, match="rival todavía no está confirmado"):
        career.start_live_match()


def test_v100_empty_calendar_state_is_explicit_at_season_end(monkeypatch):
    career = ManagerCareerRuntime9394.create(team_id=16, seed=12005, through_matchday=7)
    career.state["completed_matchday"] = career._controlled_total_rounds()
    monkeypatch.setattr(career, "next_scheduled_fixture", lambda: None)
    context = career.calendar_context_snapshot()
    assert context == {
        "state": "season_complete",
        "label": "Calendario completado",
        "detail": "No quedan jornadas oficiales por disputar en esta temporada.",
        "availability_count": 0,
    }


def test_v100_live_injury_has_one_story_home_profile_briefing_news_and_calendar():
    career = _matchday(12006)
    snap = career.start_live_match()
    player = next(p for p in snap["controlled_on_pitch"] if str(p.get("position") or "").lower() not in {"portero", "por", "gk"})
    pid = int(player["id"])
    live = career.state["live_match"]
    live["events"].append({
        "minute": 31, "kind": "injury", "team_id": str(career.state["team_id"]),
        "player_id": str(pid), "player_name": player["display_name"], "detail": "Problemas físicos",
        "secondary_player_id": None, "secondary_player_name": None,
    })
    career.simulate_live_match()

    profile = career.player_detail(pid)
    assert int(profile["injury_days"]) > 0
    assert "d" in str(profile.get("status") or "")
    dashboard = career.manager_dashboard()
    assert any(int(row["player_id"]) == pid and row["kind"] == "injury" for row in dashboard["unavailable_players"])
    briefing = career.match_briefing_snapshot()
    assert any(int(row["player_id"]) == pid and row["kind"] == "injury" for row in briefing["own_absences"])
    calendar = career.career_calendar()
    assert any(any(int(a["player_id"]) == pid and a["kind"] == "injury" for a in row.get("availability") or []) for row in calendar if not row.get("played"))
    assert any(str(row.get("headline") or "").startswith("Lesión de") and int((row.get("entity") or {}).get("player_id") or 0) == pid for row in career.news_snapshot())
    assert career.selection_snapshot()["valid"] is False
