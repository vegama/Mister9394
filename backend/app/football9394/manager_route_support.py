from __future__ import annotations

from collections import OrderedDict
import os
from threading import RLock

from fastapi import HTTPException

from .app_paths import default_app_paths
from .manager_career import ManagerCareerRuntime9394, ManagerCareerStore9394

DEFAULT_CAREER_SAVE_ROOT = default_app_paths().saves
_RUNTIME_CACHE: OrderedDict[str, tuple[int, ManagerCareerRuntime9394]] = OrderedDict()
_RUNTIME_CACHE_LOCK = RLock()
_RUNTIME_CACHE_LIMIT = 2


def _career_store() -> ManagerCareerStore9394:
    try:
        from . import webapp as webapp_module
        root = getattr(webapp_module, "CAREER_SAVE_ROOT", DEFAULT_CAREER_SAVE_ROOT)
    except Exception:
        root = DEFAULT_CAREER_SAVE_ROOT
    backup_override = os.environ.get("MISTER9394_BACKUP_DIR")
    return ManagerCareerStore9394(root, backup_root=backup_override or None)


def _runtime_cache_key(store: ManagerCareerStore9394, career_id: str) -> str:
    return str(store.path_for(career_id).resolve(strict=False))


def _remember_manager_career(career: ManagerCareerRuntime9394, *, store: ManagerCareerStore9394 | None = None) -> None:
    """Keep a validated runtime hot after create/load/save operations.

    Store.load() returns the exact cached state object while the file signature
    remains unchanged. Keying the runtime entry by that object's identity means
    an external save edit/recovery automatically creates a fresh runtime, while
    normal UI requests reuse roster/schedule/strength indexes already built.
    """
    store = store or _career_store()
    key = _runtime_cache_key(store, str(career.state.get("career_id") or ""))
    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE[key] = (id(career.state), career)
        _RUNTIME_CACHE.move_to_end(key)
        while len(_RUNTIME_CACHE) > _RUNTIME_CACHE_LIMIT:
            _RUNTIME_CACHE.popitem(last=False)


def _clear_runtime_cache() -> None:
    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE.clear()
    ManagerCareerStore9394.clear_memory_cache()


def _load_manager_career(career_id: str) -> ManagerCareerRuntime9394:
    store = _career_store()
    key = _runtime_cache_key(store, career_id)
    try:
        state = store.load(career_id)
        with _RUNTIME_CACHE_LOCK:
            cached = _RUNTIME_CACHE.get(key)
            if cached is not None and cached[0] == id(state):
                _RUNTIME_CACHE.move_to_end(key)
                return cached[1]
        runtime = ManagerCareerRuntime9394(state)
        _remember_manager_career(runtime, store=store)
        return runtime
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Carrera Míster 93/94 no encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
