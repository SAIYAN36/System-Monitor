"""A small rebuildable grid used for the drive and adapter tables.

Drives and network adapters come and go while the application runs. Rows are
therefore created and destroyed as the device set changes, but existing rows are
updated in place so the table does not flicker on every refresh.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from app.ui.theme import Theme

CellFactory = Callable[[object], Sequence[QWidget]]


class DeviceTable(QWidget):
    """Header row plus one row per device, keyed by a stable identifier."""

    def __init__(
        self,
        headers: Sequence[str],
        parent: Optional[QWidget] = None,
        *,
        theme: Optional[Theme] = None,
        column_stretch: Optional[Sequence[int]] = None,
        label_widths: Optional[Sequence[int]] = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._headers = list(headers)
        self._keys: List[object] = []
        self._widgets: Dict[object, List[QWidget]] = {}
        self._header_labels: List[QLabel] = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(9)

        for column, text in enumerate(self._headers):
            label = QLabel(text.upper())
            label.setObjectName("SectionTitle")
            self._header_labels.append(label)
            self.grid.addWidget(label, 0, column)
            if label_widths and column < len(label_widths):
                self.grid.setColumnMinimumWidth(column, label_widths[column])
        if column_stretch:
            for column, stretch in enumerate(column_stretch):
                self.grid.setColumnStretch(column, stretch)

    # -------------------------------------------------------------------- api
    def sync(self, keys: Sequence[object], cell_factory: CellFactory) -> None:
        """Ensure exactly one row per key, creating cells for new devices."""
        keys = list(keys)
        if keys == self._keys:
            # Same devices as last time; the cells are updated in place.
            return

        for key in [item for item in self._keys if item not in keys]:
            for widget in self._widgets.pop(key, []):
                widget.setParent(None)
                widget.deleteLater()

        self._keys = keys
        for row, key in enumerate(keys):
            widgets = self._widgets.get(key)
            if widgets is None:
                widgets = list(cell_factory(key))
                self._widgets[key] = widgets
            for column, widget in enumerate(widgets):
                self.grid.addWidget(widget, row + 1, column)

    def row_widgets(self, key: object) -> List[QWidget]:
        """The cell widgets of one row, for updating their contents."""
        return self._widgets.get(key, [])

    def keys(self) -> List[object]:
        return list(self._keys)

    def is_empty(self) -> bool:
        return not self._keys

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def cell(text: str = "", *, bold: bool = False, selectable: bool = False) -> QLabel:
        """Create a table cell label with consistent styling."""
        label = QLabel(text)
        label.setObjectName("InfoValue" if bold else "InfoLabel")
        label.setWordWrap(False)
        if selectable:
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label
