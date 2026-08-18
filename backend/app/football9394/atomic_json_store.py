from __future__ import annotations

import json
import logging
import os
import shutil
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
    payload = json.loads(path.read_text(encoding="utf-8"))
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
        previous_tmp = previous.with_suffix(previous.suffix + ".tmp")
        _write_bytes_fsynced(previous_tmp, backup.read_bytes())
        os.replace(previous_tmp, previous)
    backup_tmp = backup.with_suffix(backup.suffix + ".tmp")
    _write_bytes_fsynced(backup_tmp, encoded)
    os.replace(backup_tmp, backup)
    _fsync_directory(backup.parent)


def atomic_json_save(path: Path, payload: dict[str, Any], *, validator: Validator, backup_root: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_path(path, backup_root)

    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    _write_bytes_fsynced(tmp, encoded)
    # Validation happens before the atomic replacement, so a serialization or
    # schema problem cannot destroy the current primary.
    _read_json(tmp, validator)
    os.replace(tmp, path)
    _fsync_directory(path.parent)

    # Once the primary has been committed, publish a byte-identical known-good
    # backup. The prior backup is retained as .prev for a second recovery rung.
    _publish_backup(backup, encoded)
    return path


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
