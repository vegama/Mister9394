from __future__ import annotations

import itertools
import json
import logging
import os
import shutil
import threading
import time

try:
    import orjson
except ImportError:  # pragma: no cover - compatibility fallback
    orjson = None
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

LOGGER = logging.getLogger("mister9394.save")
Validator = Callable[[dict[str, Any]], None]

# Windows can transiently deny os.replace() (WinError 5/32) when antivirus or
# an indexer briefly opens the just-written file between close() and the
# rename; the same rename would simply succeed on retry a few ms later. POSIX
# rename() has no such window, so this only ever loops there.
_REPLACE_RETRY_DELAYS = (0.05, 0.1, 0.2, 0.4, 0.8)


def _replace_with_retry(src: Path, dst: Path) -> None:
    for delay in _REPLACE_RETRY_DELAYS:
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            time.sleep(delay)
    os.replace(src, dst)


# Two concurrent requests can save the same career (e.g. two panels each
# refreshing and persisting state on page load) from different threads.
# A shared "<name>.tmp" path meant one writer's os.replace() could consume
# the other's tmp file out from under it, turning a harmless double-save
# into a FileNotFoundError. Each write gets its own tmp path instead; the
# final os.replace() onto the real path is still atomic and last-write-wins,
# which is fine since both writers are persisting the same in-process state.
_tmp_suffix_counter = itertools.count()


def _unique_tmp_path(path: Path) -> Path:
    token = f"{os.getpid()}-{threading.get_ident()}-{next(_tmp_suffix_counter)}"
    return path.with_suffix(path.suffix + f".{token}.tmp")


# Unique tmp names stop writers from stepping on each other's tmp file, but
# atomic_json_save is a multi-step protocol (write primary, rotate backup to
# .prev, publish new backup) built assuming a single writer per path. Two
# concurrent saves to the *same* career file can still race a later step -
# e.g. both see the backup exists and both try to rename it to .prev, so the
# second one finds it already gone. A per-path lock serializes writers to the
# same destination while leaving unrelated saves (different careers/files)
# free to run in parallel.
_path_locks: dict[str, threading.Lock] = {}
_path_locks_guard = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path)
    with _path_locks_guard:
        lock = _path_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _path_locks[key] = lock
        return lock


class SaveRecoveryError(ValueError):
    pass


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_json(path: Path, validator: Validator) -> dict[str, Any]:
    if orjson is not None:
        # orjson parses UTF-8 bytes directly, avoiding Python's slower Unicode
        # decoder + stdlib JSON scanner on 8-12 MB career saves.
        payload = orjson.loads(path.read_bytes())
    else:
        # Compatibility fallback for environments where the optional wheel is
        # not available.
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("el save no contiene un objeto JSON")
    validator(payload)
    return payload


def _write_bytes_fsynced(path: Path, data: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _backup_path(path: Path, backup_root: Path | None) -> Path:
    if backup_root is None:
        return path.with_suffix(path.suffix + ".bak")
    return backup_root / path.name


def _publish_backup(backup: Path, encoded: bytes) -> None:
    backup.parent.mkdir(parents=True, exist_ok=True)
    previous = backup.with_suffix(backup.suffix + ".prev")
    if backup.exists():
        # The current backup is already a validated, fsynced file. Rotate it
        # atomically instead of reading and rewriting another multi-megabyte
        # copy on every action. If publishing the new backup fails afterwards,
        # recovery still has this known-good ``.prev`` rung.
        _replace_with_retry(backup, previous)
        _fsync_directory(backup.parent)
    backup_tmp = _unique_tmp_path(backup)
    _write_bytes_fsynced(backup_tmp, encoded)
    _replace_with_retry(backup_tmp, backup)
    _fsync_directory(backup.parent)


def atomic_json_save(path: Path, payload: dict[str, Any], *, validator: Validator, backup_root: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_path(path, backup_root)

    # Validate the in-memory state before touching disk. ``json.dumps`` below is
    # itself the serialization gate (and still fails on non-JSON values), so
    # parsing the just-written 10+ MB temporary file again only duplicated CPU
    # and I/O on every player action. Compact JSON also cuts save/load bytes by
    # roughly a third while preserving exactly the same recovery format.
    validator(payload)
    if orjson is not None:
        encoded = orjson.dumps(
            payload,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_APPEND_NEWLINE | orjson.OPT_PASSTHROUGH_DATETIME,
        )
    else:
        encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _lock_for(path):
        tmp = _unique_tmp_path(path)
        _write_bytes_fsynced(tmp, encoded)
        _replace_with_retry(tmp, path)
        _fsync_directory(path.parent)

        # Once the primary has been committed, publish a byte-identical known-good
        # backup. The prior backup is retained as .prev for a second recovery rung.
        _publish_backup(backup, encoded)
    return path



def atomic_json_checkpoint(path: Path, payload: dict[str, Any], *, validator: Validator) -> Path:
    """Atomically publish a durable JSON checkpoint without backup rotation.

    This is intended for small derivative journals/overlays whose canonical
    parent already has the full backup ladder. The previous checkpoint remains
    visible until the replacement has been completely written and fsynced.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    validator(payload)
    if orjson is not None:
        encoded = orjson.dumps(
            payload,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_APPEND_NEWLINE | orjson.OPT_PASSTHROUGH_DATETIME,
        )
    else:
        encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _lock_for(path):
        tmp = _unique_tmp_path(path)
        _write_bytes_fsynced(tmp, encoded)
        _replace_with_retry(tmp, path)
        _fsync_directory(path.parent)
    return path


def load_json_checkpoint(path: Path, *, validator: Validator) -> dict[str, Any]:
    return _read_json(path, validator)

def recover_json_load(path: Path, *, validator: Validator, backup_root: Path | None = None) -> dict[str, Any]:
    backup = _backup_path(path, backup_root)
    candidates = (backup, backup.with_suffix(backup.suffix + ".prev"))
    try:
        return _read_json(path, validator)
    except FileNotFoundError:
        if not any(candidate.exists() for candidate in candidates):
            raise
        primary_error: Exception = FileNotFoundError(path)
    except Exception as exc:
        primary_error = exc

    errors: list[str] = []
    payload: dict[str, Any] | None = None
    used: Path | None = None
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            payload = _read_json(candidate, validator)
            used = candidate
            break
        except Exception as exc:
            errors.append(f"{candidate.name}: {exc}")
    if payload is None or used is None:
        raise SaveRecoveryError(
            f"No se pudo abrir el save '{path.name}'. Primario: {primary_error}. Backups: {'; '.join(errors) or 'no disponibles'}."
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if path.exists():
        corrupt = path.with_suffix(path.suffix + f".corrupt-{stamp}")
        try:
            shutil.copy2(path, corrupt)
        except OSError:
            LOGGER.exception("No se pudo conservar copia del save corrupto %s", path)
    LOGGER.warning("Save recuperado desde backup válido: %s. Error primario: %s", used, primary_error)
    return payload
