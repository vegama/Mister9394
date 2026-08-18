from __future__ import annotations

import pytest

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _reach_matchday(career: ManagerCareerRuntime9394) -> None:
    step = career.advance_day()
    assert step["requires_match"] is True


def test_v100_preview_is_not_available_before_matchday():
    career = ManagerCareerRuntime9394.create(team_id=16, seed=10001, through_matchday=0)
    with pytest.raises(ValueError, match="todavía no es día de partido"):
        career.start_live_match()


def test_v100_cancel_preview_rebuilds_match_with_revised_lineup():
    career = ManagerCareerRuntime9394.create(team_id=16, seed=10002, through_matchday=7)
    _reach_matchday(career)
    first = career.start_live_match()
    original_ids = {int(p["id"]) for p in first["controlled_on_pitch"]}
    career.cancel_live_preview()

    selection = career.selection_snapshot()
    starters = list(selection["starter_ids"])
    starter_rows = {int(p["id"]): p for p in selection["starters"]}
    bench_rows = {int(p["id"]): p for p in selection["bench"]}
    pair = next(
        (
            (starter_id, bench_id)
            for starter_id, starter in starter_rows.items()
            for bench_id, substitute in bench_rows.items()
            if starter.get("position") == substitute.get("position")
            and str(starter.get("position") or "").lower() not in {"portero", "por", "gk"}
        ),
        None,
    )
    assert pair is not None, "El fixture necesita al menos un relevo natural de campo"
    outgoing, incoming = pair
    revised = [incoming if pid == outgoing else pid for pid in starters]
    career.set_selection(revised)

    rebuilt = career.start_live_match()
    rebuilt_ids = {int(p["id"]) for p in rebuilt["controlled_on_pitch"]}
    assert incoming in rebuilt_ids and outgoing not in rebuilt_ids
    assert rebuilt_ids != original_ids


def test_v100_manual_and_instant_result_share_committed_postmatch_contract():
    manual = ManagerCareerRuntime9394.create(team_id=16, seed=10003, through_matchday=7)
    instant = ManagerCareerRuntime9394.create(team_id=16, seed=10003, through_matchday=7)
    _reach_matchday(manual); _reach_matchday(instant)

    manual.start_live_match()
    while manual.live_match_snapshot()["status"] != "finished":
        manual.advance_live_match(45)
    manual_result = manual.finish_live_match()

    instant.start_live_match()
    instant_result = instant.simulate_live_match()

    for result in (manual_result, instant_result):
        assert result["match"]["committed"] is True
        assert result["career"]["live_match"] is None
        assert result["career"]["completed_matchday"] == 8
        assert result["career"]["result_count"] == 80
        assert result["match"]["status"] == "finished"
        assert result["match"]["events"][-1]["kind"] == "fulltime"
