"""Memory detail page: RAM and page-file/swap usage with history."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage
from app.ui.theme import usage_color
from app.ui.widgets.cards import Card, InfoGrid
from app.ui.widgets.common import UsageBar, section_title
from app.ui.widgets.gauge import RingGauge
from app.ui.widgets.graph import LineGraph
from app.utils.formatting import UNAVAILABLE, format_bytes, format_percent

_RAM_ROWS = (
    ("total", "Total physical memory"),
    ("used", "Used"),
    ("available", "Available"),
    ("percent", "Utilisation"),
)

_SWAP_ROWS = (
    ("total", "Total page file"),
    ("used", "Used"),
    ("free", "Free"),
    ("percent", "Utilisation"),
)


class MemoryPage(ScrollPage):
    key = "memory"
    title = "Memory"
    subtitle = "Physical memory and page file usage."

    def populate(self) -> None:
        self.gauge = RingGauge(theme=self.theme, caption="RAM in use")
        gauge_card = Card(theme=self.theme, title="RAM usage", icon_name="memory")
        gauge_card.add_widget(self.gauge, 1)

        self.info = InfoGrid(columns=1, label_width=180)
        self.info.add_rows(_RAM_ROWS)
        info_card = Card(theme=self.theme, title="Physical memory", icon_name="info")
        info_card.add_widget(self.info)
        info_card.body.addStretch(1)
        self.add_row([gauge_card, info_card])

        self.add_content(section_title("Usage history"))
        self.bar = UsageBar(self, theme=self.theme)
        self.graph = LineGraph(theme=self.theme, minimum_height=200)
        self.graph.set_fixed_range(0.0, 100.0)
        self.graph.add_series("Memory", self.theme.purple)
        graph_card = Card(theme=self.theme, title="Memory usage history", icon_name="memory")
        graph_card.add_widget(self.bar)
        graph_card.add_widget(self.graph, 1)
        self.stats_label = QLabel("Waiting for data...")
        self.stats_label.setObjectName("MetricCaption")
        graph_card.add_widget(self.stats_label)
        self.add_content(graph_card)

        self.add_content(section_title("Page file / swap"))
        self.swap_gauge = RingGauge(
            theme=self.theme, caption="Page file in use", diameter=148
        )
        swap_gauge_card = Card(theme=self.theme, title="Page file usage", icon_name="swap")
        swap_gauge_card.add_widget(self.swap_gauge, 1)

        self.swap_info = InfoGrid(columns=1, label_width=150)
        self.swap_info.add_rows(_SWAP_ROWS)
        swap_info_card = Card(theme=self.theme, title="Page file", icon_name="info")
        swap_info_card.add_widget(self.swap_info)
        swap_info_card.body.addStretch(1)
        self.add_row([swap_gauge_card, swap_info_card])

        self.add_stretch()

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        memory = update.snapshot.memory
        percent = memory.percent

        self.gauge.set_value(percent)
        self.gauge.set_detail(f"{format_bytes(memory.used)} / {format_bytes(memory.total)}")
        self.bar.set_usage(percent)

        self.info.set_values(
            {
                "total": format_bytes(memory.total),
                "used": format_bytes(memory.used),
                "available": format_bytes(memory.available),
                "percent": format_percent(percent),
            }
        )
        self.info.set_color("percent", usage_color(self.theme, percent))

        values = update.values("memory")
        self.graph.set_series_values("Memory", values)
        if values:
            self.stats_label.setText(
                f"Current {format_percent(values[-1])} · "
                f"Average {format_percent(sum(values) / len(values))} · "
                f"Peak {format_percent(max(values))} · {len(values)} samples"
            )

        if memory.swap_total:
            self.swap_gauge.set_value(memory.swap_percent)
            self.swap_gauge.set_detail(
                f"{format_bytes(memory.swap_used)} / {format_bytes(memory.swap_total)}"
            )
            self.swap_info.set_values(
                {
                    "total": format_bytes(memory.swap_total),
                    "used": format_bytes(memory.swap_used),
                    "free": format_bytes(memory.swap_free),
                    "percent": format_percent(memory.swap_percent),
                }
            )
            self.swap_info.set_color(
                "percent", usage_color(self.theme, memory.swap_percent)
            )
        else:
            self.swap_gauge.set_value(None)
            self.swap_info.reset()
            self.swap_info.set_value("total", UNAVAILABLE)
            self.swap_info.set_value("percent", "No page file reported")
