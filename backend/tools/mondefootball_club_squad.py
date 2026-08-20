from __future__ import annotations

"""Lee de mondefootball.fr la plantilla de temporada de un club.

Es la mejor de las fuentes probadas y con diferencia, porque **una sola peticion
por club** trae todo lo que hace falta:

* plantilla de la **temporada completa**, no solo la eliminatoria europea;
* nombre, pais y **fecha de nacimiento en la propia fila**, sin visitar la ficha
  de cada futbolista —que es justo lo que hizo que Transfermarkt nos bloqueara—;
* **foto con URL directa y predecible**: ``.../gfx/person/cropped/250x250/<id>.png``.

Es la misma plataforma que worldfootball.net, que esta detras de Cloudflare y no
responde; mondefootball sirve los mismos datos sin bloqueo.

Un aviso: **el titulo de la pagina miente**. Para la temporada 93-94 sigue
diciendo "effectif 2026". El contenido si es el del ano pedido —salen
Skammelsrud, By Rise, Brattbakk y Hoftun—, asi que no hay que fiarse del titulo
para comprobar que se ha cargado la temporada correcta; hay que mirar las fichas.
"""

import argparse
import json
from pathlib import Path
import re
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120 Safari/537.36")}
SQUAD_URL = "https://www.mondefootball.fr/teams/te{club}/x/vs{season}/squad/"
PERSON_URL = "https://www.mondefootball.fr/person/pe{person}/x/"
PHOTO_URL = "https://s.hs-data.com/gfx/person/cropped/250x250/{person}.png"

_ROW = re.compile(r'<tr class="entry[^"]*"[^>]*>(.*?)</tr>', re.S)
_PERSON = re.compile(r'class="person-name[^"]*"><a href="/person/pe(\d+)/[^"]*">([^<]+)</a>')
_COUNTRY = re.compile(r'class="country-name[^"]*"[^>]*><a href="/overview/cy(\d+)/[^"]*">([^<]+)</a>')
_BIRTH = re.compile(r'class="person-birthday">\s*(\d{2})\.(\d{2})\.(\d{4})\s*</td>')
_SHIRT = re.compile(r'class="team_person-shirtnumber[^"]*">\s*(\d+)?\s*</td>')
# La demarcacion es la cabecera de bloque de la tabla, no un <h2>. El ultimo
# bloque es el del entrenador y sus ayudantes: si no se distinguen, Nils Arne
# Eggen entra en la plantilla como centrocampista.
_SECTION = re.compile(r'<th[^>]*class="role">\s*([^<]+?)\s*</th>', re.S)

SECTIONS = {
    "gardiens de but": "POR",
    "defenseurs": "DEF",
    "milieux de terrain": "MED",
    "attaquants": "DEL",
}
STAFF_SECTIONS = ("entraineur",)


def fold(text: str) -> str:
    import unicodedata
    raw = unicodedata.normalize("NFKD", text)
    return "".join(c for c in raw if not unicodedata.combining(c)).casefold().strip()


def section_of(html: str, position: int) -> str | None:
    """Demarcacion segun el ultimo bloque abierto por encima de la fila.

    Devuelve ``None`` para los bloques de cuerpo tecnico, que asi quedan fuera.
    """
    last = None
    for mark in _SECTION.finditer(html):
        if mark.start() > position:
            break
        label = fold(mark.group(1))
        last = None if label.startswith(STAFF_SECTIONS) else SECTIONS.get(label)
    return last


def read_squad(club_id: str, *, season: str = "1993-1994") -> dict[str, Any]:
    url = SQUAD_URL.format(club=club_id, season=season)
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    players: list[dict[str, Any]] = []
    warnings: list[str] = []
    for mark in _ROW.finditer(html):
        row = mark.group(1)
        person = _PERSON.search(row)
        if not person:
            continue
        person_id, name = person.group(1), person.group(2).strip()
        code = section_of(html, mark.start())
        if code is None:
            continue  # cuerpo tecnico, no plantilla
        birth = _BIRTH.search(row)
        if not birth:
            warnings.append(f"sin fecha de nacimiento: {name}")
            continue
        day, month, year = birth.groups()
        country = _COUNTRY.search(row)
        shirt = _SHIRT.search(row)
        players.append({
            "mondefootball_id": person_id,
            "display_name": name.split()[-1],
            "full_name": name,
            "birth_date": f"{year}-{month}-{day}",
            "broad_position": code,
            "country_name": country.group(2) if country else None,
            "shirt_number": int(shirt.group(1)) if shirt and shirt.group(1) else None,
            "profile_url": PERSON_URL.format(person=person_id),
            "photo_url": PHOTO_URL.format(person=person_id),
            "minutes": None,
            "matches": None,
        })
    return {
        "mondefootball_club_id": club_id,
        "season": season,
        "source": url,
        "squad_scope": "plantilla de temporada completa",
        "players": len(players),
        "without_birth_date": len(warnings),
        "warnings": warnings,
        "squad": players,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("club", help="identificador sin el prefijo te, p.ej. 1578")
    parser.add_argument("--season", default="1993-1994")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    payload = read_squad(args.club, season=args.season)
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"club {args.club} temporada {args.season}: {payload['players']} jugadores, "
          f"{payload['without_birth_date']} sin fecha")
    for aviso in payload["warnings"]:
        print(f"   AVISO: {aviso}")
    for row in payload["squad"]:
        print(f"   {row['broad_position']:<5}{row['full_name']:<30}{row['birth_date']}  "
              f"{row['country_name'] or ''}")


if __name__ == "__main__":
    main()
