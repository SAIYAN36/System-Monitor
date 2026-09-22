"""Sidebar navigation."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_DISPLAY_NAME, APP_VERSION
from app.ui.icons import make_icon
from app.ui.theme import Theme

NavItem = Tuple[str, str, str]  # (key, label, icon name)


class Sidebar(QFrame):
    """Vertical navigation rail; emits :attr:`pageSelected` with a page key."""

    pageSelected = Signal(str)

    def __init__(
        self,
        items: Sequence[NavItem],
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(214)
        self._theme = theme
        self._buttons: List[Tuple[str, QPushButton]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(4)

        layout.addLayout(self._build_header())
        layout.addSpacing(14)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for key, label, icon_name in items:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(38)
            button.setIconSize(QSize(18, 18))
            button.setProperty("pageKey", key)
            button.clicked.connect(lambda _checked=False, k=key: self.pageSelected.emit(k))
            button.toggled.connect(self._refresh_icons)
            self._group.addButton(button)
            self._buttons.append((key, button))
            layout.addWidget(button)

        layout.addStretch(1)

        self.footer = QLabel("")
        self.footer.setObjectName("SidebarSubtitle")
        self.footer.setWordWrap(True)
        layout.addWidget(self.footer)

        self._refresh_icons()

    # -------------------------------------------------------------------- api
    def set_current(self, key: str) -> None:
        for candidate, button in self._buttons:
            if candidate == key:
                button.setChecked(True)
                self._refresh_icons()
                return

    def current_key(self) -> Optional[str]:
        for key, button in self._buttons:
            if button.isChecked():
                return key
        return None

    def set_status(self, text: str) -> None:
        self.footer.setText(text)

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._refresh_icons()

    # ---------------------------------------------------------------- internal
    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(9)

        self._logo = QLabel()
        self._logo.setFixedSize(30, 30)
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self._logo)

        text_column = QVBoxLayout()
        text_column.setSpacing(0)
        title = QLabel(APP_DISPLAY_NAME)
        title.setObjectName("SidebarTitle")
        subtitle = QLabel(f"v{APP_VERSION}")
        subtitle.setObjectName("SidebarSubtitle")
        text_column.addWidget(title)
        text_column.addWidget(subtitle)
        header.addLayout(text_column)
        header.addStretch(1)
        return header

    def _refresh_icons(self) -> None:
        if self._theme is None:
            return
        self._logo.setPixmap(make_icon("dashboard", self._theme.accent, 24).pixmap(24, 24))
        for _key, button in self._buttons:
            color = self._theme.accent if button.isChecked() else self._theme.muted
            icon_name = _NAV_ICONS.get(button.text(), "info")
            button.setIcon(make_icon(icon_name, color, 18))


# Maps the visible label back to its glyph so icons can be re-tinted on theme
# changes without storing them next to the buttons.
_NAV_ICONS = {
    "Dashboard": "dashboard",
    "CPU": "cpu",
    "Memory": "memory",
    "Disk": "disk",
    "Network": "network",
    "Processes": "processes",
    "System Information": "info",
    "Settings": "settings",
}
