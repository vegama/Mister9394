from __future__ import annotations

"""Lee de BDFutbol la plantilla europea 1993-94 de un club.

Es la fuente que resuelve el problema de los clubes de ligas no simuladas: el
juego los tiene con plantilla inventada por la base original de UNIFUTBOL, y
Wikipedia no publica páginas de temporada para ellos. BDFutbol sí, con
identificador propio por futbolista y retrato para todos.

La página de plantilla no trae la fecha de nacimiento, sólo la edad, que no basta
para reconciliar contra la base sin riesgo de atar la ficha a otra persona. Por
eso se visita además la ficha de cada uno. Es una petición por jugador, así que
va con pausa y con caché en disco.

Aviso sobre lo que se obtiene: es la plantilla **de la eliminatoria europea**, no
la de liga. Un club que cayó en la primera ronda puede dar catorce fichas. Son
reales y verificables, pero no siempre una plantilla completa de temporada.
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
CACHE = DATA / "bdfutbol_player_dob_cache.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394HistoricalGame/1.0)"}
SQUAD_URL = "https://www.bdfutbol.com/es/t/t1993-94{club}.html"
PLAYER_URL = "https://www.bdfutbol.com/es/j/j{player}.html"
PHOTO_URL = "https://www.bdfutbol.com/i/j/{player}.jpg"

# BDFutbol nombra la demarcación con la abreviatura catalana. "cen" es el
# central, que aquí es defensa como cualquier otro.
POSITIONS = {"por": "POR", "def": "DEF", "cen": "DEF", "mig": "MED", "dav": "DEL"}

# Se parsea fila a fila y no de una pasada sobre la página entera. Con una sola
# expresión regular y ".*?" una fila que no cierra se traga la siguiente: así se
# perdieron Kvarme —cuya demarcación es "cen"— y Rune Tangen, que iba detrás.
_TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_ID = re.compile(r'mini-foto-jugador" src="[^"]*?/i/m/(\d+)\.png"')
_COUNTRY = re.compile(r"<div class='pais ([a-z\-]+)'></div>")
_NAMES = re.compile(
    r"<span class='font-weight-bold mr-2 float-left'>([^<]*)</span>"
    r"<span class='d-none d-md-block float-left'>([^<]*)</span>"
)
_POSITION = re.compile(r'<div class="fit ([a-z]+)"></div>')


def parse_rows(html: str) -> tuple[list[dict[str, str]], list[str]]:
    """Devuelve (filas de jugador, avisos). Nunca descarta a nadie en silencio."""
    rows: list[dict[str, str]] = []
    warnings: list[str] = []
    for row in _TR.findall(html):
        found = _ID.search(row)
        if not found:
            continue
        player_id = found.group(1)
        names = _NAMES.search(row)
        position = _POSITION.search(row)
        if not names or not position:
            warnings.append(f"fila ilegible del jugador {player_id}")
            continue
        code = position.group(1)
        if code not in POSITIONS:
            warnings.append(f"demarcacion desconocida '{code}' en el jugador {player_id}")
            continue
        country = _COUNTRY.search(row)
        rows.append({
            "id": player_id,
            "country": country.group(1) if country else "",
            "short": names.group(1).strip(),
            "full": names.group(2).strip(),
            "position": POSITIONS[code],
        })
    return rows, warnings


_DOB = re.compile(r"(?:Fecha de nacimiento|Date of birth)</[^>]+>\s*<[^>]+>\s*([0-3]?\d/[01]?\d/\d{4})")


def load_cache() -> dict[str, str]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_birth_date(client: httpx.Client, player_id: str) -> str | None:
    response = client.get(PLAYER_URL.format(player=player_id), headers=HEADERS, timeout=25, follow_redirects=True)
    response.raise_for_status()
    match = _DOB.search(response.text)
    if not match:
        return None
    day, month, year = match.group(1).split("/")
    return f"{year}-{int(month):02d}-{int(day):02d}"


def read_squad(club_id: str, *, delay: float = 0.5) -> dict[str, Any]:
    cache = load_cache()
    players: list[dict[str, Any]] = []
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        response = client.get(SQUAD_URL.format(club=club_id))
        response.raise_for_status()
        html = response.text
        club_name = (re.findall(r"<title>Plantilla del (.+?) 1993-94", html) or ["?"])[0]
        rows, warnings = parse_rows(html)
        for row in rows:
            player_id = row["id"]
            birth = cache.get(player_id)
            if birth is None:
                birth = fetch_birth_date(client, player_id) or ""
                cache[player_id] = birth
                time.sleep(delay)
            players.append({
                "bdfutbol_id": player_id,
                "display_name": row["short"],
                "full_name": row["full"],
                "birth_date": birth or None,
                "broad_position": row["position"],
                "country_slug": row["country"],
                "photo_url": PHOTO_URL.format(player=player_id),
                "profile_url": PLAYER_URL.format(player=player_id),
            })
    save_cache(cache)
    return {
        "bdfutbol_club_id": club_id,
        "club_name": club_name,
        "source": SQUAD_URL.format(club=club_id),
        "squad_scope": "plantilla de la eliminatoria europea 1993-94, no de liga",
        "players": len(players),
        "without_birth_date": sum(1 for p in players if not p["birth_date"]),
        "warnings": warnings,
        "squad": players,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("club_id", help="identificador de BDFutbol, p.ej. 10038 para el Rosenborg")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()
    payload = read_squad(args.club_id, delay=args.delay)
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{payload['club_name']}: {payload['players']} jugadores, "
          f"{payload['without_birth_date']} sin fecha de nacimiento")
    for aviso in payload["warnings"]:
        print(f"   AVISO: {aviso}")
    for row in payload["squad"]:
        print(f"   {row['bdfutbol_id']:<9}{row['broad_position']:<5}{row['full_name']:<34}{row['birth_date'] or '?'}")


if __name__ == "__main__":
    main()
