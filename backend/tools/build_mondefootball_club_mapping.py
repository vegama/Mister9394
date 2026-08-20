from __future__ import annotations

"""Empareja los clubes leidos de mondefootball con la base original del juego.

Es la pieza mas delicada de todo esto, porque un emparejamiento malo no da error:
mete la plantilla de un club dentro de otro. Ya paso dos veces.

**Todas las palabras del nombre deben coincidir.** Relajarlo ataba
"warta-poznan" con el Lech, "hutnik-krakow" con el Wisla y "polonia-warszawa"
con el Legia.

**Un nombre de una sola palabra no vale como prueba**, porque suele ser la
ciudad. "lks-lodz" se queda en {lodz} al descartar las siglas, casaba con el
Widzew Lodz y le metia dentro los diecisiete futbolistas del LKS. Se exige
igualdad exacta o que el nombre contenido tenga al menos dos palabras.

**Dos clubes no pueden reclamar el mismo equipo.** Si el equipo ya esta pedido,
el segundo pasa a revision en vez de sobrescribir al primero.

Lo que no casa no se fuerza: sale en la lista de dudosos con sus candidatos para
resolverlo a mano, y en `sin_equipo_en_la_base` si es que el juego nunca modelo
ese club.
"""

import argparse
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from backend.app.football9394.mdb_jet4 import Jet4MDB

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
SQUADS = DATA / "mondefootball_squads_1993.json"
OUT = DATA / "mondefootball_club_mapping.json"
SOURCE_MDB = Path(r"C:\UNIFUTBOL\UNIFUTBOL v14.5\datos.vin\1993\basedatos\basedatos.mdb")

# NFKD no descompone estas letras y sin sustituirlas "Wisla" nunca casa con
# "Wisła" ni "Lodz" con "Łódź".
EXTRA = {"ł": "l", "đ": "d", "ø": "o", "ţ": "t", "ş": "s", "ș": "s", "ț": "t", "æ": "ae", "å": "a"}
STOP = {"fc", "cf", "sk", "bk", "if", "ac", "as", "sc", "cs", "fk", "ks", "nk", "pfc", "pfk",
        "ofk", "mks", "gks", "lks", "fks", "acs", "acf", "csm", "il", "is", "ff", "ik", "sa", "old"}

# Resueltos a mano porque el automatismo no puede decidirlos sin riesgo.
BY_HAND = {
    "fcsb": (613, "FC Steaua Bucureşti",
             "FCSB es el nombre actual del Steaua; crearlo habria duplicado el club"),
    "fc-timisoara": (615, "FC Timisoara", "el otro candidato es el club sucesor moderno"),
    "cska-sofia": (477, "CSKA Sofía", "el otro candidato es el filial"),
}


def fold(text: Any) -> str:
    raw = str(text or "")
    for a, b in EXTRA.items():
        raw = raw.replace(a, b).replace(a.upper(), b.upper())
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(c for c in raw if not unicodedata.combining(c)).casefold()
    for a, b in (("oe", "o"), ("ae", "a"), ("aa", "a")):
        raw = raw.replace(a, b)
    return raw


def tokens(name: Any) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", fold(name)) if len(w) > 2 and w not in STOP}


def matches(club: set[str], team: set[str]) -> bool:
    return bool(club) and (club == team or (len(club) >= 2 and club <= team))


def build(snapshot_path: Path, squads_path: Path, mdb_path: Path) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    squads = json.loads(squads_path.read_text(encoding="utf-8"))
    db = Jet4MDB(mdb_path)
    index = [(int(r["Id"]), str(r.get("Nombre") or ""), tokens(r.get("Nombre")))
             for r in db.rows("Equipo") if r.get("Id")]
    in_game = {int(t["source_id"]) for t in snapshot["teams"]}

    confident: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    claimed: dict[int, str] = {}
    for slug, (team_id, name, why) in BY_HAND.items():
        claimed[team_id] = slug

    for country, block in squads.items():
        for club in block["clubs"]:
            slug = club["slug"]
            if slug in BY_HAND:
                continue
            wanted = tokens(slug)
            found = [(i, n) for i, n, g in index if matches(wanted, g)]
            if len(found) == 1 and found[0][0] not in claimed:
                claimed[found[0][0]] = slug
                confident.append({"pais": country, "slug": slug, "mf": club["mondefootball_id"],
                                  "mdb": found[0][0], "nombre": found[0][1],
                                  "en_juego": found[0][0] in in_game})
                continue
            reason = ("el equipo ya lo reclama " + claimed[found[0][0]]) if len(found) == 1 else \
                     ("varios candidatos" if found else "ningun equipo con ese nombre en la base")
            review.append({"pais": country, "slug": slug, "mf": club["mondefootball_id"],
                           "fichas": club["players"], "motivo": reason,
                           "candidatos": [[i, n] for i, n in found[:3]]})

    return {
        "policy": ("todas las palabras deben coincidir; un nombre de una sola palabra no vale "
                   "como prueba porque suele ser la ciudad; dos clubes no pueden reclamar el "
                   "mismo equipo"),
        "seguros": confident,
        "a_mano": {slug: {"mdb": t, "nombre": n, "motivo": w} for slug, (t, n, w) in BY_HAND.items()},
        "dudosos": review,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--squads", type=Path, default=SQUADS)
    parser.add_argument("--mdb", type=Path, default=SOURCE_MDB)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = build(args.snapshot, args.squads, args.mdb)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"seguros {len(payload['seguros'])} | a mano {len(payload['a_mano'])} | "
          f"a revisar {len(payload['dudosos'])}")
    for row in payload["dudosos"]:
        print(f"   {row['pais']:<10}{row['slug']:<26}{row['motivo']}")


if __name__ == "__main__":
    main()
