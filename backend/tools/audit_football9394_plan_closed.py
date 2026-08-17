from __future__ import annotations

"""Reproducible P6-P10 closure audit.

Runs real match simulations for the P6 environment/signature gate and the P10
playability/nomad/invariant gate. Subjective fun/beauty scores are deliberately
not fabricated.
"""

from collections import defaultdict
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.football9394.career_quality_gate import technical_memorable_career_gate
from backend.app.football9394.coaching import source_coach_for_team
from backend.app.football9394.match_engine import FootballMatchEngine9394, SPAIN_PRIMERA_SIMULATION_1993_94
from backend.app.football9394.match_signatures import aggregate_match_environment, player_match_boxscore, player_signature
from backend.app.football9394.refereeing import referee_for_match
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.tactical_ai import ai_tactics_for_squad
from backend.app.football9394.team_builder import build_snapshot_team_sheet
from backend.app.football9394.venue import venue_for_team


def p6_gate() -> dict:
    universe = default_runtime_snapshot()
    team_ids = [int(row["source_id"]) for row in universe.teams(league_id=1)]
    sheets = {}
    for team_id in team_ids:
        coach = source_coach_for_team(universe, team_id)
        plan = ai_tactics_for_squad(universe.players_by_team[team_id], coach)
        sheets[team_id] = build_snapshot_team_sheet(universe, team_id, tactics=plan, coach_profile=coach)

    engine = FootballMatchEngine9394(profile=SPAIN_PRIMERA_SIMULATION_1993_94)
    results = []
    totals = defaultdict(lambda: defaultdict(float))
    starts = defaultdict(int)
    for index, fixture in enumerate(universe.league_calendar(1)[:120]):
        home_id = int(fixture["home_team_id"]); away_id = int(fixture["away_team_id"])
        seed = 910_000 + index * 101 + int(fixture["id"])
        result = engine.simulate(
            sheets[home_id], sheets[away_id], seed=seed,
            referee=referee_for_match(1, seed=seed), venue=venue_for_team(universe, home_id),
        )
        results.append(result)
        box = player_match_boxscore(result, sheets[home_id], sheets[away_id])
        for sheet in (sheets[home_id], sheets[away_id]):
            tid = str(sheet.team_id)
            for player in sheet.starters:
                signature = player_signature(player)["primary"]
                starts[signature] += 1
                for key, value in box[tid][str(player.id)].items():
                    if isinstance(value, (int, float)):
                        totals[signature][key] += float(value)

    env = aggregate_match_environment(results)
    per_start = {
        signature: {
            key: round(totals[signature][key] / count, 3)
            for key in ("shots", "shots_on_target", "chances_created", "set_piece_chances", "saves", "goals", "assists")
        }
        for signature, count in starts.items()
    }
    target = float(SPAIN_PRIMERA_SIMULATION_1993_94.target_goals_per_match or 2.55)
    environment_checks = {
        "goals": abs(float(env["goals"]) - target) < .25,
        "shots": 17 <= float(env["shots"]) <= 29,
        "shots_on_target": 6 <= float(env["shots_on_target"]) <= 13,
        "corners": 3 <= float(env["corners"]) <= 8,
        "fouls": 8 <= float(env["fouls"]) <= 24,
        "discipline": .3 <= float(env["yellow_cards"]) <= 4 and 0 <= float(env["red_cards"]) <= .25,
        "rare_events": .03 <= float(env["penalties"]) <= .4 and .03 <= float(env["injuries"]) <= .5,
        "set_pieces": .8 <= float(env["set_piece_chances"]) <= 4,
    }
    signature_checks = {
        "goalkeepers_save": per_start.get("portero", {}).get("saves", 0) > 2,
        "creators_create": per_start.get("creador", {}).get("chances_created", 0) > 1,
        "set_piece_specialists_take_set_pieces": per_start.get("balon_parado", {}).get("set_piece_chances", 0) > .2,
        "finishers_shoot": per_start.get("finalizador", {}).get("shots", 0) > 1.5,
        "wing_dribblers_attack": per_start.get("desborde", {}).get("shots", 0) > 1,
        "aerial_forwards_attack": per_start.get("aereo", {}).get("shots", 0) > 1,
    }
    return {
        "passed": all(environment_checks.values()) and all(signature_checks.values()),
        "matches": len(results), "environment": env, "target_goals_per_match": target,
        "signature_starts": dict(starts), "per_start": per_start,
        "checks": {"environment": environment_checks, "signatures": signature_checks},
    }


def main() -> None:
    report = {
        "p6": p6_gate(),
        "p10": technical_memorable_career_gate(matches_per_profile=10, seed=9394),
    }
    report["passed"] = bool(report["p6"]["passed"] and report["p10"]["passed"])
    output = REPO_ROOT / "docs" / "p6_p10_closure_audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report={output}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
