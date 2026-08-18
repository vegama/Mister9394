from __future__ import annotations

import pytest

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
                and starter.get("nationality_id") == substitute.get("nationality_id")
            ),
            None,
        )
    assert pair is not None, "El fixture necesita un cambio de campo legal"
    return pair


def test_v100_red_card_removes_player_from_live_options_and_cannot_be_replaced():
    career = _matchday(11001)
    snap = career.start_live_match()
    expelled = next(p for p in snap["controlled_on_pitch"] if str(p.get("position") or "").lower() not in {"portero", "por", "gk"})
    expelled_id = int(expelled["id"])
    incoming_id = int(snap["controlled_bench"][-1]["id"])

    live = career.state["live_match"]
    side_key = "home" if int(live["home_team_id"]) == int(career.state["team_id"]) else "away"
    live[side_key].setdefault("sent_off", []).append(str(expelled_id))
    live[side_key]["reds"] = int(live[side_key].get("reds") or 0) + 1

    after = career.live_match_snapshot()
    assert expelled_id not in {int(p["id"]) for p in after["controlled_on_pitch"]}
    assert expelled_id in {int(p["id"]) for p in after["controlled_sent_off"]}
    assert len(after["controlled_on_pitch"]) == 10
    with pytest.raises(ValueError, match="expulsado"):
        career.substitute_live_match(expelled_id, incoming_id)


def test_v100_halftime_is_a_stable_state_and_resume_starts_second_half():
    career = _matchday(11002)
    career.start_live_match()
    half = career.advance_live_match(45)
    assert half["minute"] == 45
    assert half["status"] == "halftime"
    assert any(row.get("kind") == "halftime" for row in half["events"])

    resumed = career.advance_live_match(1)
    assert resumed["minute"] >= 46
    assert resumed["status"] == "live"
    assert any(row.get("kind") == "second_half" for row in resumed["events"])


def test_v100_two_substitution_limit_is_exposed_and_third_change_is_blocked():
    career = _matchday(11003)
    snap = career.start_live_match()
    first_out, first_in = _natural_change(snap)
    snap = career.substitute_live_match(first_out, first_in)
    second_out, second_in = _natural_change(snap, avoid={first_in})
    snap = career.substitute_live_match(second_out, second_in)

    assert snap["controlled_substitutions_used"] == 2
    assert snap["controlled_substitutions_remaining"] == 0
    third_out = next(int(p["id"]) for p in snap["controlled_on_pitch"] if int(p["id"]) not in {first_in, second_in})
    third_in = int(snap["controlled_bench"][0]["id"])
    with pytest.raises(ValueError, match="dos cambios permitidos"):
        career.substitute_live_match(third_out, third_in)


def test_v100_training_injury_repairs_a_saved_lineup_before_matchday():
    career = ManagerCareerRuntime9394.create(team_id=16, seed=11004, through_matchday=7)
    before = career.selection_snapshot()
    injured_id = int(before["starter_ids"][1])
    career.state["player_development"][str(injured_id)]["injury_days"] = 6
    career._rebuild_rosters()
    assert career.selection_snapshot()["valid"] is False

    career._repair_selection_after_roster_departures([
        {"kind": "training_injury", "player_id": injured_id, "team_id": 16}
    ])
    after = career.selection_snapshot()
    assert after["valid"] is True
    assert injured_id not in set(after["starter_ids"] + after["bench_ids"])
    assert any(row.get("kind") == "manager_note" and row.get("title") == "Convocatoria reajustada" for row in career.state.get("world_events", []))


def test_v100_league_cards_create_real_suspension_news_and_next_match_availability():
    career = _matchday(11005)
    snap = career.start_live_match()
    player = next(p for p in snap["controlled_on_pitch"] if str(p.get("position") or "").lower() not in {"portero", "por", "gk"})
    player_id = int(player["id"])
    cycle = career._league_yellow_cycle(int(career.state["team_id"]))
    career.state["player_development"][str(player_id)]["season_yellows"] = cycle - 1

    live = career.state["live_match"]
    live["events"].append({
        "minute": 1, "kind": "yellow", "team_id": str(career.state["team_id"]),
        "player_id": str(player_id), "player_name": player["display_name"],
        "detail": "Tarjeta amarilla", "secondary_player_id": None, "secondary_player_name": None,
    })
    result = career.simulate_live_match()
    assert result["match"]["committed"] is True

    dev = career.state["player_development"][str(player_id)]
    assert dev["season_yellows"] >= cycle
    assert dev["league_suspension_matches"] == 1
    assert "amarillas" in str(dev["league_suspension_reason"])
    selection = career.selection_snapshot()
    assert selection["valid"] is False
    assert any("sancionado" in issue.lower() for issue in selection["issues"])
    assert any("Sanción para" in str(row.get("headline") or "") and int((row.get("entity") or {}).get("player_id") or 0) == player_id for row in career.news_snapshot())
    assert career.manager_dashboard()["unavailable_count"] >= 1

    career.state["selection"] = career._safe_auto_selection()
    assert player_id not in set(career.selection_snapshot()["starter_ids"] + career.selection_snapshot()["bench_ids"])
    while True:
        step = career.advance_day()
        if step.get("requires_match"):
            break
    career.start_live_match()
    career.simulate_live_match()
    assert int(career.state["player_development"][str(player_id)].get("league_suspension_matches") or 0) == 0


def test_v100_postmatch_chain_updates_table_morale_news_and_next_fixture_together():
    career = _matchday(11006)
    controlled = int(career.state["team_id"])
    before = next(row for row in career.standings() if int(row["team_id"]) == controlled)
    before_played = int(before["played"])

    career.start_live_match()
    result = career.simulate_live_match()
    after = next(row for row in career.standings() if int(row["team_id"]) == controlled)
    dashboard = career.manager_dashboard()
    next_fixture = career.next_scheduled_fixture()

    assert result["match"]["committed"] is True
    assert int(after["played"]) == before_played + 1
    assert career.state["last_match_report"]["committed"] is True
    assert dashboard["recent_form"]
    assert isinstance(dashboard["morale_average"], int)
    assert any(controlled in {int((row.get("entity") or {}).get("team_id") or 0), int((row.get("entity") or {}).get("home_team_id") or 0), int((row.get("entity") or {}).get("away_team_id") or 0)} for row in career.news_snapshot())
    assert next_fixture is not None
    assert int(next_fixture.get("matchday") or 0) > 8
    assert str(next_fixture.get("date")) > str(career.current_date)


def test_v100_live_injury_reaches_medical_status_news_and_next_lineup():
    career = _matchday(11007)
    snap = career.start_live_match()
    player = next(p for p in snap["controlled_on_pitch"] if str(p.get("position") or "").lower() not in {"portero", "por", "gk"})
    player_id = int(player["id"])
    live = career.state["live_match"]
    live["events"].append({
        "minute": 12, "kind": "injury", "team_id": str(career.state["team_id"]),
        "player_id": str(player_id), "player_name": player["display_name"],
        "detail": "Problemas físicos", "secondary_player_id": None, "secondary_player_name": None,
    })
    career.simulate_live_match()

    dev = career.state["player_development"][str(player_id)]
    assert int(dev.get("injury_days") or 0) > 0
    assert any(
        str(row.get("headline") or "").startswith("Lesión de")
        and int((row.get("entity") or {}).get("player_id") or 0) == player_id
        for row in career.news_snapshot()
    )
    selection = career.selection_snapshot()
    assert selection["valid"] is False
    assert any("lesionado" in issue.lower() or "no disponible" in issue.lower() for issue in selection["issues"])
    career._repair_selection_after_roster_departures([{"kind": "training_injury", "player_id": player_id, "team_id": 16}])
    assert career.selection_snapshot()["valid"] is True
    assert player_id not in set(career.selection_snapshot()["starter_ids"] + career.selection_snapshot()["bench_ids"])
