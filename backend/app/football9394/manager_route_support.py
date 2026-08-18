from __future__ import annotations

import os

from fastapi import HTTPException

from .app_paths import default_app_paths
from .manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394

DEFAULT_CAREER_SAVE_ROOT = default_app_paths().saves

def _career_store() -> ManagerCareerStore9394:
    try:
        from . import webapp as webapp_module
        root = getattr(webapp_module, "CAREER_SAVE_ROOT", DEFAULT_CAREER_SAVE_ROOT)
    except Exception:
        root = DEFAULT_CAREER_SAVE_ROOT
    backup_override = os.environ.get("MISTER9394_BACKUP_DIR")
    return ManagerCareerStore9394(root, backup_root=backup_override or None)

def _load_manager_career(career_id: str) -> ManagerCareerRuntime9394:
    try:
        return ManagerCareerRuntime9394(_career_store().load(career_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Carrera Míster 93/94 no encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
