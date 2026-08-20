from __future__ import annotations

"""Normalize downloaded historical player portraits to the game's native 40x55 format.

This tool deliberately does not download images. It consumes a directory produced by
our BDFutbol photo workflow (or any manually verified source), resolves each file to a
Míster 93/94 player id, then writes compact RGB JPEGs that match the historical asset
pack exactly.

Resolution order:
1. filename stem is already a Míster source_id (e.g. 9495312.png);
2. filename stem is a BDFutbol person id present in bdfutbol_photo_queue.json;
3. explicit --mapping JSON maps arbitrary filename stems to source ids.

The output is always 40x55, RGB, JPEG.  Images are center-cropped with ImageOps.fit,
which preserves aspect ratio instead of stretching faces.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUEUE = ROOT / "data" / "football9394" / "bdfutbol_photo_queue.json"
DEFAULT_OUTPUT = ROOT / "frontend" / "public" / "historical9394" / "players"
TARGET_SIZE = (40, 55)
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _load_queue(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("players", payload) if isinstance(payload, dict) else payload


def build_resolution_map(queue_path: Path = DEFAULT_QUEUE, mapping_path: Path | None = None) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for row in _load_queue(queue_path):
        sid = int(row["source_id"])
        mapping[str(sid)] = sid
        bid = str(row.get("bdfutbol_id") or "").strip()
        if bid:
            mapping[bid] = sid
    if mapping_path:
        extra = json.loads(mapping_path.read_text(encoding="utf-8"))
        if isinstance(extra, dict):
            for key, value in extra.items():
                mapping[str(key)] = int(value)
    return mapping


def _rgb_canvas(image: Image.Image) -> Image.Image:
    # PNG thumbnails can carry transparency. Composite them before conversion so they
    # do not acquire a black halo in JPEG.
    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (238, 238, 238, 255))
        bg.alpha_composite(rgba)
        return bg.convert("RGB")
    return image.convert("RGB")


def normalize_image(source: Path, destination: Path, *, quality: int = 88) -> dict[str, Any]:
    with Image.open(source) as im:
        original_size = tuple(im.size)
        rgb = _rgb_canvas(im)
        fitted = ImageOps.fit(rgb, TARGET_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        destination.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(destination, format="JPEG", quality=quality, optimize=True, progressive=False)
    with Image.open(destination) as out:
        assert tuple(out.size) == TARGET_SIZE
        assert out.mode == "RGB"
    return {
        "source": str(source),
        "destination": str(destination),
        "original_size": list(original_size),
        "output_size": list(TARGET_SIZE),
        "mode": "RGB",
    }


def normalize_directory(
    input_dir: Path,
    output_dir: Path = DEFAULT_OUTPUT,
    *,
    queue_path: Path = DEFAULT_QUEUE,
    mapping_path: Path | None = None,
    overwrite: bool = False,
    quality: int = 88,
) -> dict[str, Any]:
    resolution = build_resolution_map(queue_path, mapping_path)
    converted: list[dict[str, Any]] = []
    skipped_existing: list[str] = []
    unresolved: list[str] = []
    invalid: list[dict[str, str]] = []

    for source in sorted(input_dir.iterdir()):
        if not source.is_file() or source.suffix.lower() not in SUPPORTED:
            continue
        stem = source.stem
        # The European downloader keeps provenance in raw filenames as
        # bdf_<bdfutbol_id>.jpg. Accept that form as well as the queue's plain
        # numeric id, otherwise verified downloads remain stranded in raw/.
        sid = resolution.get(stem)
        if sid is None and stem.lower().startswith("bdf_"):
            sid = resolution.get(stem[4:])
        if sid is None:
            unresolved.append(source.name)
            continue
        dest = output_dir / f"{sid}.jpg"
        if dest.exists() and not overwrite:
            skipped_existing.append(source.name)
            continue
        try:
            row = normalize_image(source, dest, quality=quality)
            row["source_id"] = sid
            converted.append(row)
        except Exception as exc:  # pragma: no cover - defensive batch reporting
            invalid.append({"file": source.name, "error": str(exc)})

    return {
        "status": "complete" if not invalid else "complete_with_errors",
        "target_size": list(TARGET_SIZE),
        "format": "JPEG",
        "mode": "RGB",
        "converted": len(converted),
        "skipped_existing": len(skipped_existing),
        "unresolved": len(unresolved),
        "invalid": len(invalid),
        "converted_rows": converted,
        "unresolved_files": unresolved,
        "invalid_files": invalid,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--quality", type=int, default=88)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = normalize_directory(
        args.input_dir,
        args.output_dir,
        queue_path=args.queue,
        mapping_path=args.mapping,
        overwrite=args.overwrite,
        quality=max(50, min(95, int(args.quality))),
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
