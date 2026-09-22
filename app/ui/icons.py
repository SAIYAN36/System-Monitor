"""Vector icons drawn at runtime with QPainter.

Defining the icons in code avoids shipping (and bundling) image files, and lets
each icon take the colour of the theme it is drawn in. Every glyph is drawn in a
24x24 coordinate space and scaled to the requested size.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Callable, Dict

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from app.config import assets_dir

_GRID = 24.0
_SUPERSAMPLE = 2  # draw at 2x so the icons stay crisp on high-DPI screens

Builder = Callable[[QPainter, QColor], None]
_BUILDERS: Dict[str, Builder] = {}


def _icon(name: str) -> Callable[[Builder], Builder]:
    def register(builder: Builder) -> Builder:
        _BUILDERS[name] = builder
        return builder

    return register


def _pen(color: QColor, width: float = 1.8) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


# --------------------------------------------------------------------- glyphs
@_icon("dashboard")
def _dashboard(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    for x, y in ((3.5, 3.5), (13.0, 3.5), (3.5, 13.0), (13.0, 13.0)):
        painter.drawRoundedRect(QRectF(x, y, 7.5, 7.5), 2.0, 2.0)


@_icon("cpu")
def _cpu(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawRoundedRect(QRectF(5.0, 5.0, 14.0, 14.0), 2.0, 2.0)
    painter.drawRoundedRect(QRectF(9.5, 9.5, 5.0, 5.0), 1.0, 1.0)
    for offset in (8.5, 12.0, 15.5):
        painter.drawLine(QPointF(offset, 2.5), QPointF(offset, 5.0))
        painter.drawLine(QPointF(offset, 19.0), QPointF(offset, 21.5))
        painter.drawLine(QPointF(2.5, offset), QPointF(5.0, offset))
        painter.drawLine(QPointF(19.0, offset), QPointF(21.5, offset))


@_icon("memory")
def _memory(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawRoundedRect(QRectF(2.5, 7.5, 19.0, 10.0), 2.0, 2.0)
    painter.drawLine(QPointF(8.5, 7.5), QPointF(8.5, 17.5))
    painter.drawLine(QPointF(15.5, 7.5), QPointF(15.5, 17.5))
    for offset in (6.0, 12.0, 18.0):
        painter.drawLine(QPointF(offset, 20.0), QPointF(offset, 17.5))


@_icon("disk")
def _disk(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawRoundedRect(QRectF(3.0, 5.5, 18.0, 13.0), 3.0, 3.0)
    painter.drawLine(QPointF(3.0, 13.5), QPointF(21.0, 13.5))
    painter.drawEllipse(QPointF(7.5, 16.5), 1.1, 1.1)


@_icon("network")
def _network(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawEllipse(QPointF(12.0, 4.5), 2.4, 2.4)
    painter.drawEllipse(QPointF(4.5, 18.0), 2.4, 2.4)
    painter.drawEllipse(QPointF(19.5, 18.0), 2.4, 2.4)
    painter.drawLine(QPointF(11.0, 6.6), QPointF(5.2, 15.7))
    painter.drawLine(QPointF(13.0, 6.6), QPointF(18.8, 15.7))
    painter.drawLine(QPointF(6.9, 18.0), QPointF(17.1, 18.0))


@_icon("processes")
def _processes(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    for y, length in ((6.0, 13.0), (12.0, 9.0), (18.0, 11.0)):
        painter.setBrush(color)
        painter.drawEllipse(QPointF(4.2, y), 1.2, 1.2)
        painter.drawLine(QPointF(8.0, y), QPointF(8.0 + length, y))


@_icon("info")
def _info(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawEllipse(QPointF(12.0, 12.0), 8.5, 8.5)
    painter.setBrush(color)
    painter.drawEllipse(QPointF(12.0, 8.3), 1.0, 1.0)
    painter.drawLine(QPointF(12.0, 11.2), QPointF(12.0, 16.6))


@_icon("settings")
def _settings(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.save()
    painter.translate(QPointF(12.0, 12.0))
    for index in range(8):
        painter.save()
        painter.rotate(index * 45.0)
        painter.drawLine(QPointF(0.0, -6.4), QPointF(0.0, -9.6))
        painter.restore()
    painter.drawEllipse(QPointF(0.0, 0.0), 6.4, 6.4)
    painter.drawEllipse(QPointF(0.0, 0.0), 2.4, 2.4)
    painter.restore()


@_icon("temperature")
def _temperature(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawRoundedRect(QRectF(9.4, 3.0, 5.2, 11.5), 2.6, 2.6)
    painter.drawEllipse(QPointF(12.0, 17.2), 3.6, 3.6)
    painter.drawLine(QPointF(12.0, 12.0), QPointF(12.0, 18.0))


@_icon("clock")
def _clock(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawEllipse(QPointF(12.0, 12.0), 8.5, 8.5)
    painter.drawLine(QPointF(12.0, 7.0), QPointF(12.0, 12.0))
    painter.drawLine(QPointF(12.0, 12.0), QPointF(15.6, 13.8))


@_icon("speed")
def _speed(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawArc(QRectF(3.5, 6.0, 17.0, 17.0), 0, 180 * 16)
    painter.drawLine(QPointF(12.0, 14.5), QPointF(16.6, 9.6))
    painter.setBrush(color)
    painter.drawEllipse(QPointF(12.0, 14.5), 1.3, 1.3)


@_icon("window")
def _window(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawRoundedRect(QRectF(3.0, 4.5, 18.0, 15.0), 2.5, 2.5)
    painter.drawLine(QPointF(3.0, 9.0), QPointF(21.0, 9.0))
    painter.setBrush(color)
    painter.drawEllipse(QPointF(6.2, 6.8), 0.9, 0.9)


@_icon("swap")
def _swap(painter: QPainter, color: QColor) -> None:
    painter.setPen(_pen(color))
    painter.drawLine(QPointF(4.0, 8.5), QPointF(19.0, 8.5))
    painter.drawLine(QPointF(15.5, 5.0), QPointF(19.0, 8.5))
    painter.drawLine(QPointF(20.0, 15.5), QPointF(5.0, 15.5))
    painter.drawLine(QPointF(8.5, 12.0), QPointF(5.0, 15.5))


# ----------------------------------------------------------------------- api
def draw_glyph(painter: QPainter, name: str, color: str, rect: QRectF) -> None:
    """Draw a glyph into ``rect`` of an existing painter.

    Used by :func:`make_icon` and by the icon-file generator, so the drawn
    artwork and the packaged icon can never drift apart.
    """
    builder = _BUILDERS.get(name, _BUILDERS["info"])
    side = min(rect.width(), rect.height())
    if side <= 0:
        return
    painter.save()
    painter.translate(rect.topLeft())
    painter.scale(side / _GRID, side / _GRID)
    builder(painter, QColor(color))
    painter.restore()


@lru_cache(maxsize=256)
def make_icon(name: str, color: str, size: int = 18) -> QIcon:
    """Build (and cache) an icon of ``name`` tinted ``color``."""
    pixels = int(size * _SUPERSAMPLE)
    pixmap = QPixmap(pixels, pixels)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    draw_glyph(painter, name, color, QRectF(0.0, 0.0, pixels, pixels))
    painter.end()

    pixmap.setDevicePixelRatio(float(_SUPERSAMPLE))
    return QIcon(pixmap)


def app_icon_pixmap(
    size: int = 256,
    accent: str = "#4c8dff",
    glyph: str = "dashboard",
    *,
    device_pixel_ratio: float = float(_SUPERSAMPLE),
) -> QPixmap:
    """The application badge: a rounded accent tile with the glyph on top.

    ``device_pixel_ratio`` makes the pixmap crisp on high-DPI screens. The icon
    file generator passes ``1.0`` so the bytes it writes have exactly the pixel
    dimensions asked for.
    """
    pixels = max(1, int(round(size * device_pixel_ratio)))
    pixmap = QPixmap(pixels, pixels)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(pixels / float(size), pixels / float(size))

    tile = QPainterPath()
    radius = size * 0.24
    tile.addRoundedRect(QRectF(0.0, 0.0, float(size), float(size)), radius, radius)
    painter.fillPath(tile, QColor(accent))

    inset = size * 0.19
    draw_glyph(
        painter,
        glyph,
        "#ffffff",
        QRectF(inset, inset, size - 2 * inset, size - 2 * inset),
    )
    painter.end()

    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


@lru_cache(maxsize=1)
def application_icon() -> QIcon:
    """The window and taskbar icon.

    Prefers ``assets/icon.ico`` so the running application matches the icon
    embedded in the built executable, and falls back to drawing the badge when
    running from a tree where the asset has not been generated yet.
    """
    path = assets_dir() / "icon.ico"
    try:
        if path.exists():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    except OSError:
        pass
    return QIcon(app_icon_pixmap(256))


def icon_names() -> tuple:
    """All glyph names, mainly useful for tests."""
    return tuple(sorted(_BUILDERS))
