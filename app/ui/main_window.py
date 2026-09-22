"""The application window: sidebar navigation, page stack, tray and status bar."""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Dict, Optional

from PySide6.QtCore import QByteArray, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QWidget,
)

from app.config import APP_DISPLAY_NAME, APP_VERSION
from app.monitoring.collector import SystemMonitor
from app.services.history import MetricHistory, MetricsUpdate
from app.services.monitor_service import MonitorWorker
from app.services.settings import Settings, SettingsManager
from app.ui.context import AppContext
from app.ui.icons import app_icon_pixmap
from app.ui.pages import PAGE_DEFINITIONS
from app.ui.theme import apply_theme, get_theme
from app.ui.widgets.sidebar import Sidebar
from app.utils.formatting import format_duration

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Owns the monitoring thread, the tray icon and every page."""

    def __init__(
        self,
        settings_manager: SettingsManager,
        *,
        start_minimized: bool = False,
    ) -> None:
        super().__init__()
        self.settings_manager = settings_manager
        self.settings: Settings = settings_manager.settings
        self.theme = get_theme(self.settings.theme)
        # The pages mutate the very same Settings object, so the applied theme
        # has to be remembered separately to detect a change.
        self._applied_theme: str = self.settings.theme
        self._quitting = False
        self._tray_notified = False
        self._last_update: Optional[MetricsUpdate] = None
        self.pages: Dict[str, QWidget] = {}
        self.current_key = ""

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(1060, 680)

        # Built before the pages so the Settings page knows whether a tray
        # icon exists.
        self.tray = self._create_tray()

        self.history = MetricHistory(self.settings.history_samples)
        self.monitor = SystemMonitor(
            temperature_enabled=self.settings.temperature_enabled,
            temperature_interval_s=self.settings.temperature_interval_s,
        )
        self.worker = MonitorWorker(
            self.monitor,
            self.history,
            self.settings.refresh_interval_ms,
        )
        self.context = AppContext(
            monitor=self.monitor,
            settings=self.settings,
            settings_manager=self.settings_manager,
            history=self.history,
            theme=self.theme,
            worker=self.worker,
            tray_available=self.tray is not None,
        )

        self._build_ui()
        self._connect_worker()
        self._restore_geometry()

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self._tick_clock)
        self.clock_timer.start()
        self._tick_clock()

        self.worker.start()
        self._start_minimized = bool(start_minimized)

    # ------------------------------------------------------------------ UI setup
    def _build_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(
            [(key, label, icon) for key, label, icon, _cls in PAGE_DEFINITIONS],
            theme=self.theme,
        )
        self.sidebar.pageSelected.connect(self.show_page)
        layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self._page_classes = {item[0]: item[3] for item in PAGE_DEFINITIONS}
        self._build_status_bar()
        self.show_page(PAGE_DEFINITIONS[0][0], force=True)

    def _build_status_bar(self) -> None:
        bar = QStatusBar()
        bar.setSizeGripEnabled(False)
        self.setStatusBar(bar)

        self.status_label = QLabel("Starting monitoring...")
        self.status_label.setObjectName("HeaderMeta")
        bar.addWidget(self.status_label, 1)

        self.clock_label = QLabel("")
        self.clock_label.setObjectName("HeaderClock")
        bar.addPermanentWidget(self.clock_label)

        self.theme_button = QPushButton("Switch theme")
        self.theme_button.setToolTip("Toggle between the dark and light themes")
        self.theme_button.clicked.connect(self.toggle_theme)
        bar.addPermanentWidget(self.theme_button)

    def _create_tray(self) -> Optional[QSystemTrayIcon]:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.info("No system tray is available")
            return None

        tray = QSystemTrayIcon(QIcon(app_icon_pixmap(32, self.theme.accent)), self)
        tray.setToolTip(f"{APP_DISPLAY_NAME} {APP_VERSION}")
        menu = QMenu()

        show_action = QAction("Show dashboard", self)
        show_action.triggered.connect(self._restore_window)
        menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _connect_worker(self) -> None:
        self.worker.updateReady.connect(self._on_update)
        self.worker.pollFailed.connect(self._on_poll_failed)

    # ------------------------------------------------------------------- pages
    def ensure_page(self, key: str) -> Optional[QWidget]:
        """Create a page the first time it is opened.

        Building all eight pages up front costs roughly a second of start-up
        time and several megabytes for screens the user may never open, so a
        page is constructed on first visit and then kept.
        """
        existing = self.pages.get(key)
        if existing is not None:
            return existing

        page_class = self._page_classes.get(key)
        if page_class is None:
            logger.warning("Unknown page requested: %s", key)
            return None

        page = page_class(self.context)
        page.settingsChanged.connect(self.apply_settings)
        page.statusMessage.connect(self.show_status)
        self.pages[key] = page
        self.stack.addWidget(page)

        # A page created after start-up still needs the current look and the
        # current settings applied to it.
        page.apply_theme(self.theme)
        page.apply_settings(self.settings)
        return page

    def show_page(self, key: str, *, force: bool = False) -> None:
        """Switch the visible page, telling both pages about the change."""
        if not force and key == self.current_key:
            return

        page = self.ensure_page(key)
        if page is None:
            return

        previous = self.pages.get(self.current_key)
        if previous is not None:
            previous.on_deactivated()

        self.stack.setCurrentWidget(page)
        self.current_key = key
        self.sidebar.set_current(key)

        page.on_activated()
        if self._last_update is not None:
            page.apply_update(self._last_update)

        label = next((item[1] for item in PAGE_DEFINITIONS if item[0] == key), "")
        self.setWindowTitle(f"{APP_DISPLAY_NAME} · {label}" if label else APP_DISPLAY_NAME)

    # ------------------------------------------------------------------ updates
    def _on_update(self, update: MetricsUpdate) -> None:
        """Deliver a reading to the visible page only; hidden ones cost nothing."""
        self._last_update = update
        page = self.pages.get(self.current_key)
        if page is not None:
            page.apply_update(update)

        snapshot = update.snapshot
        memory = snapshot.memory.percent
        status = (
            f"Updated {_dt.datetime.fromtimestamp(snapshot.timestamp).strftime('%H:%M:%S')}"
            f" · every {self.settings.refresh_interval_ms / 1000:g}s"
        )
        if memory is not None:
            status += f" · RAM {memory:.0f}%"
        if snapshot.cpu.percent is not None:
            status += f" · CPU {snapshot.cpu.percent:.0f}%"
        self.status_label.setText(status)

        uptime = snapshot.uptime
        process_count = snapshot.process_count
        footer = []
        if uptime is not None:
            footer.append(f"Uptime {format_duration(uptime)}")
        if process_count is not None:
            footer.append(f"{process_count} processes")
        self.sidebar.set_status("\n".join(footer))

    def _on_poll_failed(self, message: str) -> None:
        self.status_label.setText(f"Monitoring error: {message}")

    def _tick_clock(self) -> None:
        self.clock_label.setText(_dt.datetime.now().strftime("%H:%M:%S"))

    # ---------------------------------------------------------------- settings
    def apply_settings(self, settings: Settings) -> None:
        """Apply and persist a settings change coming from the Settings page."""
        theme_changed = settings.theme != self._applied_theme
        self.settings = settings
        self.context.settings = settings
        self.settings_manager.settings = settings

        if theme_changed:
            self.theme = apply_theme(QApplication.instance(), settings.theme)
            self._applied_theme = settings.theme
            self.context.theme = self.theme
            self.sidebar.set_theme(self.theme)
            for page in self.pages.values():
                page.apply_theme(self.theme)
            if self.tray is not None:
                self.tray.setIcon(QIcon(app_icon_pixmap(32, self.theme.accent)))

        self.worker.set_interval_ms(settings.refresh_interval_ms)
        self.history.set_capacity(settings.history_samples)
        self.monitor.set_temperature_enabled(settings.temperature_enabled)
        self.monitor.set_temperature_interval(settings.temperature_interval_s)

        for page in self.pages.values():
            page.apply_settings(settings)

        self.settings_manager.save(settings)
        self._sync_close_behaviour()
        self.show_status("Settings applied.")

    def toggle_theme(self) -> None:
        """Flip between the dark and light themes and persist the choice."""
        self.settings.theme = "light" if self.settings.theme == "dark" else "dark"
        self.apply_settings(self.settings)
        self.show_status(f"{self.settings.theme.title()} theme applied.")

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)

    # -------------------------------------------------------------------- tray
    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_window()

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _sync_close_behaviour(self) -> None:
        """Keep the application alive when it is meant to live in the tray."""
        keep_alive = self.tray is not None and self.settings.minimize_to_tray
        QApplication.instance().setQuitOnLastWindowClosed(not keep_alive)

    def quit_application(self) -> None:
        """Really exit, regardless of the tray preference."""
        self._quitting = True
        self.close()

    def notify_started_minimized(self) -> None:
        if self.tray is not None and not self._tray_notified:
            self._tray_notified = True
            self.tray.showMessage(
                APP_DISPLAY_NAME,
                "System Monitor is running in the background. "
                "Double-click the icon to open the dashboard.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )

    # --------------------------------------------------------------- lifecycle
    def show_if_allowed(self) -> None:
        """Show the window unless the user asked it to start minimized."""
        wants_hidden = self._start_minimized or self.settings.start_minimized
        if wants_hidden and self.tray is not None:
            self.notify_started_minimized()
            return
        if wants_hidden:
            # Without a tray icon a hidden window would be unreachable.
            logger.warning("Start minimized was requested but no tray is available")
        self.show()
        self._sync_close_behaviour()

    def _restore_geometry(self) -> None:
        stored = self.settings.window_geometry
        if not stored:
            self.resize(1240, 800)
            return
        try:
            self.restoreGeometry(QByteArray.fromBase64(stored.encode("ascii")))
        except (ValueError, TypeError):
            self.resize(1240, 800)

    def _persist_geometry(self) -> None:
        try:
            self.settings.window_geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
            self.settings_manager.save(self.settings)
        except Exception as exc:  # noqa: BLE001 - geometry is a nice-to-have
            logger.debug("Could not store the window geometry: %r", exc)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt naming
        if (
            not self._quitting
            and self.tray is not None
            and self.settings.minimize_to_tray
            and self.isVisible()
        ):
            event.ignore()
            self.hide()
            self.notify_started_minimized()
            return

        self.shutdown()
        event.accept()

    def shutdown(self) -> None:
        """Stop every background thread and persist the window geometry."""
        logger.info("Shutting down")
        self.clock_timer.stop()
        self.worker.request_stop()
        if not self.worker.wait(3000):
            logger.warning("The monitoring thread did not stop in time")
        self.monitor.sensors.stop()
        self._persist_geometry()
        if self.tray is not None:
            self.tray.hide()
