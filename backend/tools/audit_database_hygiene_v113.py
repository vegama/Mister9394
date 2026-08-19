from __future__ import annotations

"""Executable database-quality gate for the v1.1.3 historical cleanup."""

import json
from pathlib import Path
import re
import unicodedata
from collections import defaultdict
from typing import Any
from backend.app.football9394.player_names import short_historical_display_name

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "database_hygiene_v113_audit.json"

VERIFIED_DISTINCT = {
    frozenset((1759, 1774)), frozenset((6729, 6749)), frozenset((2539, 2735)),
    frozenset((3312, 3867)), frozenset((4817, 7976)), frozenset((2833, 2836)),
    frozenset((6533, 6534)), frozenset((7248, 7249)), frozenset((9496380, 9496385)),
    frozenset((4552, 4562)), frozenset((4200, 4203)), frozenset((8238, 8911)),
    frozenset((1021, 3074)),
}


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def walk_ids(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key in {"source_id", "resolved_source_id", "created_source_id", "matched_existing_id"} and isinstance(child, int):
                yield child_path, child
            elif key in {"attribute_comparable_source_ids"} and isinstance(child, list):
                for i, sid in enumerate(child):
                    if isinstance(sid, int):
                        yield f"{child_path}[{i}]", sid
            elif key in {"primary_comparable", "secondary_comparable"} and isinstance(child, dict):
                sid = child.get("source_id")
                if isinstance(sid, int):
                    yield f"{child_path}.source_id", sid
            yield from walk_ids(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk_ids(child, f"{path}[{i}]")


def audit() -> dict[str, Any]:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    players = snapshot["players"]
    teams = {int(t["source_id"]): t for t in snapshot["teams"]}
    by_id = {int(p["source_id"]): p for p in players}
    active = [p for p in players if not p.get("retired")]
    active_ids = {int(p["source_id"]) for p in active}

    failures: list[dict[str, Any]] = []
    checks: dict[str, Any] = {}

    # Stable IDs, aliases and runtime-facing roster identity.
    checks["unique_source_ids"] = len(by_id) == len(players)
    if not checks["unique_source_ids"]:
        failures.append({"check": "unique_source_ids"})
    bad_aliases = []
    for p in players:
        if p.get("retired") and p.get("merged_into_source_id") is not None:
            target = int(p["merged_into_source_id"])
            if target not in active_ids:
                bad_aliases.append((int(p["source_id"]), target))
    checks["retired_alias_targets_active"] = not bad_aliases
    if bad_aliases:
        failures.append({"check": "retired_alias_targets_active", "rows": bad_aliases[:20]})

    # User-reported Racing/Russia problem.
    critical = {
        515: (17, "Dmitri Popov"),
        517: (17, "Dmitri Radchenko"),
        2705: (871, None),
        9497352: (9315002, None),
    }
    critical_errors = []
    for sid, (team_id, display) in critical.items():
        p = by_id.get(sid)
        if not p or p.get("retired") or int(p.get("team_id") or 0) != team_id or (display and p.get("display_name") != display):
            critical_errors.append({"source_id": sid, "actual": p, "expected_team_id": team_id, "expected_display": display})
    checks["critical_russia_summer_1993_clubs"] = not critical_errors
    if critical_errors:
        failures.append({"check": "critical_russia_summer_1993_clubs", "rows": critical_errors})

    # Routine Russian presentation cannot expose patronymics; full name must survive.
    russian_team_ids = {tid for tid, t in teams.items() if int(t.get("league_id") or 0) == 930015 or int(t.get("country_id") or 0) == 40}
    russian_long = []
    preserved = 0
    for p in active:
        text = " ".join(str(p.get(k) or "") for k in ("historical_data_source", "historical_profile_source", "creation_batch", "market_container_origin")).lower()
        in_scope = int(p.get("team_id") or 0) in russian_team_ids or "russia" in text or "rusia" in text
        if not in_scope:
            continue
        display = " ".join(str(p.get("display_name") or "").split())
        expected = short_historical_display_name(p)
        if expected and expected != display:
            russian_long.append((int(p["source_id"]), p.get("display_name"), p.get("first_name"), expected))
        if p.get("historical_full_name"):
            preserved += 1
    checks["russian_ui_names_short"] = not russian_long
    checks["russian_full_name_preserved_count"] = preserved
    if russian_long:
        failures.append({"check": "russian_ui_names_short", "rows": russian_long[:20]})

    # Patronymics must not leak into routine UI just because the player has
    # already moved outside Russia (e.g. ex-USSR players in Turkey).
    patronymic_ui = []
    for p in active:
        first = " ".join(str(p.get("first_name") or "").split())
        family = " ".join(str(p.get("surname1") or "").split())
        display = " ".join(str(p.get("display_name") or "").split())
        expected = short_historical_display_name(p)
        if first and family and display == f"{first} {family}" and expected and expected != display:
            patronymic_ui.append((int(p["source_id"]), display, expected, p.get("team_id")))
    checks["no_patronymics_in_routine_ui"] = not patronymic_ui
    if patronymic_ui:
        failures.append({"check": "no_patronymics_in_routine_ui", "rows": patronymic_ui[:20]})

    # Exact active duplicate identity groups; explicit known-different people are allowed.
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in active:
        key = (norm(p.get("display_name")), str(p.get("birth_date") or "")[:10])
        if key[0] and key[1]:
            groups[key].append(p)
    duplicate_groups = []
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        ids = frozenset(int(p["source_id"]) for p in rows)
        if ids in VERIFIED_DISTINCT:
            continue
        # Distinct external BDF profiles are a strong keep-separate signal.
        bdfs = {str(p.get("bdfutbol_id")) for p in rows if p.get("bdfutbol_id")}
        if len(bdfs) == len(rows) and len(bdfs) > 1:
            continue
        duplicate_groups.append({"key": key, "rows": [(p["source_id"], p.get("display_name"), p.get("team_id"), p.get("bdfutbol_id")) for p in rows]})
    checks["no_unresolved_exact_identity_duplicates"] = not duplicate_groups
    if duplicate_groups:
        failures.append({"check": "no_unresolved_exact_identity_duplicates", "rows": duplicate_groups[:20]})

    # No whitespace-corrupted identities and no ambiguous same-team display names.
    bad_ws = []
    for p in active:
        for key in ("display_name", "first_name", "surname1", "surname2"):
            value = p.get(key)
            if isinstance(value, str) and value != " ".join(value.split()):
                bad_ws.append((int(p["source_id"]), key, value))
    checks["identity_whitespace_clean"] = not bad_ws
    if bad_ws:
        failures.append({"check": "identity_whitespace_clean", "rows": bad_ws[:20]})

    team_names: dict[tuple[int, str], list[int]] = defaultdict(list)
    for p in active:
        tid = int(p.get("team_id") or 0)
        name = norm(p.get("display_name"))
        if tid and name:
            team_names[(tid, name)].append(int(p["source_id"]))
    same_team = [{"team_id": k[0], "display": k[1], "source_ids": ids} for k, ids in team_names.items() if len(ids) > 1]
    checks["same_team_display_names_unambiguous"] = not same_team
    if same_team:
        failures.append({"check": "same_team_display_names_unambiguous", "rows": same_team[:20]})

    # Specific identity/references repaired by the pass.
    specific_errors = []
    expected = {
        503: (9315004, False), 9495356: (None, True),
        9496512: (9357009, False), 9499000: (9400015, False), 9495160: (None, False),
        336: (16, False), 3491: (None, True), 7283: (9400034, False),
        9496515: (9357010, False), 9496672: (9315004, False),
    }
    for sid, (tid, retired) in expected.items():
        p = by_id.get(sid)
        if not p or bool(p.get("retired")) != retired or (tid is not None and int(p.get("team_id") or 0) != tid):
            specific_errors.append({"source_id": sid, "row": p, "expected_team_id": tid, "expected_retired": retired})
    if by_id.get(9495160, {}).get("display_name") != "Cvijan Milošević":
        specific_errors.append({"source_id": 9495160, "reason": "Cvijan identity overwritten"})
    checks["specific_identity_repairs"] = not specific_errors
    if specific_errors:
        failures.append({"check": "specific_identity_repairs", "rows": specific_errors})

    ecuador = teams.get(9400034)
    checks["otros_ecuador_nonempty"] = bool(ecuador and any(int(p.get("team_id") or 0) == 9400034 for p in active))
    if not checks["otros_ecuador_nonempty"]:
        failures.append({"check": "otros_ecuador_nonempty"})

    # World Cup and staging references must resolve to active identities.
    wc = json.loads((DATA / "world_cup_1994_squads.json").read_text(encoding="utf-8"))
    bad_wc = [(path, sid) for path, sid in walk_ids(wc) if "resolved_source_id" in path and sid not in active_ids]
    checks["world_cup_resolved_ids_active"] = not bad_wc
    if bad_wc:
        failures.append({"check": "world_cup_resolved_ids_active", "rows": bad_wc[:20]})

    wc_metadata_missing = []
    for team in wc.get("teams", []):
        for row in team.get("players", []):
            sid = int(row.get("resolved_source_id") or 0)
            player = by_id.get(sid)
            if not player or player.get("retired") or player.get("historical_squad_1994") is not True or not player.get("world_cup_1994"):
                wc_metadata_missing.append((team.get("team_code"), sid, row.get("display_name")))
    checks["world_cup_canonical_metadata_complete"] = not wc_metadata_missing
    if wc_metadata_missing:
        failures.append({"check": "world_cup_canonical_metadata_complete", "rows": wc_metadata_missing[:20]})

    active_team_ids = {int(p.get("team_id") or 0) for p in active}
    empty_market = [(tid, t.get("name")) for tid, t in teams.items() if t.get("market_container") and tid not in active_team_ids]
    checks["active_market_containers_nonempty"] = not empty_market
    if empty_market:
        failures.append({"check": "active_market_containers_nonempty", "rows": empty_market})

    bad_staging = []
    for name in ("russia_1993_roster_staging.json", "turkey_1993_94_roster_staging.json", "greece_1993_94_roster_staging.json", "belgium_1993_94_roster_staging.json"):
        path = DATA / name
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for ref_path, sid in walk_ids(payload):
            if ref_path.endswith("resolved_source_id") and sid not in active_ids:
                bad_staging.append((name, ref_path, sid))
    checks["staging_resolved_ids_active"] = not bad_staging
    if bad_staging:
        failures.append({"check": "staging_resolved_ids_active", "rows": bad_staging[:20]})

    # Profile comparable links cannot point at a retired alias.
    reviews = json.loads((DATA / "created_player_profile_reviews.json").read_text(encoding="utf-8"))
    bad_comparables = []
    for path, sid in walk_ids(reviews):
        if any(token in path for token in ("comparable", "matched_existing_id")) and sid in by_id and by_id[sid].get("retired"):
            bad_comparables.append((path, sid, by_id[sid].get("merged_into_source_id")))
    checks["profile_comparables_not_retired"] = not bad_comparables
    if bad_comparables:
        failures.append({"check": "profile_comparables_not_retired", "rows": bad_comparables[:20]})

    # Minimum active squad floor: playable teams should not have been gutted by merges.
    counts = defaultdict(int)
    for p in active:
        counts[int(p.get("team_id") or 0)] += 1
    russian_counts = {tid: counts[tid] for tid in russian_team_ids if int(teams.get(tid, {}).get("league_id") or 0) == 930015}
    checks["russian_min_active_squad"] = min(russian_counts.values()) if russian_counts else 0
    if russian_counts and min(russian_counts.values()) < 18:
        failures.append({"check": "russian_min_active_squad", "counts": sorted(russian_counts.items(), key=lambda x: x[1])[:10]})

    # Coverage debt is tracked separately from identity hygiene.  A short
    # historical roster is not fabricated away here, but it must remain
    # visible so later source passes can add real 1993-94 players.
    leagues = {int(row["source_id"]): row for row in snapshot.get("leagues", [])}
    roster_shortages = []
    for tid, team in teams.items():
        league = leagues.get(int(team.get("league_id") or 0))
        if not league or not league.get("admitted") or team.get("market_container"):
            continue
        active_count = int(counts.get(tid, 0))
        if active_count < 18:
            roster_shortages.append({
                "team_id": tid,
                "team": team.get("name"),
                "league_id": int(team.get("league_id") or 0),
                "league": league.get("name"),
                "country": league.get("country"),
                "active_players": active_count,
                "deficit_to_18": 18 - active_count,
            })
    roster_shortages.sort(key=lambda row: (row["active_players"], row["country"] or "", row["league"] or "", row["team"] or ""))
    checks["admitted_short_roster_team_count"] = len(roster_shortages)
    checks["admitted_roster_total_deficit_to_18"] = sum(row["deficit_to_18"] for row in roster_shortages)
    checks["admitted_min_active_squad"] = min((row["active_players"] for row in roster_shortages), default=18)

    report = {
        "checkpoint": "1.1.3",
        "status": "pass" if not failures else "fail",
        "active_players": len(active),
        "retired_aliases": sum(bool(p.get("retired")) and p.get("merged_into_source_id") is not None for p in players),
        "checks": checks,
        "warnings": {
            "admitted_roster_shortages": roster_shortages,
            "note": "Coverage backlog only: do not invent players; fill from verified 1993-94 sources.",
        },
        "failures": failures,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
