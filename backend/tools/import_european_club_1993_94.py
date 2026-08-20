from __future__ import annotations

"""Levanta un club europeo del 93-94 con su plantilla real.

Junta tres fuentes, cada una para lo que sabe:

* **La base original del juego** da la ficha del club —estadio, presidente,
  socios, palmarés, rival— porque el club siempre estuvo ahí; lo que el
  importador no seleccionó fue su liga. Se copia, no se inventa.
* **BDFutbol** da la plantilla real de la eliminatoria europea, con
  identificador propio y foto de cada futbolista.
* **El universo actual** manda sobre las dos anteriores: a quien ya existe no se
  le vuelve a crear.

Dos reglas que evitan destrozos:

**Sólo se mueve a quien está en un contenedor.** Kåre Ingebrigtsen aparece en la
plantilla europea del Rosenborg y en el juego está en el Manchester City, que es
donde lo puso la fuente de la temporada: se fue a Inglaterra ese mismo año.
Sacarlo de un club modelado por haber jugado una eliminatoria sería empeorar el
dato, así que a quien ya tiene club se le deja donde está.

**Los atributos se anclan a futbolistas reales.** Igual que el resto de altas del
proyecto, cada ficha nueva se deriva después de dos comparables de su demarcación
con ``anchor_pool_profiles_to_comparables``; aquí sólo se crean.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.app.football9394.mdb_import import normalize_team_row
from backend.app.football9394.mdb_jet4 import Jet4MDB, json_safe
from backend.tools.bdfutbol_club_squad import read_squad
from backend.tools.enrich_world_cup_1994 import (
    build_identity_candidate_index,
    derived_attributes,
    identity_candidate_pool,
    position_fields,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SOURCE_MDB = Path(r"C:\UNIFUTBOL\UNIFUTBOL v14.5\datos.vin\1993\basedatos\basedatos.mdb")

BATCH = "european_participants_1993_94"
ORIGIN = "european_club_1993_94"
POSITION_CODES = {"POR": "GK", "DEF": "DF", "MED": "MF", "DEL": "FW"}


def mdb_team(team_id: int, mdb_path: Path) -> dict[str, Any]:
    db = Jet4MDB(mdb_path)
    row = next((r for r in db.rows("Equipo") if int(r.get("Id") or 0) == team_id), None)
    if row is None:
        raise SystemExit(f"el equipo {team_id} no esta en {mdb_path}")
    return json_safe(asdict(normalize_team_row(row, activation_reason="continental_participant")))


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split()
    return (parts[0], parts[-1]) if len(parts) > 1 else (full_name, full_name)


def build_player(row: dict[str, Any], *, source_id: int, team_id: int, country_id: int,
                 club_name: str, overall: int) -> dict[str, Any]:
    given, family = split_name(row["full_name"])
    code = POSITION_CODES[row["broad_position"]]
    primary, broad, role_ratings = position_fields(code)
    fuente = f"BDFutbol - plantilla europea 1993-94 del {club_name}"
    return {
        "source_id": source_id,
        "team_id": team_id,
        "display_name": row["display_name"] or row["full_name"],
        "first_name": given,
        "surname1": family,
        "surname2": None,
        "birth_date": f"{row['birth_date']}T00:00:00",
        "birth_country_id": country_id,
        "international_country_id": country_id,
        "preferred_foot": 1,
        "shirt_number": None,
        "primary_role": primary,
        "broad_position": broad,
        "overall": overall,
        "category": min(99, overall + 1),
        "height_cm": None, "weight_kg": None, "salary": 0, "release_clause": 0,
        "contract_start_year": None, "contract_end_year": None,
        "loan": False, "initially_reserve": False, "retired": False,
        "attributes": derived_attributes(overall, code, f"european-club-{source_id}"),
        "birth_city_id": 0, "naturalized_country_id": None, "basque_origin": False,
        "favorite_shirt_number": 0, "injury_proneness": 0, "progression_mean": 0,
        "fan_affection": 5, "academy_team_id": 0, "previous_team_id": 0,
        "previous_team_years": 0, "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False,
                          "long_shots": False, "cuts_inside": False, "first_time_play": False,
                          "dives": False},
        "identity_source": fuente,
        "identity_source_url": row["profile_url"],
        "historical_data_source": fuente,
        "bdfutbol_id": row["bdfutbol_id"],
        "bdfutbol_url": row["profile_url"],
        "attribute_source": "provisional_pending_profile_review",
        "profile_review_required": True,
        "role_detail_source": "verified_historical_broad_position",
        "historical_club_1994": club_name,
        "overall_source": "inferido: nivel del club y minutos jugados en la eliminatoria europea",
        "external_origin": ORIGIN,
        "creation_batch": BATCH,
    }


def club_anchor(snapshot: dict[str, Any], team_id: int, fallback: int) -> int:
    """Nivel del club, tomado de los suyos que ya tienen ficha en el juego.

    Es mucho mejor referencia que un número fijo: al Rosenborg ya se le conocen
    Løken, Strand, Leonhardsen y By Rise entre 73 y 75, así que el club es de ese
    nivel y no del 68 por defecto.
    """
    ratings = sorted(
        int(p.get("overall") or 0) for p in snapshot["players"]
        if int(p.get("team_id") or 0) == team_id and p.get("overall")
    )
    return ratings[len(ratings) // 2] if ratings else fallback


def minutes_overall(anchor: int, minutes: int | None, best: int) -> int:
    """Reparte la media alrededor del nivel del club segun lo que jugo cada uno.

    Sin esto la plantilla entera sale clavada a la misma media, que es tan falso
    como inventarla. Los minutos de la eliminatoria son dato real de la fuente:
    quien jugo los cuatro partidos enteros era titular y quien no salio del
    banquillo, no. Es una inferencia, y como tal queda etiquetada en la ficha.
    """
    share = (minutes / best) if (minutes and best) else 0.0
    # El reparto va del nivel del club hacia abajo y nunca por encima: los que ya
    # tenian ficha son los documentados —Leonhardsen, Strand, By Rise— y una
    # media inferida no puede pasarles por delante sin ninguna prueba.
    return max(20, min(anchor, anchor - 6 + round(6 * share)))


def import_club(club_bdfutbol_id: str, team_source_id: int, *, country_id: int,
                baseline: int, snapshot_path: Path, mdb_path: Path, delay: float) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    squad = read_squad(club_bdfutbol_id, delay=delay)

    teams = {int(t["source_id"]): t for t in snapshot["teams"]}
    team = teams.get(team_source_id)
    created_team = False
    if team is None:
        team = mdb_team(team_source_id, mdb_path)
        snapshot["teams"].append(team)
        created_team = True
    club_name = team.get("name") or squad["club_name"]

    index = build_identity_candidate_index(snapshot["players"])
    by_id = {int(p["source_id"]): p for p in snapshot["players"]}
    containers = {int(t["source_id"]) for t in snapshot["teams"] if t.get("market_container")}
    next_id = max([int(p["source_id"]) for p in snapshot["players"]]
                  + [int(t["source_id"]) for t in snapshot["teams"]]) + 1

    moved: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    created: list[dict[str, Any]] = []
    not_applied: list[dict[str, Any]] = []

    pending: list[dict[str, Any]] = []
    for row in squad["squad"]:
        if not row["birth_date"]:
            not_applied.append({"bdfutbol_id": row["bdfutbol_id"], "name": row["full_name"],
                                "reason": "sin fecha de nacimiento, no se puede reconciliar"})
            continue
        given, family = split_name(row["full_name"])
        candidates = identity_candidate_pool(index, display=row["full_name"], given=given, family=family,
                                             dob=row["birth_date"], expected_team=None, override=None)
        result = reconcile_player_identity(candidates, target_display=row["full_name"], target_given=given,
                                           target_family=family, target_birth_date=row["birth_date"],
                                           target_country_id=country_id)
        if result.resolution == "ambiguous_existing_candidates":
            not_applied.append({"bdfutbol_id": row["bdfutbol_id"], "name": row["full_name"],
                                "reason": "varios candidatos existentes, no se decide a ciegas"})
            continue
        if result.player is not None:
            player = by_id[int(result.player["source_id"])]
            player.setdefault("bdfutbol_id", row["bdfutbol_id"])
            player.setdefault("bdfutbol_url", row["profile_url"])
            if int(player.get("team_id") or 0) in containers:
                player["team_id"] = team_source_id
                player["historical_club_1994"] = club_name
                moved.append({"source_id": int(player["source_id"]), "name": player.get("display_name")})
            else:
                kept.append({"source_id": int(player["source_id"]), "name": player.get("display_name"),
                             "team_id": int(player.get("team_id") or 0)})
            continue
        pending.append(row)

    # El nivel del club se calcula cuando ya estan dentro los que se conocian:
    # hacerlo antes daria el valor por defecto y saldria una plantilla plana.
    anchor = club_anchor(snapshot, team_source_id, baseline)
    # Hay clubes cuya pagina existe pero no trae plantilla: BDFutbol simplemente
    # no la tiene. No es un error de lectura y no debe cortar el lote.
    best = max((r.get("minutes") or 0) for r in squad["squad"]) if squad["squad"] else 0
    for row in pending:
        overall = minutes_overall(anchor, row.get("minutes"), best)
        snapshot["players"].append(build_player(row, source_id=next_id, team_id=team_source_id,
                                                country_id=country_id, club_name=club_name,
                                                overall=overall))
        created.append({"source_id": next_id, "name": row["full_name"],
                        "minutes": row.get("minutes"), "overall": overall})
        next_id += 1

    snapshot["players"].sort(key=lambda p: int(p["source_id"]))
    snapshot["teams"].sort(key=lambda t: int(t["source_id"]))
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "complete",
        "club": club_name,
        "team_source_id": team_source_id,
        "team_created": created_team,
        "squad_read": len(squad["squad"]),
        "moved_from_container": moved,
        "left_in_their_club": kept,
        "created": created,
        "not_applied": not_applied,
        "club_level_anchor": anchor,
        "overall_policy": "nivel del club por sus jugadores ya conocidos, repartido por minutos reales de la eliminatoria",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bdfutbol_id", help="identificador de BDFutbol, p.ej. 10038")
    parser.add_argument("team_source_id", type=int, help="identificador en la base original, p.ej. 599")
    parser.add_argument("--country-id", type=int, required=True)
    parser.add_argument("--baseline", type=int, default=68,
                        help="media a usar si el club aun no tiene con quien comparar")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--mdb", type=Path, default=SOURCE_MDB)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = import_club(args.bdfutbol_id, args.team_source_id, country_id=args.country_id,
                         baseline=args.baseline, snapshot_path=args.snapshot,
                         mdb_path=args.mdb, delay=args.delay)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['club']}: leidos {report['squad_read']} | creados {len(report['created'])} | "
          f"movidos del contenedor {len(report['moved_from_container'])} | "
          f"dejados en su club {len(report['left_in_their_club'])} | "
          f"sin aplicar {len(report['not_applied'])}")
    for row in report["left_in_their_club"]:
        print(f"   se queda donde esta: {row['name']}")
    for row in report["not_applied"]:
        print(f"   SIN APLICAR {row['name']}: {row['reason']}")


if __name__ == "__main__":
    main()
