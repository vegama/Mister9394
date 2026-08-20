from __future__ import annotations

"""Ancla los perfiles del pool de selecciones a futbolistas reales comparables.

Los 1.073 futbolistas creados desde convocatorias entraron con atributos
provisionales: una media estimada y el resto rellenado por defecto. El proyecto
no admite eso, y con razón —es la diferencia entre un dato inferido y un dato
inventado—. La regla que ya siguen las 2.103 fichas creadas antes es que los
atributos **se derivan de dos futbolistas reales de la misma demarcación y nivel
parecido**, y se deja escrito de quiénes.

Aquí se hace lo mismo:

* Los comparables salen siempre de jugadores **de la fuente original**, nunca de
  otros creados, para no encadenar estimaciones sobre estimaciones.
* Misma demarcación y la media más próxima a la estimada.
* El vector resultante se escala a la media objetivo y lleva una variación
  pequeña y determinista por ficha. Sin ella dos futbolistas anclados a la misma
  pareja saldrían clonados, y un clon es tan falso como un invento.

Lo que no cambia: la media estimada al crearlos, que ya venía del club real o
del nivel de su competición.
"""

import argparse
from hashlib import blake2b
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
REPORT = DATA / "national_pool_profile_anchoring_report.json"

BATCH = "fixed_source_comparable_real_squad_v113"
OWNED = {"world_cup_1994", "national_pool_1993_94", "european_club_1993_94", "league_club_1993_94"}

ATTRS = (
    "pace", "acceleration", "jumping", "stamina", "strength", "tackling",
    "work_rate", "aggression", "anticipation", "marking", "discipline",
    "positioning", "leadership", "consistency", "vision", "short_pass",
    "long_pass", "dribbling", "finishing", "heading", "off_ball",
    "shot_power", "free_kicks", "penalties", "technique",
)


def jitter(source_id: int, attribute: str) -> int:
    """Variación determinista de -2..+2. Misma ficha, mismo resultado siempre."""
    digest = blake2b(f"{source_id}:{attribute}".encode(), digest_size=2).digest()
    return (int.from_bytes(digest, "big") % 5) - 2


def anchor(snapshot_path: Path = SNAPSHOT, report_path: Path = REPORT) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    players = snapshot["players"]

    # Sólo valen como referencia los que vienen de la base original y tienen el
    # cuadro de atributos completo.
    real: dict[str, list[dict[str, Any]]] = {}
    for player in players:
        if player.get("external_origin") or player.get("retired"):
            continue
        attributes = player.get("attributes") or {}
        if not all(attributes.get(name) for name in ATTRS):
            continue
        position = player.get("broad_position")
        if position:
            real.setdefault(position, []).append(player)
    for rows in real.values():
        rows.sort(key=lambda p: int(p.get("overall") or 0))

    # Tambien hay que rehacer los perfiles cuyos comparables ya no existen: al
    # sustituir plantillas inventadas por reales se borraron futbolistas que
    # servian de referencia a otros, y una ficha que apunta a alguien que no esta
    # es una ficha sin respaldo.
    alive = {int(p["source_id"]) for p in players}
    def orphan_refs(player: dict[str, Any]) -> bool:
        for comparable in player.get("attribute_comparable_source_ids") or []:
            if int(comparable) not in alive:
                return True
        review = player.get("profile_review_0_23") or {}
        for key in ("primary_comparable", "secondary_comparable"):
            row = review.get(key) or {}
            if row.get("source_id") and int(row["source_id"]) not in alive:
                return True
        return False

    orphaned = [p for p in players if orphan_refs(p)]
    pending = [
        p for p in players
        if p.get("external_origin") in OWNED
        and not str(p.get("attribute_source") or "").startswith("fixed_source_comparable_")
    ]
    for player in orphaned:
        if player not in pending:
            pending.append(player)

    used_vectors = {
        tuple(int((p.get("attributes") or {}).get(name) or 0) for name in ATTRS)
        for p in players if p not in pending
    }

    anchored = 0
    skipped: list[dict[str, Any]] = []
    for player in pending:
        position = player.get("broad_position")
        pool = real.get(position or "")
        if not pool:
            skipped.append({"source_id": int(player["source_id"]),
                            "display_name": player.get("display_name"),
                            "reason": f"sin comparables reales para la demarcación {position!r}"})
            continue
        target = max(20, min(99, int(player.get("overall") or 65)))
        nearest = sorted(pool, key=lambda p: (abs(int(p.get("overall") or 0) - target), int(p["source_id"])))[:2]
        if len(nearest) < 2:
            skipped.append({"source_id": int(player["source_id"]),
                            "display_name": player.get("display_name"),
                            "reason": "hacen falta dos comparables y sólo hay uno"})
            continue

        base_overall = sum(int(p.get("overall") or target) for p in nearest) / len(nearest)
        scale = target / base_overall if base_overall else 1.0
        attributes: dict[str, int] = {}
        for name in ATTRS:
            average = sum(int(p["attributes"][name]) for p in nearest) / len(nearest)
            value = round(average * scale) + jitter(int(player["source_id"]), name)
            attributes[name] = max(20, min(99, value))

        # Un clon delataría que el perfil no es suyo: se desplaza hasta que el
        # vector sea único, siempre de forma determinista.
        vector = tuple(attributes[name] for name in ATTRS)
        shift = 0
        while vector in used_vectors and shift < 12:
            shift += 1
            name = ATTRS[shift % len(ATTRS)]
            attributes[name] = max(20, min(99, attributes[name] + (1 if shift % 2 else -1)))
            vector = tuple(attributes[name2] for name2 in ATTRS)
        if vector in used_vectors:
            skipped.append({"source_id": int(player["source_id"]),
                            "display_name": player.get("display_name"),
                            "reason": "no se ha podido obtener un perfil distinto de los demás"})
            continue
        used_vectors.add(vector)

        player["attributes"] = attributes
        # A quien ya tenia perfil curado se le repara la referencia rota pero se
        # le respeta la etiqueta de su tanda: decir que el perfil de un griego
        # del lote 0.31 viene de este es falso y ademas borra su rastro.
        previous = str(player.get("attribute_source") or "")
        player["attribute_source"] = previous if previous.startswith("fixed_source_comparable_") else BATCH
        player["attribute_comparable_source_ids"] = [int(p["source_id"]) for p in nearest]
        # Si la revision antigua apuntaba a alguien que ya no esta, sobra: el
        # respaldo pasa a ser la pareja de comparables recien elegida.
        review = player.get("profile_review_0_23") or {}
        if any(int((review.get(k) or {}).get("source_id") or 0) not in alive
               for k in ("primary_comparable", "secondary_comparable") if review.get(k)):
            player.pop("profile_review_0_23", None)
        anchored += 1

    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "complete",
        "batch": BATCH,
        "policy": "atributos derivados de dos futbolistas reales de la misma demarcación y media próxima",
        "candidates": len(pending),
        "anchored": anchored,
        "skipped": len(skipped),
        "skipped_detail": skipped,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    report = anchor(args.snapshot, args.report)
    print(json.dumps({k: v for k, v in report.items() if k != "skipped_detail"}, ensure_ascii=False, indent=2))
    for row in report["skipped_detail"][:10]:
        print(f"   SIN ANCLAR {row['source_id']} {row['display_name']}: {row['reason']}")


if __name__ == "__main__":
    main()
