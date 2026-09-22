"""Settings page: every user-configurable option in one place."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.config import (
    MAX_HISTORY_SAMPLES,
    MAX_REFRESH_MS,
    MAX_TEMPERATURE_INTERVAL_S,
    MIN_HISTORY_SAMPLES,
    MIN_REFRESH_MS,
    MIN_TEMPERATURE_INTERVAL_S,
)
from app.services import autostart
from app.services.settings import DASHBOARD_CARDS, DASHBOARD_GRAPHS, Settings
from app.ui.pages.base import ScrollPage
from app.ui.widgets.cards import Card
from app.ui.widgets.common import badge, section_title


class SliderField(QWidget):
    """A labelled slider with a live value read-out."""

    changed = Signal()

    def __init__(
        self,
        label: str,
        minimum: int,
        maximum: int,
        step: int,
        value: int,
        formatter: Callable[[int], str],
        parent: Optional[QWidget] = None,
        *,
        note: str = "",
    ) -> None:
        super().__init__(parent)
        self._formatter = formatter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        top = QHBoxLayout()
        self.label = QLabel(label)
        top.addWidget(self.label)
        top.addStretch(1)
        self.value_label = QLabel(formatter(value))
        self.value_label.setObjectName("InfoValue")
        top.addWidget(self.value_label)
        layout.addLayout(top)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setSingleStep(step)
        self.slider.setPageStep(step * 4)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self.slider)

        if note:
            caption = QLabel(note)
            caption.setObjectName("MetricCaption")
            caption.setWordWrap(True)
            layout.addWidget(caption)

    def _on_changed(self, value: int) -> None:
        self.value_label.setText(self._formatter(value))
        self.changed.emit()

    def value(self) -> int:
        raw = self.slider.value()
        step = self.slider.singleStep()
        # Snap to the step so the stored value is always a round figure.
        return int(round(raw / step) * step)

    def set_value(self, value: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(int(value))
        self.slider.blockSignals(False)
        self.value_label.setText(self._formatter(int(value)))

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt naming
        super().setEnabled(enabled)
        self.slider.setEnabled(enabled)


class SettingsPage(ScrollPage):
    key = "settings"
    title = "Settings"
    subtitle = "Changes are applied when you press Save."

    def populate(self) -> None:
        self._loading = True

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save)
        self.header_extra.addWidget(self.save_button)

        self.dirty_badge = badge("No changes")
        self.header_extra.addWidget(self.dirty_badge)

        self._build_monitoring_card()
        self._build_temperature_card()
        self._build_startup_card()
        self._build_appearance_card()
        self._build_dashboard_card()

        self.add_content(section_title("Storage"))
        storage_card = Card(theme=self.theme, title="Where settings are stored", icon_name="info")
        self.storage_label = QLabel(str(self.context.settings_manager.path))
        self.storage_label.setObjectName("InfoValue")
        self.storage_label.setWordWrap(True)
        self.storage_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        storage_card.add_widget(self.storage_label)
        self.add_content(storage_card)

        self.add_content(section_title("Actions"))
        actions_card = Card(theme=self.theme, title="Reset", icon_name="settings")
        reset_row = QHBoxLayout()
        self.reset_button = QPushButton("Restore defaults")
        self.reset_button.setToolTip("Reset every option and save immediately")
        self.reset_button.clicked.connect(self._reset)
        reset_row.addWidget(self.reset_button)
        reset_row.addStretch(1)
        actions_card.add_layout(reset_row)
        self.action_status = QLabel("")
        self.action_status.setObjectName("MetricCaption")
        self.action_status.setWordWrap(True)
        actions_card.add_widget(self.action_status)
        self.add_content(actions_card)

        self.add_stretch()
        self.load_from_settings()
        self._loading = False

    # ------------------------------------------------------------- construction
    def _build_monitoring_card(self) -> None:
        card = Card(theme=self.theme, title="Monitoring", icon_name="speed")

        self.refresh_field = SliderField(
            "Refresh interval",
            MIN_REFRESH_MS,
            MAX_REFRESH_MS,
            250,
            self.context.settings.refresh_interval_ms,
            lambda value: f"{value / 1000:.2f} s",
            note="How often CPU, memory, disk and network are sampled. "
            "500 ms is the practical minimum.",
        )
        self.refresh_field.changed.connect(self._mark_dirty)
        card.add_widget(self.refresh_field)

        self.history_field = SliderField(
            "Graph history length",
            MIN_HISTORY_SAMPLES,
            MAX_HISTORY_SAMPLES,
            10,
            self.context.settings.history_samples,
            lambda value: f"{value} samples",
            note="Samples kept in memory for the live graphs (oldest are dropped).",
        )
        self.history_field.changed.connect(self._mark_dirty)
        card.add_widget(self.history_field)

        self.add_content(card)

    def _build_temperature_card(self) -> None:
        card = Card(theme=self.theme, title="CPU temperature", icon_name="temperature")

        self.temperature_check = QCheckBox("Read the CPU temperature")
        self.temperature_check.toggled.connect(self._on_temperature_toggled)
        card.add_widget(self.temperature_check)

        self.temperature_field = SliderField(
            "Temperature refresh interval",
            MIN_TEMPERATURE_INTERVAL_S,
            MAX_TEMPERATURE_INTERVAL_S,
            5,
            self.context.settings.temperature_interval_s,
            lambda value: f"{value} s",
            note="Temperature is read on a slower cadence than the other metrics "
            "because sensors are expensive to query.",
        )
        self.temperature_field.changed.connect(self._mark_dirty)
        card.add_widget(self.temperature_field)

        self.temperature_status = QLabel("")
        self.temperature_status.setObjectName("MetricCaption")
        self.temperature_status.setWordWrap(True)
        card.add_widget(self.temperature_status)
        self.add_content(card)

    def _build_startup_card(self) -> None:
        card = Card(theme=self.theme, title="Startup", icon_name="window")

        self.minimized_check = QCheckBox("Start minimized")
        self.minimized_check.setToolTip(
            "Open without showing the window, leaving the icon in the notification area."
        )
        self.minimized_check.toggled.connect(self._mark_dirty)
        card.add_widget(self.minimized_check)

        self.autostart_check = QCheckBox("Start with Windows")
        self.autostart_check.toggled.connect(self._mark_dirty)
        if not autostart.is_supported():
            self.autostart_check.setEnabled(False)
        card.add_widget(self.autostart_check)

        self.autostart_note = QLabel("")
        self.autostart_note.setObjectName("MetricCaption")
        self.autostart_note.setWordWrap(True)
        card.add_widget(self.autostart_note)

        self.tray_check = QCheckBox("Keep running in the notification area when closed")
        self.tray_check.toggled.connect(self._mark_dirty)
        card.add_widget(self.tray_check)
        self.tray_note = QLabel("")
        self.tray_note.setObjectName("MetricCaption")
        self.tray_note.setWordWrap(True)
        card.add_widget(self.tray_note)
        self.add_content(card)

    def _build_appearance_card(self) -> None:
        card = Card(theme=self.theme, title="Appearance & safety", icon_name="settings")

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.setFixedWidth(150)
        self.theme_combo.currentIndexChanged.connect(self._mark_dirty)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        card.add_layout(theme_row)

        self.confirm_check = QCheckBox("Ask before ending a process")
        self.confirm_check.setToolTip(
            "Strongly recommended: terminating a process can lose unsaved work."
        )
        self.confirm_check.toggled.connect(self._mark_dirty)
        card.add_widget(self.confirm_check)
        self.add_content(card)

    def _build_dashboard_card(self) -> None:
        card = Card(theme=self.theme, title="Dashboard content", icon_name="dashboard")

        groups = QVBoxLayout()
        groups.setSpacing(8)

        cards_row = QHBoxLayout()
        cards_row.addWidget(QLabel("Metric cards"))
        cards_column = QGridLayout()
        cards_column.setHorizontalSpacing(20)
        cards_column.setVerticalSpacing(6)
        self.card_checks: Dict[str, QCheckBox] = {}
        for index, (key, label) in enumerate(DASHBOARD_CARDS.items()):
            check = QCheckBox(label)
            check.toggled.connect(self._mark_dirty)
            self.card_checks[key] = check
            cards_column.addWidget(check, index // 2, index % 2)
        cards_row.addLayout(cards_column)
        cards_row.addStretch(1)
        groups.addLayout(cards_row)

        graphs_row = QHBoxLayout()
        graphs_row.addWidget(QLabel("Graphs"))
        graphs_column = QGridLayout()
        graphs_column.setHorizontalSpacing(20)
        graphs_column.setVerticalSpacing(6)
        self.graph_checks: Dict[str, QCheckBox] = {}
        for index, (key, label) in enumerate(DASHBOARD_GRAPHS.items()):
            check = QCheckBox(label)
            check.toggled.connect(self._mark_dirty)
            self.graph_checks[key] = check
            graphs_column.addWidget(check, index // 2, index % 2)
        graphs_row.addLayout(graphs_column)
        graphs_row.addStretch(1)
        groups.addLayout(graphs_row)

        card.add_layout(groups)
        self.add_content(card)

    # ------------------------------------------------------------- load/save
    def load_from_settings(self) -> None:
        """Copy the current settings into the controls."""
        settings = self.context.settings
        self._loading = True

        self.refresh_field.set_value(settings.refresh_interval_ms)
        self.history_field.set_value(settings.history_samples)
        self.temperature_check.setChecked(settings.temperature_enabled)
        self.temperature_field.set_value(settings.temperature_interval_s)
        self.temperature_field.setEnabled(settings.temperature_enabled)
        self.minimized_check.setChecked(settings.start_minimized)
        self.autostart_check.setChecked(_autostart_state(settings))
        self.tray_check.setChecked(settings.minimize_to_tray)
        self.confirm_check.setChecked(settings.confirm_terminate)

        index = self.theme_combo.findData(settings.theme)
        self.theme_combo.setCurrentIndex(max(0, index))

        for key, check in self.card_checks.items():
            check.setChecked(settings.dashboard_cards.get(key, True))
        for key, check in self.graph_checks.items():
            check.setChecked(settings.dashboard_graphs.get(key, True))

        self._update_autostart_note()
        self._update_tray_note()
        self._loading = False
        self._set_dirty(False)

    def _collect(self) -> Settings:
        """Read the controls back into the settings object."""
        settings = self.context.settings
        settings.refresh_interval_ms = self.refresh_field.value()
        settings.history_samples = self.history_field.value()
        settings.temperature_enabled = self.temperature_check.isChecked()
        settings.temperature_interval_s = self.temperature_field.value()
        settings.start_minimized = self.minimized_check.isChecked()
        settings.start_with_windows = self.autostart_check.isChecked()
        settings.minimize_to_tray = self.tray_check.isChecked()
        settings.confirm_terminate = self.confirm_check.isChecked()
        settings.theme = self.theme_combo.currentData() or settings.theme
        settings.dashboard_cards = {
            key: check.isChecked() for key, check in self.card_checks.items()
        }
        settings.dashboard_graphs = {
            key: check.isChecked() for key, check in self.graph_checks.items()
        }
        return settings.normalize()

    def _save(self) -> None:
        previous_autostart = _autostart_state(self.context.settings)
        settings = self._collect()

        if settings.start_with_windows != previous_autostart:
            if not self._apply_autostart(settings.start_with_windows):
                # Put the checkbox back so the UI reflects the real state.
                settings.start_with_windows = previous_autostart
                self._loading = True
                self.autostart_check.setChecked(previous_autostart)
                self._loading = False

        self.settingsChanged.emit(settings)
        self._update_autostart_note()
        self._set_dirty(False)
        self.action_status.setText("Settings saved and applied.")

    def _reset(self) -> None:
        current = self.context.settings
        fresh = Settings().normalize()
        # Keep the window geometry: it is not editable from this page.
        fresh.window_geometry = current.window_geometry
        if current.start_with_windows:
            self._apply_autostart(False)
        # Copy into the existing object so every page keeps its reference.
        for name, value in fresh.to_dict().items():
            setattr(current, name, value)
        self.context.settings_manager.save(current)
        self.load_from_settings()
        self.settingsChanged.emit(current)
        self.action_status.setText("All options were restored to their defaults.")

    def _apply_autostart(self, enabled: bool) -> bool:
        try:
            autostart.set_enabled(enabled)
            return True
        except autostart.AutostartError as exc:
            QMessageBox.warning(self, "Startup entry", str(exc))
            return False

    # ---------------------------------------------------------------- helpers
    def _on_temperature_toggled(self, checked: bool) -> None:
        self.temperature_field.setEnabled(checked)
        self._mark_dirty()

    def _mark_dirty(self, *args) -> None:
        if self._loading:
            return
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        self.save_button.setEnabled(dirty)
        self.dirty_badge.setText("Unsaved changes" if dirty else "No changes")
        if dirty:
            self.action_status.setText("")

    def _update_autostart_note(self) -> None:
        if not autostart.is_supported():
            self.autostart_note.setText(
                "Starting with the operating system is only supported on Windows."
            )
            return
        entry = autostart.current_entry()
        self.autostart_note.setText(
            f"Registered command: {entry}"
            if entry
            else "No startup entry is registered."
        )

    def _update_tray_note(self) -> None:
        if self.context.tray_available:
            self.tray_note.setText(
                "Closing the window keeps monitoring running in the notification area."
            )
            self.tray_check.setEnabled(True)
        else:
            self.tray_check.setEnabled(False)
            self.tray_note.setText(
                "No notification area is available, so the window closes normally."
            )

    def on_activated(self) -> None:
        # The provider probe touches WMI, so defer it until the page has painted.
        QTimer.singleShot(0, self._refresh_temperature_status)

    def apply_settings(self, settings) -> None:
        # Something else may have changed the settings (the theme toggle, for
        # example), so mirror the current values back into the controls.
        self.load_from_settings()
        QTimer.singleShot(0, self._refresh_temperature_status)

    def _refresh_temperature_status(self) -> None:
        sensors = self.context.monitor.sensors
        if not sensors.enabled:
            self.temperature_status.setText("Temperature reading is turned off.")
            return
        providers = sensors.available_providers()
        value = sensors.read()
        if sensors.provider_name and value is not None:
            self.temperature_status.setText(
                f"Reading {value:.1f} °C via {sensors.provider_name}."
            )
        elif providers:
            self.temperature_status.setText(
                "Usable sources: " + ", ".join(providers) + ". Waiting for a reading..."
            )
        else:
            reason = sensors.last_error or "no supported sensor"
            self.temperature_status.setText(
                f"This system does not expose a CPU temperature ({reason}). "
                "A tool such as LibreHardwareMonitor can provide one."
            )


def _autostart_state(settings: Settings) -> bool:
    """Whether autostart is actually registered (falls back to the setting)."""
    if not autostart.is_supported():
        return False
    return autostart.is_enabled()
