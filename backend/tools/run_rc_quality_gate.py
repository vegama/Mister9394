from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DEFAULT_REPORT = ROOT / "docs" / "qa" / "rc-quality-gate.json"


@dataclass(frozen=True)
class Gate:
    name: str
    command: tuple[str, ...]
    cwd: Path = ROOT
    timeout: int = 120


MANAGER = "backend/tests/test_football9394_manager_career.py"
M4M8 = "backend/tests/test_football9394_m4_m8_gameplay.py"

GATES = [
    Gate("frontend-version", ("npm", "run", "check:version"), FRONTEND, 30),
    Gate("frontend-sfc", ("npm", "run", "check:sfc"), FRONTEND, 30),
    Gate("frontend-ui", ("npm", "run", "check:ui"), FRONTEND, 30),
    Gate("frontend-ux", ("npm", "run", "check:ux"), FRONTEND, 30),
    Gate("frontend-vue-syntax", ("npm", "run", "check:vue"), FRONTEND, 45),
    Gate("chromium-responsive", (sys.executable, "backend/tools/rc_browser_matrix.py"), ROOT, 90),
    Gate("chromium-history", (sys.executable, "backend/tools/rc_navigation_history.py"), ROOT, 60),
    Gate("webapp-01", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_football_api_is_separate_and_exposes_1993_94_laws"), ROOT, 45),
    Gate("webapp-02", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_unknown_competition_never_receives_generic_rules"), ROOT, 45),
    Gate("webapp-03", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_match_endpoint_returns_football_stats_and_respects_substitution_cap"), ROOT, 45),
    Gate("webapp-04", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_competition_audit_has_no_career_limbo_rows"), ROOT, 45),
    Gate("webapp-05", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_world_season_endpoint_uses_persistent_world_payload_contract"), ROOT, 45),
    Gate("webapp-06", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_manager_career_api_persists_day_and_matchday"), ROOT, 45),
    Gate("webapp-07", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_manager_career_api_persists_tactical_choices"), ROOT, 45),
    Gate("webapp-08", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_national_teams_api_is_source_backed"), ROOT, 45),
    Gate("webapp-09", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_career_transfer_changes_squad_and_cash"), ROOT, 45),
    Gate("webapp-10", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_background_league_standings_are_persistent_in_career"), ROOT, 45),
    Gate("webapp-11", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_career_exposes_world_economy_and_real_contract_renewal_decision"), ROOT, 45),
    Gate("webapp-12", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_new_career_options_expose_real_league_and_team_selection"), ROOT, 45),
    Gate("webapp-13", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_career_selection_and_dashboard_endpoints"), ROOT, 45),
    Gate("webapp-14", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_dismissed_manager_can_accept_same_league_job_through_api"), ROOT, 45),
    Gate("webapp-15", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_role_promise_endpoint_persists_explicit_squad_commitment"), ROOT, 45),
    Gate("webapp-16", (sys.executable, "-m", "pytest", "-q", "backend/tests/test_football9394_webapp.py::test_nf0_staff_responsibility_api_persists_and_validates"), ROOT, 45),
    Gate("career-daily", (sys.executable, "-m", "pytest", "-q",
        f"{MANAGER}::test_persistent_career_starts_before_matchday_8_and_does_not_recompute_past",
        f"{MANAGER}::test_advance_stops_for_controlled_match_and_playing_advances_whole_world_matchday",
        f"{MANAGER}::test_user_tactics_are_durable_between_days_and_matches",
        f"{MANAGER}::test_controlled_continental_match_stops_daily_advance_and_is_played_by_career",
        f"{MANAGER}::test_career_can_start_from_another_certified_league_and_from_season_start"), ROOT, 90),
    Gate("career-selection-dashboard-entities", (sys.executable, "-m", "pytest", "-q",
        f"{MANAGER}::test_uruguay_odd_team_calendar_keeps_two_historical_round_robins_and_byes",
        f"{MANAGER}::test_selection_is_persistent_and_drives_controlled_team_sheet",
        f"{MANAGER}::test_selection_rejects_an_injured_starter",
        f"{MANAGER}::test_manager_dashboard_has_real_objective_confidence_and_pending_decisions",
        f"{MANAGER}::test_career_options_expose_useful_club_preview_details",
        f"{MANAGER}::test_cross_entity_team_detail_preserves_career_context_and_scouting_uncertainty",
        f"{MANAGER}::test_cross_entity_team_detail_api_is_available_and_returns_404_for_unknown_team"), ROOT, 60),
    Gate("season-rollover-9495", (sys.executable, "-m", "pytest", "-q",
        f"{MANAGER}::test_full_9394_rollover_builds_playable_9495_with_honours_europe_and_summer_market"), ROOT, 90),
    Gate("season-rollover-9596", (sys.executable, "-m", "pytest", "-q",
        f"{MANAGER}::test_rollover_can_repeat_into_9596_without_resetting_history"), ROOT, 90),
    # Run HTTP journeys in isolated processes: local TestClient instances in this legacy
    # file can retain lifespan resources when several are grouped in one pytest process.
    Gate("journey-live-halftime-substitution", (sys.executable, "-m", "pytest", "-q",
        f"{M4M8}::test_m4_m8_api_live_player_and_economy_contract"), ROOT, 60),
    Gate("journey-result-postmatch", (sys.executable, "-m", "pytest", "-q",
        f"{M4M8}::test_m5_api_result_from_preview_finishes_and_commits"), ROOT, 60),
    Gate("journey-market-multiday", (sys.executable, "-m", "pytest", "-q",
        f"{M4M8}::test_m7_api_opens_persistent_multiday_negotiation"), ROOT, 60),
    Gate("journey-preview-return", (sys.executable, "-m", "pytest", "-q",
        f"{M4M8}::test_m5_api_can_return_from_preview_to_lineup_without_committing"), ROOT, 60),
]


def run_gate(gate: Gate) -> dict:
    started = time.monotonic()
    proc = subprocess.Popen(
        gate.command,
        cwd=gate.cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        output, _ = proc.communicate(timeout=gate.timeout)
        status = "pass" if proc.returncode == 0 else "fail"
        return {
            "name": gate.name,
            "status": status,
            "returncode": proc.returncode,
            "duration_seconds": round(time.monotonic() - started, 2),
            "command": list(gate.command),
            "output_tail": "\n".join((output or "").splitlines()[-18:]),
        }
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, _ = proc.communicate(timeout=5)
        return {
            "name": gate.name,
            "status": "timeout",
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 2),
            "command": list(gate.command),
            "output_tail": "\n".join((output or "").splitlines()[-18:]),
        }


def production_state() -> dict:
    vite = FRONTEND / "node_modules" / ".bin" / "vite"
    frontend_dist = FRONTEND / "dist" / "index.html"
    deploy_dist = ROOT / "deploy_dist" / "index.html"
    bundle = frontend_dist if frontend_dist.is_file() else deploy_dist if deploy_dist.is_file() else None
    if bundle is not None:
        return {
            "status": "available",
            "vite": vite.is_file(),
            "rebuild_available": vite.is_file(),
            "dist": frontend_dist.is_file(),
            "deploy_dist": deploy_dist.is_file(),
            "bundle": str(bundle.relative_to(ROOT)),
        }
    return {
        "status": "blocked",
        "vite": vite.is_file(),
        "rebuild_available": vite.is_file(),
        "dist": False,
        "deploy_dist": False,
        "reason": "Falta un bundle de producción: frontend/dist/index.html o deploy_dist/index.html.",
        "missing": ["frontend/dist/index.html o deploy_dist/index.html"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate reproducible de preparación Beta/RC de Míster 93/94")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--require-production", action="store_true", help="Falla si no existe un bundle de producción (frontend/dist o deploy_dist).")
    args = parser.parse_args()

    rows = []
    progress_path = args.report.with_suffix('.progress.json')
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    for gate in GATES:
        row = run_gate(gate)
        rows.append(row)
        progress_path.write_text(json.dumps({"gates": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{row['status'].upper():7} {gate.name:<38} {row['duration_seconds']:>6.2f}s", flush=True)
        if row["status"] != "pass" and row["output_tail"]:
            print(row["output_tail"], flush=True)

    production = production_state()
    source_browser_pass = all(row["status"] == "pass" for row in rows)
    passed = source_browser_pass and (production["status"] == "available" or not args.require_production)
    report = {
        "kind": "mister9394-beta-rc-quality-gate",
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "source_browser_gate_passed": source_browser_pass,
        "production_e2e": production,
        "production_required": args.require_production,
        "passed": passed,
        "gates": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Production E2E: {production['status'].upper()}")
    print(f"Report: {args.report}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
