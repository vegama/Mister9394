from __future__ import annotations

"""Source-backed Uruguay 1993 roster coverage for the v1.1.3 data pass.

The pass is deliberately conservative:
- only identities with an independently verified DOB/role are added;
- a dated 1993 squad/match/club-history source must place the player at the club;
- attributes are fixed one-time estimates from same-era role/level comparables;
- no synthetic filler is created simply to reach a squad-size target.
"""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "database_uruguay_roster_coverage_v113.json"

RACING_TEAM_ID = 404
LIVERPOOL_TEAM_ID = 997
URUGUAY_COUNTRY_ID = 2

RACING_1993_SOURCE = "https://historiascoperas.blogspot.com/2015/12/racing-club-de-montevideo.html"
LIVERPOOL_1993_SOURCE = "https://historiascoperas.blogspot.com/2016/04/liverpool-futbol-club-montevideo-uruguay.html"
LIVERPOOL_NACIONAL_1993_SOURCE = "https://www.tenfield.com.uy/campeonato-uruguayo-liverpool-no-le-gana-a-nacional-en-belvedere-desde-1993/"

# These are deliberately not a full reconstructed roster.  Each addition has
# both identity evidence and explicit 1993 club evidence.
URUGUAY_ADDITIONS: tuple[dict[str, Any], ...] = (
    {
        "source_id": 9499110,
        "team_id": RACING_TEAM_ID,
        "display_name": "Euler Correa",
        "first_name": "Euler Selvino",
        "surname1": "Correa",
        "surname2": None,
        "historical_full_name": "Euler Selvino Correa",
        "birth_date": "1970-07-20T00:00:00",
        "birth_place_text": "Salto, Uruguay",
        "primary_role": 1,
        "broad_position": "DEF",
        "historical_position_1993_94": "Right Back",
        "overall": 70,
        "preferred_foot": 1,
        "comparable_source_id": 9706,  # Leonardo Jara, same Racing/role/level
        "identity_source": "Transfermarkt · Euler Correa profile",
        "identity_source_url": "https://www.transfermarkt.es/euler-correa/profil/spieler/1478671",
        "club_source": "Racing Club de Montevideo · 1993 historical squad photograph",
        "club_source_url": RACING_1993_SOURCE,
        "source_note": "Named in Racing 1993 historical squad; identity/DOB/right-back role independently verified.",
    },
    {
        "source_id": 9499111,
        "team_id": RACING_TEAM_ID,
        "display_name": "Richard López",
        "first_name": "Richard Javier",
        "surname1": "López",
        "surname2": "Saldia",
        "historical_full_name": "Richard Javier López Saldia",
        "birth_date": "1972-05-09T00:00:00",
        "birth_place_text": "Montevideo, Uruguay",
        "primary_role": 8,
        "broad_position": "MED",
        "historical_position_1993_94": "Attacking Midfielder",
        "overall": 69,
        "preferred_foot": 1,
        "comparable_source_id": 9749,  # Uruguay attacking/midfield level anchor
        "identity_source": "Atilio · Richard López",
        "identity_source_url": "https://atilio.uy/jugador:1044",
        "club_source": "Racing 1993 historical squad + Progreso 1-2 Racing, 18 Apr 1993",
        "club_source_url": RACING_1993_SOURCE,
        "source_note": "Named in Racing 1993 squad and scored for Racing against Progreso on 18 Apr 1993.",
    },
    {
        "source_id": 9499112,
        "team_id": RACING_TEAM_ID,
        "display_name": "Diego Seoane",
        "first_name": "Diego",
        "surname1": "Seoane",
        "surname2": None,
        "historical_full_name": "Diego Seoane",
        "birth_date": "1969-01-10T00:00:00",
        "birth_place_text": "Montevideo, Uruguay",
        "primary_role": 17,
        "broad_position": "DEL",
        "historical_position_1993_94": "Forward",
        "overall": 70,
        "preferred_foot": 1,
        "comparable_source_id": 9714,  # Raul Roganovich, Racing forward anchor
        "identity_source": "Asociación Uruguaya de Fútbol · Diego Seoane",
        "identity_source_url": "https://www.auf.org.uy/diego-seoane/",
        "club_source": "FootballDatabase · Diego Seoane club history",
        "club_source_url": "https://www.footballdatabase.eu/en/player/details/52053-diego-seoane",
        "source_note": "Club history places him at Racing CM in 1992 and 1993; AUF verifies DOB and forward position.",
    },
    {
        "source_id": 9499120,
        "team_id": LIVERPOOL_TEAM_ID,
        "display_name": "Ramón Castro",
        "first_name": "Ramón Víctor",
        "surname1": "Castro",
        "surname2": "García",
        "historical_full_name": "Ramón Víctor Castro García",
        "birth_date": "1964-06-13T00:00:00",
        "birth_place_text": "Montevideo, Uruguay",
        "primary_role": 7,
        "broad_position": "MED",
        "historical_position_1993_94": "Central Midfielder",
        "overall": 73,
        "preferred_foot": 1,
        "height_cm": 178,
        "weight_kg": 78,
        "comparable_source_id": 9709,  # Gustavo Dalto, Uruguay central-midfield level anchor
        "identity_source": "Asociación Uruguaya de Fútbol · Ramón Castro García",
        "identity_source_url": "https://www.auf.org.uy/ramon-castro-garcia/",
        "club_source": "Tenfield · Liverpool 1-0 Nacional, 24 Apr 1993",
        "club_source_url": LIVERPOOL_NACIONAL_1993_SOURCE,
        "source_note": "Started for Liverpool and scored the winning goal against Nacional on 24 Apr 1993.",
    },
)


def _scaled_attributes(source: dict[str, Any], target_overall: int) -> dict[str, int]:
    delta = int(target_overall) - int(source.get("overall") or target_overall)
    attrs = deepcopy(source.get("attributes") or {})
    return {key: max(35, min(92, int(value) + delta)) for key, value in attrs.items()}


def _role_ratings(role: int) -> dict[str, int]:
    ratings = {str(i): 0 for i in range(18)}
    ratings[str(role)] = 100
    secondary = {
        1: (3, 4),
        7: (6, 8),
        8: (7, 9),
        17: (11,),
    }.get(role, ())
    for item in secondary:
        ratings[str(item)] = 80
    return ratings


def _new_player(spec: dict[str, Any], comparable: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(comparable)
    row.update({
        "source_id": int(spec["source_id"]),
        "team_id": int(spec["team_id"]),
        "display_name": spec["display_name"],
        "first_name": spec["first_name"],
        "surname1": spec["surname1"],
        "surname2": spec.get("surname2"),
        "historical_full_name": spec["historical_full_name"],
        "birth_date": spec["birth_date"],
        "birth_country_id": URUGUAY_COUNTRY_ID,
        "birth_city_id": None,
        "international_country_id": None,
        "naturalized_country_id": None,
        "historical_birth_place_text": spec.get("birth_place_text"),
        "primary_role": int(spec["primary_role"]),
        "broad_position": spec["broad_position"],
        "historical_position_1993_94": spec["historical_position_1993_94"],
        "overall": int(spec["overall"]),
        "category": int(spec["overall"]),
        "attributes": _scaled_attributes(comparable, int(spec["overall"])),
        "role_ratings": _role_ratings(int(spec["primary_role"])),
        "preferred_foot": int(spec["preferred_foot"]),
        "shirt_number": None,
        "height_cm": spec.get("height_cm"),
        "weight_kg": spec.get("weight_kg"),
        "retired": False,
        "external_origin": "verified_uruguay_1993_roster_v113",
        "creation_batch": "roster_coverage_v113_uruguay",
        "identity_source": spec["identity_source"],
        "identity_source_url": spec["identity_source_url"],
        "historical_data_source": spec["club_source"],
        "historical_profile_source_url": spec["identity_source_url"],
        "historical_club_source_url": spec["club_source_url"],
        "historical_club_1993": "Racing Club de Montevideo" if int(spec["team_id"]) == RACING_TEAM_ID else "Liverpool Fútbol Club",
        "attribute_source": "fixed_same_era_role_level_comparable_v113",
        "attribute_comparable_source_id": int(spec["comparable_source_id"]),
        "attribute_comparable_source_ids": [int(spec["comparable_source_id"])],
        "attribute_method_note": "Fixed one-time estimate from same-era Uruguay role/team-level comparable; not a runtime formula.",
        "profile_review_required": False,
        "source_confidence": "high_identity_high_1993_club_medium_attributes",
        "source_note_v113": spec["source_note"],
    })
    # Comparable provides only the football attribute shape.  Never inherit its
    # biography, IDs, contracts, transfer metadata or merge history.
    for key in (
        "bdfutbol_id", "bdfutbol_url", "source_profile_url",
        "identity_merge_history", "merged_into_source_id", "historical_exclusion_reason",
        "snapshot_inactive_reason", "snapshot_inactive_source_url", "snapshot_inactive_semantics",
        "contract_start_year", "contract_end_year", "previous_team_id", "previous_team_years",
        "loan", "buyback_option", "release_clause", "historical_club_spells_1993_94",
        "historical_club_spells_later", "identity_aliases", "transliteration_aliases",
    ):
        row.pop(key, None)
    row["contract_start_year"] = None
    row["contract_end_year"] = None
    row["previous_team_id"] = 0
    row["previous_team_years"] = 0
    row["loan"] = False
    row["buyback_option"] = 0
    row["release_clause"] = 0
    return row


def apply() -> dict[str, Any]:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    players: list[dict[str, Any]] = snapshot["players"]
    by_id = {int(p["source_id"]): p for p in players}

    # Stable baseline for idempotent reruns: count the active snapshot before
    # this tool's own additions, while retaining all other chronology fixes.
    before = {
        RACING_TEAM_ID: sum(1 for p in players if int(p.get("team_id") or 0) == RACING_TEAM_ID and not p.get("retired") and p.get("creation_batch") != "roster_coverage_v113_uruguay"),
        LIVERPOOL_TEAM_ID: sum(1 for p in players if int(p.get("team_id") or 0) == LIVERPOOL_TEAM_ID and not p.get("retired") and p.get("creation_batch") != "roster_coverage_v113_uruguay"),
    }
    additions: list[dict[str, Any]] = []

    for spec in URUGUAY_ADDITIONS:
        source_id = int(spec["source_id"])
        comparable = by_id[int(spec["comparable_source_id"])]
        rebuilt = _new_player(spec, comparable)
        if source_id in by_id:
            existing = by_id[source_id]
            if existing.get("creation_batch") != "roster_coverage_v113_uruguay":
                raise RuntimeError(f"Refusing to overwrite unrelated source_id {source_id}")
            existing.clear()
            existing.update(rebuilt)
        else:
            players.append(rebuilt)
            by_id[source_id] = rebuilt
        additions.append({
            "source_id": source_id,
            "display_name": rebuilt["display_name"],
            "team_id": rebuilt["team_id"],
            "overall": rebuilt["overall"],
            "primary_role": rebuilt["primary_role"],
            "identity_source_url": rebuilt["identity_source_url"],
            "club_source_url": rebuilt["historical_club_source_url"],
        })

    after = {
        RACING_TEAM_ID: sum(1 for p in players if int(p.get("team_id") or 0) == RACING_TEAM_ID and not p.get("retired")),
        LIVERPOOL_TEAM_ID: sum(1 for p in players if int(p.get("team_id") or 0) == LIVERPOOL_TEAM_ID and not p.get("retired")),
    }

    snapshot.setdefault("database_hygiene", {}).setdefault("v1.1.3", {})["uruguay_1993_roster_coverage"] = {
        "active_before": {"Racing de Montevideo": before[RACING_TEAM_ID], "Liverpool": before[LIVERPOOL_TEAM_ID]},
        "active_after": {"Racing de Montevideo": after[RACING_TEAM_ID], "Liverpool": after[LIVERPOOL_TEAM_ID]},
        "source_backed_additions": [int(spec["source_id"]) for spec in URUGUAY_ADDITIONS],
        "policy": "Verified identities and explicit 1993 club evidence only; no count-driven filler.",
    }
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "checkpoint": "1.1.3-data",
        "status": "pass",
        "active_before": {"Racing de Montevideo": before[RACING_TEAM_ID], "Liverpool": before[LIVERPOOL_TEAM_ID]},
        "active_after": {"Racing de Montevideo": after[RACING_TEAM_ID], "Liverpool": after[LIVERPOOL_TEAM_ID]},
        "additions": additions,
        "policy": "Real source-backed 1993 players only; fixed conservative attributes; no synthetic filler.",
        "remaining_note": "Neither club is padded to 18 if another identity cannot yet be independently verified.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
