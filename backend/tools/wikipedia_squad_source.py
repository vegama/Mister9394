from __future__ import annotations

"""Lectura de convocatorias históricas reales desde Wikipedia.

Las páginas de plantillas de torneo (``1994 African Cup of Nations squads``,
``1993 Copa América squads``…) guardan cada convocatoria en plantillas
``{{nat fs player|...}}`` con una estructura muy regular:

    {{nat fs player|no=1|pos=GK|name=[[Ousmane Farota]]
     |age={{Birth date and age2|df=yes|1994|3|26|1964|12|6}}
     |caps=|club=[[Stade Malien]]|clubnat=Mali}}

De ahí salen nombre, demarcación, **fecha de nacimiento** y club, que es
identidad suficiente para dar de alta a un futbolista real sin inventar nada.

Este módulo sólo lee y normaliza: no toca la base del juego. Quien decide qué
hacer con estos datos es ``import_national_squads.py``, que además reconcilia
contra lo que ya existe para no duplicar personas.
"""

from dataclasses import dataclass, field
import re
from typing import Any

import httpx

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "Mister9394-HistoricalGame/1.0 (personal hobby project; contact: jaricma@gmail.com)",
}

POSITIONS = {"GK": "POR", "DF": "DEF", "MF": "MED", "FW": "DEL"}

_PLAYER = re.compile(r"\{\{nat fs (?:g )?player\s*\|(.+?)\}\}\s*(?=\{\{nat fs|\n)", re.S)
_SECTION = re.compile(r"^===\s*([^=]+?)\s*===\s*$", re.M)
_BIRTH = re.compile(r"\{\{[Bb]irth date[^}]*?\|(\d{4})\|(\d{1,2})\|(\d{1,2})\}\}")
_BIRTH2 = re.compile(r"\{\{[Bb]irth date and age2[^}]*?\|\d{4}\|\d{1,2}\|\d{1,2}\|(\d{4})\|(\d{1,2})\|(\d{1,2})")


@dataclass(frozen=True, slots=True)
class SquadPlayer:
    name: str
    position: str          # POR / DEF / MED / DEL
    birth_date: str | None  # ISO, cuando la fuente la da
    club: str | None
    club_country: str | None
    shirt_number: int | None
    nation: str
    source: str

    @property
    def has_identity(self) -> bool:
        """Sin fecha de nacimiento no se puede reconciliar con seguridad."""
        return bool(self.name and self.birth_date)


@dataclass
class SquadPage:
    title: str
    nations: dict[str, list[SquadPlayer]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.nations.values())


def _clean_name(raw: str) -> str:
    value = raw.strip()
    value = re.sub(r"\{\{ill\|([^|}]+)(\|[^}]*)?\}\}", r"\1", value)   # {{ill|Nombre|pl}}
    value = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", value)        # [[destino|texto]]
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)                   # [[Nombre]]
    value = re.sub(r"\{\{[^}]*\}\}", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _birth_date(raw: str) -> str | None:
    match = _BIRTH2.search(raw) or _BIRTH.search(raw)
    if not match:
        return None
    year, month, day = (int(g) for g in match.groups())
    if not (1930 <= year <= 1985 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _fields(block: str) -> dict[str, str]:
    """Separa los campos de la plantilla respetando las llaves anidadas."""
    parts: list[str] = []
    depth = 0
    current = ""
    for char in block:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        if char == "|" and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    out: dict[str, str] = {}
    for part in parts:
        if "=" in part:
            key, _, value = part.partition("=")
            out[key.strip().lower()] = value.strip()
    return out


def parse_wikitext(title: str, wikitext: str) -> SquadPage:
    page = SquadPage(title=title)
    marks = list(_SECTION.finditer(wikitext))
    for index, mark in enumerate(marks):
        nation = _clean_name(mark.group(1))
        end = marks[index + 1].start() if index + 1 < len(marks) else len(wikitext)
        body = wikitext[mark.end():end]
        players: list[SquadPlayer] = []
        for raw in _PLAYER.finditer(body):
            data = _fields(raw.group(1))
            name = _clean_name(data.get("name", ""))
            if not name:
                continue
            shirt = data.get("no", "").strip()
            players.append(SquadPlayer(
                name=name,
                position=POSITIONS.get(data.get("pos", "").strip().upper(), "MED"),
                birth_date=_birth_date(data.get("age", "")),
                club=_clean_name(data.get("club", "")) or None,
                club_country=(data.get("clubnat") or "").strip() or None,
                shirt_number=int(shirt) if shirt.isdigit() else None,
                nation=nation,
                source=title,
            ))
        if players:
            page.nations[nation] = players
    return page


def fetch_squad_page(title: str, client: httpx.Client | None = None) -> SquadPage:
    owns = client is None
    client = client or httpx.Client()
    try:
        response = client.get(WIKI_API, params={
            "action": "parse", "page": title, "prop": "wikitext",
            "format": "json", "formatversion": 2,
        }, headers=HEADERS, timeout=40)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise KeyError(f"Wikipedia no tiene '{title}': {payload['error'].get('info')}")
        return parse_wikitext(title, payload["parse"]["wikitext"])
    finally:
        if owns:
            client.close()


if __name__ == "__main__":  # pragma: no cover - inspección manual
    import sys
    for page_title in sys.argv[1:] or ["1994 African Cup of Nations squads"]:
        page = fetch_squad_page(page_title)
        con_dob = sum(1 for rows in page.nations.values() for row in rows if row.has_identity)
        print(f"\n{page.title}: {len(page.nations)} selecciones, {page.total} jugadores "
              f"({con_dob} con fecha de nacimiento)")
        for nation, rows in page.nations.items():
            ok = sum(1 for row in rows if row.has_identity)
            print(f"   {nation:<22} {len(rows):>3} jugadores  {ok:>3} con fecha")
