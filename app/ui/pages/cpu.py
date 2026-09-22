"""CPU detail page: overall load, per-core load, clock speed and history."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage, wrap_layout
from app.ui.theme import usage_color
from app.ui.widgets.cards import Card, InfoGrid
from app.ui.widgets.common import badge, section_title
from app.ui.widgets.gauge import CoreUsageBars, RingGauge
from app.ui.widgets.graph import LineGraph
from app.utils.formatting import (
    UNAVAILABLE,
    format_frequency,
    format_percent,
    format_temperature,
)

_ROWS = (
    ("model", "Processor"),
    ("physical", "Physical cores"),
    ("threads", "Threads"),
    ("frequency", "Current frequency"),
    ("max_frequency", "Maximum frequency"),
    ("architecture", "Architecture"),
    ("temperature", "Temperature"),
    ("load", "Load average (1/5/15 min)"),
)


class CpuPage(ScrollPage):
    key = "cpu"
    title = "CPU"
    subtitle = "Processor load, per-core breakdown and clock speed."

    def populate(self) -> None:
        self.gauge = RingGauge(theme=self.theme, caption="Total utilisation")
        gauge_card = Card(theme=self.theme, title="Overall usage", icon_name="cpu")
        gauge_card.add_widget(self.gauge, 1)

        self.info = InfoGrid(columns=1, label_width=180)
        self.info.add_rows(_ROWS)
        info_card = Card(theme=self.theme, title="Processor", icon_name="info")
        info_card.add_widget(self.info)
        info_card.body.addStretch(1)
        self.add_row([gauge_card, info_card])

        self.add_content(section_title("Per-core utilisation"))
        self.cores = CoreUsageBars(theme=self.theme)
        cores_card = Card(theme=self.theme, title="Cores", icon_name="cpu")
        cores_card.add_widget(self.cores)
        self.add_content(cores_card)

        self.add_content(section_title("History"))
        self.graph = LineGraph(theme=self.theme, minimum_height=210)
        self.graph.set_fixed_range(0.0, 100.0)
        self.graph.add_series("CPU", self.theme.accent)
        graph_card = Card(theme=self.theme, title="CPU usage history", icon_name="cpu")
        graph_card.add_widget(self.graph, 1)
        self.stats_label = QLabel("Waiting for data...")
        self.stats_label.setObjectName("MetricCaption")
        graph_card.add_widget(self.stats_label)
        self.add_content(graph_card)
        self.add_stretch()

        # The sensor badge updates itself once the background probe has run.
        self.sensor_badge = badge("Temperature: probing...")
        self.header_extra.addWidget(self.sensor_badge)

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        snapshot = update.snapshot
        theme = self.theme
        cpu = snapshot.cpu

        self.gauge.set_value(cpu.percent)

        info = self.context.monitor.cpu_info
        self.info.set_values(
            {
                "model": info.name,
                "physical": info.physical_cores if info.physical_cores else None,
                "threads": info.logical_cores if info.logical_cores else len(cpu.per_core) or None,
                "frequency": _frequency_text(cpu.frequency_mhz),
                "max_frequency": _frequency_text(info.max_frequency_mhz),
                "architecture": info.architecture or None,
                "temperature": _temperature_text(cpu.temperature_c),
                "load": _load_text(cpu.load_average),
            }
        )

        cores = cpu.per_core or ()
        self.cores.set_values(cores)
        if cores:
            busiest = max(cores)
            idle = min(cores)
            self.cores.setToolTip(
                f"{len(cores)} logical cores · busiest {busiest:.1f}% · idlest {idle:.1f}%"
            )

        self._update_graph(update)
        self._update_sensor_badge(snapshot)

    def apply_settings(self, settings) -> None:
        pass

    def _update_graph(self, update: MetricsUpdate) -> None:
        values = update.values("cpu")
        self.graph.set_series_values("CPU", values)
        if not values:
            self.stats_label.setText("Waiting for data...")
            return
        average = sum(values) / len(values)
        peak = max(values)
        self.stats_label.setText(
            f"Current {format_percent(values[-1])} · Average {format_percent(average)}"
            f" · Peak {format_percent(peak)} · {len(values)} samples"
        )

    def _update_sensor_badge(self, snapshot) -> None:
        sensors = self.context.monitor.sensors
        if snapshot.cpu.temperature_c is not None:
            provider = sensors.provider_name or "sensor"
            self.sensor_badge.setText(f"{snapshot.cpu.temperature_c:.1f} °C via {provider}")
            return
        if not sensors.enabled:
            self.sensor_badge.setText("Temperature reading disabled")
        elif not sensors.probed:
            self.sensor_badge.setText("Temperature: probing...")
        else:
            self.sensor_badge.setText("Temperature: unavailable")


def _frequency_text(value) -> str:
    text = format_frequency(value)
    return None if text == UNAVAILABLE else text


def _temperature_text(value) -> str:
    text = format_temperature(value)
    return None if text == UNAVAILABLE else text


def _load_text(load) -> str:
    if not load:
        return None
    return " / ".join(f"{value:.2f}" for value in load)
