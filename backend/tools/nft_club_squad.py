from __future__ import annotations

"""Lee de national-football-teams.com la plantilla de un club por temporada.

Es la tercera fuente y cubre lo que las otras dos no:

* **Trae la fecha de nacimiento en la propia tabla del club**, asi que basta una
  peticion por club. BDFutbol y Transfermarkt obligan a visitar la ficha de cada
  futbolista, que es lo que acabo provocando el bloqueo de Transfermarkt.
* **No limita el ritmo.**
* **Tiene retrato** en la ficha del jugador, util para los 187 que BDFutbol no
  tiene (404 comprobado).
* Da partidos y goles de la temporada, que es la unica señal real de jerarquia
  cuando no hay minutos.

Su limite: **solo lista a los internacionales**. Del Rosenborg da trece donde
Transfermarkt da veintisiete. No sirve para completar una plantilla entera, pero
si para los clubes de los que BDFutbol no tiene absolutamente nada, y para
verificar identidades.

El buscador devuelve JSON en ``/search.html?term=<nombre>&ajax=true``.
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
SEARCH_URL = "https://www.national-football-teams.com/search.html"
CLUB_URL = "https://www.national-football-teams.com/club/{club}/{season}/x.html"
PLAYER_URL = "https://www.national-football-teams.com/player/{player}/x.html"

# La clase de la fila da la demarcacion.
POSITIONS = {"gk": "POR", "d": "DEF", "m": "MED", "st": "DEL"}

_ROW = re.compile(
    r'<tr class="(\w+)"[^>]*itemprop="athlete".*?'
    r'href="/player/(\d+)/[^"]*".*?'
    r'itemprop="familyName">([^<]*)</span>,\s*'
    r'<span[^>]*itemprop="givenName">([^<]*)</span>.*?'
    r'itemprop="birthDate">([\d-]+)</td>'
    r'(.*?)</tr>',
    re.S,
)
_STATS = re.compile(r'<td class="stats \w+">\s*(\d+)\s*</td>')
_PHOTO = re.compile(r'src="(https://[^"]*person_photos/[^"]+)"')
_TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def find_club(name: str, client: httpx.Client) -> list[dict[str, str]]:
    response = client.get(SEARCH_URL, params={"term": name, "ajax": "true"},
                          headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"})
    response.raise_for_status()
    try:
        rows = response.json()
    except ValueError:
        return []
    return [{"id": str(r["value"]), "name": r["label"]}
            for r in rows if r.get("category") == "club"]


def photo_url(player_id: str, client: httpx.Client) -> str | None:
    response = client.get(PLAYER_URL.format(player=player_id))
    if response.status_code != 200:
        return None
    found = _PHOTO.search(response.text)
    return found.group(1) if found else None


def read_squad(club_id: str, *, season: int = 1993, with_photos: bool = False,
               delay: float = 0.4) -> dict[str, Any]:
    import time
    players: list[dict[str, Any]] = []
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        response = client.get(CLUB_URL.format(club=club_id, season=season))
        response.raise_for_status()
        html = response.text
        title = (_TITLE.findall(html) or [""])[0].strip()
        for code, player_id, family, given, birth, tail in _ROW.findall(html):
            numbers = [int(n) for n in _STATS.findall(tail)]
            row = {
                "nft_id": player_id,
                "display_name": family.strip(),
                "full_name": f"{given.strip()} {family.strip()}".strip(),
                "birth_date": birth.strip() or None,
                "broad_position": POSITIONS.get(code, "MED"),
                "matches": numbers[0] if numbers else None,
                "goals": numbers[1] if len(numbers) > 1 else None,
                "profile_url": PLAYER_URL.format(player=player_id),
                "photo_url": None,
            }
            if with_photos:
                row["photo_url"] = photo_url(player_id, client)
                time.sleep(delay)
            players.append(row)
    return {
        "nft_club_id": club_id,
        "page_title": title,
        "source": CLUB_URL.format(club=club_id, season=season),
        "squad_scope": "solo futbolistas internacionales de esa temporada",
        "players": len(players),
        "without_birth_date": sum(1 for p in players if not p["birth_date"]),
        "squad": players,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("club", help="identificador, o un nombre con --search")
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--season", type=int, default=1993)
    parser.add_argument("--photos", action="store_true")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.search:
        with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
            for row in find_club(args.club, client):
                print(f"   {row['id']:<10}{row['name']}")
        return

    payload = read_squad(args.club, season=args.season, with_photos=args.photos, delay=args.delay)
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{payload['page_title']}: {payload['players']} jugadores, "
          f"{payload['without_birth_date']} sin fecha")
    for row in payload["squad"]:
        foto = " foto" if row["photo_url"] else ""
        print(f"   {row['broad_position']:<5}{row['full_name']:<30}{row['birth_date']}  "
              f"{row['matches']} part {row['goals']} gol{foto}")


if __name__ == "__main__":
    main()
