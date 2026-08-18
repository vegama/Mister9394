from backend.app.football9394.development import apply_match_development
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _row():
    return {
        "form": 70,
        "morale": 70,
        "condition": 100,
        "training_load": 0,
        "fatigue": 0,
        "season_appearances": 0,
        "season_starts": 0,
        "season_minutes": 0,
        "season_goals": 0,
        "season_assists": 0,
    }


def test_non_league_match_changes_player_state_but_not_league_counters():
    state = {"10": _row()}
    apply_match_development(
        state,
        player_ids=["10"],
        starter_ids=["10"],
        won=True,
        drew=False,
        goal_ids=["10"],
        assist_ids=["10"],
        seed=1,
        record_season_stats=False,
    )
    row = state["10"]
    assert row["season_appearances"] == 0
    assert row["season_starts"] == 0
    assert row["season_minutes"] == 0
    assert row["season_goals"] == 0
    assert row["season_assists"] == 0
    assert row["form"] > 70
    assert row["condition"] < 100


def test_league_match_updates_league_counters_once():
    state = {"10": _row()}
    apply_match_development(
        state,
        player_ids=["10"],
        starter_ids=["10"],
        won=False,
        drew=True,
        goal_ids=["10"],
        assist_ids=["10"],
        seed=2,
        record_season_stats=True,
    )
    row = state["10"]
    assert row["season_appearances"] == 1
    assert row["season_starts"] == 1
    assert row["season_minutes"] == 90
    assert row["season_goals"] == 1
    assert row["season_assists"] == 1


def test_twenty_five_league_plus_five_other_matches_archive_as_twenty_five():
    state = {"10": _row()}
    for seed in range(25):
        apply_match_development(
            state, player_ids=["10"], starter_ids=["10"], won=seed % 3 == 0,
            drew=seed % 3 == 1, goal_ids=[], assist_ids=[], seed=100 + seed,
            record_season_stats=True,
        )
    for seed in range(5):
        apply_match_development(
            state, player_ids=["10"], starter_ids=["10"], won=False,
            drew=True, goal_ids=[], assist_ids=[], seed=300 + seed,
            record_season_stats=False,
        )
    assert state["10"]["season_appearances"] == 25
    assert state["10"]["season_starts"] == 25
    assert state["10"]["season_minutes"] == 25 * 90


def test_league_match_rates_both_teams_and_archives_opponent_line():
    from backend.app.football9394.manager_career import ManagerCareerRuntime9394
    from backend.app.football9394.career_performance import archive_managed_season

    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=93941, through_matchday=7)
    controlled = int(career.state["team_id"])
    fixture = next(row for row in career._league_schedule(1) if int(row.get("matchday") or 0) == 8 and controlled in {int(row["home_team_id"]), int(row["away_team_id"])})
    opponent = int(fixture["away_team_id"] if int(fixture["home_team_id"]) == controlled else fixture["home_team_id"])
    opponent_ids = [int(row["source_id"]) for row in career._career_players_by_team[opponent]]
    before = {pid: int((career.state["player_development"].get(str(pid)) or {}).get("season_appearances") or 0) for pid in opponent_ids}
    career.state["current_date"] = "1993-10-24"
    career._simulate_matchday(8)
    match = next(row for row in career.state["results"] if int(row.get("matchday") or 0) == 8 and controlled in {int(row["home_team_id"]), int(row["away_team_id"])})
    rated = [pid for pid in opponent_ids if int((career.state["player_development"].get(str(pid)) or {}).get("season_rating_count") or 0) > 0 and int((career.state["player_development"].get(str(pid)) or {}).get("season_appearances") or 0) > before[pid]]
    assert rated
    archive_managed_season(career.state, "1993-94")
    stored = career.state["player_season_archive"][str(rated[0])][-1]
    assert stored["appearances"] == before[rated[0]] + 1
    assert stored["competition_scope"] == "league_only"
    assert 4.0 <= stored["average_rating"] <= 10.0


def test_league_awards_use_league_wide_ratings():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=9394, through_matchday=7)
    awards = career._league_player_awards(league_id=1, table=career.standings())
    best = awards["best_player"]
    assert best and best["rating_count"] >= awards["minimum_rated_matches"]
    assert 4.0 <= best["average_rating"] <= 10.0
    assert awards["top_scorer"] and awards["top_scorer"]["goals"] >= 0
    assert len(awards["team_of_season"]) == 11
    assert len({row["player_id"] for row in awards["team_of_season"]}) == 11
