"""Base classes for the stacked pages."""

from __future__ import annotations

from typing import Optional, Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.history import MetricsUpdate
from app.ui.context import AppContext
from app.ui.theme import Theme


class Page(QWidget):
    """Common behaviour for every page.

    Pages receive one :class:`MetricsUpdate` per refresh while they are visible
    and nothing at all while they are hidden, which is what keeps the hidden
    pages from costing any CPU.
    """

    key: str = ""
    title: str = "Page"
    subtitle: str = ""

    #: Emitted after the page mutates the settings object it was given.
    settingsChanged = Signal(object)
    #: Emitted with a short message for the window's status bar.
    statusMessage = Signal(str)

    def __init__(self, context: AppContext, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.context = context
        self.theme: Theme = context.theme
        self.build()

    # ------------------------------------------------------------- subclassing
    def build(self) -> None:
        """Create the widgets. Called once from ``__init__``."""

    def populate(self) -> None:
        """Build page content (used by :class:`ScrollPage`)."""

    def apply_update(self, update: MetricsUpdate) -> None:
        """Refresh from a new metrics reading."""

    def on_activated(self) -> None:
        """The page became visible."""

    def on_deactivated(self) -> None:
        """The page was hidden."""

    def apply_settings(self, settings) -> None:
        """React to a settings change."""

    def apply_theme(self, theme: Theme) -> None:
        """Re-tint every child widget that supports theming."""
        self.theme = theme
        for child in self.findChildren(QWidget):
            setter = getattr(child, "set_theme", None)
            if callable(setter):
                setter(theme)


class ScrollPage(Page):
    """A page with a title header and a scrollable content column."""

    def __init__(self, context: AppContext, parent: Optional[QWidget] = None) -> None:
        self.content_layout: QVBoxLayout
        self.header_extra: QHBoxLayout
        super().__init__(context, parent)

    def build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 14)
        outer.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(12)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("PageTitle")
        titles.addWidget(self.title_label)
        self.subtitle_label = QLabel(self.subtitle)
        self.subtitle_label.setObjectName("PageSubtitle")
        self.subtitle_label.setWordWrap(True)
        titles.addWidget(self.subtitle_label)
        header.addLayout(titles)
        header.addStretch(1)

        self.header_extra = QHBoxLayout()
        self.header_extra.setSpacing(8)
        header.addLayout(self.header_extra)
        outer.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("PageScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 10, 6)
        self.content_layout.setSpacing(14)
        self.scroll.setWidget(content)
        outer.addWidget(self.scroll, 1)

        self.populate()

    # ----------------------------------------------------------------- helpers
    def add_content(self, widget: QWidget, stretch: int = 0) -> None:
        self.content_layout.addWidget(widget, stretch)

    def add_row(self, widgets: Sequence[QWidget], stretch: int = 0) -> None:
        """Add several widgets side by side on one content row."""
        row = QHBoxLayout()
        row.setSpacing(14)
        for widget in widgets:
            row.addWidget(widget, 1)
        self.content_layout.addLayout(row, stretch)

    def add_stretch(self) -> None:
        self.content_layout.addStretch(1)

    @staticmethod
    def make_grid(columns: int = 4, spacing: int = 14) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(spacing)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        return grid

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)


def wrap_layout(layout) -> QWidget:
    """Wrap a layout in a bare widget so it can join a content column."""
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def clear_layout(layout) -> None:
    """Remove and delete every widget/item in a layout.

    Used by the pages whose tables are rebuilt whenever the underlying device
    list changes (drives appearing or disappearing, adapters coming up).
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)
            child_layout.deleteLater()
