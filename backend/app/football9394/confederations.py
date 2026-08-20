from __future__ import annotations

"""Reparto de selecciones por confederación, tal como estaban en 1993.

Hasta ahora el Mundial cogía ``catalog[:24]``, es decir las veinticuatro
selecciones con mejor plantilla del mundo. Eso deja un torneo con dieciocho
europeas y ningún africano, que es justo lo contrario de lo que hace un mundial
de verdad: la gracia del formato es que cada continente trae a los suyos. Para
poder repartir plazas por continente hace falta saber a qué confederación
pertenece cada país, y eso el MDB no lo trae.

Dos detalles de época que no son erratas:

* **Australia juega en la OFC.** No se pasa a la AFC hasta 2006, así que aquí
  pelea su plaza en Oceanía, no en Asia.
* **Yugoslavia sigue en la UEFA.** En 1993 estaba sancionada por la FIFA, pero
  este mundo es historia alternativa y una Yugoslavia con ochenta y cuatro
  internacionales elegibles es demasiado buen material para dejarlo fuera.

Los identificadores son los del universo; los nombres viven en
``PRESENTATION_COUNTRIES``.
"""

from typing import Iterable

UEFA = "UEFA"
CONMEBOL = "CONMEBOL"
CAF = "CAF"
AFC = "AFC"
CONCACAF = "CONCACAF"
OFC = "OFC"

CONFEDERATION_NAMES = {
    UEFA: "Europa",
    CONMEBOL: "Sudamérica",
    CAF: "África",
    AFC: "Asia",
    CONCACAF: "Norteamérica",
    OFC: "Oceanía",
}

COUNTRY_CONFEDERATION: dict[int, str] = {
    # UEFA
    1: UEFA, 3: UEFA, 4: UEFA, 5: UEFA, 6: UEFA, 10: UEFA, 11: UEFA,
    16: UEFA, 17: UEFA, 20: UEFA, 21: UEFA, 31: UEFA, 33: UEFA, 36: UEFA,
    40: UEFA, 41: UEFA, 43: UEFA, 44: UEFA, 45: UEFA, 46: UEFA, 47: UEFA,
    60: UEFA, 61: UEFA, 70: UEFA, 72: UEFA, 75: UEFA, 79: UEFA, 80: UEFA,
    84: UEFA, 85: UEFA, 93: UEFA,
    # CONMEBOL — los diez de siempre
    2: CONMEBOL, 19: CONMEBOL, 23: CONMEBOL, 26: CONMEBOL, 34: CONMEBOL,
    62: CONMEBOL, 63: CONMEBOL, 68: CONMEBOL, 69: CONMEBOL, 86: CONMEBOL,
    # CAF
    12: CAF, 14: CAF, 29: CAF, 35: CAF, 42: CAF, 56: CAF, 59: CAF, 66: CAF,
    74: CAF, 77: CAF, 78: CAF, 83: CAF, 87: CAF, 88: CAF, 103: CAF,
    112: CAF, 117: CAF, 120: CAF, 124: CAF, 169: CAF,
    # AFC
    13: AFC, 24: AFC, 28: AFC, 48: AFC, 50: AFC, 203: AFC,
    # CONCACAF
    22: CONCACAF, 38: CONCACAF, 64: CONCACAF,
    # OFC
    15: OFC,
    # Países con muy pocos futbolistas en la base. No dan para selección jugable,
    # pero sin confederación quedarían fuera de cualquier reparto continental el
    # día que la den.
    8: UEFA, 18: UEFA, 25: UEFA, 37: UEFA, 39: UEFA, 54: UEFA, 65: UEFA,
    76: UEFA, 104: UEFA, 130: UEFA, 131: UEFA,
    # Israel entra en la UEFA en 1994 tras años sin confederación estable; en
    # esta temporada ya disputa la clasificación europea.
    49: UEFA,
    67: CAF, 81: CAF, 115: CAF, 121: CAF, 125: CAF, 149: CAF, 151: CAF,
    170: CAF, 173: CAF, 194: CAF, 213: CAF,
    30: CONCACAF, 92: CONCACAF, 106: CONCACAF, 107: CONCACAF, 119: CONCACAF,
    126: CONCACAF, 147: CONCACAF, 200: CONCACAF, 219: CONCACAF,
    110: OFC, 150: OFC, 185: OFC,
    218: AFC,
}

# Plazas del mundial de veinticuatro equipos. Es el reparto de Italia 90 y
# Estados Unidos 94: trece europeos, cuatro sudamericanos, tres africanos, dos
# asiáticos y dos del área norteamericana, con Oceanía peleando su billete en
# una repesca que aquí se resuelve dentro de su propio grupo.
WORLD_CUP_24_BERTHS = {
    UEFA: 13,
    CONMEBOL: 4,
    CAF: 3,
    CONCACAF: 2,
    AFC: 2,
    OFC: 0,
}


def confederation_of(country_id: int | None) -> str | None:
    if country_id is None:
        return None
    return COUNTRY_CONFEDERATION.get(int(country_id))


def by_confederation(country_ids: Iterable[int]) -> dict[str, list[int]]:
    """Agrupa una lista de países por confederación, descartando los que no
    tenemos mapeados: es preferible dejar fuera a un país sin clasificar que
    colocarlo en un continente al azar."""
    out: dict[str, list[int]] = {key: [] for key in CONFEDERATION_NAMES}
    for country_id in country_ids:
        key = confederation_of(country_id)
        if key is not None:
            out[key].append(int(country_id))
    return out
