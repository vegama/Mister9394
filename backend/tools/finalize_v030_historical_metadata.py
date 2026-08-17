from __future__ import annotations

"""Close v0.30 metadata gaps without fabricating historical facts.

- Repairs stale comparable metadata/attributes when a later position correction made
  the original v0.23 comparable position incompatible.
- Explicitly marks unresolved stadium and referee-pool provenance for the four newly
  reconstructed leagues instead of inventing historical entities.
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from tools.review_created_player_profiles import materialise_attributes

DATA = ROOT / "data" / "football9394"
SNAP = DATA / "historical_snapshot.json"
REG = DATA / "created_players_registry.json"
NEW_LEAGUES = {930052: "Belgium", 930057: "Turkey", 930015: "Russia", 930047: "Greece"}


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def comparables(originals: list[dict], broad: str, overall: int, sid: int):
    pool = [p for p in originals if p.get("broad_position") == broad and p.get("attributes")]
    pool.sort(key=lambda p: (abs(int(p.get("overall") or 0) - overall), int(p.get("source_id") or 0)))
    pool = pool[:32]
    if len(pool) < 2:
        raise RuntimeError(f"No source-backed comparables for {broad}")
    a = pool[(sid * 11) % len(pool)]
    b = pool[(sid * 17 + 3) % len(pool)]
    if int(a["source_id"]) == int(b["source_id"]):
        b = pool[(pool.index(a) + 1) % len(pool)]
    return a, b


def main() -> None:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    registry = json.loads(REG.read_text(encoding="utf-8"))
    by_id = {int(p["source_id"]): p for p in snap["players"]}
    originals = [p for p in snap["players"] if not p.get("external_origin") and not p.get("creation_batch")]
    reg_by_id = {int(r["source_id"]): r for r in registry["players"]}

    repaired = []
    for p in snap["players"]:
        if not p.get("external_origin"):
            continue
        current_ids = p.get("attribute_comparable_source_ids") or []
        if current_ids:
            sources = [by_id.get(int(source_id)) for source_id in current_ids]
            if all(src and src.get("broad_position") == p.get("broad_position") for src in sources):
                continue
        else:
            review = p.get("profile_review_0_23") or {}
            refs = [review.get("primary_comparable"), review.get("secondary_comparable")]
            refs = [r for r in refs if isinstance(r, dict) and r.get("source_id") is not None]
            if len(refs) != 2:
                continue
            sources = [by_id.get(int(r["source_id"])) for r in refs]
            if all(src and src.get("broad_position") == p.get("broad_position") for src in sources):
                continue
        broad = str(p.get("broad_position"))
        sid = int(p["source_id"])
        a, b = comparables(originals, broad, int(p.get("overall") or 70), sid)
        p["attributes"] = materialise_attributes(int(p.get("overall") or 70), a, b)
        p["attribute_source"] = "fixed_source_comparable_profile_coherence_0.30"
        p["attribute_comparable_source_ids"] = [int(a["source_id"]), int(b["source_id"])]
        p["profile_review_0_30"] = {
            "reason": "current broad position no longer matched the v0.23 comparable position",
            "policy": "fixed source-backed same-position comparables; no runtime formula; no football 75/25",
            "primary_comparable": {"source_id": int(a["source_id"]), "display_name": a["display_name"]},
            "secondary_comparable": {"source_id": int(b["source_id"]), "display_name": b["display_name"]},
        }
        r = reg_by_id.get(sid)
        if r is not None:
            r["attribute_source"] = p["attribute_source"]
            r["profile_review_required"] = False
        repaired.append({
            "source_id": sid,
            "display_name": p["display_name"],
            "broad_position": broad,
            "comparables": p["attribute_comparable_source_ids"],
        })

    unresolved_venues = []
    for team in snap["teams"]:
        league_id = team.get("league_id")
        if league_id in NEW_LEAGUES and team.get("stadium_id") is None:
            team["venue_source_status"] = "unresolved_historical_1993_94"
            team["venue_source_policy"] = "Do not invent a stadium; recover a source-backed 1993/94 venue before binding one."
            unresolved_venues.append(int(team["source_id"]))

    unresolved_referees = []
    for league in snap["leagues"]:
        lid = int(league.get("source_id") or 0)
        if lid in NEW_LEAGUES:
            hints = league.setdefault("source_rule_hints", {})
            hints["referee_pool_status"] = "unresolved_historical_1993_94"
            hints["referee_pool_policy"] = "No modern or fabricated referee pool is silently substituted for the historical competition."
            unresolved_referees.append(lid)

    previous_path = DATA / "historical_metadata_gaps_v030.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    cumulative_repairs = {int(row["source_id"]): row for row in previous.get("profile_comparable_coherence_repairs", [])}
    cumulative_repairs.update({int(row["source_id"]): row for row in repaired})
    audit = {
        "schema_version": 1,
        "checkpoint": "0.30.0-full-rosters-1993-country-context",
        "status": "pass",
        "profile_comparable_coherence_repairs": [cumulative_repairs[k] for k in sorted(cumulative_repairs)],
        "unresolved_historical_venue_team_ids": unresolved_venues,
        "unresolved_historical_referee_pool_league_ids": sorted(unresolved_referees),
        "policy": "Known gaps are explicit and source-gated; no historical stadium/referee fact is invented merely to satisfy runtime metadata coverage.",
    }
    dump(SNAP, snap)
    dump(REG, registry)
    dump(DATA / "historical_metadata_gaps_v030.json", audit)
    print(json.dumps({
        "profile_repairs": len(repaired),
        "unresolved_venues": len(unresolved_venues),
        "unresolved_referee_pools": len(unresolved_referees),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
