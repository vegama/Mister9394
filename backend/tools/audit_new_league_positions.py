from __future__ import annotations

"""Audita posiciones y cobertura de todas las ligas históricas incorporadas."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "mondefootball_squads_1993.json"
REPORT = DATA / "new_leagues_positions_audit.json"

LEAGUE_IDS = {
    "Rumanía": 56, "Bulgaria": 66, "Polonia": 89, "Suecia": 91,
    "Noruega": 88, "Dinamarca": 69, "Austria": 62, "Suiza": 55,
    "Ucrania": 12,
}
SOURCE_COUNTRY = {
    "Rumania": "Rumanía", "Bulgaria": "Bulgaria", "Polonia": "Polonia",
    "Suecia": "Suecia", "Noruega": "Noruega", "Dinamarca": "Dinamarca",
    "Austria": "Austria", "Suiza": "Suiza", "Ucrania": "Ucrania",
}
ROLE_BROAD = {
    0: "POR", 1: "DEF", 2: "DEF", 3: "DEF", 4: "DEF", 5: "DEF",
    6: "MED", 7: "MED", 8: "MED", 9: "MED", 10: "MED", 11: "MED",
    12: "DEL", 13: "MED", 14: "MED", 15: "DEL", 16: "DEL", 17: "DEL",
}


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    squads = json.loads(SQUADS.read_text(encoding="utf-8"))
    leagues = {int(x["source_id"]): x for x in snapshot.get("leagues", [])}
    teams = {int(x["source_id"]): x for x in snapshot.get("teams", [])}
    players = [x for x in snapshot.get("players", []) if not x.get("retired")]
    by_mf = {str(x.get("mondefootball_id")): x for x in players if x.get("mondefootball_id")}
    report: dict[str, Any] = {
        "status": "pass", "scope": "all_new_domestic_leagues_1993_94",
        "leagues": [], "global": {},
    }
    all_conflicts: list[dict[str, Any]] = []
    all_unmatched: list[dict[str, Any]] = []

    for source_country, block in squads.items():
        country = SOURCE_COUNTRY.get(source_country)
        if country not in LEAGUE_IDS:
            continue
        league_id = LEAGUE_IDS[country]
        league = leagues.get(league_id, {})
        league_teams = [x for x in teams.values() if int(x.get("league_id") or -1) == league_id]
        league_team_ids = {int(x["source_id"]) for x in league_teams}
        active_players = [x for x in players if int(x.get("team_id") or -1) in league_team_ids]
        rows = [row for club in block.get("clubs", []) for row in club.get("squad", [])]
        conflicts = []
        unmatched = []
        for row in rows:
            player = by_mf.get(str(row.get("mondefootball_id")))
            if player is None:
                unmatched.append({"name": row.get("full_name"), "mondefootball_id": row.get("mondefootball_id")})
                continue
            expected = row.get("broad_position")
            actual = player.get("broad_position")
            if expected != actual:
                conflicts.append({
                    "name_source": row.get("full_name"),
                    "name_database": player.get("display_name"),
                    "source_id": player.get("source_id"),
                    "mondefootball_id": row.get("mondefootball_id"),
                    "source_broad_position": expected,
                    "database_broad_position": actual,
                    "database_primary_role": player.get("primary_role"),
                    "historical_position": player.get("historical_position_1993_94"),
                    "profile_source_position": player.get("source_profile_position"),
                    "position_source": player.get("historical_position_source") or player.get("role_detail_source"),
                })
        invalid = [
            {"source_id": p.get("source_id"), "name": p.get("display_name"), "role": p.get("primary_role")}
            for p in active_players
            if not isinstance(p.get("primary_role"), int) or p.get("primary_role") not in ROLE_BROAD
        ]
        broad_mismatch = [
            {"source_id": p.get("source_id"), "name": p.get("display_name"),
             "role": p.get("primary_role"), "broad": p.get("broad_position"),
             "derived_broad": ROLE_BROAD.get(p.get("primary_role"))}
            for p in active_players
            if ROLE_BROAD.get(p.get("primary_role")) != p.get("broad_position")
        ]
        league_report = {
            "league_id": league_id, "league": league.get("name"), "country": country,
            "teams_in_league": len(league_teams), "active_players": len(active_players),
            "source_rows": len(rows), "source_rows_matched": len(rows) - len(unmatched),
            "position_source_distribution": dict(Counter(row.get("broad_position") for row in rows)),
            "database_position_distribution": dict(Counter(p.get("broad_position") for p in active_players)),
            "missing_broad_position": sum(not p.get("broad_position") for p in active_players),
            "invalid_primary_roles": invalid, "role_broad_inconsistencies": broad_mismatch,
            "source_position_conflicts": conflicts, "unmatched_source_rows": unmatched,
        }
        report["leagues"].append(league_report)
        all_conflicts.extend([{**x, "league_id": league_id, "country": country} for x in conflicts])
        all_unmatched.extend([{**x, "league_id": league_id, "country": country} for x in unmatched])

    report["global"] = {
        "leagues_audited": len(report["leagues"]),
        "active_players_in_audited_leagues": sum(x["active_players"] for x in report["leagues"]),
        "source_rows": sum(x["source_rows"] for x in report["leagues"]),
        "source_position_conflicts": len(all_conflicts),
        "unmatched_source_rows": len(all_unmatched),
        "invalid_primary_roles": sum(len(x["invalid_primary_roles"]) for x in report["leagues"]),
        "role_broad_inconsistencies": sum(len(x["role_broad_inconsistencies"]) for x in report["leagues"]),
        "missing_broad_position": sum(x["missing_broad_position"] for x in report["leagues"]),
    }
    report["status"] = "pass" if not any(report["global"][key] for key in (
        "invalid_primary_roles", "role_broad_inconsistencies", "missing_broad_position")) else "review"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["global"], ensure_ascii=False, indent=2))
    for row in report["leagues"]:
        print(f"{row['country']}: equipos={row['teams_in_league']} jugadores={row['active_players']} "
              f"filas={row['source_rows']} conflictos={len(row['source_position_conflicts'])} "
              f"no_encontrados={len(row['unmatched_source_rows'])}")


if __name__ == "__main__":
    main()
