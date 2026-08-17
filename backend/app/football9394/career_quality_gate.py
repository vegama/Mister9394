from __future__ import annotations

"""P10 · technical evidence for a memorable long career.

This gate intentionally separates what automation can prove (playability,
regulatory/economic invariants, explainability and persistent memory) from
subjective human judgements such as whether a particular ten-match run is fun.
"""

from copy import deepcopy
from datetime import date
from typing import Any

from .era_policy import regulatory_integrity_report
from .manager_career import ManagerCareerRuntime9394

PROFILE_STARTS_9394 = (
    ("favorito", 1, 3),
    ("medio", 1, 16),
    ("modesto_primera", 1, 692),
    ("division_inferior", 10, 27),
)
LONG_HORIZONS = (3, 10, 20, 30)


def profile_playability_gate(*, matches_per_profile: int = 10, seed: int = 9394) -> dict[str, Any]:
    reports=[]
    for index,(label,league_id,team_id) in enumerate(PROFILE_STARTS_9394):
        career=ManagerCareerRuntime9394.create(team_id=team_id,league_id=league_id,seed=seed+index*97+team_id,through_matchday=0)
        lineup_decisions=0
        played=0
        for _ in range(int(matches_per_profile)):
            if career.next_scheduled_fixture() is None:
                break
            if not career.selection_snapshot()["valid"]:
                pending=career.manager_dashboard()["pending_decisions"]
                if any(row.get("kind")=="lineup" for row in pending):
                    career.state["selection"]=career._safe_auto_selection();lineup_decisions+=1
            if not career.selection_snapshot()["valid"]:
                break
            career.play_next_matchday();played+=1
        snap=career.snapshot()
        reports.append({
            "profile":label,"league_id":league_id,"team_id":team_id,"matches_played":played,
            "lineup_decisions":lineup_decisions,"active":snap.get("job_status")=="active",
            "next_match_available":snap.get("next_match") is not None,"squad_size":len(snap.get("squad") or []),
            "board_score":(snap.get("manager_dashboard") or {}).get("board",{}).get("score"),
            "memory_entries":sum(len(v) for v in (career.state.get("player_match_history") or {}).values()),
            "rules_ok":bool((snap.get("regulatory_integrity") or {}).get("passed")),
        })
    passed=all(r["matches_played"]==int(matches_per_profile) and r["squad_size"]>=18 and r["rules_ok"] for r in reports)
    return {"passed":passed,"matches_per_profile":int(matches_per_profile),"profiles":reports}


def nomad_gate(*, seed: int = 9394) -> dict[str, Any]:
    career=ManagerCareerRuntime9394.create(team_id=3,league_id=1,seed=seed,through_matchday=1)
    visited=[int(career.state["team_id"])]
    for _ in range(2):
        career.state["job_status"]="dismissed"
        career._handle_user_dismissal()
        offers=(career.snapshot().get("user_manager") or {}).get("job_offers") or []
        if not offers:
            return {"passed":False,"visited":visited,"reason":"sin ofertas tras destitución"}
        career.accept_job_offer(offers[0]["id"]);visited.append(int(career.state["team_id"]))
    profile=career.snapshot()["user_manager"]
    return {"passed":len(set(visited))==3 and len(profile.get("tenures") or [])==2,"visited":visited,"tenures":len(profile.get("tenures") or [])}


def long_horizon_invariant_gate(career: ManagerCareerRuntime9394, *, horizons: tuple[int,...]=LONG_HORIZONS) -> dict[str, Any]:
    baseline_players=career.squad()[:8]
    baseline_ages={int(p["id"]):p.get("age") for p in baseline_players}
    reports=[]
    for seasons in horizons:
        probe=ManagerCareerRuntime9394(deepcopy(career.state))
        year=1993+int(seasons)
        probe.state["season"]=f"{year}-{str(year+1)[-2:]}"
        probe.state["current_date"]=date(year,10,23).isoformat()
        integrity=regulatory_integrity_report(probe.universe,season=probe.state["season"],sample_years=(1993,year))
        ages={pid:probe.player_detail(pid).get("age") for pid in baseline_ages}
        frozen=ages==baseline_ages
        generated=sum(1 for p in probe._all_player_rows() if bool(p.get("generated")))
        reports.append({"seasons":int(seasons),"year":year,"rules_ok":integrity["passed"],"ages_frozen":frozen,"generated_players":generated,"rules_policy":probe.state.get("rules_policy")})
    passed=all(r["rules_ok"] and r["ages_frozen"] and r["rules_policy"]=="frozen_1993_94" for r in reports)
    return {"passed":passed,"horizons":reports,"scope":"long-horizon invariant probe; no fabricated season results"}


def technical_memorable_career_gate(*, matches_per_profile: int = 10, seed: int = 9394) -> dict[str, Any]:
    profile=profile_playability_gate(matches_per_profile=matches_per_profile,seed=seed)
    nomad=nomad_gate(seed=seed^0x10)
    base=ManagerCareerRuntime9394.create(team_id=16,league_id=1,seed=seed^0x30,through_matchday=0)
    horizons=long_horizon_invariant_gate(base)
    return {
        "passed":bool(profile["passed"] and nomad["passed"] and horizons["passed"]),
        "profile_playability":profile,"nomad_career":nomad,"long_horizon":horizons,
        "automated_dimensions":{
            "realism":"regulatory + match/roster gates","clarity":"explainable state exposed by snapshots/UI gates",
            "depth":"player memory, manager mobility, market/tactical consequences","economic_sporting_coherence":"covered by existing economy/roster gates",
            "story_memory":"managed match history + tenures + persistent world state",
        },
        "human_only_dimensions":["diversión percibida","belleza percibida","ganas de continuar"],
        "human_score_fabricated":False,
    }
