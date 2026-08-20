from __future__ import annotations

"""Da de alta clubes de liga con la plantilla real leida de mondefootball.

Es el hermano de ``import_european_club_1993_94.py``, que hace lo mismo con las
plantillas de eliminatoria de BDFutbol. Cambian dos cosas:

* La plantilla es **de temporada completa**, asi que los clubes salen con
  dieciocho o veinte fichas en vez de con las cinco que jugaron una eliminatoria.
* No hay minutos por partido, asi que el reparto de medias se apoya en el orden
  de la plantilla y en el nivel del club, no en lo jugado.

Lo que no cambia, porque es lo que sostiene todo esto:

* la ficha del club sale de la base original del juego, no se inventa;
* a quien ya existe no se le vuelve a crear;
* **a quien ya tiene club no se le mueve**: si la fuente lo pone en su club de
  origen pero el juego lo tiene en el Hamburgo, es que fichó, y la fuente de la
  temporada manda;
* un caso ambiguo se aparta en el informe y no se aplica.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.app.football9394.mdb_import import normalize_team_row
from backend.app.football9394.mdb_jet4 import Jet4MDB, json_safe
from backend.tools.enrich_world_cup_1994 import (
    build_identity_candidate_index,
    derived_attributes,
    identity_candidate_pool,
    position_fields,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "mondefootball_squads_1993.json"
MAPPING = DATA / "mondefootball_club_mapping.json"
SOURCE_MDB = Path(r"C:\UNIFUTBOL\UNIFUTBOL v14.5\datos.vin\1993\basedatos\basedatos.mdb")
REPORT = DATA / "mondefootball_league_import_report.json"

BATCH = "league_squads_1993_94"
ORIGIN = "league_club_1993_94"
POSITION_CODES = {"POR": "GK", "DEF": "DF", "MED": "MF", "DEL": "FW"}


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split()
    return (parts[0], parts[-1]) if len(parts) > 1 else (full_name, full_name)


def squad_overall(anchor: int, position_in_squad: int, squad_size: int) -> int:
    """Reparte la media del club de arriba abajo segun el orden de la plantilla.

    mondefootball lista por demarcacion y, dentro de cada una, por peso en el
    equipo. No es tan buena señal como los minutos, pero es la que hay, y sin
    ella la plantilla entera saldria con la misma media, que es tan falso como
    inventarla. Nunca sube del nivel del club: los documentados mandan.
    """
    if squad_size <= 1:
        return anchor
    share = 1.0 - (position_in_squad / (squad_size - 1))
    return max(20, min(anchor, anchor - 6 + round(6 * share)))


def club_anchor(snapshot: dict[str, Any], team_id: int, fallback: int) -> int:
    ratings = sorted(int(p.get("overall") or 0) for p in snapshot["players"]
                     if int(p.get("team_id") or 0) == team_id and p.get("overall"))
    return ratings[len(ratings) // 2] if ratings else fallback


def build_player(row: dict[str, Any], *, source_id: int, team_id: int, country_id: int,
                 club_name: str, overall: int) -> dict[str, Any]:
    given, family = split_name(row["full_name"])
    code = POSITION_CODES[row["broad_position"]]
    primary, broad, role_ratings = position_fields(code)
    fuente = f"mondefootball - plantilla 1993-94 del {club_name}"
    return {
        "source_id": source_id, "team_id": team_id,
        "display_name": row["display_name"] or row["full_name"],
        "first_name": given, "surname1": family, "surname2": None,
        "birth_date": f"{row['birth_date']}T00:00:00",
        "birth_country_id": country_id, "international_country_id": country_id,
        "preferred_foot": 1, "shirt_number": row.get("shirt_number"),
        "primary_role": primary, "broad_position": broad,
        "overall": overall, "category": min(99, overall + 1),
        "height_cm": None, "weight_kg": None, "salary": 0, "release_clause": 0,
        "contract_start_year": None, "contract_end_year": None,
        "loan": False, "initially_reserve": False, "retired": False,
        "attributes": derived_attributes(overall, code, f"league-club-{source_id}"),
        "birth_city_id": 0, "naturalized_country_id": None, "basque_origin": False,
        "favorite_shirt_number": 0, "injury_proneness": 0, "progression_mean": 0,
        "fan_affection": 5, "academy_team_id": 0, "previous_team_id": 0,
        "previous_team_years": 0, "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False,
                          "long_shots": False, "cuts_inside": False, "first_time_play": False,
                          "dives": False},
        "identity_source": fuente, "identity_source_url": row["profile_url"],
        "historical_data_source": fuente,
        "mondefootball_id": row["mondefootball_id"],
        "photo_source_url": row.get("photo_url"),
        "attribute_source": "provisional_pending_profile_review",
        "profile_review_required": True,
        "role_detail_source": "verified_historical_broad_position",
        "historical_club_1994": club_name,
        "overall_source": "inferido: nivel del club y orden en la plantilla",
        "external_origin": ORIGIN, "creation_batch": BATCH,
    }


def import_clubs(*, only_new: bool, baseline: int, snapshot_path: Path,
                 squads_path: Path, mapping_path: Path, mdb_path: Path) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    squads = json.loads(squads_path.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    by_mf = {}
    for country, block in squads.items():
        for club in block["clubs"]:
            by_mf[str(club["mondefootball_id"])] = (country, club)

    db = Jet4MDB(mdb_path)
    mdb_rows = {int(r["Id"]): r for r in db.rows("Equipo") if r.get("Id")}
    league_country = {int(l["Id"]): int(l.get("IdPais") or 0) for l in db.rows("Liga")}

    teams = {int(t["source_id"]): t for t in snapshot["teams"]}
    containers = {int(t["source_id"]) for t in snapshot["teams"] if t.get("market_container")}
    index = build_identity_candidate_index(snapshot["players"])
    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    next_id = max([int(p["source_id"]) for p in snapshot["players"]]
                  + [int(t["source_id"]) for t in snapshot["teams"]]) + 1

    done: list[dict[str, Any]] = []
    for entry in mapping["seguros"]:
        if only_new and entry["en_juego"]:
            continue
        found = by_mf.get(str(entry["mf"]))
        if found is None:
            continue
        country, club = found
        team_id = int(entry["mdb"])
        row = mdb_rows.get(team_id)
        team = teams.get(team_id)
        created_team = False
        if team is None:
            if row is None:
                continue
            team = json_safe(asdict(normalize_team_row(row, activation_reason="domestic_league")))
            snapshot["teams"].append(team)
            teams[team_id] = team
            created_team = True
        club_name = team.get("name") or entry["nombre"]
        country_id = league_country.get(int(row.get("Liga") or 0), 0) if row else 0

        moved: list[dict[str, Any]] = []
        kept: list[dict[str, Any]] = []
        created: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []
        for player_row in club["squad"]:
            given, family = split_name(player_row["full_name"])
            candidates = identity_candidate_pool(index, display=player_row["full_name"], given=given,
                                                 family=family, dob=player_row["birth_date"],
                                                 expected_team=None, override=None)
            result = reconcile_player_identity(candidates, target_display=player_row["full_name"],
                                               target_given=given, target_family=family,
                                               target_birth_date=player_row["birth_date"],
                                               target_country_id=country_id or None)
            if result.resolution == "ambiguous_existing_candidates":
                skipped.append({"name": player_row["full_name"],
                                "reason": "varios candidatos existentes, no se decide a ciegas"})
                continue
            if result.player is not None:
                player = by_id[int(result.player["source_id"])]
                player.setdefault("mondefootball_id", player_row["mondefootball_id"])
                if int(player.get("team_id") or 0) in containers:
                    player["team_id"] = team_id
                    player["historical_club_1994"] = club_name
                    moved.append({"source_id": int(player["source_id"]),
                                  "name": player.get("display_name")})
                else:
                    kept.append({"source_id": int(player["source_id"]),
                                 "name": player.get("display_name"),
                                 "team_id": int(player.get("team_id") or 0)})
                continue
            pending.append(player_row)

        anchor = club_anchor(snapshot, team_id, baseline)
        for position, player_row in enumerate(pending):
            overall = squad_overall(anchor, position, len(pending))
            snapshot["players"].append(build_player(player_row, source_id=next_id, team_id=team_id,
                                                    country_id=country_id, club_name=club_name,
                                                    overall=overall))
            created.append({"source_id": next_id, "name": player_row["full_name"], "overall": overall})
            next_id += 1

        done.append({"country": country, "club": club_name, "team_source_id": team_id,
                     "team_created": created_team, "squad_read": len(club["squad"]),
                     "club_level_anchor": anchor, "created": created,
                     "moved_from_container": moved, "left_in_their_club": kept,
                     "not_applied": skipped})

    snapshot["players"].sort(key=lambda p: int(p["source_id"]))
    snapshot["teams"].sort(key=lambda t: int(t["source_id"]))
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "complete", "batch": BATCH, "clubs": len(done),
        "created": sum(len(d["created"]) for d in done),
        "moved_from_container": sum(len(d["moved_from_container"]) for d in done),
        "left_in_their_club": sum(len(d["left_in_their_club"]) for d in done),
        "not_applied": sum(len(d["not_applied"]) for d in done),
        "detail": done,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only-new", action="store_true",
                        help="salta los clubes que ya existen en el juego, que exigen borrar su plantilla inventada")
    parser.add_argument("--baseline", type=int, default=68)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--squads", type=Path, default=SQUADS)
    parser.add_argument("--mapping", type=Path, default=MAPPING)
    parser.add_argument("--mdb", type=Path, default=SOURCE_MDB)
    args = parser.parse_args()
    report = import_clubs(only_new=args.only_new, baseline=args.baseline,
                          snapshot_path=args.snapshot, squads_path=args.squads,
                          mapping_path=args.mapping, mdb_path=args.mdb)
    print(f"clubes {report['clubs']} | creados {report['created']} | "
          f"del contenedor {report['moved_from_container']} | "
          f"dejados en su club {report['left_in_their_club']} | "
          f"sin aplicar {report['not_applied']}")
    for row in report["detail"]:
        print(f"   {row['country']:<10}{row['club']:<28}leidos {row['squad_read']:>2} | "
              f"nuevos {len(row['created']):>2} | rescatados {len(row['moved_from_container'])} | "
              f"nivel {row['club_level_anchor']}")


if __name__ == "__main__":
    main()
