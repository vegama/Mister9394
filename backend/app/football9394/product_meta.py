from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
VERSION_FILE = ROOT / "VERSION"
PROJECT_FILE = ROOT / "project_football9394.json"


@lru_cache(maxsize=1)
def product_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version:
        raise RuntimeError("VERSION está vacío")
    return version


@lru_cache(maxsize=1)
def product_metadata() -> dict[str, Any]:
    payload = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    return {
        "project": payload.get("project", "Mister 93/94"),
        "version": product_version(),
        "checkpoint": payload.get("checkpoint", ""),
        "season_start": payload.get("season_start", "1993-94"),
    }
