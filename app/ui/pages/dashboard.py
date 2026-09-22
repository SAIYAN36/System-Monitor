"""The overview dashboard: headline metrics plus live graphs."""

from __future__ import annotations

import datetime as _dt
from typing import Dict, Optional

from PySide6.QtWidgets import QGridLayout, QWidget

from app.services.history import MetricsUpdate
from app.ui.context import AppContext
from app.ui.pages.base import ScrollPage
from app.ui.theme import Theme, usage_color
from app.ui.widgets.cards import Card, MetricCard
from app.ui.widgets.common import section_title
from app.ui.widgets.graph import LineGraph
from app.utils.formatting import (
    UNAVAILABLE,
    format_bytes,
    format_clock,
    format_count,
    format_duration,
    format_frequency,
    format_percent,
    format_rate,
    format_temperature,
    format_timestamp,
)

#: (key, title, icon) for the metric cards, in display order.
CARD_DEFINITIONS = (
    ("cpu", "CPU usage", "cpu"),
    ("memory", "RAM usage", "memory"),
    ("disk", "Disk usage", "disk"),
    ("network", "Network speed", "network"),
    ("uptime", "System uptime", "clock"),
    ("temperature", "CPU temperature", "temperature"),
    ("processes", "Running processes", "processes"),
    ("clock", "Current time", "clock"),
)

#: (key, title, icon) for the history graphs.
GRAPH_DEFINITIONS = (
    ("cpu", "CPU usage", "cpu"),
    ("memory", "Memory usage", "memory"),
    ("network", "Network traffic", "network"),
    ("disk", "Disk activity", "disk"),
)


class DashboardPage(ScrollPage):
    """At-a-glance view of the whole machine."""

    key = "dashboard"
    title = "Dashboard"
    subtitle = "Live system overview, refreshed automatically."

    def populate(self) -> None:
        self.cards: Dict[str, MetricCard] = {}
        self.graphs: Dict[str, LineGraph] = {}

        self.add_content(section_title("Live metrics"))
        cards_grid = self.make_grid(columns=4, spacing=14)
        for index, (key, label, icon) in enumerate(CARD_DEFINITIONS):
            card = MetricCard(
                theme=self.theme,
                title=label,
                icon_name=icon,
                formatter=format_percent,
                show_bar=key in ("cpu", "memory", "disk"),
            )
            self.cards[key] = card
            cards_grid.addWidget(card, index // 4, index % 4)
        self.add_content(_wrap(cards_grid))

        self.add_content(section_title("History"))
        graphs_grid = self.make_grid(columns=2, spacing=14)
        for index, (key, label, icon) in enumerate(GRAPH_DEFINITIONS):
            graph = LineGraph(theme=self.theme, minimum_height=156)
            self.graphs[key] = graph
            graphs_grid.addWidget(
                self._graph_card(label, icon, graph), index // 2, index % 2
            )
        self.add_content(_wrap(graphs_grid))

        # Percentage graphs keep a fixed 0-100 axis; the throughput graphs scale
        # themselves to whatever peak they have seen.
        self.graphs["cpu"].set_fixed_range(0.0, 100.0)
        self.graphs["cpu"].add_series("CPU", self.theme.accent)
        self.graphs["memory"].set_fixed_range(0.0, 100.0)
        self.graphs["memory"].add_series("Memory", self.theme.purple)
        self.graphs["network"].set_formatter(format_rate)
        self.graphs["network"].set_legend_visible(True)
        self.graphs["network"].add_series("Download", self.theme.accent)
        self.graphs["network"].add_series("Upload", self.theme.warning)
        self.graphs["disk"].set_formatter(format_rate)
        self.graphs["disk"].set_legend_visible(True)
        self.graphs["disk"].add_series("Read", self.theme.success)
        self.graphs["disk"].add_series("Write", self.theme.danger)

        self.add_stretch()
        self._apply_visibility()

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        self._update_cards(update)
        self._update_graphs(update)

    def apply_settings(self, settings) -> None:
        self._apply_visibility()

    # ---------------------------------------------------------------- internals
    def _update_cards(self, update: MetricsUpdate) -> None:
        snapshot = update.snapshot
        theme = self.theme

        cpu = snapshot.cpu.percent
        self.cards["cpu"].set_value(
            cpu, color=usage_color(theme, cpu), caption=self._cpu_caption(snapshot)
        )

        memory = snapshot.memory.percent
        self.cards["memory"].set_value(
            memory,
            color=usage_color(theme, memory),
            caption=f"{format_bytes(snapshot.memory.used)} of "
            f"{format_bytes(snapshot.memory.total)} in use",
        )

        self._update_disk_card(snapshot)

        self.cards["network"].set_value(
            snapshot.network.download_rate,
            formatter=format_rate,
            color=theme.accent,
            caption=f"Upload {format_rate(snapshot.network.upload_rate)}",
        )

        self.cards["uptime"].set_value(
            snapshot.uptime,
            formatter=format_duration,
            color=theme.text,
            caption=self._boot_caption(snapshot),
        )

        self.cards["temperature"].set_value(
            snapshot.cpu.temperature_c,
            formatter=format_temperature,
            color=_temperature_color(theme, snapshot.cpu.temperature_c),
            caption=self._temperature_caption(snapshot),
        )

        count = snapshot.process_count
        self.cards["processes"].set_value(
            count,
            formatter=format_count,
            color=theme.text,
            caption="Active processes"
            if count is not None
            else "Detailed while the Processes page is open",
        )

        now = _dt.datetime.now()
        self.cards["clock"].set_text(
            format_clock(now), caption=now.strftime("%A, %d %B %Y")
        )

    def _update_disk_card(self, snapshot) -> None:
        partitions = snapshot.disk.partitions
        if not partitions:
            self.cards["disk"].set_value(
                None, caption="No volumes detected", color=self.theme.muted
            )
            return
        total = sum(part.total or 0 for part in partitions)
        used = sum(part.used or 0 for part in partitions)
        percent = (used / total * 100.0) if total else None
        self.cards["disk"].set_value(
            percent,
            color=usage_color(self.theme, percent),
            caption=f"{format_bytes(used)} of {format_bytes(total)} across "
            f"{len(partitions)} volume(s)",
        )

    def _update_graphs(self, update: MetricsUpdate) -> None:
        self.graphs["cpu"].set_series_values("CPU", update.values("cpu"))
        self.graphs["memory"].set_series_values("Memory", update.values("memory"))
        self.graphs["network"].set_values(
            {
                "Download": update.values("net_download"),
                "Upload": update.values("net_upload"),
            }
        )
        self.graphs["disk"].set_values(
            {"Read": update.values("disk_read"), "Write": update.values("disk_write")}
        )

    def _cpu_caption(self, snapshot) -> str:
        info = snapshot.system.cpu if snapshot.system else None
        if info is None:
            return "Processor details unavailable"
        frequency = format_frequency(info.max_frequency_mhz)
        if info.physical_cores and info.logical_cores:
            return (
                f"{info.physical_cores} cores / {info.logical_cores} threads"
                + (f" · {frequency}" if frequency != UNAVAILABLE else "")
            )
        return info.name

    def _boot_caption(self, snapshot) -> str:
        boot = snapshot.system.boot_time if snapshot.system else None
        return f"Booted {format_timestamp(boot)}" if boot else "Boot time unavailable"

    def _temperature_caption(self, snapshot) -> str:
        if snapshot.cpu.temperature_c is not None:
            provider = self.context.monitor.sensors.provider_name
            return f"via {provider}" if provider else "Sensor reading"
        reason = self.context.monitor.sensors.last_error or "no supported sensor"
        return f"Not exposed by this system ({reason})"

    def _graph_card(self, title: str, icon_name: str, graph: LineGraph) -> Card:
        card = Card(theme=self.theme, title=title, icon_name=icon_name)
        card.add_widget(graph, 1)
        return card

    def _apply_visibility(self) -> None:
        settings = self.context.settings
        for key, card in self.cards.items():
            card.setVisible(settings.dashboard_cards.get(key, True))
        for key, graph in self.graphs.items():
            # The graph lives inside a card; hide the card, not just the plot.
            target: QWidget = graph.parentWidget() or graph
            target.setVisible(settings.dashboard_graphs.get(key, True))


def _wrap(layout) -> QWidget:
    """Wrap a layout in a bare widget so it can join the scroll column."""
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def _temperature_color(theme: Theme, value: Optional[float]) -> str:
    if value is None:
        return theme.muted
    if value >= 85:
        return theme.danger
    if value >= 70:
        return theme.warning
    return theme.success
