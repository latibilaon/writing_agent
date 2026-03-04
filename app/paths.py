from __future__ import annotations

import os
import platform
from pathlib import Path

APP_NAME = "UofferApplication"


def _home() -> Path:
    return Path.home()


def user_config_dir() -> Path:
    system = platform.system().lower()
    if system == "darwin":
        return _home() / "Library" / "Application Support" / APP_NAME
    if system == "windows":
        base = os.environ.get("APPDATA")
        return Path(base) / APP_NAME if base else _home() / "AppData" / "Roaming" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME")
    return Path(base) / APP_NAME if base else _home() / ".config" / APP_NAME


def user_data_dir() -> Path:
    system = platform.system().lower()
    if system == "darwin":
        return _home() / "Library" / "Application Support" / APP_NAME / "data"
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / APP_NAME / "data" if base else _home() / "AppData" / "Local" / APP_NAME / "data"
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) / APP_NAME / "data" if base else _home() / ".local" / "share" / APP_NAME / "data"


def settings_path() -> Path:
    return user_config_dir() / "settings.json"


def log_path() -> Path:
    return user_config_dir() / "app.log"


def ensure_dirs(data_root: Path | None = None) -> dict[str, Path]:
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)

    root = data_root or user_data_dir()
    root.mkdir(parents=True, exist_ok=True)

    dirs = {
        "root": root,
        "materials": root / "materials",
        "converted": root / "converted",
        "output": root / "output",
        "templates": root / "templates",
        "contracts": root / "contracts",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    return dirs
