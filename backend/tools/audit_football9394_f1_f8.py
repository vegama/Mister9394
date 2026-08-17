from __future__ import annotations

from collections import Counter
from statistics import mean
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.football9394.coaching import source_coach_for_team
from backend.app.football9394.match_engine import FootballMatchEngine9394, SPAIN_PRIMERA_SIMULATION_1993_94
from backend.app.football9394.player_identity import player_archetype
from backend.app.football9394.refereeing import referee_for_match
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.tactical_ai import ai_tactics_for_squad
from backend.app.football9394.team_builder import build_snapshot_team_sheet
from backend.app.football9394.venue import venue_for_team


def main() -> None:
    universe = default_runtime_snapshot()
    teams = [int(row["source_id"]) for row in universe.teams(league_id=1)]
    plans = {}
    formation_counts = Counter()
    mentality_counts = Counter()
    archetypes = Counter()
    for team_id in teams:
        coach = source_coach_for_team(universe, team_id)
        plan = ai_tactics_for_squad(universe.players_by_team[team_id], coach)
        plans[team_id] = (coach, plan)
        formation_counts[plan.formation] += 1
        mentality_counts[plan.mentality] += 1
        for player in universe.players_by_team[team_id]:
            archetypes[player_archetype(player)[0]] += 1

    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    sheets = {
        team_id: build_snapshot_team_sheet(universe, team_id, tactics=plans[team_id][1], coach_profile=plans[team_id][0])
        for team_id in teams
    }
    fixtures = universe.league_calendar(1)[:120]
    totals = Counter()
    goals = []
    for index, fixture in enumerate(fixtures):
        home = int(fixture["home_team_id"]); away = int(fixture["away_team_id"])
        seed = 800_000 + index * 101 + int(fixture["id"])
        result = engine.simulate(sheets[home], sheets[away], seed=seed, referee=referee_for_match(1, seed=seed), venue=venue_for_team(universe, home))
        goals.append(result.home.goals + result.away.goals)
        totals["shots"] += result.home.shots + result.away.shots
        totals["shots_on_target"] += result.home.shots_on_target + result.away.shots_on_target
        totals["yellow_cards"] += result.home.yellow_cards + result.away.yellow_cards
        totals["red_cards"] += result.home.red_cards + result.away.red_cards
        totals.update(event.kind for event in result.events)

    goal_avg = mean(goals)
    target = float(SPAIN_PRIMERA_SIMULATION_1993_94.target_goals_per_match or 2.55)
    checks = {
        "goal_environment": abs(goal_avg - target) < 0.25,
        "tactical_variety": len(formation_counts) >= 4 and len(mentality_counts) >= 2,
        "player_identity_variety": len(archetypes) >= 10,
        "causal_chance_chain": all(totals[k] > 0 for k in ("chance", "defensive_error", "second_ball", "set_piece_chance", "free_kick_chance")),
        "coach_adjustments": totals["tactical_adjustment"] > 0,
        "source_referee_discipline": totals["yellow_cards"] > 0,
        "source_venue_coverage": all(venue_for_team(universe, team_id) is not None for team_id in teams),
        "coach_set_piece_identity": len({sheets[team_id].set_piece_usage for team_id in teams}) >= 2,
    }
    print("F1-F8 REALISM/FUN GATE")
    print(f"matches={len(fixtures)} goals_per_match={goal_avg:.3f} target={target:.3f}")
    print("formations=", dict(formation_counts))
    print("mentalities=", dict(mentality_counts))
    print("archetypes=", len(archetypes), dict(archetypes.most_common(8)))
    print("events=", {k: totals[k] for k in ("chance","goal","defensive_error","second_ball","set_piece_chance","free_kick_chance","tactical_adjustment","yellow_cards","red_cards")})
    print("checks=", checks)
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
