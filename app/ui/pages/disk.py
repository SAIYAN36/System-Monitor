"""Disk page: volumes, capacity and read/write activity."""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from app.models.snapshot import PartitionInfo
from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage, wrap_layout
from app.ui.theme import usage_color
from app.ui.widgets.cards import Card, MetricCard
from app.ui.widgets.common import UsageBar, section_title
from app.ui.widgets.graph import LineGraph
from app.ui.widgets.table import DeviceTable
from app.utils.formatting import (
    UNAVAILABLE,
    format_bytes,
    format_count,
    format_percent,
    format_rate,
)

_VOLUME_HEADERS = ("Volume", "Usage", "Used / Total", "Free", "Type", "File system")


class DiskPage(ScrollPage):
    key = "disk"
    title = "Disk"
    subtitle = "Volume capacity and read/write activity."

    def populate(self) -> None:
        #: Latest partition details by mount point, used when building a new row.
        self._latest: Dict[str, PartitionInfo] = {}
        #: Mutable cells of each volume row, keyed by mount point.
        self._rows: Dict[str, Dict[str, object]] = {}

        self.add_content(section_title("Activity"))
        self.read_card = MetricCard(
            theme=self.theme, title="Read", icon_name="disk", formatter=format_rate
        )
        self.write_card = MetricCard(
            theme=self.theme, title="Write", icon_name="disk", formatter=format_rate
        )
        self.total_read_card = MetricCard(
            theme=self.theme, title="Total read since boot", icon_name="disk",
            formatter=format_bytes,
        )
        self.total_write_card = MetricCard(
            theme=self.theme, title="Total written since boot", icon_name="disk",
            formatter=format_bytes,
        )
        row = self.make_grid(columns=4, spacing=14)
        for index, card in enumerate(
            (self.read_card, self.write_card, self.total_read_card, self.total_write_card)
        ):
            row.addWidget(card, 0, index)
        self.add_content(wrap_layout(row))

        self.add_content(section_title("Volumes"))
        self.volumes = DeviceTable(
            _VOLUME_HEADERS,
            theme=self.theme,
            column_stretch=(0, 3, 2, 0, 0, 0),
            label_widths=(150, 170, 170, 0, 0, 0),
        )
        self.volume_card = Card(theme=self.theme, title="Detected drives", icon_name="disk")
        self.volume_card.add_widget(self.volumes)
        self.empty_label = QLabel("No volumes detected.")
        self.empty_label.setObjectName("MetricCaption")
        self.volume_card.add_widget(self.empty_label)
        self.add_content(self.volume_card)

        self.add_content(section_title("Activity history"))
        self.graph = LineGraph(theme=self.theme, minimum_height=190)
        self.graph.set_formatter(format_rate)
        self.graph.set_legend_visible(True)
        self.graph.add_series("Read", self.theme.success)
        self.graph.add_series("Write", self.theme.danger)
        graph_card = Card(theme=self.theme, title="Disk activity", icon_name="disk")
        graph_card.add_widget(self.graph, 1)
        self.io_note = QLabel("")
        self.io_note.setObjectName("MetricCaption")
        self.io_note.setWordWrap(True)
        graph_card.add_widget(self.io_note)
        self.add_content(graph_card)
        self.add_stretch()

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        io = update.snapshot.disk.io

        if io is None:
            self.read_card.set_value(None)
            self.write_card.set_value(None)
            self.total_read_card.set_value(None)
            self.total_write_card.set_value(None)
            self.io_note.setText(
                "This system does not expose disk I/O counters, so activity is unavailable."
            )
        else:
            self.read_card.set_value(io.read_rate, color=self.theme.success)
            self.write_card.set_value(io.write_rate, color=self.theme.danger)
            self.total_read_card.set_value(io.read_bytes)
            self.total_write_card.set_value(io.write_bytes)
            if io.read_count is not None and io.write_count is not None:
                self.io_note.setText(
                    f"{format_count(io.read_count)} read and "
                    f"{format_count(io.write_count)} write operations since boot."
                )
            else:
                self.io_note.setText("Cumulative counters since boot.")

        self._sync_volumes(update.snapshot.disk.partitions)
        self.graph.set_values(
            {"Read": update.values("disk_read"), "Write": update.values("disk_write")}
        )

    # ---------------------------------------------------------------- internals
    def _sync_volumes(self, partitions) -> None:
        self._latest = {part.mountpoint or part.device: part for part in partitions}
        keys = list(self._latest)
        self.volumes.sync(keys, self._build_row)
        self.empty_label.setVisible(not keys)

        for key, part in self._latest.items():
            widgets = self._rows.get(key)
            if widgets is None:
                continue
            percent = part.percent
            bar: UsageBar = widgets["bar"]  # type: ignore[assignment]
            bar.set_usage(percent)

            usage: QLabel = widgets["usage"]  # type: ignore[assignment]
            usage.setText(format_percent(percent))
            usage.setStyleSheet(
                f"color: {usage_color(self.theme, percent)}; font-weight: 600;"
            )
            widgets["used"].setText(  # type: ignore[union-attr]
                f"{format_bytes(part.used)} / {format_bytes(part.total)}"
            )
            widgets["free"].setText(format_bytes(part.free))  # type: ignore[union-attr]

    def _build_row(self, key: object) -> List:
        """Create the cells for one volume row."""
        part = self._latest.get(str(key), PartitionInfo(mountpoint=str(key)))
        name = DeviceTable.cell(part.display_name, bold=True)
        name.setToolTip(part.device or part.mountpoint)

        bar = UsageBar(self, theme=self.theme)
        bar.setMinimumWidth(110)
        usage = DeviceTable.cell()
        usage.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._rows[str(key)] = {
            "bar": bar,
            "usage": usage,
            "used": DeviceTable.cell(),
            "free": DeviceTable.cell(),
        }
        return [
            name,
            bar,
            self._rows[str(key)]["used"],
            self._rows[str(key)]["free"],
            DeviceTable.cell(part.drive_type or UNAVAILABLE),
            DeviceTable.cell(part.fstype or UNAVAILABLE),
        ]
