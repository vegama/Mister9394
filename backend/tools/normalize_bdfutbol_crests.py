from __future__ import annotations

"""Normalize historical club crests to Míster 93/94's native 40x40 GIF asset contract.

BDFutbol is used only as the verified image source. Runtime lookups remain the
same as for all original clubs: ``/historical9394/clubs/{team_id}.gif``.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TARGET_SIZE = (40, 40)
DEFAULT_OUTPUT = ROOT / "frontend" / "public" / "historical9394" / "clubs"
DEFAULT_REGISTRY = ROOT / "data" / "football9394" / "belgium_1993_94_club_assets.json"


def _rgba_square(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    rgba.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", TARGET_SIZE, (255, 255, 255, 0))
    x = (TARGET_SIZE[0] - rgba.width) // 2
    y = (TARGET_SIZE[1] - rgba.height) // 2
    canvas.alpha_composite(rgba, (x, y))
    return canvas


def normalize_crest(source: Path, destination: Path) -> dict[str, Any]:
    with Image.open(source) as im:
        original_size = list(im.size)
        square = _rgba_square(im)
        # GIF transparency is retained with a single transparent palette index.
        pal = square.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        alpha = square.getchannel("A")
        mask = Image.eval(alpha, lambda a: 255 if a <= 12 else 0)
        pal.paste(255, mask=mask)
        pal.info["transparency"] = 255
        destination.parent.mkdir(parents=True, exist_ok=True)
        pal.save(destination, format="GIF", transparency=255, optimize=True)
    with Image.open(destination) as out:
        assert out.size == TARGET_SIZE
        assert out.format == "GIF"
    return {"source": str(source), "destination": str(destination), "original_size": original_size}


def normalize_registry(registry_path: Path, input_dir: Path, output_dir: Path = DEFAULT_OUTPUT, *, overwrite: bool = False) -> dict[str, Any]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    rows = payload["clubs"]
    converted = []
    retained = []
    missing = []
    for row in rows:
        team_id = int(row["team_id"])
        dest = output_dir / f"{team_id}.gif"
        if dest.exists() and not overwrite:
            retained.append(team_id)
            row["crest_status"] = "retained_existing_game_asset"
            continue
        source = input_dir / f"{int(row['bdfutbol_team_id'])}.png"
        if not source.exists():
            missing.append({"team_id": team_id, "expected": str(source)})
            row["crest_status"] = "source_image_missing"
            continue
        normalize_crest(source, dest)
        converted.append(team_id)
        row["crest_status"] = "normalized_bdfutbol_40x40_gif"
    registry_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "complete" if not missing else "incomplete",
        "clubs": len(rows), "converted": len(converted), "retained": len(retained), "missing": missing,
        "target_size": list(TARGET_SIZE), "format": "GIF",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input_dir", type=Path)
    p.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    report = normalize_registry(a.registry, a.input_dir, a.output_dir, overwrite=a.overwrite)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
