"""User settings: defaults, validation and JSON persistence.

The settings file lives in the per-user application data directory (on Windows
``%APPDATA%\\SystemMonitor\\settings.json``) so the project folder stays clean.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import (
    DEFAULT_HISTORY_SAMPLES,
    DEFAULT_REFRESH_MS,
    DEFAULT_TEMPERATURE_INTERVAL_S,
    MAX_HISTORY_SAMPLES,
    MAX_REFRESH_MS,
    MAX_TEMPERATURE_INTERVAL_S,
    MIN_HISTORY_SAMPLES,
    MIN_REFRESH_MS,
    MIN_TEMPERATURE_INTERVAL_S,
    ensure_directories,
    settings_path,
)

logger = logging.getLogger(__name__)

THEMES = ("dark", "light")

#: Dashboard metric cards, keyed by stable id and labelled for the UI.
DASHBOARD_CARDS: Dict[str, str] = {
    "cpu": "CPU usage",
    "memory": "RAM usage",
    "disk": "Disk usage",
    "network": "Network speed",
    "uptime": "System uptime",
    "temperature": "CPU temperature",
    "processes": "Running processes",
    "clock": "Current time",
}

#: Dashboard graphs, keyed by stable id and labelled for the UI.
DASHBOARD_GRAPHS: Dict[str, str] = {
    "cpu": "CPU usage graph",
    "memory": "Memory usage graph",
    "network": "Network traffic graph",
    "disk": "Disk activity graph",
}


@dataclass
class Settings:
    """Everything the user can configure, with sane defaults."""

    refresh_interval_ms: int = DEFAULT_REFRESH_MS
    history_samples: int = DEFAULT_HISTORY_SAMPLES
    theme: str = "dark"
    start_minimized: bool = False
    start_with_windows: bool = False
    minimize_to_tray: bool = True
    confirm_terminate: bool = True
    temperature_enabled: bool = True
    temperature_interval_s: int = DEFAULT_TEMPERATURE_INTERVAL_S
    dashboard_cards: Dict[str, bool] = field(
        default_factory=lambda: {key: True for key in DASHBOARD_CARDS}
    )
    dashboard_graphs: Dict[str, bool] = field(
        default_factory=lambda: {key: True for key in DASHBOARD_GRAPHS}
    )
    window_geometry: Optional[str] = None

    # ------------------------------------------------------------ validation
    def normalize(self) -> "Settings":
        """Clamp and coerce every field, repairing a hand-edited file."""
        self.refresh_interval_ms = _clamp_int(
            self.refresh_interval_ms, MIN_REFRESH_MS, MAX_REFRESH_MS, DEFAULT_REFRESH_MS
        )
        self.history_samples = _clamp_int(
            self.history_samples, MIN_HISTORY_SAMPLES, MAX_HISTORY_SAMPLES, DEFAULT_HISTORY_SAMPLES
        )
        self.temperature_interval_s = _clamp_int(
            self.temperature_interval_s,
            MIN_TEMPERATURE_INTERVAL_S,
            MAX_TEMPERATURE_INTERVAL_S,
            DEFAULT_TEMPERATURE_INTERVAL_S,
        )
        if self.theme not in THEMES:
            self.theme = "dark"
        if not isinstance(self.window_geometry, str):
            self.window_geometry = None

        for attribute in (
            "start_minimized",
            "start_with_windows",
            "minimize_to_tray",
            "confirm_terminate",
            "temperature_enabled",
        ):
            setattr(self, attribute, bool(getattr(self, attribute)))

        self.dashboard_cards = _normalize_flag_map(
            self.dashboard_cards, DASHBOARD_CARDS, default=True
        )
        self.dashboard_graphs = _normalize_flag_map(
            self.dashboard_graphs, DASHBOARD_GRAPHS, default=True
        )
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SettingsManager:
    """Loads and stores :class:`Settings` as JSON, never raising on bad input."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else settings_path()
        self.settings = Settings()

    def load(self) -> Settings:
        """Read the settings file, falling back to defaults on any problem."""
        try:
            if not self.path.exists():
                logger.info("No settings file yet at %s; using defaults", self.path)
                return self.settings
            with self.path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read settings (%s); using defaults", exc)
            return self.settings

        if not isinstance(raw, dict):
            logger.warning("Settings file is not a JSON object; using defaults")
            return self.settings

        known = {item.name for item in fields(Settings)}
        loaded = Settings(**{key: value for key, value in raw.items() if key in known})
        if extra := set(raw) - known:
            logger.debug("Ignoring unknown settings keys: %s", ", ".join(sorted(extra)))
        self.settings = loaded.normalize()
        return self.settings

    def save(self, settings: Optional[Settings] = None) -> bool:
        """Write the settings atomically; returns success."""
        if settings is not None:
            self.settings = settings.normalize()

        payload = json.dumps(self.settings.to_dict(), indent=2, sort_keys=True)
        try:
            ensure_directories()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temp file in the same directory, then replace, so a
            # crash mid-write cannot leave a truncated settings file behind.
            handle = tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=str(self.path.parent),
                prefix=".settings-",
                suffix=".tmp",
                delete=False,
            )
            temp_path = Path(handle.name)
            with handle:
                handle.write(payload)
            os.replace(temp_path, self.path)
            logger.info("Settings saved to %s", self.path)
            return True
        except OSError as exc:
            logger.error("Could not save settings: %s", exc)
            return False

    def reset(self) -> Settings:
        """Return (and persist) a fresh default configuration."""
        self.settings = Settings().normalize()
        self.save()
        return self.settings


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _normalize_flag_map(value: Any, template: Dict[str, str], *, default: bool) -> Dict[str, bool]:
    """Keep only known keys, filling in any that are missing."""
    result: Dict[str, bool] = {}
    source = value if isinstance(value, dict) else {}
    for key in template:
        entry = source.get(key, default)
        result[key] = bool(entry)
    return result
