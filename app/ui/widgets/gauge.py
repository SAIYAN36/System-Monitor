"""Circular gauge and per-core utilisation bars."""

from __future__ import annotations

import math
from typing import Callable, List, Optional, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.theme import Theme, usage_color
from app.utils.formatting import UNAVAILABLE, format_percent


class RingGauge(QWidget):
    """A ring showing a percentage, with the value in the middle."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        caption: str = "",
        formatter: Optional[Callable[[float], str]] = None,
        thickness: float = 12.0,
        diameter: int = 168,
        fixed_color: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._caption = caption
        self._formatter = formatter or format_percent
        self._thickness = thickness
        self._value: Optional[float] = None
        self._detail = ""
        self._fixed_color = fixed_color

        self.setMinimumSize(diameter, diameter)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    # -------------------------------------------------------------------- api
    def set_value(self, value: Optional[float]) -> None:
        self._value = value
        self.update()

    def set_caption(self, caption: str) -> None:
        self._caption = caption
        self.update()

    def set_detail(self, detail: str) -> None:
        """Small line of text shown under the caption."""
        self._detail = detail
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    # --------------------------------------------------------------- painting
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if theme is None:
            painter.end()
            return

        side = min(self.width(), self.height()) - 10.0
        ring = QRectF(
            (self.width() - side) / 2.0,
            (self.height() - side) / 2.0 - 4.0,
            side,
            side,
        )
        ring = ring.adjusted(
            self._thickness, self._thickness, -self._thickness, -self._thickness
        )

        track_pen = QPen(QColor(theme.border), self._thickness)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(ring, 0, 360 * 16)

        percent = self._value
        color = QColor(
            self._fixed_color
            if self._fixed_color
            else usage_color(theme, percent if percent is not None else 0.0)
        )
        if percent is not None and percent > 0:
            value_pen = QPen(color, self._thickness)
            value_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(value_pen)
            # Qt measures angles counter-clockwise from 3 o'clock, so start at
            # the top (90 degrees) and sweep clockwise with a negative span.
            span = -int(min(100.0, max(0.0, percent)) / 100.0 * 360 * 16)
            painter.drawArc(ring, 90 * 16, span)

        value_font = QFont(self.font())
        value_font.setPointSizeF(value_font.pointSizeF() + 9.0)
        value_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(value_font)
        painter.setPen(QColor(theme.text))
        text = self._formatter(percent) if percent is not None else UNAVAILABLE
        painter.drawText(
            QRectF(0.0, ring.center().y() - 30.0, self.width(), 34.0),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

        caption_font = QFont(self.font())
        caption_font.setPointSizeF(max(7.5, caption_font.pointSizeF() - 0.5))
        painter.setFont(caption_font)
        painter.setPen(QColor(theme.muted))
        painter.drawText(
            QRectF(0.0, ring.center().y() + 6.0, self.width(), 18.0),
            Qt.AlignmentFlag.AlignCenter,
            self._caption,
        )
        if self._detail:
            painter.drawText(
                QRectF(0.0, ring.center().y() + 24.0, self.width(), 18.0),
                Qt.AlignmentFlag.AlignCenter,
                self._detail,
            )
        painter.end()


class CoreUsageBars(QWidget):
    """Per-core utilisation drawn as a compact grid of labelled bars."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        cell_width: int = 196,
        row_height: int = 26,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._values: List[float] = []
        self._cell_width = max(120, int(cell_width))
        self._row_height = max(18, int(row_height))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._recompute_height()

    # -------------------------------------------------------------------- api
    def set_values(self, values: Sequence[float]) -> None:
        self._values = [float(value) for value in values]
        self._recompute_height()
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        self._recompute_height()

    # ---------------------------------------------------------------- internal
    def _columns(self) -> int:
        return max(1, self.width() // self._cell_width)

    def _recompute_height(self) -> None:
        count = max(1, len(self._values))
        rows = math.ceil(count / self._columns())
        self.setMinimumHeight(rows * self._row_height + 4)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        theme = self._theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if theme is None or not self._values:
            painter.setPen(QColor(theme.muted) if theme else QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No core data")
            painter.end()
            return

        columns = self._columns()
        rows = math.ceil(len(self._values) / columns)
        cell_height = self.height() / max(1, rows)
        column_width = self.width() / columns

        label_font = QFont(self.font())
        label_font.setPointSizeF(max(7.5, label_font.pointSizeF() - 1.0))
        painter.setFont(label_font)
        metrics = painter.fontMetrics()

        label_width = metrics.horizontalAdvance("Core 00") + 8.0
        value_width = metrics.horizontalAdvance("100.0%") + 8.0

        for index, value in enumerate(self._values):
            row = index // columns
            column = index % columns
            cell_top = row * cell_height
            left = column * column_width

            bar_left = left + label_width
            bar_right = left + column_width - value_width - 10.0
            bar_width = max(20.0, bar_right - bar_left)
            bar_height = 7.0
            bar_top = cell_top + (cell_height - bar_height) / 2.0

            painter.setPen(QColor(theme.muted))
            painter.drawText(
                QRectF(left, cell_top, label_width - 6.0, cell_height),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"Core {index}",
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.border))
            painter.drawRoundedRect(QRectF(bar_left, bar_top, bar_width, bar_height), 3.5, 3.5)

            ratio = min(100.0, max(0.0, value)) / 100.0
            if ratio > 0:
                painter.setBrush(QColor(usage_color(theme, value)))
                painter.drawRoundedRect(
                    QRectF(bar_left, bar_top, max(4.0, bar_width * ratio), bar_height),
                    3.5,
                    3.5,
                )

            painter.setPen(QColor(theme.text))
            painter.drawText(
                QRectF(bar_right + 6.0, cell_top, value_width, cell_height),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{value:.1f}%",
            )
        painter.end()
