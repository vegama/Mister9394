from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIR_NAME = "Mister9394"


def _base_user_data_dir() -> Path:
    override = os.environ.get("MISTER9394_USER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / APP_DIR_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    return Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")) / APP_DIR_NAME


@dataclass(frozen=True, slots=True)
class AppPaths9394:
    root: Path
    saves: Path
    backups: Path
    logs: Path

    def ensure(self) -> "AppPaths9394":
        for path in (self.root, self.saves, self.backups, self.logs):
            path.mkdir(parents=True, exist_ok=True)
        return self


def default_app_paths() -> AppPaths9394:
    root = _base_user_data_dir()
    saves = Path(os.environ.get("MISTER9394_SAVE_DIR", root / "saves")).expanduser()
    backups = Path(os.environ.get("MISTER9394_BACKUP_DIR", root / "backups")).expanduser()
    logs = Path(os.environ.get("MISTER9394_LOG_DIR", root / "logs")).expanduser()
    return AppPaths9394(root=root, saves=saves, backups=backups, logs=logs)
