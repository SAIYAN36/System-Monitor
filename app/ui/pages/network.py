"""Network page: throughput, totals, adapters and addresses."""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtWidgets import QLabel

from app.models.snapshot import NetworkInterface
from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage, wrap_layout
from app.ui.widgets.cards import Card, MetricCard
from app.ui.widgets.common import badge, section_title
from app.ui.widgets.graph import LineGraph
from app.ui.widgets.table import DeviceTable
from app.utils.formatting import (
    UNAVAILABLE,
    format_bytes,
    format_link_speed,
    format_rate,
)

_ADAPTER_HEADERS = ("Adapter", "Status", "IPv4", "MAC address", "Link", "Received", "Sent")


class NetworkPage(ScrollPage):
    key = "network"
    title = "Network"
    subtitle = "Live throughput, totals and adapter details."

    def populate(self) -> None:
        self._latest: Dict[str, NetworkInterface] = {}
        self._rows: Dict[str, Dict[str, object]] = {}

        self.add_content(section_title("Throughput"))
        self.download_card = MetricCard(
            theme=self.theme, title="Download", icon_name="network", formatter=format_rate
        )
        self.upload_card = MetricCard(
            theme=self.theme, title="Upload", icon_name="network", formatter=format_rate
        )
        self.received_card = MetricCard(
            theme=self.theme, title="Total received", icon_name="network",
            formatter=format_bytes,
        )
        self.sent_card = MetricCard(
            theme=self.theme, title="Total sent", icon_name="network", formatter=format_bytes
        )
        row = self.make_grid(columns=4, spacing=14)
        for index, card in enumerate(
            (self.download_card, self.upload_card, self.received_card, self.sent_card)
        ):
            row.addWidget(card, 0, index)
        self.add_content(wrap_layout(row))

        self.add_content(section_title("Traffic history"))
        self.graph = LineGraph(theme=self.theme, minimum_height=200)
        self.graph.set_formatter(format_rate)
        self.graph.set_legend_visible(True)
        self.graph.add_series("Download", self.theme.accent)
        self.graph.add_series("Upload", self.theme.warning)
        graph_card = Card(theme=self.theme, title="Network traffic", icon_name="network")
        graph_card.add_widget(self.graph, 1)
        self.stats_label = QLabel("Waiting for data...")
        self.stats_label.setObjectName("MetricCaption")
        graph_card.add_widget(self.stats_label)
        self.add_content(graph_card)

        self.add_content(section_title("Adapters"))
        self.adapters = DeviceTable(
            _ADAPTER_HEADERS,
            theme=self.theme,
            column_stretch=(0, 0, 2, 0, 0, 0, 0),
            label_widths=(180, 0, 130, 0, 0, 0, 0),
        )
        self.adapter_card = Card(theme=self.theme, title="Detected interfaces", icon_name="network")
        self.adapter_card.add_widget(self.adapters)
        self.empty_label = QLabel("No network interfaces detected.")
        self.empty_label.setObjectName("MetricCaption")
        self.adapter_card.add_widget(self.empty_label)
        self.add_content(self.adapter_card)
        self.add_stretch()

        self.ip_badge = badge("IP: unknown")
        self.header_extra.addWidget(self.ip_badge)

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        network = update.snapshot.network

        self.download_card.set_value(
            network.download_rate, color=self.theme.accent, caption="Aggregate of active adapters"
        )
        self.upload_card.set_value(
            network.upload_rate, color=self.theme.warning, caption="Aggregate of active adapters"
        )
        self.received_card.set_value(network.total_recv)
        self.sent_card.set_value(network.total_sent)

        values = update.values("net_download")
        uploads = update.values("net_upload")
        self.graph.set_values({"Download": values, "Upload": uploads})
        if values:
            peak_down = max(values)
            peak_up = max(uploads) if uploads else 0.0
            self.stats_label.setText(
                f"Peak download {format_rate(peak_down)} · Peak upload {format_rate(peak_up)}"
                f" · {len(values)} samples"
            )

        primary = network.primary_ipv4
        self.ip_badge.setText(f"IP: {primary}" if primary else "IP: unavailable")

        self._sync_adapters(network.interfaces)

    # ---------------------------------------------------------------- internals
    def _sync_adapters(self, interfaces) -> None:
        self._latest = {nic.name: nic for nic in interfaces}
        keys = list(self._latest)
        self.adapters.sync(keys, self._build_row)
        self.empty_label.setVisible(not keys)

        for key, nic in self._latest.items():
            widgets = self._rows.get(key)
            if widgets is None:
                continue
            widgets["status"].setText(_status_text(nic))  # type: ignore[union-attr]
            widgets["status"].setStyleSheet(  # type: ignore[union-attr]
                f"color: {_status_color(self.theme, nic)}; font-weight: 600;"
            )
            widgets["ipv4"].setText(nic.ipv4 or UNAVAILABLE)  # type: ignore[union-attr]
            widgets["mac"].setText(nic.mac or UNAVAILABLE)  # type: ignore[union-attr]
            widgets["link"].setText(format_link_speed(nic.speed_mbps))  # type: ignore[union-attr]
            widgets["received"].setText(format_bytes(nic.bytes_recv))  # type: ignore[union-attr]
            widgets["sent"].setText(format_bytes(nic.bytes_sent))  # type: ignore[union-attr]

    def _build_row(self, key: object) -> List:
        nic = self._latest.get(str(key), NetworkInterface(name=str(key)))
        name = DeviceTable.cell(nic.name, bold=True)
        tooltip = [f"MTU: {nic.mtu}" if nic.mtu else "", nic.ipv6 or ""]
        name.setToolTip("\n".join(part for part in tooltip if part) or nic.name)

        self._rows[str(key)] = {
            "status": DeviceTable.cell(bold=True),
            "ipv4": DeviceTable.cell(selectable=True),
            "mac": DeviceTable.cell(selectable=True),
            "link": DeviceTable.cell(),
            "received": DeviceTable.cell(selectable=True),
            "sent": DeviceTable.cell(selectable=True),
        }
        return [
            name,
            self._rows[str(key)]["status"],
            self._rows[str(key)]["ipv4"],
            self._rows[str(key)]["mac"],
            self._rows[str(key)]["link"],
            self._rows[str(key)]["received"],
            self._rows[str(key)]["sent"],
        ]


def _status_text(nic: NetworkInterface) -> str:
    if nic.is_loopback:
        return "Loopback"
    return "Up" if nic.is_up else "Down"


def _status_color(theme, nic: NetworkInterface) -> str:
    if nic.is_loopback:
        return theme.muted
    return theme.success if nic.is_up else theme.muted
