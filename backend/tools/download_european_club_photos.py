from __future__ import annotations

"""Descarga los retratos de los futbolistas traidos de plantillas de BDFutbol.

Las altas de clubes europeos llegan con su identificador de BDFutbol en la ficha,
asi que la foto es directa: ``/i/j/<id>.jpg``. No hay que buscar por nombre ni
verificar contra la fecha de nacimiento como en las tandas anteriores, porque el
identificador ya viene de la propia plantilla y no hay ambiguedad posible.

Se normaliza al formato nativo del juego —40x55 JPEG— con el mismo normalizador
que el resto de retratos, para que no se note de donde vino cada uno.
"""

import argparse
import json
from pathlib import Path
import time
from typing import Any

import httpx

from backend.tools.normalize_bdfutbol_photos import normalize_image

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
SNAPSHOT = DATA / "historical_snapshot.json"
RAW = DATA / "bdfutbol_photos_raw"
PORTRAITS = ROOT / "frontend" / "public" / "historical9394" / "players"
REPORT = DATA / "european_club_photo_download_report.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Mister9394HistoricalGame/1.0)"}
PHOTO_URL = "https://www.bdfutbol.com/i/j/{bdfutbol_id}.jpg"
ORIGIN = "european_club_1993_94"


def download(snapshot_path: Path = SNAPSHOT, *, origin: str | None = ORIGIN,
             delay: float = 0.4, overwrite: bool = False) -> dict[str, Any]:
    """``origin=None`` cubre a cualquiera que tenga identificador de BDFutbol y le
    falte el retrato, venga del lote que venga. Hace falta porque un futbolista
    rescatado de un contenedor conserva su origen anterior, y tandas antiguas
    dejaron fichas con identificador y sin foto."""
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    RAW.mkdir(parents=True, exist_ok=True)
    PORTRAITS.mkdir(parents=True, exist_ok=True)

    targets = [p for p in snapshot["players"]
               if p.get("bdfutbol_id") and not p.get("retired")
               and (origin is None or p.get("external_origin") == origin)]
    downloaded: list[dict[str, Any]] = []
    already: list[int] = []
    missing: list[dict[str, Any]] = []

    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for player in targets:
            source_id = int(player["source_id"])
            portrait = PORTRAITS / f"{source_id}.jpg"
            if portrait.exists() and not overwrite:
                already.append(source_id)
                continue
            bdfutbol_id = str(player["bdfutbol_id"])
            response = client.get(PHOTO_URL.format(bdfutbol_id=bdfutbol_id))
            if response.status_code != 200 or not response.content:
                missing.append({"source_id": source_id, "display_name": player.get("display_name"),
                                "bdfutbol_id": bdfutbol_id, "status": response.status_code})
                time.sleep(delay)
                continue
            raw = RAW / f"bdf_{bdfutbol_id}.jpg"
            raw.write_bytes(response.content)
            info = normalize_image(raw, portrait)
            player["photo_status"] = "bundled_normalized_bdfutbol"
            player["photo_source_url"] = PHOTO_URL.format(bdfutbol_id=bdfutbol_id)
            downloaded.append({"source_id": source_id, "display_name": player.get("display_name"),
                               "bdfutbol_id": bdfutbol_id, "size": info.get("size")})
            time.sleep(delay)

    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "complete",
        "origin": origin,
        "candidates": len(targets),
        "downloaded": len(downloaded),
        "already_present": len(already),
        "missing": missing,
        "detail": downloaded,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--origin", default=ORIGIN)
    parser.add_argument("--all-missing", action="store_true",
                        help="cualquiera con identificador de BDFutbol al que le falte el retrato")
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    report = download(args.snapshot, origin=None if args.all_missing else args.origin,
                      delay=args.delay, overwrite=args.overwrite)
    print(f"candidatos {report['candidates']} | descargados {report['downloaded']} | "
          f"ya estaban {report['already_present']} | sin foto {len(report['missing'])}")
    for row in report["missing"][:10]:
        print(f"   SIN FOTO {row['display_name']} (bdf {row['bdfutbol_id']}, HTTP {row['status']})")


if __name__ == "__main__":
    main()
