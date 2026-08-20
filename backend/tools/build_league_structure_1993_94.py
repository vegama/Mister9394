from __future__ import annotations

"""Crea las seis ligas del 93-94 y coloca en ellas a sus clubes.

Las ligas del MDB no sirven aunque existan: la rumana Liga 1 es de 2016 y la
Eliteserien de 2017, por eso el importador nunca las admitio -solo acepta las
marcadas con temporada 1993-. Peor todavia, los clubes que si estaban en la base
arrastran su ``league_id`` de aquellas temporadas y alguno apunta a la segunda
division. Asi que se crean como entidades nuevas del 93-94 y se reasigna todo.

Con la clasificacion real de Wikipedia se hacen ademas dos cosas que el
importador no podia:

**Poner nombre de 1993.** La tabla de Wikipedia trae el nombre de la epoca como
texto del enlace, asi que Electroputere Craiova deja de llamarse FC Caracal y
Politehnica Timisoara deja de ser FC Timisoara.

**Repartir el nivel por posicion final.** Al importar las plantillas, un club sin
ningun futbolista conocido se quedaba con la media por defecto y el Malmö
acababa igualado con el ultimo de su liga. Con la clasificacion, el campeon vale
mas que el colista, que es lo que pasaba de verdad. Solo se retoca a los
futbolistas creados por estas tandas: a quien viene de la fuente original o
llega documentado no se le toca la media.

**Sin ascensos ni descensos**: se modela una sola division por pais, asi que la
liga es un grupo cerrado. Y el calendario sera generado, no historico, como el
resto de lo que este juego genera.
"""

import argparse
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "mondefootball_squads_1993.json"
STANDINGS = DATA / "league_standings_1993_94.json"
MAPPING = DATA / "mondefootball_club_mapping.json"
REPORT = DATA / "league_structure_1993_94_report.json"

# Nombre de la competicion en 1993-94, no el de hoy.
# Se reutiliza el identificador de liga del MDB en vez de inventar uno nuevo. No
# es cosmetico: los arbitros del catalogo van por identificador de liga, y las
# seis tienen veinte cada una. Con un identificador nuevo la competicion nacia
# sin cuadro arbitral y el juego exige que toda liga tenga el suyo.
LEAGUES = {
    "Rumania":   {"id": 56, "name": "Divizia A",   "country_id": 72, "level": 1},
    "Bulgaria":  {"id": 66, "name": "A Grupa",     "country_id": 21, "level": 1},
    "Polonia":   {"id": 89, "name": "Ekstraklasa", "country_id": 70, "level": 1},
    "Suecia":    {"id": 91, "name": "Allsvenskan", "country_id": 79, "level": 1},
    "Noruega":   {"id": 88, "name": "Tippeligaen", "country_id": 60, "level": 1},
    "Dinamarca": {"id": 69, "name": "Superligaen", "country_id": 33, "level": 1},
    "Austria":   {"id": 62, "name": "Bundesliga", "country_id": 16, "level": 1},
    "Suiza":     {"id": 55, "name": "Nationalliga A", "country_id": 80, "level": 1},
    "Ucrania":   {"id": 12, "name": "Vyshcha Liha", "country_id": 85, "level": 1},
}

# Un club solo se activa si puede alinear once y nombrar suplentes. Con menos, el
# motor de partido revienta al pedirle alineacion -"UTA Arad: solo hay 6
# futbolistas historicos disponibles"-. Los que no llegan se quedan sin liga y
# apuntados, para completarlos mas adelante.
MIN_SQUAD_TO_ACTIVATE = 16

# Cupo de extranjeros de la epoca: el mismo 3+2 que rige el resto del juego.
MAX_FOREIGN_STARTING = 3
MAX_FOREIGN_SQUAD = 5

# Rango de nivel de estas ligas. Son competiciones menores que las modeladas, asi
# que el campeon no llega al nivel de un grande europeo.
TOP_LEVEL = 76
BOTTOM_LEVEL = 63

CREATED_ORIGINS = {"league_club_1993_94", "european_club_1993_94"}

EXTRA = {"ł": "l", "đ": "d", "ø": "o", "ţ": "t", "ş": "s", "ș": "s", "ț": "t", "æ": "ae", "å": "a"}
STOP = {"fc", "cf", "sk", "bk", "if", "ac", "as", "sc", "cs", "fk", "ks", "nk", "pfc", "pfk",
        "ofk", "mks", "gks", "lks", "fks", "acs", "acf", "csm", "il", "is", "ff", "ik", "sa", "old"}

# Clubes que el cruce por palabras no situa: nombre actual frente al de 1993, o
# transliteracion distinta. Escritos a mano y revisables, como el resto.
POSITION_ALIASES = {
    # El nombre con el que la clasificacion de Wikipedia llama a cada club.
    "fcsb": "Steaua București",
    # Nombre ingles frente al del pais.
    "legia-warszawa": "Legia Warsaw",
    "polonia-warszawa": "Polonia Warsaw",
    "fc-koebenhavn": "F.C. Copenhagen",
    # Abreviaturas con las que el club es conocido en su liga.
    "aalborg-bk": "AaB",
    "aarhus-gf": "AGF",
    "odense-bk": "OB",
    "hamarkameratene": "HamKam",
    # Nombres que cambiaron: el club de Pniewy se llamaba Miliarder en 1993-94,
    # y el de Caracal era el Electroputere de Craiova.
    "sokol-pniewy": "Miliarder Pniewy",
    "fc-caracal": "Electroputere Craiova",
    "gornik-zabrze": "Górnik Zabrze",
    "widzew-lodz": "Widzew Łódź",
    "oergryte-is": "Örgryte IS",
    "oesters-if": "Östers IF",
    "fc-universitatea-craiova": "FC U Craiova",
}


def fold(text: Any) -> str:
    raw = str(text or "")
    for a, b in EXTRA.items():
        raw = raw.replace(a, b).replace(a.upper(), b.upper())
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(c for c in raw if not unicodedata.combining(c)).casefold()
    for a, b in (("oe", "o"), ("ae", "a"), ("aa", "a")):
        raw = raw.replace(a, b)
    return raw


def tokens(name: Any) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", fold(name)) if len(w) > 2 and w not in STOP}


def same_club(a: set[str], b: set[str]) -> bool:
    """Dos nombres del mismo club, no dos clubes de la misma ciudad.

    Compartir una palabra no basta y no es un matiz: "Warta Poznan" y "Lech
    Poznan" comparten la ciudad, y el CSKA y el Levski comparten Sofia. Con esa
    regla el Warta acababa renombrado como Lech. Se exige que un nombre este
    contenido entero en el otro, que es lo que distingue "Rosenborg" de
    "Rosenborg BK" sin confundir a dos vecinos.
    """
    # Y un nombre de una sola palabra no vale como prueba, porque suele ser la
    # ciudad: "FC U Craiova" se queda en {craiova} y casaba con el Electroputere
    # de Craiova, que acababa tercero en vez de decimocuarto.
    return bool(a and b and (a == b or (len(a) >= 2 and a <= b) or (len(b) >= 2 and b <= a)))


# Marcas de que el nombre guardado es el de hoy y no el de 1993: un año entre
# parentesis, un "(old)", o el sufijo de un club refundado.
_MODERN_MARK = re.compile(r"\(|\d{4}|old", re.I)


def better_name(current: str, from_standings: str) -> str | None:
    """Devuelve el nombre a usar, o None si conviene dejar el que ya hay.

    La clasificacion de Wikipedia abrevia -"Rosenborg" por "Rosenborg BK",
    "Brann" por "SK Brann"- y en algun caso moderniza: llama "Lyngby FC" a lo que
    en 1993 era el Lyngby BK. Cambiar por sistema empeoraba nombres correctos.
    Solo se sustituye cuando el guardado lleva marca de epoca equivocada, como
    "PFC Shumen 2010" o "FC Chernomorets Burgas (old)".
    """
    if not from_standings:
        return None
    if _MODERN_MARK.search(current or ""):
        return from_standings
    # Solo se cambia si el nombre de la clasificacion **anade** algo: "Sportul
    # Studenţesc" gana con el "Bucuresti" y el Dobrudzha con el "Dobrich". Al
    # reves seria empeorar, y por eso "CS Universitatea Craiova" no pasa a ser
    # "FC U Craiova" ni "AIK Solna" se queda en "AIK".
    if tokens(from_standings) - tokens(current):
        return from_standings
    return None


def level_for(position: int, teams: int) -> int:
    if teams <= 1:
        return TOP_LEVEL
    share = position / (teams - 1)
    return round(TOP_LEVEL - (TOP_LEVEL - BOTTOM_LEVEL) * share)


def build(snapshot_path: Path, squads_path: Path, standings_path: Path,
          mapping_path: Path) -> dict[str, Any]:
    from backend.app.football9394.source_catalog_runtime import default_source_catalog
    catalog = default_source_catalog()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    squads = json.loads(squads_path.read_text(encoding="utf-8"))
    standings = json.loads(standings_path.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    club_team_id: dict[str, int] = {}
    for entry in mapping["seguros"]:
        club_team_id[entry["slug"]] = int(entry["mdb"])
    for slug, fix in mapping.get("a_mano", {}).items():
        club_team_id[slug] = int(fix["mdb"])
    teams_by_id = {int(t["source_id"]): t for t in snapshot["teams"]}
    by_mondefootball = {str(t.get("mondefootball_id")): t for t in snapshot["teams"]
                        if t.get("mondefootball_id")}

    # Reejecutable: se quitan las ligas que creo esta herramienta antes de
    # volver a crearlas, o cada pasada añadiria seis mas.
    ours = {spec["id"] for spec in LEAGUES.values()} | {
        int(l["source_id"]) for l in snapshot["leagues"]
        if str(l.get("structure_source", "")).startswith("participantes y clasificacion")}
    snapshot["leagues"] = [l for l in snapshot["leagues"] if int(l["source_id"]) not in ours]
    for team in snapshot["teams"]:
        if int(team.get("league_id") or 0) in ours:
            team["league_id"] = None
            team["league_position"] = None

    players_by_team: dict[int, list[dict[str, Any]]] = {}
    for player in snapshot["players"]:
        players_by_team.setdefault(int(player.get("team_id") or 0), []).append(player)

    done: list[dict[str, Any]] = []
    for country, block in squads.items():
        spec = LEAGUES[country]
        order = standings.get(country, {}).get("standings", [])
        # Cada club viaja con el nombre con el que ha casado. Antes se guardaba
        # solo la posicion y luego se renombraba con order[indice-tras-ordenar],
        # que no es lo mismo: los que no casaban se amontonaban al final y
        # desplazaban a los demas, asi que el Dinamo acababa llamandose Steaua y
        # el Warta Poznan, Lech.
        clubs: list[dict[str, Any]] = []
        unplaced: list[str] = []
        for club in block["clubs"]:
            slug = club["slug"]
            team = teams_by_id.get(club_team_id.get(slug, -1)) or by_mondefootball.get(str(club["mondefootball_id"]))
            if team is None:
                unplaced.append(slug)
                continue
            wanted = tokens(POSITION_ALIASES.get(slug) or slug)
            match = next(((i, name) for i, name in enumerate(order)
                          if same_club(wanted, tokens(name))), None)
            clubs.append({"team": team, "slug": slug,
                          "position": match[0] if match else len(order),
                          "matched_name": match[1] if match else None})

        clubs.sort(key=lambda c: c["position"])
        league = {
            "source_id": spec["id"], "country_id": spec["country_id"],
            "country": country, "name": spec["name"], "short_name": spec["name"],
            "level": spec["level"], "team_count": len(clubs), "turns": 2,
            "yellow_card_cycle": 5,
            "max_foreigners_starting": MAX_FOREIGN_STARTING,
            "max_foreigners_squad": MAX_FOREIGN_SQUAD,
            "prefer_nationals": False,
            "source_edition": "1993",
            "admitted": True, "signable": True,
            "structure_source": ("participantes y clasificacion reales de 1993-94; "
                                 "calendario generado, no historico"),
            "promotion_relegation": False,
        }
        snapshot["leagues"].append(league)

        renamed: list[dict[str, Any]] = []
        levelled: list[dict[str, Any]] = []
        incomplete: list[dict[str, Any]] = []
        for position, row in enumerate(clubs):
            team, slug = row["team"], row["slug"]
            alive = [p for p in players_by_team.get(int(team["source_id"]), [])
                     if not p.get("retired")]
            # Un club activo tambien tiene que tener estadio resuelto en el
            # catalogo. Los que hemos creado nosotros no estan en la base
            # original y no lo tienen, asi que tampoco pueden activarse.
            has_venue = catalog.stadium(team.get("stadium_id")) is not None
            if len(alive) < MIN_SQUAD_TO_ACTIVATE or not has_venue:
                # Se queda fuera de la liga pero no se pierde: sigue en el mundo
                # con su plantilla y queda apuntado para completarlo.
                team["league_id"] = None
                team["league_position"] = None
                team["pending_activation"] = {
                    "league": spec["name"], "country": country,
                    "real_position": position + 1,
                    "squad": len(alive), "needed": MIN_SQUAD_TO_ACTIVATE,
                    "has_venue": has_venue,
                    "reason": ("sin plantilla para alinear once y nombrar suplentes"
                               if len(alive) < MIN_SQUAD_TO_ACTIVATE
                               else "sin estadio en el catalogo de la fuente"),
                }
                incomplete.append({"club": team.get("name"), "posicion": position + 1,
                                   "fichas": len(alive), "estadio": has_venue})
                continue
            team.pop("pending_activation", None)
            team["league_id"] = league["source_id"]
            team["league_position"] = position + 1
            # Solo se renombra con el nombre que ha casado con ESTE club; si no
            # caso ninguno, se queda con el suyo.
            candidate = row["matched_name"]
            if candidate:
                candidate = re.sub(r"^\[\[|\]\]$", "", candidate).strip()
            real_name = better_name(team.get("name") or "", candidate or "")
            if real_name and real_name != team.get("name"):
                renamed.append({"antes": team.get("name"), "ahora": real_name})
                team["name"] = real_name
                team["long_name"] = real_name
                team["short_name"] = real_name
                team["name_source"] = "nombre de 1993-94 segun la clasificacion de Wikipedia"

            target = level_for(position, len(clubs))
            squad = [p for p in players_by_team.get(int(team["source_id"]), [])
                     if p.get("external_origin") in CREATED_ORIGINS]
            if squad:
                current = sorted(int(p.get("overall") or 0) for p in squad)
                top = current[-1] if current else target
                shift = target - top
                if shift:
                    for player in squad:
                        player["overall"] = max(20, min(99, int(player.get("overall") or target) + shift))
                        player["category"] = min(99, player["overall"] + 1)
                    levelled.append({"club": team["name"], "posicion": position + 1,
                                     "nivel": target, "ajuste": shift, "fichas": len(squad)})

        league["team_count"] = len(clubs) - len(incomplete)
        league["clubs_pending_activation"] = len(incomplete)
        done.append({"country": country, "league_id": league["source_id"], "name": spec["name"],
                     "clubs": len(clubs), "activated": len(clubs) - len(incomplete),
                     "unplaced": unplaced, "renamed": renamed, "levelled": levelled,
                     "incomplete": incomplete})

    snapshot["leagues"].sort(key=lambda l: int(l["source_id"]))
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"status": "complete", "leagues": len(done),
              "clubs": sum(d["clubs"] for d in done),
              "activated": sum(d["activated"] for d in done),
              "pending_activation": sum(len(d["incomplete"]) for d in done),
              "renamed": sum(len(d["renamed"]) for d in done),
              "levelled": sum(len(d["levelled"]) for d in done),
              "unplaced": sum(len(d["unplaced"]) for d in done),
              "detail": done}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--squads", type=Path, default=SQUADS)
    parser.add_argument("--standings", type=Path, default=STANDINGS)
    parser.add_argument("--mapping", type=Path, default=MAPPING)
    args = parser.parse_args()
    report = build(args.snapshot, args.squads, args.standings, args.mapping)
    print(f"ligas {report['leagues']} | clubes {report['clubs']} | "
          f"activados {report['activated']} | pendientes {report['pending_activation']} | "
          f"renombrados {report['renamed']}")
    for block in report["detail"]:
        print(f"\n{block['name']} ({block['country']}, liga {block['league_id']}): {block['clubs']} clubes")
        for row in block["renamed"][:6]:
            print(f"   renombrado: {row['antes']} -> {row['ahora']}")
        for row in block["incomplete"]:
            marca = f"{row['fichas']} fichas" + ("" if row.get("estadio", True) else ", sin estadio")
            print(f"   sin activar: {row['club']} ({row['posicion']}o, {marca})")
        if block["unplaced"]:
            print(f"   SIN COLOCAR: {block['unplaced']}")


if __name__ == "__main__":
    main()
