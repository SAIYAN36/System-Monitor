"""The shared state handed to every page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.monitoring.collector import SystemMonitor
from app.services.history import MetricHistory
from app.services.monitor_service import MonitorWorker
from app.services.settings import Settings, SettingsManager
from app.ui.theme import Theme


@dataclass
class AppContext:
    """Live references the pages need, held in one place."""

    monitor: SystemMonitor
    settings: Settings
    settings_manager: SettingsManager
    history: MetricHistory
    theme: Theme
    #: The polling thread; pages use it to ask for a different collection mode.
    worker: Optional[MonitorWorker] = None
    #: Set by the main window once the tray icon exists.
    tray_available: bool = field(default=False)
