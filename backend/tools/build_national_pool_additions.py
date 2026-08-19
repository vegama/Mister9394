from __future__ import annotations

"""Convierte convocatorias reales de torneo en altas para los pools nacionales.

Lee las plantillas históricas con ``wikipedia_squad_source`` y produce el JSON de
altas que ya consume ``enrich_national_pools_1993_94.py``, que es quien
reconcilia contra toda la base y aloja a cada futbolista en su contenedor
``Otros-País``. Aquí no se escribe nada en el universo.

Tres decisiones que conviene tener presentes al leer el resultado:

**Países de 1993.** Se usan los nombres y las entidades de la temporada, no los
actuales: Zaire y no RD Congo, Yugoslavia y no Serbia, Chequia y Eslovaquia ya
separadas. La CEI queda fuera porque dejó de existir en 1992.

**Suelo de edad.** Las convocatorias de 1995-96 aportan la hornada joven de la
época, que es deseable, pero también gente que en 1993-94 tenía doce años. Se
exige haber cumplido 16 el 1 de enero de 1994, que no es un número inventado:
es exactamente el mínimo que ya tienen por sí solas las convocatorias de
1992-94.

**Nivel.** No sale de ningún sitio la media de un futbolista, así que se infiere
y se etiqueta como tal, por orden de fiabilidad: el club real si está modelado
en el juego, y si no el nivel típico de la competición donde jugaba. A los
menores de 20 se les da valoración de cantera y, en su lugar, progresión alta:
``progression_mean`` es un campo documentado de la fuente (0..9) que
``coaching.py`` usa para acelerar el desarrollo. Así un chaval de 1993-94 no
empieza siendo la estrella en que llegó a convertirse, pero puede llegar a
serlo mucho más rápido que un veterano.
"""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import time
import unicodedata
from typing import Any

import httpx

from backend.tools.wikipedia_squad_source import fetch_squad_page

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
CATALOG = DATA / "historical_source_catalog.json"

REFERENCE_DAY = date(1994, 1, 1)
MINIMUM_AGE = 16
YOUTH_AGE = 20
FIRST_SOURCE_ID = 9498000

# Nombre en Wikipedia -> nombre del país en el catálogo del juego, con la
# entidad que existía en 1993-94.
NATION_TO_COUNTRY = {
    "Zambia": "Zambia", "Zaire": "República Democrática del Congo", "Ghana": "Ghana",
    "Nigeria": "Nigeria", "Egypt": "Egipto", "Tunisia": "Túnez", "Mali": "Malí",
    "Ivory Coast": "Costa de Marfil", "Senegal": "Senegal", "Guinea": "Guinea",
    "Gabon": "Gabón", "Sierra Leone": "Sierra Leona", "Cameroon": "Camerún",
    "Morocco": "Marruecos", "Algeria": "Argelia", "South Africa": "Sudáfrica",
    "Burkina Faso": "Burkina Faso", "Liberia": "Liberia", "Angola": "Angola",
    "Mozambique": "Mozambique", "Togo": "Togo", "Gambia": "Gambia", "Kenya": "Kenia",
    "Sudan": "Sudán", "Ethiopia": "Etiopía", "Congo": "República del Congo",
    "Bolivia": "Bolivia", "Chile": "Chile", "Paraguay": "Paraguay", "Peru": "Perú",
    "Ecuador": "Ecuador", "Venezuela": "Venezuela", "Uruguay": "Uruguay",
    "Colombia": "Colombia", "Brazil": "Brasil", "Argentina": "Argentina",
    "Mexico": "México", "United States": "E.E.U.U.",
    "South Korea": "Corea del Sur", "North Korea": "Corea del Norte",
    "Japan": "Japón", "Saudi Arabia": "Arabia Saudí", "China": "China",
    "Iran": "Irán", "Iraq": "Irak", "Kuwait": "Kuwait", "Qatar": "Qatar",
    "Syria": "Siria", "Thailand": "Tailandia", "Uzbekistan": "Uzbekistán",
    "Germany": "Alemania", "Spain": "España", "Italy": "Italia", "France": "Francia",
    "England": "Inglaterra", "Scotland": "Escocia", "Wales": "Gales",
    "Netherlands": "Holanda", "Portugal": "Portugal", "Denmark": "Dinamarca",
    "Sweden": "Suecia", "Norway": "Noruega", "Russia": "Rusia", "Romania": "Rumanía",
    "Bulgaria": "Bulgaria", "Croatia": "Croacia", "Switzerland": "Suiza",
    "Belgium": "Bélgica", "Austria": "Austria", "Greece": "Grecia", "Turkey": "Turquía",
    "Republic of Ireland": "República Irlanda", "Northern Ireland": "Irlanda del Norte",
    "Czech Republic": "República Checa", "Slovakia": "Eslovaquia",
    "Hungary": "Hungría", "Poland": "Polonia", "Finland": "Finlandia",
    "FR Yugoslavia": "Serbia",
}
# La Comunidad de Estados Independientes desapareció tras la Eurocopa de 1992:
# sus jugadores pertenecen ya a Rusia, Ucrania y las demás, así que asignarlos
# en bloque sería falsear la nacionalidad.
EXCLUDED_NATIONS = {"CIS", "Soviet Union", "Czechoslovakia"}

# Nivel típico por procedencia del club, cuando no hay un club modelado que
# sirva de ancla. Son valores inferidos, no dato histórico.
LEAGUE_TIER_BASELINE = {
    "ITA": 78, "ESP": 77, "GER": 77, "ENG": 76, "FRA": 74, "POR": 73, "NED": 73,
    "SCO": 71, "BEL": 71, "TUR": 70, "GRE": 70, "RUS": 70, "SUI": 69, "AUT": 69,
    "BRA": 74, "ARG": 73, "MEX": 70, "URU": 70, "COL": 70, "CHI": 68, "PAR": 68,
}
DEFAULT_BASELINE = 65          # liga no modelada (nacional africana, asiática…)
YOUTH_BASELINE = 58            # valoración de cantera
POSITION_CODE = {"POR": "GK", "DEF": "DF", "MED": "MF", "DEL": "FW"}


def fold(text: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in raw if not unicodedata.combining(c)).casefold().strip()


def age_at_reference(birth_date: str) -> int:
    year, month, day = (int(x) for x in birth_date.split("-"))
    return (REFERENCE_DAY - date(year, month, day)).days // 365


def load_country_ids() -> dict[str, int]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {fold(row["name"]): int(row["source_id"]) for row in catalog["countries"]}


def load_existing(snapshot: dict[str, Any]) -> tuple[set[tuple[str, str]], dict[str, list[dict]]]:
    """Índices de reconciliación: por (apellido, fecha) y por fecha suelta."""
    by_name_dob: set[tuple[str, str]] = set()
    by_dob: dict[str, list[dict]] = {}
    for row in snapshot["players"]:
        birth = str(row.get("birth_date") or "")[:10]
        if not birth:
            continue
        by_dob.setdefault(birth, []).append(row)
        for field in ("display_name", "surname1"):
            if row.get(field):
                by_name_dob.add((fold(row[field]), birth))
    return by_name_dob, by_dob


def club_anchor(club: str | None, snapshot: dict[str, Any], position: str) -> int | None:
    """Media del club real, si ese club existe en el juego."""
    if not club:
        return None
    target = fold(club)
    teams = {fold(t.get("name")): int(t["source_id"]) for t in snapshot["teams"] if t.get("name")}
    team_id = teams.get(target)
    if team_id is None:
        return None
    ratings = [
        int(p.get("overall") or 0) for p in snapshot["players"]
        if int(p.get("team_id") or 0) == team_id and p.get("broad_position") == position
        and p.get("overall")
    ]
    if not ratings:
        return None
    ratings.sort()
    return ratings[len(ratings) // 2]


def estimate_level(player, snapshot: dict[str, Any], *, appearances: int) -> tuple[int, int, str]:
    """Devuelve (media, progresión, cómo se ha estimado).

    ``appearances`` es en cuántas convocatorias distintas aparece el futbolista.
    Es la única señal de jerarquía que dan estas fuentes y es real: quien fue
    convocado a tres torneos seguidos era un fijo de su selección, no un
    suplente ocasional. Junto al dorsal bajo evita que una plantilla entera
    salga clavada a la misma media.
    """
    age = age_at_reference(player.birth_date)
    if age < YOUTH_AGE:
        # Cantera: nivel bajo y progresión alta. El techo lo pone su carrera
        # posterior, que este juego deliberadamente no adelanta.
        level = YOUTH_BASELINE + max(0, age - 16)
        progression = 7 if age <= 18 else 6
        return level, progression, "cantera_por_edad"

    progression = 4 if age <= 24 else 2
    jerarquia = (appearances - 1) * 3 + (2 if (player.shirt_number or 99) <= 11 else 0)

    anchor = club_anchor(player.club, snapshot, player.position)
    if anchor is not None:
        return anchor + min(3, jerarquia), progression, "media_del_club_real"

    baseline = LEAGUE_TIER_BASELINE.get((player.club_country or "").upper(), DEFAULT_BASELINE)
    return baseline + jerarquia, progression, "nivel_tipico_de_su_liga"


def split_name(full: str) -> tuple[str, str]:
    parts = full.split()
    if len(parts) == 1:
        return full, full
    return parts[0], " ".join(parts[1:])


def build(pages: list[str], nations: set[str] | None, *, start_id: int) -> dict[str, Any]:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    countries = load_country_ids()
    seen_name_dob, _ = load_existing(snapshot)

    rows: list[dict[str, Any]] = []
    stats = {"leidos": 0, "ya_existen": 0, "sin_fecha": 0, "muy_jovenes": 0,
             "pais_desconocido": 0, "duplicado_en_lote": 0, "nuevos": 0}
    lote: set[tuple[str, str]] = set()
    next_id = start_id

    # Primera pasada: cuántas convocatorias distintas acumula cada persona.
    apariciones: dict[tuple[str, str], int] = {}
    paginas: list[Any] = []
    with httpx.Client() as client:
        for title in pages:
            page = fetch_squad_page(title, client)
            paginas.append(page)
            for players in page.nations.values():
                for row in players:
                    if row.birth_date:
                        clave = (fold(row.name), row.birth_date)
                        apariciones[clave] = apariciones.get(clave, 0) + 1
            time.sleep(0.3)

    if True:
        for page in paginas:
            for nation, players in page.nations.items():
                if nation in EXCLUDED_NATIONS:
                    continue
                if nations and nation not in nations:
                    continue
                country_name = NATION_TO_COUNTRY.get(nation)
                country_id = countries.get(fold(country_name)) if country_name else None
                for player in players:
                    stats["leidos"] += 1
                    if country_id is None:
                        stats["pais_desconocido"] += 1
                        continue
                    if not player.birth_date:
                        stats["sin_fecha"] += 1
                        continue
                    if age_at_reference(player.birth_date) < MINIMUM_AGE:
                        stats["muy_jovenes"] += 1
                        continue
                    key = (fold(player.name), player.birth_date)
                    if key in seen_name_dob:
                        stats["ya_existen"] += 1
                        continue
                    if key in lote:
                        stats["duplicado_en_lote"] += 1
                        continue
                    lote.add(key)
                    level, progression, how = estimate_level(
                        player, snapshot, appearances=apariciones.get(key, 1))
                    first, last = split_name(player.name)
                    rows.append({
                        "source_id": next_id,
                        "display_name": player.name,
                        "first_name": first,
                        "surname1": last,
                        "birth_date": player.birth_date,
                        "country_id": country_id,
                        "country_name": country_name,
                        "position_code": POSITION_CODE.get(player.position, "MF"),
                        "overall": int(level),
                        "progression_mean": int(progression),
                        "historical_club_1994": player.club,
                        "identity_source": f"Wikipedia · {player.source}",
                        "historical_context": (
                            f"Internacional por {country_name} en {player.source.replace(' squads','')}"
                            + (f"; club {player.club}" if player.club else "")
                        ),
                        "level_estimation": how,
                        "tournament_appearances": apariciones.get(key, 1),
                        "source_confidence": "high" if player.birth_date else "medium",
                        "creation_batch": "national_pool_tournament_squads_v113",
                    })
                    next_id += 1
                    stats["nuevos"] += 1

    return {
        "schema_version": 1,
        "batch": "national_pool_tournament_squads_v113",
        "policy": (
            "Jugadores reales de convocatorias históricas. Entidades de 1993-94. "
            "Suelo de 16 años a 1 de enero de 1994. Nivel inferido y etiquetado, "
            "nunca presentado como dato histórico."
        ),
        "stats": stats,
        "players": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera altas de pools nacionales desde convocatorias reales")
    parser.add_argument("--page", action="append", dest="pages", required=True)
    parser.add_argument("--nation", action="append", dest="nations")
    parser.add_argument("--start-id", type=int, default=FIRST_SOURCE_ID)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = build(args.pages, set(args.nations) if args.nations else None, start_id=args.start_id)
    print(json.dumps(payload["stats"], ensure_ascii=False, indent=2))
    by_nation: dict[str, int] = {}
    for row in payload["players"]:
        by_nation[row["country_name"]] = by_nation.get(row["country_name"], 0) + 1
    for name, count in sorted(by_nation.items(), key=lambda x: -x[1]):
        print(f"   {name:<32} {count:>3} altas")
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nEscrito {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
