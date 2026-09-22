"""Small shared building blocks used across the pages."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QWidget

from app.ui.theme import Theme, usage_color


class UsageBar(QProgressBar):
    """Thin horizontal bar for a percentage value."""

    def __init__(self, parent: Optional[QWidget] = None, *, theme: Optional[Theme] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setTextVisible(False)
        # Ten steps per percent keeps the bar from appearing chunky.
        self.setRange(0, 1000)
        self.setValue(0)

    def set_usage(self, percent: Optional[float], color: Optional[str] = None) -> None:
        if percent is None:
            self.setValue(0)
            return
        self.setValue(int(max(0.0, min(100.0, percent)) * 10))
        if self._theme is not None:
            tint = color or usage_color(self._theme, percent)
            self.setStyleSheet(
                f"QProgressBar {{ background: {self._theme.border}; border: none;"
                f" border-radius: 4px; }}"
                f"QProgressBar::chunk {{ background: {tint}; border-radius: 4px; }}"
            )

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.set_usage(self.value() / 10.0)


def section_title(text: str) -> QLabel:
    """A muted, uppercase-style section heading."""
    label = QLabel(text.upper())
    label.setObjectName("SectionTitle")
    return label


def muted_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("InfoLabel")
    return label


def value_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("InfoValue")
    return label


def badge(text: str) -> QLabel:
    """A small pill used for inline status hints."""
    label = QLabel(text)
    label.setObjectName("Badge")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label
