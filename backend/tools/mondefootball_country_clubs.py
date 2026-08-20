from __future__ import annotations

"""Saca de mondefootball los clubes de un pais en la temporada 93-94.

Hace falta porque su buscador no existe: no hay endpoint que devuelva un club
por nombre, asi que el identificador ``te`` hay que sacarlo de algun sitio. La
cadena que si funciona es:

    /overview/cy<pais>/            -> competiciones de ese pais
    /competition/co<liga>/...      -> selector con todas las temporadas
    .../se<temporada>/1993/...     -> los clubes, con su te

Con eso sale la lista entera de una liga de un tiron, que es mucho mas barato
que ir club por club, y ademas trae el escudo por URL predecible.
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
OUT = DATA / "mondefootball_clubs_1993.json"

BASE = "https://www.mondefootball.fr"
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120 Safari/537.36")}
CREST_URL = "https://s.hs-data.com/gfx/emblem/common/150x150/{team}.png"

def get(client: httpx.Client, url: str, *, attempts: int = 5) -> httpx.Response | None:
    """Peticion con espera creciente.

    mondefootball no bloquea como Transfermarkt, pero responde 429 si se le
    pide seguido. Con esperas de 3, 6, 9... segundos se recupera solo y no hay
    que abandonar la liga a medias.
    """
    for attempt in range(attempts):
        try:
            response = client.get(url)
        except httpx.HTTPError:
            time.sleep(3 * (attempt + 1))
            continue
        if response.status_code == 200:
            return response
        if response.status_code not in (429, 503):
            return None
        time.sleep(3 * (attempt + 1))
    return None


_COMPETITION = re.compile(r'/competition/(co\d+)/([a-z0-9\-]+)/')
_OPTION = re.compile(r'<option[^>]*value="([^"]*)"[^>]*>\s*([^<]*?)\s*</option>')
_TEAM = re.compile(r'/teams/te(\d+)/([a-z0-9\-]+)/')

# Etiquetas de temporada validas para 1993-94, segun si la liga es de ano
# natural (Noruega, Suecia) o de calendario partido.
SEASON_LABELS = ("1993", "1993/1994", "1993-1994")


def competitions(country_id: str, client: httpx.Client) -> list[tuple[str, str]]:
    response = get(client, f"{BASE}/overview/cy{country_id}/x/")
    if response is None:
        return []
    found = {(cid, name) for cid, name in _COMPETITION.findall(response.text)}
    # Las competiciones de otros paises tambien salen en el menu; se filtran por
    # el prefijo del nombre, que en esta web lleva siempre el pais delante.
    return sorted(found)


def season_url(competition: str, slug: str, client: httpx.Client) -> str | None:
    response = get(client, f"{BASE}/competition/{competition}/{slug}/results-and-standings/")
    if response is None:
        return None
    for value, label in _OPTION.findall(response.text):
        if label.strip() in SEASON_LABELS and "/se" in value:
            return value if value.startswith("http") else BASE + value
    return None


def clubs_in(url: str, client: httpx.Client) -> list[dict[str, str]]:
    response = get(client, url)
    if response is None:
        return []
    seen: dict[str, str] = {}
    for team_id, slug in _TEAM.findall(response.text):
        seen.setdefault(team_id, slug)
    return [{"mondefootball_id": k, "slug": v, "crest_url": CREST_URL.format(team=k)}
            for k, v in sorted(seen.items(), key=lambda x: int(x[0]))]


def collect(country_id: str, *, only: str | None = None, delay: float = 0.5) -> dict[str, Any]:
    out: list[dict[str, Any]] = []
    with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
        for competition, slug in competitions(country_id, client):
            if only and only not in slug:
                continue
            url = season_url(competition, slug, client)
            time.sleep(delay)
            if not url:
                continue
            rows = clubs_in(url, client)
            time.sleep(delay)
            if rows:
                out.append({"competition": competition, "slug": slug, "season_url": url,
                            "clubs": rows})
    return {"country_id": country_id, "competitions": len(out), "detail": out}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("country", help="identificador cy sin prefijo, p.ej. 156 para Noruega")
    parser.add_argument("--only", help="filtra por texto del nombre de competicion")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = collect(args.country, only=args.only, delay=args.delay)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for block in payload["detail"]:
        print(f"{block['slug']} ({len(block['clubs'])} clubes)")
        for row in block["clubs"]:
            print(f"   te{row['mondefootball_id']:<8}{row['slug']}")


if __name__ == "__main__":
    main()
