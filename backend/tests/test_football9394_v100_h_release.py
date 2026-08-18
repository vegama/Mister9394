from __future__ import annotations

import json

import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.football9394.app_paths import default_app_paths
from backend.app.football9394.atomic_json_store import SaveRecoveryError
from backend.app.football9394.manager_career import ManagerCareerStore9394
from backend.app.football9394.product_meta import product_version
from backend.app.football9394.webapp import app
from backend.app.football9394.world_career import WorldCareerStore9394


ROOT = Path(__file__).resolve().parents[2]


def test_version_file_is_single_release_source():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version == "1.0.0-h"
    assert product_version() == version
    project = json.loads((ROOT / "project_football9394.json").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))
    assert project["version"] == package["version"] == lock["version"] == version
    assert lock["packages"][""]["version"] == version


def test_api_exposes_canonical_version():
    response = TestClient(app).get("/api/football9394/health")
    assert response.status_code == 200
    assert response.json()["version"] == product_version()
    assert app.version == product_version()


def test_app_paths_live_outside_repo_when_user_data_override_is_used(monkeypatch, tmp_path):
    root = tmp_path / "profile-data"
    monkeypatch.setenv("MISTER9394_USER_DATA_DIR", str(root))
    for key in ("MISTER9394_SAVE_DIR", "MISTER9394_BACKUP_DIR", "MISTER9394_LOG_DIR"):
        monkeypatch.delenv(key, raising=False)
    paths = default_app_paths().ensure()
    assert paths.root == root
    assert paths.saves == root / "saves"
    assert paths.backups == root / "backups"
    assert paths.logs == root / "logs"
    assert all(path.is_dir() for path in (paths.saves, paths.backups, paths.logs))


def test_manager_save_is_atomic_and_recovers_latest_valid_backup(tmp_path):
    saves = tmp_path / "saves"
    store = ManagerCareerStore9394(saves)
    state = {"career_id": "release-gate", "schema": 23, "marker": 1}
    path = store.save(state)
    assert path.exists()
    backup = tmp_path / "backups" / path.name
    assert backup.exists()
    assert json.loads(backup.read_text(encoding="utf-8"))["marker"] == 1

    state["marker"] = 2
    store.save(state)
    assert json.loads(path.read_text(encoding="utf-8"))["marker"] == 2
    assert json.loads(backup.read_text(encoding="utf-8"))["marker"] == 2
    previous = backup.with_suffix(backup.suffix + ".prev")
    assert json.loads(previous.read_text(encoding="utf-8"))["marker"] == 1

    path.write_text('{"schema":23,"career_id":"release-gate",', encoding="utf-8")
    restored = store.load("release-gate")
    assert restored["marker"] == 2
    assert list(saves.glob("release-gate.json.corrupt-*"))


def test_corrupt_primary_and_corrupt_latest_backup_can_fall_back_to_previous(tmp_path):
    saves = tmp_path / "saves"
    store = ManagerCareerStore9394(saves)
    state = {"career_id": "double-recovery", "schema": 23, "marker": "old"}
    path = store.save(state)
    state["marker"] = "new"
    store.save(state)
    backup = tmp_path / "backups" / path.name
    path.write_text("{bad", encoding="utf-8")
    backup.write_text("{also-bad", encoding="utf-8")
    restored = store.load("double-recovery")
    assert restored["marker"] == "old"


def test_store_respects_explicit_backup_root_for_manager_and_world(tmp_path):
    saves = tmp_path / "custom-saves"
    backups = tmp_path / "custom-backups"

    manager = ManagerCareerStore9394(saves, backup_root=backups)
    manager_path = manager.save({"career_id": "manager-custom", "schema": 23, "marker": 7})
    assert (backups / manager_path.name).is_file()

    world = WorldCareerStore9394(saves, backup_root=backups)
    world_path = world.save({"career_id": "world-custom", "schema": 1, "season": "1993-94"})
    assert (backups / world_path.name).is_file()
    assert world.load("world-custom")["season"] == "1993-94"


def test_recovery_error_is_readable_when_no_valid_copy_survives(tmp_path):
    store = ManagerCareerStore9394(tmp_path / "saves")
    path = store.path_for("no-valid-copy")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")
    backup = tmp_path / "backups" / path.name
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text("{also-broken", encoding="utf-8")
    with pytest.raises(SaveRecoveryError) as excinfo:
        store.load("no-valid-copy")
    message = str(excinfo.value)
    assert "No se pudo abrir el save" in message
    assert path.name in message
    assert backup.name in message
