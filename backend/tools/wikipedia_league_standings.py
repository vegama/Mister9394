from __future__ import annotations

"""Clasificacion final de una liga del 93-94, leida de Wikipedia.

Hace falta por dos cosas y ninguna es cosmetica:

**El nivel de los clubes.** Al importar las plantillas, un club sin ningun
futbolista conocido se quedaba con la media por defecto, asi que el Malmö
acababa igualado con el Cherno More. La posicion final es una medida real de lo
bueno que era cada equipo, y reparte los niveles con criterio en vez de a ojo.

**El orden de la liga.** Sin clasificacion no hay campeon al que dar la plaza
europea ni colista al que descender, y aunque aqui no haya descensos, el orden
sigue siendo lo que da forma a la temporada.

mondefootball no sirve para esto: tiene los clubes del 93-94 pero su tabla esta
a cero. Wikipedia si, aunque cada pagina usa una plantilla distinta, asi que se
prueban las que hay.
"""

import argparse
import json
from pathlib import Path
import re
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "football9394" / "league_standings_1993_94.json"

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Mister9394-HistoricalGame/1.0 (personal hobby project; contact: jaricma@gmail.com)"}

PAGES = {
    "Rumania": "1993–94 Divizia A",
    "Bulgaria": "1993–94 A Group",
    "Polonia": "1993–94 Ekstraklasa",
    "Suecia": "1993 Allsvenskan",
    "Noruega": "1993 Tippeligaen",
    "Dinamarca": "1993–94 Danish Superliga",
    "Austria": "1993–94 Austrian Football Bundesliga",
    "Suiza": "1993–94 Nationalliga A",
    "Hungria": "1993–94 Nemzeti Bajnokság I",
    "Israel": "1993–94 Liga Leumit",
    "Irlanda": "1993–94 League of Ireland Premier Division",
    # Ucrania y Croacia no tienen tabla legible en Wikipedia: sus clubes entran
    # sin posicion y con el nivel por defecto hasta que haya de donde sacarla.
}

# La plantilla moderna de tablas deportivas numera los equipos con team1, team2...
_SPORTS_TABLE = re.compile(r"\|\s*team(\d+)\s*=\s*([^\n|]+)")
# El nombre que se enseña es el alias del enlace, no su destino: la fila dice
# ``|name_ELE = [[FC Caracal (2004)|Electroputere Craiova]]`` y el bueno para
# 1993 es el segundo. Quedarse con el destino ponia en la liga los nombres
# modernos de los clubes, que es lo que este proyecto evita tambien con los paises.
_TEAM_NAME = re.compile(
    r"\|\s*name_([^\s=|]+)\s*=\s*"
    r"(?:\[\[(?P<target>[^\]|]+)(?:\|(?P<alias>[^\]]+))?\]\]|(?P<plain>[^\n|]+))"
)
# Las paginas antiguas usan una tabla wiki corriente con enlaces por fila.
_PLAIN_ROW = re.compile(r"^\|\s*(\d+)\s*\n\|\s*(?:align=[^|]*\|)?\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", re.M)


def fetch(title: str, client: httpx.Client) -> str:
    response = client.get(WIKI_API, params={
        "action": "parse", "page": title, "prop": "wikitext",
        "format": "json", "formatversion": 2,
    }, headers=HEADERS, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise KeyError(f"Wikipedia no tiene '{title}'")
    return payload["parse"]["wikitext"]


def sports_table_block(wikitext: str) -> str:
    """El primer bloque de tabla deportiva y solo ese.

    Una pagina de temporada trae varias tablas -la clasificacion, la rejilla de
    resultados, a veces las de los play-offs- y todas usan la misma plantilla.
    Barrer la pagina entera devolvia cada equipo tres veces y una clasificacion
    de cincuenta y cuatro puestos para una liga de dieciocho.
    """
    start = wikitext.find("{{#invoke:Sports table")
    if start < 0:
        return ""
    depth = 0
    for position in range(start, len(wikitext)):
        if wikitext.startswith("{{", position):
            depth += 1
        elif wikitext.startswith("}}", position):
            depth -= 1
            if depth == 0:
                return wikitext[start:position + 2]
    return wikitext[start:]


def parse_standings(wikitext: str) -> list[str]:
    """Devuelve los equipos en orden de clasificacion, del campeon al ultimo."""
    block = sports_table_block(wikitext) or wikitext
    codes = _SPORTS_TABLE.findall(block)
    if codes:
        names = {}
        for match in _TEAM_NAME.finditer(wikitext):
            label = match.group("alias") or match.group("target") or match.group("plain") or ""
            names[match.group(1)] = label.strip()
        # Hay ligas cuyo bloque define la tabla dos veces -fase regular y fase
        # final-, asi que el mismo codigo aparece con dos numeros. Se conserva la
        # primera aparicion, que es la de la clasificacion general.
        ordered = []
        vistos: set[str] = set()
        for _, code in sorted(codes, key=lambda x: int(x[0])):
            code = code.strip()
            if code in vistos:
                continue
            vistos.add(code)
            ordered.append((names.get(code) or code).strip())
        if len(ordered) >= 8:
            return ordered
    rows = _PLAIN_ROW.findall(wikitext)
    if rows:
        return [(alias or link).strip() for _, link, alias in sorted(rows, key=lambda x: int(x[0]))]
    return []


def collect(pages: dict[str, str] = PAGES) -> dict[str, Any]:
    out: dict[str, Any] = {}
    with httpx.Client() as client:
        for country, title in pages.items():
            try:
                table = parse_standings(fetch(title, client))
            except KeyError as error:
                out[country] = {"page": title, "error": str(error), "standings": []}
                continue
            out[country] = {"page": title, "teams": len(table), "standings": table}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = collect()
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for country, block in payload.items():
        print(f"{country}: {block.get('teams', 0)} equipos  ({block['page']})")
        for position, name in enumerate(block["standings"], 1):
            print(f"   {position:>2}. {name}")


if __name__ == "__main__":
    main()
