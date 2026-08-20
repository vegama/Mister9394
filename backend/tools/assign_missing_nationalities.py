from __future__ import annotations

"""Da nacionalidad internacional a quien no la tiene en la base.

Ocho mil futbolistas activos llegaron del MDB sin ``international_country_id``.
Para las convocatorias no se notaba —``_country_id`` ya caía hacia el país de
nacimiento— pero la ficha del jugador sí lo enseña: gente con club, edad y media
y el apartado de nacionalidad en blanco.

La regla es la que aplica el fútbol por defecto: **se juega donde se ha
nacido**, salvo que algo diga lo contrario. Aquí no hay nada que diga lo
contrario, así que se rellena desde el país de nacimiento y se deja constancia
de que es una inferencia y no un dato de fuente, que es la política de este
proyecto para todo lo que no sale de un documento.

Dos precisiones:

* **Quien no tiene ni país de nacimiento se queda en blanco.** Son unos
  cuatrocientos y no hay de dónde sacarlo; inventarles una selección sería
  exactamente lo que no queremos.
* **Montenegro no existe como selección en 1993.** Sus futbolistas jugaban con
  Yugoslavia y no tienen equipo propio hasta 2006, así que la nacionalidad
  deportiva se apunta a Yugoslavia aunque el lugar de nacimiento se conserve.
"""

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "nationality_backfill_report.json"

# Entidades que en 1993-94 no tenían selección propia: el lugar de nacimiento se
# respeta, pero la nacionalidad deportiva es la del país que sí competía.
SPORTING_SUCCESSION = {
    76: 75,   # Montenegro -> Yugoslavia
}

# Errores del país de origen en la fuente. Se corrigen uno a uno y con nombre y
# apellidos, nunca por regla: aquí el MDB apuntó a Papúa Nueva Guinea (185) a dos
# futbolistas guineanos (91), casi seguro por el parecido del nombre del país.
# Titi Camara jugaba en el Saint-Étienne y Mohamed Sylla en el Willem II, donde
# coincidía con Soumah, que sí figura como guineano.
BIRTH_COUNTRY_CORRECTIONS = {
    6225: (185, 91, "Titi Camara"),
    6710: (185, 91, "Mohamed Sylla"),
}


def backfill(snapshot_path: Path = SNAPSHOT, report_path: Path = REPORT) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    asignados = 0
    sucesion = 0
    corregidos: list[dict[str, Any]] = []
    sin_pista: list[dict[str, Any]] = []

    for player in snapshot.get("players", []):
        fix = BIRTH_COUNTRY_CORRECTIONS.get(int(player.get("source_id") or 0))
        if fix is None:
            continue
        wrong, right, expected_name = fix
        if int(player.get("birth_country_id") or 0) != wrong:
            continue  # ya corregido, o la ficha ha cambiado: no se toca a ciegas
        player["birth_country_id"] = right
        history = player.setdefault("verified_data_corrections", [])
        history.append({
            "batch": "nationality_backfill_v113",
            "field": "birth_country_id",
            "before": wrong,
            "after": right,
            "reason": "el país de origen de la fuente era erróneo; el futbolista es guineano",
        })
        corregidos.append({"source_id": int(player["source_id"]), "display_name": expected_name,
                           "before": wrong, "after": right})

    for player in snapshot.get("players", []):
        if player.get("retired") or player.get("international_country_id"):
            continue
        birth = player.get("birth_country_id")
        if not birth:
            sin_pista.append({
                "source_id": int(player["source_id"]),
                "display_name": player.get("display_name"),
                "team_id": player.get("team_id"),
            })
            continue
        country_id = SPORTING_SUCCESSION.get(int(birth), int(birth))
        if country_id != int(birth):
            sucesion += 1
        player["international_country_id"] = country_id
        player["international_country_source"] = "inferido_del_pais_de_nacimiento"
        asignados += 1

    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "complete",
        "policy": "international_country_id = birth_country_id, marcado como inferencia",
        "assigned": asignados,
        "sporting_succession_applied": sucesion,
        "birth_country_corrections": corregidos,
        "left_blank_no_evidence": len(sin_pista),
        "players_without_any_country": sin_pista,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    report = backfill(args.snapshot, args.report)
    print(json.dumps({k: v for k, v in report.items() if k != "players_without_any_country"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
