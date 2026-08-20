from __future__ import annotations

"""Lee de Transfermarkt la plantilla de temporada de un club.

BDFutbol da la plantilla de la **eliminatoria europea**, que para un club
eliminado en la primera ronda son una o dos fichas: el Linfield salia con un
futbolista y el Bangor con ninguno. Transfermarkt da la plantilla **de la
temporada entera**, que es lo que hace falta para que esos clubes sean jugables
—del Rosenborg saca 27 donde BDFutbol daba 19—.

Se usa solo para completar. La identidad sigue mandandola la reconciliacion
contra la base, y las fotos siguen viniendo de BDFutbol, que es donde estan.

Dos avisos del formato:

* La plantilla no trae fecha de nacimiento, solo la edad, asi que hay que
  visitar la ficha de cada uno. Va con pausa y con cache en disco.
* ``saison_id/1993`` es la temporada 93-94 en las ligas de calendario partido,
  pero en las de ano natural —la noruega, la sueca— el propio Transfermarkt
  titula la pagina "squad 1994". Es la misma temporada que buscamos; conviene
  mirar el titulo antes de dar por bueno un club nuevo.
"""

import argparse
import json
from pathlib import Path
import re
import time
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
CACHE = DATA / "transfermarkt_player_dob_cache.json"

HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120 Safari/537.36")}
SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
SQUAD_URL = "https://www.transfermarkt.com/x/kader/verein/{club}/saison_id/{season}"
PLAYER_URL = "https://www.transfermarkt.com/x/profil/spieler/{player}"

# Transfermarkt detalla mucho la demarcacion; el juego solo distingue cuatro.
POSITIONS = {
    "goalkeeper": "POR",
    "centre-back": "DEF", "left-back": "DEF", "right-back": "DEF", "defender": "DEF",
    "defensive midfield": "MED", "central midfield": "MED", "attacking midfield": "MED",
    "left midfield": "MED", "right midfield": "MED", "midfield": "MED",
    "left winger": "DEL", "right winger": "DEL", "centre-forward": "DEL",
    "second striker": "DEL", "attack": "DEL", "forward": "DEL",
}

# Cada fila contiene una tabla anidada, asi que cortar por </tr> se queda con la
# mitad: se trocea de un <tr class="odd|even"> al siguiente.
_ROW_START = re.compile(r'<tr class="(?:odd|even)">')
_PLAYER = re.compile(r'href="/[^"]*/profil/spieler/(\d+)"[^>]*>\s*([^<]+?)\s*</a>')
# La demarcacion viene en el title de la celda del dorsal, que es mas fiable que
# buscarla en el texto de la segunda fila de la tabla anidada.
_ROLE = re.compile(r'class="[^"]*rueckennummer[^"]*"\s+title="([^"]+)"')
_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
_DOB = re.compile(r'itemprop="birthDate"[^>]*>\s*(\d{2})/(\d{2})/(\d{4})')


def split_rows(html: str) -> list[str]:
    marks = [m.start() for m in _ROW_START.finditer(html)]
    return [html[a:b] for a, b in zip(marks, marks[1:] + [len(html)])]


def load_cache() -> dict[str, str]:
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")


def find_club(name: str, client: httpx.Client) -> list[dict[str, str]]:
    response = client.get(SEARCH_URL, params={"query": name})
    response.raise_for_status()
    found = re.findall(r'href="(/[^"]+/startseite/verein/(\d+))"[^>]*>([^<]*)</a>', response.text)
    out: list[dict[str, str]] = []
    for _, club_id, label in found:
        label = label.strip()
        if label and not any(row["id"] == club_id for row in out):
            out.append({"id": club_id, "name": label})
    return out[:6]


def fetch_birth_date(player_id: str, client: httpx.Client, *, attempts: int = 4) -> str | None:
    """Transfermarkt corta con un 403 en cuanto se le pide rapido, y devolver
    ``None`` sin mas dejaba media plantilla sin fecha —y sin fecha no se puede
    reconciliar, asi que esos futbolistas se perdian—. Se espera y se reintenta."""
    for attempt in range(attempts):
        response = client.get(PLAYER_URL.format(player=player_id))
        if response.status_code == 200:
            match = _DOB.search(response.text)
            if not match:
                return None
            day, month, year = match.groups()
            return f"{year}-{month}-{day}"
        if response.status_code not in (403, 429, 503):
            return None
        time.sleep(2 * (attempt + 1))
    return None


def read_squad(club_id: str, *, season: int = 1993, delay: float = 0.6) -> dict[str, Any]:
    cache = load_cache()
    players: list[dict[str, Any]] = []
    warnings: list[str] = []
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        response = client.get(SQUAD_URL.format(club=club_id, season=season))
        response.raise_for_status()
        html = response.text
        title = (_TITLE.findall(html) or [""])[0].strip()
        for row in split_rows(html):
            found = _PLAYER.search(row)
            if not found:
                continue
            player_id, name = found.group(1), found.group(2).strip()
            role = _ROLE.search(row)
            code = POSITIONS.get((role.group(1) if role else "").strip().lower())
            if code is None:
                warnings.append(f"demarcacion desconocida {role.group(1)!r} en {name}" if role
                                else f"sin demarcacion legible en {name}")
                continue
            birth = cache.get(player_id) or None
            if birth is None:
                birth = fetch_birth_date(player_id, client) or ""
                cache[player_id] = birth
                time.sleep(delay)
            players.append({
                "transfermarkt_id": player_id,
                "display_name": name.split()[-1],
                "full_name": name,
                "birth_date": birth or None,
                "broad_position": code,
                "minutes": None,
                "matches": None,
                "profile_url": PLAYER_URL.format(player=player_id),
                "photo_url": None,
            })
    save_cache(cache)
    return {
        "transfermarkt_club_id": club_id,
        "page_title": title,
        "source": SQUAD_URL.format(club=club_id, season=season),
        "squad_scope": "plantilla de temporada completa",
        "players": len(players),
        "without_birth_date": sum(1 for p in players if not p["birth_date"]),
        "warnings": warnings,
        "squad": players,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("club", help="identificador de Transfermarkt, o --search para buscarlo")
    parser.add_argument("--search", action="store_true", help="trata el argumento como nombre a buscar")
    parser.add_argument("--season", type=int, default=1993)
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.search:
        with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
            for row in find_club(args.club, client):
                print(f"   {row['id']:<10}{row['name']}")
        return

    payload = read_squad(args.club, season=args.season, delay=args.delay)
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{payload['page_title']}")
    print(f"   {payload['players']} jugadores, {payload['without_birth_date']} sin fecha")
    for aviso in payload["warnings"]:
        print(f"   AVISO: {aviso}")
    for row in payload["squad"]:
        print(f"   {row['broad_position']:<5}{row['full_name']:<32}{row['birth_date'] or '?'}")


if __name__ == "__main__":
    main()
