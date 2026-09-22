"""Application constants, filesystem locations and runtime flags.

This module intentionally imports neither Qt nor psutil so that the monitoring
layer and the test-suite can use it in a headless environment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "SystemMonitor"
APP_DISPLAY_NAME = "System Monitor"
APP_VERSION = "1.0.0"

# Refresh interval bounds (milliseconds). The lower bound keeps the application
# itself light: polling faster than twice a second buys nothing on any sensor.
MIN_REFRESH_MS = 500
MAX_REFRESH_MS = 10_000
DEFAULT_REFRESH_MS = 1_000

# Temperatures are read from slow sources (ACPI/SMBus) so they are cached and
# refreshed on their own, much longer, cadence.
MIN_TEMPERATURE_INTERVAL_S = 5
MAX_TEMPERATURE_INTERVAL_S = 300
DEFAULT_TEMPERATURE_INTERVAL_S = 30

# Number of samples kept for the live graphs. Memory stays bounded because the
# history buffers are fixed-capacity ring buffers.
MIN_HISTORY_SAMPLES = 30
MAX_HISTORY_SAMPLES = 900
DEFAULT_HISTORY_SAMPLES = 180


def is_windows() -> bool:
    """True when running on Windows (the primary target platform)."""
    return os.name == "nt"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Directory that contains ``main.py`` (or the unpacked bundle)."""
    if is_frozen():
        bundle = getattr(sys, "_MEIPASS", None)
        if bundle:
            return Path(bundle)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def assets_dir() -> Path:
    """Directory holding bundled assets such as the application icon."""
    return project_root() / "assets"


def _platform_data_root() -> Path:
    """Per-user data root for the current platform."""
    if is_windows():
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def app_data_dir() -> Path:
    """Base directory for everything the application writes at runtime."""
    return _platform_data_root()


def logs_dir() -> Path:
    """Directory holding the rotating log files."""
    return app_data_dir() / "logs"


def settings_path() -> Path:
    """Location of the persisted JSON settings file."""
    return app_data_dir() / "settings.json"


def log_file_path() -> Path:
    """Location of the main log file."""
    return logs_dir() / "system_monitor.log"


def ensure_directories() -> Path:
    """Create the application data directories and return the base one."""
    base = app_data_dir()
    base.mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    return base
