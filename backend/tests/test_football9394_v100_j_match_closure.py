from __future__ import annotations

from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _matchday(seed: int) -> ManagerCareerRuntime9394:
    career = ManagerCareerRuntime9394.create(team_id=16, seed=seed, through_matchday=7)
    step = career.advance_day()
    assert step["requires_match"] is True
    return career


def test_v100_j_postmatch_exposes_complete_competition_matchday_results():
    career = _matchday(13001)
    career.start_live_match()
    result = career.simulate_live_match()
    report = result["match"]
    summary = report["round_summary"]

    assert report["committed"] is True
    assert summary["matchday"] == 8
    assert summary["competition_id"] == int(career.state["league_id"])
    assert summary["complete"] is True
    assert summary["fixture_count"] == summary["result_count"] == len(summary["results"])
    assert summary["fixture_count"] == len(career._teams_for_league(int(career.state["league_id"]))) // 2
    assert sum(1 for row in summary["results"] if row["controlled"]) == 1
    assert all(row["home_team"] and row["away_team"] for row in summary["results"])
    assert all(isinstance(row["home_goals"], int) and isinstance(row["away_goals"], int) for row in summary["results"])

    persisted = career.snapshot()["last_match_report"]["round_summary"]
    assert persisted == summary


def test_v100_j_postmatch_context_persists_consequences_and_next_fixture():
    career = _matchday(13002)
    controlled = int(career.state["team_id"])
    career.start_live_match()
    report = career.simulate_live_match()["match"]
    context = report["postmatch_context"]
    own = next(row for row in career.standings() if int(row["team_id"]) == controlled)

    assert context["standings"] == own
    assert isinstance(context["morale_average"], int)
    assert context["board_confidence"]
    assert context["next_match"]
    assert int(context["next_match"].get("matchday") or 0) > 8
    assert isinstance(context["next_match_absences"], list)


def test_v100_j_manual_and_result_button_share_round_summary_contract():
    manual = _matchday(13003)
    instant = _matchday(13003)

    manual.start_live_match()
    while manual.live_match_snapshot()["status"] != "finished":
        manual.advance_live_match(45)
    manual_report = manual.finish_live_match()["match"]

    instant.start_live_match()
    instant_report = instant.simulate_live_match()["match"]

    for report in (manual_report, instant_report):
        summary = report["round_summary"]
        assert report["committed"] is True
        assert summary["complete"] is True
        assert summary["result_count"] == summary["fixture_count"]
        assert sum(1 for row in summary["results"] if row["controlled"]) == 1
        assert set(report["postmatch_context"]) == {"standings", "morale_average", "board_confidence", "next_match", "next_match_absences"}

    manual_other = {(row["fixture_id"], row["home_goals"], row["away_goals"]) for row in manual_report["round_summary"]["results"] if not row["controlled"]}
    instant_other = {(row["fixture_id"], row["home_goals"], row["away_goals"]) for row in instant_report["round_summary"]["results"] if not row["controlled"]}
    assert manual_other == instant_other


def test_v100_j_result_button_delegates_realistic_bench_changes_with_historical_cap():
    career = _matchday(13004)
    career.start_live_match()
    report = career.simulate_live_match()["match"]
    controlled = str(career.state["team_id"])
    changes = [row for row in report["events"] if row.get("kind") == "substitution" and str(row.get("team_id")) == controlled]

    assert 1 <= report["controlled_substitutions_used"] <= 2
    assert report["controlled_substitutions_remaining"] == 2 - report["controlled_substitutions_used"]
    assert len(changes) == report["controlled_substitutions_used"]
    assert all("Entra " in str(row.get("detail") or "") and "sale " in str(row.get("detail") or "") for row in changes)
