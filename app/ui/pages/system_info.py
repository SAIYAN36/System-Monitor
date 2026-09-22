"""System information page: OS, machine, hardware and runtime details."""

from __future__ import annotations

import datetime as _dt

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QPushButton

from app.config import APP_DISPLAY_NAME, APP_VERSION, ensure_directories, logs_dir
from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage
from app.ui.widgets.cards import Card, InfoGrid
from app.utils.formatting import (
    UNAVAILABLE,
    format_bytes,
    format_duration,
    format_frequency,
    format_timestamp,
)

_OS_ROWS = (
    ("os", "Operating system"),
    ("edition", "Edition"),
    ("version", "Kernel version"),
    ("build", "Build"),
    ("architecture", "Architecture"),
    ("machine", "Machine type"),
    ("python", "Python runtime"),
    ("qt", "Qt / PySide6"),
    ("psutil", "psutil"),
    ("app", "Application"),
)

_MACHINE_ROWS = (
    ("hostname", "Computer name"),
    ("boot", "Boot time"),
    ("uptime", "Uptime"),
    ("local_time", "Local time"),
)

_CPU_ROWS = (
    ("name", "Processor"),
    ("physical", "Physical cores"),
    ("logical", "Logical processors"),
    ("max_frequency", "Maximum frequency"),
)

_MEMORY_ROWS = (
    ("total", "Installed memory"),
    ("swap", "Page file size"),
)

_STORAGE_ROWS = (
    ("drives", "Volumes"),
    ("physical", "Physical disks"),
)

_NETWORK_ROWS = (("adapters", "Network adapters"),)


class SystemInfoPage(ScrollPage):
    key = "system"
    title = "System Information"
    subtitle = "Static details about this machine and the running application."

    def populate(self) -> None:
        self.os_grid = InfoGrid(columns=1, label_width=170)
        self.os_grid.add_rows(_OS_ROWS)
        os_card = self._card("Operating system", "window", self.os_grid)

        self.machine_grid = InfoGrid(columns=1, label_width=170)
        self.machine_grid.add_rows(_MACHINE_ROWS)
        machine_card = self._card("Computer", "info", self.machine_grid)
        self.add_row([os_card, machine_card])

        self.cpu_grid = InfoGrid(columns=1, label_width=170)
        self.cpu_grid.add_rows(_CPU_ROWS)
        cpu_card = self._card("Processor", "cpu", self.cpu_grid)

        self.memory_grid = InfoGrid(columns=1, label_width=170)
        self.memory_grid.add_rows(_MEMORY_ROWS)
        memory_card = self._card("Memory", "memory", self.memory_grid)
        self.add_row([cpu_card, memory_card])

        self.storage_grid = InfoGrid(columns=1, label_width=170)
        self.storage_grid.add_rows(_STORAGE_ROWS)
        storage_card = self._card("Storage", "disk", self.storage_grid)

        self.network_grid = InfoGrid(columns=1, label_width=170)
        self.network_grid.add_rows(_NETWORK_ROWS)
        network_card = self._card("Network", "network", self.network_grid)
        self.add_row([storage_card, network_card])

        self.add_content(self._diagnostics_card())
        self.add_stretch()
        self._load_static()

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        system = update.snapshot.system
        if system is None:
            return

        now = _dt.datetime.now()
        self.machine_grid.set_values(
            {
                "hostname": system.hostname or None,
                "boot": format_timestamp(system.boot_time),
                "uptime": format_duration(update.snapshot.uptime),
                "local_time": f"{now.strftime('%H:%M:%S')} · {now.strftime('%d %b %Y')}",
            }
        )
        self.os_grid.set_values(
            {
                "os": system.os_name or None,
                "edition": system.os_edition or None,
                "version": system.os_version or None,
                "build": system.os_build or None,
                "architecture": system.architecture or None,
                "machine": system.machine or None,
            }
        )
        self.memory_grid.set_values(
            {
                "total": format_bytes(system.total_memory),
                "swap": format_bytes(update.snapshot.memory.swap_total),
            }
        )

        partitions = update.snapshot.disk.partitions
        self.storage_grid.set_values(
            {
                "drives": "\n".join(
                    f"{part.display_name} · {part.drive_type or 'volume'} · "
                    f"{part.fstype or 'unknown file system'}"
                    for part in partitions
                )
                or None,
                "physical": "\n".join(system.physical_disks) if system.physical_disks else None,
            }
        )

        adapters = system.network_adapters
        self.network_grid.set_values(
            {"adapters": "\n".join(adapters) if adapters else None}
        )

    # ---------------------------------------------------------------- internals
    def _card(self, title: str, icon: str, grid: InfoGrid) -> Card:
        card = Card(theme=self.theme, title=title, icon_name=icon)
        card.add_widget(grid)
        card.body.addStretch(1)
        return card

    def _diagnostics_card(self) -> Card:
        card = Card(theme=self.theme, title="Diagnostics", icon_name="settings")
        caption = QLabel(
            "Logs and settings live in your user profile, not in the project folder:"
        )
        caption.setObjectName("MetricCaption")
        caption.setWordWrap(True)
        card.add_widget(caption)

        self.log_path_label = QLabel("Unavailable")
        self.log_path_label.setObjectName("InfoValue")
        self.log_path_label.setWordWrap(True)
        self.log_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        card.add_widget(self.log_path_label)

        self.open_logs_button = QPushButton("Open log folder")
        self.open_logs_button.clicked.connect(self._open_logs)
        card.add_widget(self.open_logs_button)
        return card

    def _load_static(self) -> None:
        """Fill the values that cannot change while the application runs."""
        info = self.context.monitor.cpu_info
        self.os_grid.set_values(
            {
                "python": f"Python {_python_version()}",
                "qt": _qt_version(),
                "psutil": _psutil_version(),
                "app": f"{APP_DISPLAY_NAME} {APP_VERSION}",
            }
        )
        self.cpu_grid.set_values(
            {
                "name": info.name,
                "physical": info.physical_cores,
                "logical": info.logical_cores,
                "max_frequency": format_frequency(info.max_frequency_mhz),
            }
        )
        try:
            self.log_path_label.setText(str(logs_dir()))
        except OSError:
            self.log_path_label.setText(UNAVAILABLE)

    def _open_logs(self) -> None:
        """Reveal the log directory in the system file manager."""
        try:
            path = ensure_directories()
        except OSError:
            self.statusMessage.emit("Could not create the log directory.")
            return
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        self.statusMessage.emit(
            f"Opened {path}" if opened else f"Log directory: {path}"
        )


def _python_version() -> str:
    import platform

    return f"{platform.python_version()} ({platform.machine()})"


def _qt_version() -> str:
    try:
        import PySide6
        from PySide6.QtCore import qVersion

        return f"Qt {qVersion()} · PySide6 {PySide6.__version__}"
    except Exception:  # noqa: BLE001 - informational only
        return UNAVAILABLE


def _psutil_version() -> str:
    try:
        import psutil

        return psutil.__version__
    except Exception:  # noqa: BLE001 - informational only
        return UNAVAILABLE
