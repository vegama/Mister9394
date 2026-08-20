from __future__ import annotations

import io
import json
from pathlib import Path

import httpx
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "data" / "football9394" / "historical_snapshot.json"
OUTPUT = ROOT / "frontend" / "public" / "historical9394" / "players"


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    entries = [("José del Solar", "1433"), ("Ronald Baroni", "89709"), ("Dušan Tittel", "65442"), ("Bent Christiansen", "313")]
    applied = []
    for display_name, bdf_id in entries:
        player = next(p for p in snapshot["players"] if p.get("display_name") == display_name)
        urls = [f"https://www.bdfutbol.com/i/j/{bdf_id}b.jpg", f"https://www.bdfutbol.com/i/j/{bdf_id}.jpg"]
        content = None
        source_url = None
        for url in urls:
            response = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if response.status_code == 200 and response.content:
                with Image.open(io.BytesIO(response.content)) as image:
                    rgb = image.convert("RGB")
                    if sum(sum(pixel) for pixel in list(rgb.resize((20, 20)).getdata())) > 1000:
                        content = response.content
                        source_url = url
                        break
        if content is None:
            raise RuntimeError(f"BDFutbol no devolvió una imagen válida para {display_name}")
        with Image.open(io.BytesIO(content)) as image:
            portrait = ImageOps.fit(image.convert("RGB"), (40, 55), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
            OUTPUT.mkdir(parents=True, exist_ok=True)
            portrait.save(OUTPUT / f"{int(player['source_id'])}.jpg", "JPEG", quality=88, optimize=True)
        player["bdfutbol_id"] = bdf_id
        player["bdfutbol_url"] = f"https://www.bdfutbol.com/es/j/j{bdf_id}.html"
        player["photo_status"] = "bundled_normalized_bdfutbol_v114"
        player["photo_source_url"] = source_url
        applied.append({"source_id": player["source_id"], "name": display_name, "source_url": source_url})
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"applied": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
