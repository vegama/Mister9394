from __future__ import annotations

import json
import logging
import os
import shutil

try:
    import orjson
except ImportError:  # pragma: no cover - compatibility fallback
    orjson = None
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

LOGGER = logging.getLogger("mister9394.save")
Validator = Callable[[dict[str, Any]], None]


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
        os.replace(backup, previous)
        _fsync_directory(backup.parent)
    backup_tmp = backup.with_suffix(backup.suffix + ".tmp")
    _write_bytes_fsynced(backup_tmp, encoded)
    os.replace(backup_tmp, backup)
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
    tmp = path.with_suffix(path.suffix + ".tmp")
    _write_bytes_fsynced(tmp, encoded)
    os.replace(tmp, path)
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
    tmp = path.with_suffix(path.suffix + ".tmp")
    _write_bytes_fsynced(tmp, encoded)
    os.replace(tmp, path)
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
