from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, default=12)
    parser.add_argument("--limit", type=int, default=240)
    parser.add_argument("--glob", default="*.jpg")
    args = parser.parse_args()
    files = sorted(args.root.glob(args.glob), key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)[:args.limit]
    cell_w, cell_h = 76, 92
    out = Image.new("RGB", (args.columns * cell_w, ((len(files) + args.columns - 1) // args.columns) * cell_h), "white")
    draw = ImageDraw.Draw(out)
    for index, path in enumerate(files):
        with Image.open(path) as image:
            image = image.convert("RGB").resize((40, 55))
            x = (index % args.columns) * cell_w + 18
            y = (index // args.columns) * cell_h + 2
            out.paste(image, (x, y))
            draw.text(((index % args.columns) * cell_w + 2, y + 59), path.stem, fill="black")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output, "JPEG", quality=90)


if __name__ == "__main__":
    main()
