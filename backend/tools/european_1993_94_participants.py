from __future__ import annotations

"""Lista de participantes de las tres competiciones europeas de 1993-94.

El juego modela veinticuatro clubes de ligas que no simula —Lillestrøm, Valur,
APOEL, Degerfors…— porque jugaron Europa esa temporada. Falta el resto, y para
saber quiénes son hay que leerlos de la fuente en vez de tirar de memoria.

Cada página de Wikipedia marca a sus participantes de una manera distinta, y las
tres conviven aquí:

    Copa de Europa   |{{fba|NOR}}\\n|[[Rosenborg BK|Rosenborg]]
    Copa de la UEFA  {{fbaicon|Italy}} [[Inter Milan]]
    Recopa           * {{flagicon|LUX}} [[F91 Dudelange]]

La lectura se limita a la sección de equipos clasificados. Barrer la página
entera parecía más simple y era peor: la tabla de máximos goleadores usa el
mismo icono de bandera, así que Stoichkov, Klinsmann y Koeman entraban en la
lista como si fueran clubes.
"""

import argparse
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
OUT = DATA / "european_1993_94_participants.json"

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Mister9394-HistoricalGame/1.0 (personal hobby project; contact: jaricma@gmail.com)"}

PAGES = (
    "1993–94 UEFA Champions League",
    "1993–94 UEFA Cup",
    "1993–94 European Cup Winners' Cup",
)

_HEADING = re.compile(r"^(=+)\s*(.+?)\s*\1\s*$", re.M)
_TEAM_SECTION = re.compile(r"^(teams|qualified teams|participants|participating teams)$", re.I)

_PATTERNS = (
    re.compile(r"\{\{fba\|([A-Z]{3})[^}]*\}\}\s*\n\|\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"),
    re.compile(r"\{\{fbaicon\|([^}|]+)[^}]*\}\}\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"),
    re.compile(r"\{\{flagicon\|([A-Z]{3})[^}]*\}\}\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"),
)

# Palabras que no distinguen a un club y estorban al comparar con lo que ya
# tenemos: media Europa se llama FC algo.
_NOISE = {"fc", "cf", "sk", "bk", "if", "ac", "as", "sc", "cs", "fk", "ks", "aa", "ca",
          "de", "of", "club", "futbol", "football", "athletic", "sporting"}


# El juego escribe algunos clubes como los escribía la base española de 1993, y
# Wikipedia los llama de otra manera. Comparar por palabras no los une, así que
# se dicen a mano: son pocos y darlos por ausentes obligaría a crearlos otra vez.
ALIASES = {
    "Olympiacos F.C.": "Olympiakos Pireas",
    "Olympiacos": "Olympiakos Pireas",
    "Sporting CP": "Sporting Lisboa",
    "Heart of Midlothian F.C.": "Hearts FC",
    "Heart of Midlothian": "Hearts FC",
}


def fold(text: Any) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in raw if not unicodedata.combining(c)).casefold()


def tokens(name: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", fold(name)) if len(w) > 2 and w not in _NOISE}


def team_sections(wikitext: str) -> list[str]:
    """Devuelve el cuerpo de cada sección de equipos clasificados."""
    marks = list(_HEADING.finditer(wikitext))
    bodies: list[str] = []
    for index, mark in enumerate(marks):
        if not _TEAM_SECTION.match(mark.group(2)):
            continue
        level = len(mark.group(1))
        end = len(wikitext)
        for later in marks[index + 1:]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        bodies.append(wikitext[mark.end():end])
    return bodies


def parse_participants(wikitext: str) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for body in team_sections(wikitext):
        for pattern in _PATTERNS:
            for country, link, alias in pattern.findall(body):
                found.setdefault(link.strip(), (country.strip(), (alias or link).strip()))
    return found


def fetch(title: str, client: httpx.Client) -> str:
    response = client.get(WIKI_API, params={
        "action": "parse", "page": title, "prop": "wikitext",
        "format": "json", "formatversion": 2,
    }, headers=HEADERS, timeout=40)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise KeyError(f"Wikipedia no tiene '{title}': {payload['error'].get('info')}")
    return payload["parse"]["wikitext"]


def build(snapshot_path: Path = SNAPSHOT) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    modelled = [(t["name"], tokens(t["name"])) for t in snapshot.get("teams", [])
                if t.get("name") and not t.get("market_container")]

    everyone: dict[str, dict[str, Any]] = {}
    per_page: dict[str, int] = {}
    with httpx.Client() as client:
        for title in PAGES:
            found = parse_participants(fetch(title, client))
            per_page[title] = len(found)
            competition = title.split("1993–94 ", 1)[1]
            for link, (country, name) in found.items():
                row = everyone.setdefault(link, {"country": country, "name": name, "competitions": set()})
                row["competitions"].add(competition)

    rows: list[dict[str, Any]] = []
    for link, row in sorted(everyone.items()):
        alias = ALIASES.get(link) or ALIASES.get(row["name"])
        own = tokens(alias) if alias else tokens(link)
        match = next((name for name, other in modelled if own & other), None)
        rows.append({
            "wikipedia": link,
            "name": row["name"],
            "country": row["country"],
            "competitions": sorted(row["competitions"]),
            "in_game_as": match,
        })
    return {
        "source": "Wikipedia, páginas de las tres competiciones europeas 1993-94",
        "read_per_page": per_page,
        "participants": len(rows),
        "missing_from_game": sum(1 for r in rows if not r["in_game_as"]),
        "teams": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = build()
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "teams"}, ensure_ascii=False, indent=2))
    for row in payload["teams"]:
        if not row["in_game_as"]:
            print(f"   FALTA  {row['country']:<10}{row['name']:<30}{', '.join(row['competitions'])}")


if __name__ == "__main__":
    main()
