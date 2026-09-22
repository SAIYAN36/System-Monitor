"""Process manager: a sortable table with a safe "end task" action."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QItemSelectionModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QWidget,
)

from app.models.snapshot import ProcessInfo
from app.monitoring.processes import ProcessTerminationError
from app.services.history import MetricsUpdate
from app.ui.pages.base import ScrollPage
from app.ui.theme import Theme
from app.ui.widgets.cards import Card, InfoGrid
from app.ui.widgets.common import badge, section_title
from app.utils.formatting import format_bytes, format_percent, format_timestamp

logger = logging.getLogger(__name__)

_HEADERS = ("Process", "PID", "CPU %", "Memory %", "Memory", "Threads", "Status")

_DETAIL_ROWS = (
    ("pid", "PID"),
    ("user", "User"),
    ("exe", "Executable"),
    ("cmdline", "Command line"),
    ("started", "Started"),
    ("threads", "Threads"),
    ("status", "Status"),
    ("nice", "Priority"),
)


class ProcessTableModel(QAbstractTableModel):
    """Table model over a tuple of :class:`ProcessInfo` rows."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: List[ProcessInfo] = []
        self._theme: Optional[Theme] = None

    # -------------------------------------------------------------------- data
    def set_rows(self, rows) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        if self._rows:
            top = self.index(0, 0)
            bottom = self.index(len(self._rows) - 1, len(_HEADERS) - 1)
            self.dataChanged.emit(top, bottom, [])

    def process_at(self, row: int) -> Optional[ProcessInfo]:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(_HEADERS)

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(_HEADERS)
        ):
            return _HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        process = self._rows[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._display(process, column)
        if role == Qt.ItemDataRole.UserRole:
            # Sorting must use raw numbers, not the formatted strings.
            return self._sort_key(process, column)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in (1, 2, 3, 5):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ForegroundRole and self._theme is not None:
            return self._foreground(process, column)
        if role == Qt.ItemDataRole.ToolTipRole:
            return process.exe or process.name
        return None

    # ---------------------------------------------------------------- internals
    @staticmethod
    def _display(process: ProcessInfo, column: int) -> str:
        if column == 0:
            return process.name or f"PID {process.pid}"
        if column == 1:
            return str(process.pid)
        if column == 2:
            return format_percent(process.cpu_percent, precision=1)
        if column == 3:
            return format_percent(process.memory_percent, precision=1)
        if column == 4:
            return format_bytes(process.memory_rss)
        if column == 5:
            return "–" if process.threads is None else str(process.threads)
        return process.status.replace("_", " ") if process.status else "–"

    @staticmethod
    def _sort_key(process: ProcessInfo, column: int):
        if column == 0:
            return (process.name or "").lower()
        if column == 1:
            return process.pid
        if column == 2:
            # Unavailable readings sort to the bottom rather than to zero.
            return process.cpu_percent if process.cpu_percent is not None else -1.0
        if column == 3:
            return process.memory_percent if process.memory_percent is not None else -1.0
        if column == 4:
            return process.memory_rss or 0
        if column == 5:
            return process.threads or 0
        return process.status or ""

    def _foreground(self, process: ProcessInfo, column: int) -> Optional[QBrush]:
        theme = self._theme
        if theme is None:
            return None
        if column == 2 and process.cpu_percent is not None and process.cpu_percent >= 40.0:
            return QBrush(QColor(theme.warning))
        if column == 3 and process.memory_percent is not None and process.memory_percent >= 25.0:
            return QBrush(QColor(theme.warning))
        return None


class ProcessTask(QThread):
    """Runs one process operation (detail lookup or termination) off the UI thread."""

    detailReady = Signal(object)
    processStopped = Signal(int)
    failed = Signal(str)

    def __init__(self, collector, operation: str, pid: int, *, force: bool = False, parent=None):
        super().__init__(parent)
        self._collector = collector
        self._operation = operation
        self._pid = int(pid)
        self._force = force

    def run(self) -> None:  # noqa: D102 - QThread entry point
        try:
            if self._operation == "detail":
                self.detailReady.emit(self._collector.detail(self._pid))
            else:
                self._collector.terminate(self._pid, force=self._force)
                self.processStopped.emit(self._pid)
        except ProcessTerminationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - reported in the UI, never fatal
            logger.exception("Process operation %s failed", self._operation)
            self.failed.emit(f"Unexpected error: {exc}")


class ProcessesPage(ScrollPage):
    key = "processes"
    title = "Processes"
    subtitle = "Running processes, sortable by CPU or memory."

    def populate(self) -> None:
        self._task: Optional[ProcessTask] = None
        self._pending_pid: Optional[int] = None
        self._rows: List[ProcessInfo] = []

        # ---------------------------------------------------------- toolbar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by name, PID or status...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self._on_filter_changed)
        self.header_extra.addWidget(self.search)

        self.refresh_button = QPushButton("Refresh now")
        self.refresh_button.setToolTip("Poll the process list immediately")
        self.refresh_button.clicked.connect(self._refresh_now)
        self.header_extra.addWidget(self.refresh_button)

        self.end_button = QPushButton("End task")
        self.end_button.setObjectName("DangerButton")
        self.end_button.setEnabled(False)
        self.end_button.clicked.connect(self._end_selected)
        self.header_extra.addWidget(self.end_button)

        self.count_badge = badge("Collecting...")
        self.header_extra.addWidget(self.count_badge)

        # ------------------------------------------------------------ table
        self.model = ProcessTableModel(self)
        self.model.set_theme(self.theme)

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setDynamicSortFilter(True)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in range(1, len(_HEADERS)):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.setMinimumHeight(360)
        self.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.selection_model = self.table.selectionModel()
        self.selection_model.currentRowChanged.connect(self._on_row_changed)

        table_card = Card(theme=self.theme, title="Process list", icon_name="processes")
        table_card.add_widget(self.table, 1)
        hint = QLabel(
            "Click a column header to sort. CPU and memory readings are sampled on "
            "every refresh; percentages match Task Manager (share of total CPU)."
        )
        hint.setObjectName("MetricCaption")
        hint.setWordWrap(True)
        table_card.add_widget(hint)
        self.add_content(table_card)

        # ----------------------------------------------------------- details
        self.add_content(section_title("Selected process"))
        self.details = InfoGrid(columns=1, label_width=150)
        self.details.add_rows(_DETAIL_ROWS)
        self.details.set_value("pid", "Select a process to see its details")
        details_card = Card(theme=self.theme, title="Details", icon_name="info")
        details_card.add_widget(self.details)
        self.add_content(details_card)
        self.add_stretch()

        # Debounce the detail lookup: dragging through the list should not spawn
        # a query thread for every intermediate row.
        self._detail_timer = QTimer(self)
        self._detail_timer.setSingleShot(True)
        self._detail_timer.setInterval(160)
        self._detail_timer.timeout.connect(self._fetch_details)

    # ------------------------------------------------------------- lifecycle
    def on_activated(self) -> None:
        worker = self.context.worker
        if worker is not None:
            worker.set_collect_processes(True)

    def on_deactivated(self) -> None:
        worker = self.context.worker
        if worker is not None:
            worker.set_collect_processes(False)
        self.end_button.setEnabled(False)

    # ------------------------------------------------------------------ updates
    def apply_update(self, update: MetricsUpdate) -> None:
        processes = update.snapshot.processes

        if processes is None:
            self.count_badge.setText("Waiting for the first sample...")
            return

        self._rows = list(processes)
        selected_pid = self._selected_pid()

        self.model.set_rows(processes)

        if selected_pid is not None:
            self._select_pid(selected_pid)
        else:
            self.end_button.setEnabled(False)

        self._update_badge()

    def apply_settings(self, settings) -> None:
        # The badge quotes the refresh interval, so it has to be re-rendered.
        self._update_badge()

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        self.model.set_theme(theme)

    # ---------------------------------------------------------------- filtering
    def _on_filter_changed(self, text: str) -> None:
        self.proxy.setFilterFixedString(text)
        self._update_badge()

    def _update_badge(self) -> None:
        total = len(self._rows)
        if not total:
            self.count_badge.setText("Collecting...")
            return
        shown = self.proxy.rowCount()
        interval = self.context.settings.refresh_interval_ms / 1000.0
        if shown != total:
            self.count_badge.setText(f"{shown} of {total} shown · every {interval:g}s")
        else:
            self.count_badge.setText(f"{total} processes · every {interval:g}s")

    def _refresh_now(self) -> None:
        worker = self.context.worker
        if worker is None:
            self.statusMessage.emit("The monitoring thread is not running.")
            return
        worker.wake()
        self.statusMessage.emit("Refreshing the process list...")

    # ----------------------------------------------------------------- selection
    def _selected_pid(self) -> Optional[int]:
        indexes = self.selection_model.selectedRows()
        if not indexes:
            return None
        source = self.proxy.mapToSource(indexes[0])
        process = self.model.process_at(source.row())
        return process.pid if process else None

    def _select_pid(self, pid: int) -> None:
        for row in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(row, 0))
            process = self.model.process_at(source.row())
            if process and process.pid == pid:
                self.selection_model.setCurrentIndex(
                    self.proxy.index(row, 0),
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                self.end_button.setEnabled(True)
                return
        self.end_button.setEnabled(False)

    def _on_row_changed(self, *args) -> None:
        process = self._current_process()
        self.end_button.setEnabled(process is not None)
        if process is None:
            self.details.reset()
            self.details.set_value("pid", "Select a process to see its details")
            return
        self.details.reset()
        self.details.set_values(
            {
                "pid": process.pid,
                "status": process.status.replace("_", " "),
                "threads": process.threads,
                "exe": process.exe or None,
            }
        )
        self._detail_timer.start()

    def _current_process(self) -> Optional[ProcessInfo]:
        indexes = self.selection_model.selectedRows()
        if not indexes:
            return None
        source = self.proxy.mapToSource(indexes[0])
        return self.model.process_at(source.row())

    # ------------------------------------------------------------------ details
    def _fetch_details(self) -> None:
        process = self._current_process()
        if process is None:
            return
        collector = self.context.monitor.processes
        self._pending_pid = process.pid
        if self._task is not None and self._task.isRunning():
            # Another lookup is in flight; it will finish and this one is
            # restarted when the task completes.
            return
        self._start_task("detail", process.pid)

    def _start_task(self, operation: str, pid: int, *, force: bool = False) -> None:
        collector = self.context.monitor.processes
        task = ProcessTask(collector, operation, pid, force=force, parent=self)
        task.detailReady.connect(self._on_details_ready)
        task.processStopped.connect(self._on_terminated)
        task.failed.connect(self._on_task_failed)
        task.finished.connect(self._on_task_finished)
        self._task = task
        task.start()

    def _on_details_ready(self, detail) -> None:
        process = self._current_process()
        if process is None or detail is None:
            return
        command_line = detail.get("cmdline") or []
        self.details.set_values(
            {
                "pid": process.pid,
                "user": detail.get("username"),
                "exe": detail.get("exe"),
                "cmdline": " ".join(command_line) if command_line else None,
                "started": format_timestamp(detail.get("create_time")),
                "threads": detail.get("threads", process.threads),
                "status": (process.status or "").replace("_", " "),
                "nice": detail.get("nice"),
            }
        )

    def _on_task_finished(self) -> None:
        task = self._task
        if task is not None:
            task.deleteLater()
        self._task = None
        # If the selection moved while the lookup ran, ask again for it.
        current = self._current_process()
        if (
            self._pending_pid is not None
            and current is not None
            and current.pid != self._pending_pid
        ):
            self._detail_timer.start()

    # ------------------------------------------------------------- termination
    def _show_context_menu(self, position) -> None:
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        self.table.selectRow(index.row())
        menu = QMenu(self)
        end_action = menu.addAction("End task...")
        end_action.triggered.connect(self._end_selected)
        details_action = menu.addAction("Copy PID")
        details_action.triggered.connect(self._copy_pid)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _copy_pid(self) -> None:
        process = self._current_process()
        if process is not None:
            QApplication.clipboard().setText(str(process.pid))
            self.statusMessage.emit(f"Copied PID {process.pid} to the clipboard.")

    def _end_selected(self) -> None:
        process = self._current_process()
        if process is None:
            return

        force = False
        if self.context.settings.confirm_terminate:
            confirmed, force = self._confirm(process)
            if not confirmed:
                return

        self._start_task("terminate", process.pid, force=force)
        self.statusMessage.emit(f"Stopping {process.name} (PID {process.pid})...")

    def _confirm(self, process: ProcessInfo) -> tuple:
        """Ask before stopping a process; returns ``(confirmed, force)``."""
        critical = self.context.monitor.processes.is_critical(process.name)

        box = QMessageBox(self)
        box.setWindowTitle("End task")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(f'End "{process.name}" (PID {process.pid})?')
        details = [
            f"Memory in use: {format_bytes(process.memory_rss)}",
            f"CPU: {format_percent(process.cpu_percent)}",
            "",
            "The process is asked to close first. Unsaved work in it can be lost.",
        ]
        if critical:
            details.append(
                "This looks like a critical Windows process — ending it can make "
                "the system unstable."
            )
        box.setInformativeText("\n".join(details))
        box.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes)
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        box.button(QMessageBox.StandardButton.Yes).setText("End task")

        force_box = QCheckBox("Force kill (do not wait for a clean shutdown)")
        box.setCheckBox(force_box)

        confirmed = box.exec() == QMessageBox.StandardButton.Yes
        return confirmed, force_box.isChecked()

    def _on_terminated(self, pid: int) -> None:
        self.statusMessage.emit(f"Process {pid} was stopped.")
        logger.info("Process %s terminated by the user", pid)
        worker = self.context.worker
        if worker is not None:
            worker.wake()

    def _on_task_failed(self, message: str) -> None:
        self.statusMessage.emit(message)
        QMessageBox.warning(self, "Process action failed", message)
