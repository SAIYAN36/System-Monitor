"""A lightweight rolling line graph.

Deliberately not built on QtCharts: a single custom-painted widget with a fixed
number of points redraws in microseconds, has no animation timer, and keeps the
dependency list to PySide6 and psutil.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.theme import Theme

#: Colour cycle used when a caller does not assign colours explicitly.
_PALETTE_KEYS = ("accent", "cyan", "purple", "success", "warning")


class LineGraph(QWidget):
    """Plots one or more equally spaced sample series, oldest on the left."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        y_max: Optional[float] = None,
        auto_scale: bool = True,
        formatter: Optional[Callable[[float], str]] = None,
        fill: bool = True,
        legend: bool = False,
        minimum_height: int = 150,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._y_max = y_max
        self._auto_scale = auto_scale
        self._formatter = formatter or (lambda value: f"{value:,.0f}")
        self._fill = fill
        self._show_legend = legend
        self._series: List[Dict[str, object]] = []
        self._colors_used = 0

        self.setMinimumHeight(minimum_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAutoFillBackground(False)

    # ------------------------------------------------------------------ series
    def add_series(self, name: str, color: Optional[str] = None) -> None:
        """Declare a series so its colour and legend order are stable."""
        if self._series_by_name(name) is not None:
            return
        self._series.append(
            {"name": name, "color": QColor(color or self._next_color()), "values": ()}
        )

    def set_series_values(self, name: str, values: Sequence[float]) -> None:
        """Replace the samples of one series, creating it when unknown."""
        entry = self._series_by_name(name)
        if entry is None:
            self.add_series(name)
            entry = self._series_by_name(name)
        if entry is not None:
            entry["values"] = tuple(float(value) for value in values)
        self.update()

    def set_values(self, mapping: Dict[str, Sequence[float]]) -> None:
        """Replace every series in one repaint (the common case)."""
        for name, values in mapping.items():
            entry = self._series_by_name(name)
            if entry is None:
                self.add_series(name)
                entry = self._series_by_name(name)
            if entry is not None:
                entry["values"] = tuple(float(value) for value in values)
        self.update()

    def clear(self) -> None:
        for entry in self._series:
            entry["values"] = ()
        self.update()

    def series_names(self) -> Tuple[str, ...]:
        return tuple(str(entry["name"]) for entry in self._series)

    # ----------------------------------------------------------------- options
    def set_auto_scale(self, enabled: bool) -> None:
        self._auto_scale = bool(enabled)
        self.update()

    def set_fixed_range(self, minimum: float, maximum: float) -> None:
        """Pin the y axis (e.g. 0-100 for a percentage graph)."""
        self._auto_scale = False
        self._y_max = float(maximum)
        self.update()

    def set_formatter(self, formatter: Callable[[float], str]) -> None:
        self._formatter = formatter
        self.update()

    def set_legend_visible(self, visible: bool) -> None:
        self._show_legend = bool(visible)
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    # ----------------------------------------------------------------- painting
    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        theme = self._theme
        if theme is None:
            painter.end()
            return

        muted = QColor(theme.muted)
        axis_font = QFont(self.font())
        axis_font.setPointSizeF(max(7.0, axis_font.pointSizeF() - 1.5))
        painter.setFont(axis_font)

        label_width = self._label_width(painter)
        legend_height = 18.0 if self._show_legend and len(self._series) > 1 else 0.0
        plot = QRectF(
            label_width,
            legend_height + 4.0,
            max(1.0, self.width() - label_width - 8.0),
            max(1.0, self.height() - legend_height - 12.0),
        )

        top = self._axis_maximum()
        if top <= 0:
            top = 1.0

        self._draw_grid(painter, plot, top, muted, theme)
        if legend_height:
            self._draw_legend(painter, plot)

        series_with_data = [entry for entry in self._series if entry["values"]]
        if not series_with_data:
            painter.setPen(muted)
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "Waiting for data..."
            )
            painter.end()
            return

        painter.setClipRect(plot.adjusted(-1, -1, 1, 1))
        for entry in series_with_data:
            self._draw_series(painter, plot, top, entry)
        painter.setClipping(False)
        painter.end()

    # ---------------------------------------------------------------- internals
    def _series_by_name(self, name: str) -> Optional[Dict[str, object]]:
        for entry in self._series:
            if entry["name"] == name:
                return entry
        return None

    def _next_color(self) -> str:
        theme = self._theme
        if theme is None:
            return "#4c8dff"
        key = _PALETTE_KEYS[self._colors_used % len(_PALETTE_KEYS)]
        self._colors_used += 1
        return theme.color(key)

    def _axis_maximum(self) -> float:
        if not self._auto_scale and self._y_max is not None:
            return float(self._y_max)
        highest = 0.0
        for entry in self._series:
            values = entry["values"]
            if values:
                highest = max(highest, max(values))
        if highest <= 0:
            return 1.0
        return _nice_ceiling(highest)

    def _label_width(self, painter: QPainter) -> float:
        widest = 0.0
        for step in range(5):
            text = self._formatter(self._axis_maximum() * step / 4.0)
            widest = max(widest, painter.fontMetrics().horizontalAdvance(text))
        return widest + 12.0

    def _draw_grid(
        self, painter: QPainter, plot: QRectF, top: float, muted: QColor, theme: Theme
    ) -> None:
        grid_color = QColor(theme.grid)
        painter.setPen(Qt.PenStyle.NoPen)
        for step in range(5):
            ratio = step / 4.0
            y = plot.top() + plot.height() * ratio
            # The baseline gets a slightly stronger line to anchor the plot.
            painter.setPen(QPen(grid_color if step else QColor(theme.border), 1.0))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))

            value = top * (1.0 - ratio)
            painter.setPen(muted)
            text = self._formatter(value)
            painter.drawText(
                QRectF(0.0, y - 9.0, plot.left() - 8.0, 18.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

    def _draw_legend(self, painter: QPainter, plot: QRectF) -> None:
        x = plot.left()
        for entry in self._series:
            color = entry["color"]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x + 4.0, 9.0), 3.4, 3.4)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(self._theme.muted) if self._theme else QColor("#888888"))
            text = str(entry["name"])
            painter.drawText(
                QRectF(x + 12.0, 1.0, 90.0, 16.0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
            x += 14.0 + painter.fontMetrics().horizontalAdvance(text) + 14.0

    def _draw_series(
        self, painter: QPainter, plot: QRectF, top: float, entry: Dict[str, object]
    ) -> None:
        values: Tuple[float, ...] = entry["values"]  # type: ignore[assignment]
        color: QColor = entry["color"]  # type: ignore[assignment]
        count = len(values)

        path = QPainterPath()
        for index, value in enumerate(values):
            x = plot.left() + (
                plot.width() * index / (count - 1) if count > 1 else plot.width()
            )
            ratio = min(1.0, max(0.0, value / top))
            y = plot.bottom() - plot.height() * ratio
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        if self._fill and count > 1:
            area = QPainterPath(path)
            area.lineTo(plot.right(), plot.bottom())
            area.lineTo(plot.left(), plot.bottom())
            area.closeSubpath()
            gradient = QLinearGradient(0.0, plot.top(), 0.0, plot.bottom())
            start = QColor(color)
            start.setAlpha(72 if len(self._series) == 1 else 42)
            end = QColor(color)
            end.setAlpha(0)
            gradient.setColorAt(0.0, start)
            gradient.setColorAt(1.0, end)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawPath(area)

        pen = QPen(color)
        pen.setWidthF(1.8)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        if count:
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(path.currentPosition().x(), path.currentPosition().y()), 2.6, 2.6)


def _nice_ceiling(value: float) -> float:
    """Round a maximum up to a readable 1/2/5 x 10^n step."""
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    magnitude = 10.0**exponent
    fraction = value / magnitude
    for candidate in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0):
        if fraction <= candidate:
            return candidate * magnitude
    return 10.0 * magnitude
