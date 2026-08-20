from __future__ import annotations

"""Mapa club -> identificador de BDFutbol para las competiciones europeas 93-94.

BDFutbol publica la plantilla de cada club por temporada y competición en
``/t/t1993-94<id>.html``, con foto de todos los jugadores. Es la misma fuente que
el proyecto ya usa para retratos y fichas, así que es la mejor para levantar los
clubes europeos que faltan. Lo único que no da es un índice: su listado de
equipos es sólo de España y el buscador general no encuentra los extranjeros.

Sí se pueden leer del cuadro de la competición, donde cada partido enseña el
escudo de los dos equipos y la ruta del escudo lleva el identificador
(``/i/eg/10038.png`` es el Rosenborg). El emparejamiento se hace fila a fila
porque la tabla no es simétrica —el escudo del local va detrás de su nombre y el
del visitante delante— y hay varias disposiciones según la ronda; leer la página
entera con una expresión regular se dejaba fuera a la mitad de los clubes.
"""

import argparse
import json
from pathlib import Path
import re
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "football9394" / "bdfutbol_european_1993_94_clubs.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394HistoricalGame/1.0)"}
BASE = "https://www.bdfutbol.com/es/t/t1993-94{code}.html"

COMPETITIONS = {
    "aCHA": "Copa de Europa",
    "aREC": "Recopa",
    "aUEF": "Copa de la UEFA",
}

_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
# El identificador puede llevar sufijo de letra cuando BDFutbol guarda varias
# versiones del escudo ("10657b" es el Valur): el club es el número.
_CREST = re.compile(r'escut-mini" src="[^"]*?/i/eg/(\d+)[a-z]?\.png"')
_ANCHOR = re.compile(r"<a href='[^']*p\.php\?id=\d+'>([^<]*)</a>")
_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
# Etiquetas de ronda que ocupan una celda igual que el nombre de un equipo.
_ROUND = re.compile(r"^(clasificaci|ronda|1/|octavos|cuartos|semifinal|final|dieciseis|fase)", re.I)


def club_names(row: str) -> list[str]:
    """Nombres de equipo de una fila, en orden y sin la fecha ni la ronda."""
    out: list[str] = []
    for text in _ANCHOR.findall(row):
        name = text.strip()
        if not name or _DATE.match(name) or _ROUND.match(name) or name.isdigit():
            continue
        out.append(name)
    return out


def parse_bracket(html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for row in _ROW.findall(html):
        crests = _CREST.findall(row)
        names = club_names(row)
        if len(crests) != len(names):
            # Una fila descuadrada es una fila que no entendemos; asignar a ciegas
            # ataría un escudo al club equivocado, que es peor que perderla.
            continue
        for crest, name in zip(crests, names):
            found.setdefault(crest, name)
    return found


def build() -> dict[str, Any]:
    clubs: dict[str, dict[str, Any]] = {}
    per_competition: dict[str, int] = {}
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        for code, label in COMPETITIONS.items():
            response = client.get(BASE.format(code=code))
            response.raise_for_status()
            found = parse_bracket(response.text)
            per_competition[label] = len(found)
            for club_id, name in found.items():
                row = clubs.setdefault(club_id, {"name": name, "competitions": []})
                if label not in row["competitions"]:
                    row["competitions"].append(label)
    return {
        "source": "BDFutbol, cuadros de las tres competiciones europeas 1993-94",
        "squad_url": "https://www.bdfutbol.com/es/t/t1993-94{club_id}.html",
        "per_competition": per_competition,
        "clubs": len(clubs),
        "teams": [{"bdfutbol_id": k, **v} for k, v in sorted(clubs.items(), key=lambda x: x[1]["name"])],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = build()
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "teams"}, ensure_ascii=False, indent=2))
    for row in payload["teams"]:
        print(f"   {row['bdfutbol_id']:<8}{row['name']:<28}{', '.join(row['competitions'])}")


if __name__ == "__main__":
    main()
