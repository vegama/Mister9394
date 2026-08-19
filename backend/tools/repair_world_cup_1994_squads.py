from __future__ import annotations

"""Repara convocatorias de USA 1994 que apuntan a jugadores inexistentes.

``world_cup_1994_squads.json`` guarda los 22 de cada selección con su
``resolved_source_id``. Si uno solo de esos identificadores no existe en el
universo, ``world_cup_1994_player_ids`` devuelve la lista vacía por seguridad y
la selección entera cuenta como 0/22. El efecto no es cosmético: el Mundial no
se puede simular y **la carrera revienta con un 500 al llegar a junio de 1994**.

El caso encontrado: Nigeria y Noruega apuntaban cada una a un identificador
huérfano. Resultó que **los dos futbolistas ya existían en el universo**, con su
club real de la temporada:

- Uche Okechukwu jugaba en el Fenerbahçe;
- Gøran Sørloth jugaba en el Bursaspor.

Ambos habían entrado con el pase de la liga turca, con la misma fecha de
nacimiento y demarcación que declara la convocatoria. Lo que faltaba no era
gente: era la reconciliación entre la convocatoria del Mundial y la ficha que ya
estaba en la base.

Por eso esta herramienta **reconcilia y no crea**. Busca al futbolista por
nombre, fecha de nacimiento y país, y reapunta la convocatoria a su ficha real.
Crear un jugador nuevo habría duplicado a una persona que ya existía y la habría
dejado colgada de un contenedor ``Otros-`` en vez de en su club, que es
justamente lo que la política de identidad del proyecto prohíbe.

Uso:

    python backend/tools/repair_world_cup_1994_squads.py --check
    python backend/tools/repair_world_cup_1994_squads.py --apply
"""

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "world_cup_1994_squads.json"

BROAD_BY_POSITION = {"GK": "POR", "DF": "DEF", "MF": "MED", "FW": "DEL"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fold(text: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in raw if not unicodedata.combining(c)).casefold().strip()


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


def match_existing(snapshot: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any] | None:
    """Busca en el universo al futbolista que la convocatoria ya describe.

    El criterio es deliberadamente estricto —apellido, fecha de nacimiento y
    demarcación— porque reapuntar una convocatoria a la persona equivocada sería
    peor que dejarla rota: saldría a jugar un Mundial con la ficha de otro.
    """
    player = entry["player"]
    country_id = int(entry["team"]["country_id"])
    birth = str(player.get("birth_date") or "")[:10]
    family = fold(player.get("family_name"))
    display = fold(player.get("display_name"))
    broad = BROAD_BY_POSITION.get(str(player.get("position_code") or "").upper())
    if not birth or not family:
        return None

    for row in snapshot.get("players", []):
        if str(row.get("birth_date") or "")[:10] != birth:
            continue
        if int(row.get("birth_country_id") or 0) != country_id:
            continue
        names = {fold(row.get("surname1")), fold(row.get("display_name"))}
        if not (family in names or display in {fold(row.get("display_name"))}):
            continue
        if broad and row.get("broad_position") and row["broad_position"] != broad:
            continue
        return row
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Repara convocatorias USA 1994 con referencias huérfanas")
    parser.add_argument("--apply", action="store_true", help="Reapunta las convocatorias a la ficha real.")
    parser.add_argument("--check", action="store_true", help="Sólo informa (por defecto).")
    args = parser.parse_args()

    snapshot = load(SNAPSHOT)
    squads = load(SQUADS)
    missing = find_dangling(snapshot, squads)

    if not missing:
        print("OK: ninguna convocatoria de USA 1994 cita jugadores inexistentes.")
        return 0

    teams_by_id = {int(row["source_id"]): row.get("name") for row in snapshot.get("teams", [])}
    resolved: list[tuple[dict[str, Any], dict[str, Any]]] = []
    unresolved: list[dict[str, Any]] = []
    for entry in missing:
        found = match_existing(snapshot, entry)
        (resolved.append((entry, found)) if found is not None else unresolved.append(entry))

    print(f"Referencias huérfanas: {len(missing)}")
    for entry, found in resolved:
        club = teams_by_id.get(int(found.get("team_id") or 0)) or "sin club"
        print(f"  · {entry['player'].get('display_name')} ({entry['team'].get('name')}) "
              f"-> ya existe como {found['source_id']} en {club}")
    for entry in unresolved:
        print(f"  · {entry['player'].get('display_name')} ({entry['team'].get('name')}) "
              f"-> SIN correspondencia en el universo; requiere alta verificada a mano")

    if not args.apply:
        print("\nSin cambios. Ejecuta con --apply para reapuntar las convocatorias.")
        return 1
    if unresolved:
        print("\nNo se aplica nada: hay huérfanos sin correspondencia y crear jugadores "
              "automáticamente duplicaría personas. Resuélvelos antes.")
        return 1

    for entry, found in resolved:
        player = entry["player"]
        team = entry["team"]
        player["resolved_source_id"] = int(found["source_id"])
        player["resolution"] = "reconciled_existing_club_player"
        player["game_team_id"] = int(found.get("team_id") or 0)
        player["game_team_name"] = teams_by_id.get(int(found.get("team_id") or 0))
        # La ficha del futbolista debe llevar la marca del Mundial igual que el
        # resto de convocados; sin ella jugaría USA 94 sin que su ficha lo diga.
        found["historical_squad_1994"] = True
        found["world_cup_1994"] = {
            "team_code": team.get("team_code"),
            "country_id": int(team["country_id"]),
            "group": team.get("group"),
            "shirt_number": player.get("shirt_number"),
            "position": str(player.get("position_code") or "").upper(),
            "external_player_id": player.get("external_player_id"),
        }
    SQUADS.write_text(json.dumps(squads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nReapuntadas {len(resolved)} convocatorias en {SQUADS.relative_to(ROOT)} "
          f"y marcadas sus fichas en {SNAPSHOT.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
