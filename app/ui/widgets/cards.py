"""Dashboard cards and key/value grids."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons import make_icon
from app.ui.theme import Theme
from app.ui.widgets.common import UsageBar
from app.utils.formatting import UNAVAILABLE


class Card(QFrame):
    """A rounded surface with an optional titled header."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        title: str = "",
        icon_name: Optional[str] = None,
        subtitle: str = "",
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._theme = theme
        self._icon_name = icon_name

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(10)

        self.header = QHBoxLayout()
        self.header.setSpacing(8)
        self._icon_label: Optional[QLabel] = None
        self._title_label: Optional[QLabel] = None

        if icon_name:
            self._icon_label = QLabel()
            self._icon_label.setObjectName("CardIconChip")
            self._icon_label.setFixedSize(28, 28)
            self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.header.addWidget(self._icon_label)

        if title:
            self._title_label = QLabel(title)
            self._title_label.setObjectName("CardTitle")
            self.header.addWidget(self._title_label)

        self.subtitle_label: Optional[QLabel] = None
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("CardIconChip")
            self.subtitle_label.setObjectName("CardTitle")
            self.header.addWidget(self.subtitle_label)

        self.header.addStretch(1)
        root.addLayout(self.header)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        root.addLayout(self.body, 1)

        self._refresh_icon()

    # -------------------------------------------------------------------- api
    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.body.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0) -> None:
        self.body.addLayout(layout, stretch)

    def set_title(self, text: str) -> None:
        if self._title_label is not None:
            self._title_label.setText(text)

    def set_theme(self, theme: Theme) -> None:
        # Children are re-themed by Page.apply_theme, which walks the whole
        # page once; recursing here as well would apply every theme twice.
        self._theme = theme
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        if self._icon_label is None or self._theme is None or not self._icon_name:
            return
        icon = make_icon(self._icon_name, self._theme.accent, 16)
        self._icon_label.setPixmap(icon.pixmap(16, 16))


class MetricCard(Card):
    """A single headline number with an optional caption and usage bar."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        title: str = "",
        icon_name: str = "cpu",
        formatter: Callable[[object], str] = str,
        caption: str = "",
        show_bar: bool = False,
    ) -> None:
        super().__init__(parent, theme=theme, title=title, icon_name=icon_name)
        self._formatter = formatter
        self._value: Optional[float] = None

        self.value_label = QLabel(UNAVAILABLE)
        self.value_label.setObjectName("MetricValue")
        self.add_widget(self.value_label)

        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("MetricCaption")
        self.caption_label.setWordWrap(True)
        self.add_widget(self.caption_label)

        self.bar: Optional[UsageBar] = None
        if show_bar:
            self.bar = UsageBar(self, theme=theme)
            self.add_widget(self.bar)
        self.body.addStretch(1)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    # -------------------------------------------------------------------- api
    def set_value(
        self,
        value: Optional[float],
        *,
        formatter: Optional[Callable[[object], str]] = None,
        caption: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Update the headline number; ``None`` renders as "Unavailable"."""
        self._value = value
        formatter = formatter or self._formatter
        self.set_text(
            formatter(value) if value is not None else UNAVAILABLE,
            caption=caption,
            color=color,
        )
        if self.bar is not None:
            self.bar.set_usage(value if isinstance(value, (int, float)) else None, color)

    def set_text(
        self,
        text: str,
        *,
        caption: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Set a pre-formatted value (used for non-numeric cards)."""
        self.value_label.setText(text)
        self.value_label.setStyleSheet(f"color: {color};" if color else "")
        if caption is not None:
            self.caption_label.setText(caption)

    @property
    def value(self) -> Optional[float]:
        return self._value


class InfoGrid(QWidget):
    """A grid of label/value pairs with stable rows for cheap updating."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        columns: int = 2,
        label_width: int = 150,
    ) -> None:
        super().__init__(parent)
        self._columns = max(1, int(columns))
        self._label_width = label_width
        self._rows: Dict[str, QLabel] = {}
        self._count = 0
        self._grid = QGridLayout(self)
        self._grid.setHorizontalSpacing(14)
        self._grid.setVerticalSpacing(7)
        self._grid.setContentsMargins(0, 0, 0, 0)
        for column in range(self._columns):
            self._grid.setColumnStretch(column * 2 + 1, 1)
            self._grid.setColumnMinimumWidth(column * 2, self._label_width)

    # -------------------------------------------------------------------- api
    def add_row(self, key: str, label: str) -> None:
        """Add a permanent row (rows are not removed on refresh)."""
        if key in self._rows:
            return
        index = self._count
        self._count += 1
        row = index // self._columns
        column = index % self._columns

        name = QLabel(label)
        name.setObjectName("InfoLabel")
        name.setWordWrap(True)
        value = QLabel(UNAVAILABLE)
        value.setObjectName("InfoValue")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value.setWordWrap(True)

        self._grid.addWidget(name, row, column * 2)
        self._grid.addWidget(value, row, column * 2 + 1)
        self._rows[key] = value

    def add_rows(self, pairs: Sequence[Tuple[str, str]]) -> None:
        for key, label in pairs:
            self.add_row(key, label)

    def set_value(self, key: str, text: object) -> None:
        label = self._rows.get(key)
        if label is None:
            return
        label.setText(UNAVAILABLE if text is None else str(text))

    def set_values(self, values: Dict[str, object]) -> None:
        for key, value in values.items():
            self.set_value(key, value)

    def set_color(self, key: str, color: Optional[str]) -> None:
        """Tint one value (used to signal healthy/warning/critical figures)."""
        label = self._rows.get(key)
        if label is not None:
            label.setStyleSheet(f"color: {color};" if color else "")

    def reset(self) -> None:
        """Show "Unavailable" for every row."""
        for label in self._rows.values():
            label.setText(UNAVAILABLE)

    def keys(self) -> List[str]:
        return list(self._rows)
