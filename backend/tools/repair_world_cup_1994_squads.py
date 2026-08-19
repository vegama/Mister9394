from __future__ import annotations

"""Repara convocatorias de USA 1994 que referencian jugadores inexistentes.

``world_cup_1994_squads.json`` guarda los 22 de cada selección con su
``resolved_source_id``. Si uno solo de esos identificadores no existe en el
universo, ``world_cup_1994_player_ids`` devuelve la lista vacía por seguridad y
la selección entera pasa a contar como 0/22. El efecto no es cosmético: el
Mundial no se puede simular y **la carrera revienta con un 500 al llegar a junio
de 1994**, sin haber hecho nada raro.

El caso encontrado: Nigeria y Noruega arrastraban cada una un identificador
huérfano —Uche Okechukwu y Göran Sørloth— perdidos en algún punto del pipeline
de creación. Sus vecinos de identificador existían todos, así que eran dos
huecos en una secuencia por lo demás contigua. Mientras tanto la interfaz
mostraba «22/22» para ambas, porque ese contador mira el fichero de
convocatorias y no el universo.

La herramienta reconstruye a los jugadores que faltan:

- la **identidad** (nombre, fecha de nacimiento, dorsal, demarcación, país y
  club contenedor) sale del propio fichero de convocatorias, que es fuente
  citable — Fjelstul World Cup Database, igual que sus compañeros;
- los **atributos** no se inventan ni se clonan de un compañero concreto: se
  derivan de la mediana de sus compañeros de selección en la misma demarcación
  y quedan etiquetados como inferidos, para que nunca se confundan con dato
  histórico.

Uso:

    python backend/tools/repair_world_cup_1994_squads.py --check
    python backend/tools/repair_world_cup_1994_squads.py --apply
"""

import argparse
import json
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "world_cup_1994_squads.json"

BROAD_BY_POSITION = {"GK": "POR", "DF": "DEF", "MF": "MED", "FW": "DEL"}
ATTRIBUTE_SOURCE = "inferred_from_world_cup_cohort_repair"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_dangling(snapshot: dict[str, Any], squads: dict[str, Any]) -> list[dict[str, Any]]:
    """Jugadores citados por una convocatoria que no existen en el universo."""
    known = {int(row["source_id"]) for row in snapshot.get("players", [])}
    missing: list[dict[str, Any]] = []
    for team in squads.get("teams", []):
        for player in team.get("players", []):
            source_id = player.get("resolved_source_id")
            if source_id is None or int(source_id) in known:
                continue
            missing.append({"team": team, "player": player, "source_id": int(source_id)})
    return missing


def cohort(snapshot: dict[str, Any], country_id: int, broad: str) -> list[dict[str, Any]]:
    """Compañeros de selección en la misma demarcación."""
    rows = [
        row for row in snapshot.get("players", [])
        if int(row.get("international_country_id") or 0) == country_id
        and row.get("broad_position") == broad
    ]
    return rows or [
        row for row in snapshot.get("players", [])
        if int(row.get("international_country_id") or 0) == country_id
    ]


def median_int(values: list[Any], fallback: int) -> int:
    numbers = [int(v) for v in values if isinstance(v, (int, float))]
    return int(round(median(numbers))) if numbers else fallback


def build_player(entry: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    player = entry["player"]
    team = entry["team"]
    country_id = int(team["country_id"])
    position_code = str(player.get("position_code") or "MF").upper()
    broad = BROAD_BY_POSITION.get(position_code, "MED")
    peers = cohort(snapshot, country_id, broad)
    if not peers:
        raise ValueError(f"sin cohorte para reconstruir a {player.get('display_name')}")

    template = max(peers, key=lambda row: int(row.get("overall") or 0))
    overall = median_int([row.get("overall") for row in peers], 70)

    attributes: dict[str, int] = {}
    for key in (template.get("attributes") or {}):
        attributes[key] = median_int([(row.get("attributes") or {}).get(key) for row in peers],
                                     overall)

    role_ratings = dict(template.get("role_ratings") or {})
    birth_date = str(player.get("birth_date") or "")
    shirt = player.get("shirt_number")

    built = {key: template.get(key) for key in template}
    built.update({
        "source_id": entry["source_id"],
        "team_id": int(player.get("game_team_id") or template.get("team_id") or 0),
        "display_name": player.get("display_name"),
        "first_name": player.get("given_name"),
        "surname1": player.get("family_name"),
        "surname2": None,
        "birth_date": f"{birth_date}T00:00:00" if birth_date else None,
        "birth_country_id": country_id,
        "international_country_id": country_id,
        "shirt_number": shirt,
        "favorite_shirt_number": shirt,
        "broad_position": broad,
        "overall": overall,
        "category": overall,
        "attributes": attributes,
        "role_ratings": role_ratings,
        "historical_squad_1994": True,
        "world_cup_1994": {
            "team_code": team.get("team_code"),
            "country_id": country_id,
            "group": team.get("group"),
            "shirt_number": shirt,
            "position": position_code,
            "external_player_id": player.get("external_player_id"),
        },
        "identity_source": "Fjelstul World Cup Database",
        "attribute_source": ATTRIBUTE_SOURCE,
        "historical_club_1994": player.get("game_team_name"),
        "external_origin": "world_cup_1994",
        "repair_note": (
            "Reconstruido: la convocatoria de USA 1994 lo citaba pero no existía en el "
            "universo, lo que dejaba la selección en 0/22 y hacía fallar el Mundial. "
            "Identidad tomada de la convocatoria; atributos inferidos de la mediana de "
            "sus compañeros de selección en la misma demarcación."
        ),
    })
    # Campos que no deben heredarse del compañero usado como plantilla.
    for key in ("height_cm", "weight_kg", "previous_team_id", "academy_team_id",
                "profile_review_0_23", "profile_review_required"):
        built.pop(key, None)
    return built


def main() -> int:
    parser = argparse.ArgumentParser(description="Repara convocatorias USA 1994 con referencias huérfanas")
    parser.add_argument("--apply", action="store_true", help="Escribe los jugadores reconstruidos.")
    parser.add_argument("--check", action="store_true", help="Sólo informa (por defecto).")
    args = parser.parse_args()

    snapshot = load(SNAPSHOT)
    squads = load(SQUADS)
    missing = find_dangling(snapshot, squads)

    if not missing:
        print("OK: ninguna convocatoria de USA 1994 cita jugadores inexistentes.")
        return 0

    print(f"Referencias huérfanas encontradas: {len(missing)}")
    for entry in missing:
        player = entry["player"]
        print(f"  · {entry['source_id']} {player.get('display_name')} "
              f"({entry['team'].get('name')}, {player.get('position_code')})")

    if not args.apply:
        print("\nSin cambios. Ejecuta con --apply para reconstruirlos.")
        return 1

    built = [build_player(entry, snapshot) for entry in missing]
    snapshot["players"].extend(built)
    snapshot["players"].sort(key=lambda row: int(row["source_id"]))
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nReconstruidos {len(built)} jugadores en {SNAPSHOT.relative_to(ROOT)}:")
    for row in built:
        print(f"  · {row['source_id']} {row['display_name']} · {row['broad_position']} · media {row['overall']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
