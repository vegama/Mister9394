from __future__ import annotations

import argparse
import io
from pathlib import Path
import shutil

from PIL import Image


def black_placeholder(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            rgb = image.convert("RGB").resize((20, 20))
            pixels = list(rgb.getdata())
        if not pixels:
            return True
        black_ratio = sum(1 for pixel in pixels if max(pixel) <= 8) / len(pixels)
        mean = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3)
        return black_ratio >= 0.8 or mean <= 3.0
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("frontend/public/historical9394"))
    parser.add_argument("--quarantine", type=Path, default=Path("data/football9394/asset_recovery_quarantine/black_placeholders"))
    args = parser.parse_args()
    moved: list[str] = []
    for kind in ("players", "clubs", "stadiums"):
        source = args.root / kind
        destination = args.quarantine / kind
        destination.mkdir(parents=True, exist_ok=True)
        for path in source.iterdir():
            if path.is_file() and black_placeholder(path):
                shutil.move(str(path), str(destination / path.name))
                moved.append(f"{kind}/{path.name}")
    print({"quarantined": len(moved), "files": moved})


if __name__ == "__main__":
    main()
