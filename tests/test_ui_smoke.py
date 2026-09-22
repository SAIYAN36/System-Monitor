"""GUI tests.

Everything here renders the real widgets through Qt's ``offscreen`` platform,
so the pages are built, styled, updated and painted exactly as they are on a
desktop - without opening a window.
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QWidget  # noqa: E402

from app.models.snapshot import CpuStats, MemoryStats, ProcessInfo, Snapshot  # noqa: E402
from app.services.settings import SettingsManager  # noqa: E402
from app.ui.icons import icon_names, make_icon  # noqa: E402
from app.ui.pages import PAGE_DEFINITIONS  # noqa: E402
from app.ui.pages.processes import ProcessTableModel  # noqa: E402
from app.ui.theme import DARK, LIGHT, get_theme, usage_color  # noqa: E402
from app.ui.widgets.cards import InfoGrid, MetricCard  # noqa: E402
from app.ui.widgets.gauge import CoreUsageBars, RingGauge  # noqa: E402
from app.ui.widgets.graph import LineGraph  # noqa: E402


@pytest.fixture(autouse=True)
def qt_application(qapp):
    """Every test in this module touches Qt, which needs a live application."""
    return qapp


def distinct_colors(widget: QWidget, step: int = 9) -> int:
    """Number of distinct pixels in a rendered widget (a blank one has 1)."""
    image = widget.grab().toImage()
    assert image.width() > 0 and image.height() > 0
    colors = {
        image.pixel(x, y)
        for x in range(0, image.width(), step)
        for y in range(0, image.height(), step)
    }
    return len(colors)


def wait_until(predicate, qapp, timeout: float = 12.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    return False


# --------------------------------------------------------------------- theming
class TestTheme:
    @pytest.mark.parametrize("theme", [DARK, LIGHT])
    def test_stylesheet_mentions_the_theme_colors(self, theme):
        stylesheet = theme.stylesheet()
        assert theme.accent in stylesheet
        assert theme.surface in stylesheet
        assert "QPushButton" in stylesheet and "QTableView" in stylesheet

    def test_unknown_theme_falls_back_to_dark(self):
        assert get_theme("nonsense") is DARK

    def test_usage_color_thresholds(self):
        assert usage_color(DARK, 10) == DARK.success
        assert usage_color(DARK, 80) == DARK.warning
        assert usage_color(DARK, 95) == DARK.danger
        assert usage_color(DARK, None) == DARK.muted


# ----------------------------------------------------------------------- icons
class TestIcons:
    def test_every_glyph_renders(self):
        names = icon_names()
        assert len(names) >= 10
        for name in names:
            icon = make_icon(name, "#4c8dff", 18)
            assert not icon.isNull(), name
            assert icon.pixmap(18, 18).width() == 18

    def test_icons_are_cached(self):
        assert make_icon("cpu", "#ffffff", 20) is make_icon("cpu", "#ffffff", 20)


# --------------------------------------------------------------------- widgets
class TestWidgets:
    def test_graph_paints_samples(self, qapp):
        graph = LineGraph(theme=DARK, minimum_height=140)
        graph.resize(420, 200)
        graph.add_series("CPU", DARK.accent)
        graph.set_series_values("CPU", [10, 40, 30, 80, 55, 20])
        assert distinct_colors(graph) > 3

    def test_empty_graph_still_paints_a_placeholder(self, qapp):
        graph = LineGraph(theme=DARK)
        graph.resize(320, 160)
        assert distinct_colors(graph) > 1

    def test_graph_scales_and_clears(self, qapp):
        graph = LineGraph(theme=DARK, auto_scale=True, formatter=lambda value: f"{value:,.0f}")
        graph.set_values({"up": [5, 10, 15]})
        graph.set_values({"down": [1_000.0, 2_000.0]})
        assert set(graph.series_names()) == {"up", "down"}
        graph.clear()
        assert graph.series_names() == ("up", "down")

    def test_ring_gauge_paints(self, qapp):
        gauge = RingGauge(theme=DARK, caption="CPU")
        gauge.resize(200, 200)
        gauge.set_value(63.5)
        gauge.set_detail("1.2 GB / 8 GB")
        assert distinct_colors(gauge) > 3

    def test_ring_gauge_without_a_value(self, qapp):
        gauge = RingGauge(theme=DARK)
        gauge.resize(180, 180)
        gauge.set_value(None)
        assert distinct_colors(gauge) > 1

    def test_core_bars_size_with_the_core_count(self, qapp):
        bars = CoreUsageBars(theme=DARK)
        bars.resize(600, 200)
        bars.set_values([10.0] * 4)
        height_four = bars.minimumHeight()
        bars.set_values([10.0] * 16)
        assert bars.minimumHeight() > height_four
        assert distinct_colors(bars) > 3

    def test_metric_card_shows_unavailable_for_missing_values(self, qapp):
        card = MetricCard(theme=DARK, title="CPU usage")
        card.set_value(None)
        assert card.value_label.text() == "Unavailable"
        card.set_value(42.5, formatter=lambda value: f"{value:.1f}%")
        assert card.value_label.text() == "42.5%"

    def test_info_grid_updates_in_place(self, qapp):
        grid = InfoGrid(columns=1)
        grid.add_rows([("a", "First"), ("b", "Second")])
        assert grid.keys() == ["a", "b"]
        grid.set_values({"a": "changed"})
        assert grid.keys() == ["a", "b"]
        grid.set_value("b", None)
        grid.reset()


# --------------------------------------------------------------- process model
class TestProcessTableModel:
    def rows(self):
        return (
            ProcessInfo(pid=4, name="System", cpu_percent=0.0, memory_percent=0.1,
                        memory_rss=1024, status="running", threads=120),
            ProcessInfo(pid=1234, name="python.exe", cpu_percent=12.5,
                        memory_percent=2.0, memory_rss=1_048_576, status="running",
                        threads=8),
        )

    def test_shape(self, qapp):
        model = ProcessTableModel()
        model.set_rows(self.rows())
        assert model.rowCount() == 2
        assert model.columnCount() == 7
        assert model.headerData(0, Qt.Orientation.Horizontal) == "Process"
        assert model.headerData(0, Qt.Orientation.Vertical) is None

    def test_display_values(self, qapp):
        model = ProcessTableModel()
        model.set_rows(self.rows())
        assert model.data(model.index(1, 0)) == "python.exe"
        assert model.data(model.index(1, 1)) == "1234"
        assert model.data(model.index(1, 2)) == "12.5%"
        assert model.data(model.index(1, 4)) == "1.0 MB"

    def test_sort_keys_are_numeric(self, qapp):
        model = ProcessTableModel()
        model.set_rows(self.rows())
        assert model.data(model.index(1, 1), Qt.ItemDataRole.UserRole) == 1234
        assert model.data(model.index(1, 2), Qt.ItemDataRole.UserRole) == 12.5
        assert model.data(model.index(0, 0), Qt.ItemDataRole.UserRole) == "system"

    def test_unavailable_cpu_sorts_last(self, qapp):
        model = ProcessTableModel()
        model.set_rows((ProcessInfo(pid=1, name="x", cpu_percent=None),))
        assert model.data(model.index(0, 2), Qt.ItemDataRole.UserRole) == -1.0

    def test_reset_reports_the_new_row_count(self, qapp):
        model = ProcessTableModel()
        model.set_rows(self.rows())
        model.set_rows(self.rows()[:1])
        assert model.rowCount() == 1


# ------------------------------------------------------------------ main window
@pytest.fixture
def window(qapp, tmp_path):
    from app.ui.main_window import MainWindow

    manager = SettingsManager(tmp_path / "settings.json")
    manager.load()
    main = MainWindow(manager)
    main.resize(1280, 860)
    main.show()
    qapp.processEvents()
    try:
        yield main
    finally:
        main.shutdown()


def update_snapshot(cpu: float = 33.0) -> Snapshot:
    return Snapshot(
        timestamp=time.time(),
        cpu=CpuStats(percent=cpu, per_core=(cpu, cpu, cpu, cpu), temperature_c=None),
        memory=MemoryStats(total=8 * 1024**3, used=4 * 1024**3, percent=50.0,
                           available=4 * 1024**3, swap_total=1024**3, swap_used=1024**2,
                           swap_free=1023 * 1024**2, swap_percent=0.1),
        processes=(ProcessInfo(pid=1, name="idle", cpu_percent=0.0),) * 3,
    )


class TestMainWindow:
    def test_pages_are_created_on_first_visit(self, window, qapp):
        assert len(PAGE_DEFINITIONS) == 8
        assert window.sidebar.current_key() == "dashboard"
        # Only the opening page exists so far; the rest are built lazily.
        assert set(window.pages) == {"dashboard"}
        for key, _label, _icon, _cls in PAGE_DEFINITIONS:
            window.show_page(key)
            qapp.processEvents()
            assert key in window.pages
        assert len(window.pages) == 8

    def test_receives_live_updates(self, window, qapp):
        assert wait_until(lambda: window._last_update is not None, qapp, timeout=15)
        snapshot = window._last_update.snapshot
        assert snapshot.cpu.percent is not None
        assert snapshot.memory.total is not None

    def test_every_page_renders_after_an_update(self, window, qapp):
        assert wait_until(lambda: window._last_update is not None, qapp, timeout=15)
        for key, label, _icon, _cls in PAGE_DEFINITIONS:
            window.show_page(key)
            qapp.processEvents()
            page = window.pages[key]
            assert page.isVisible() or window.stack.currentWidget() is page
            colors = distinct_colors(page)
            assert colors > 6, f"page {key} looks blank ({colors} colours)"

    def test_window_itself_renders(self, window, qapp):
        assert wait_until(lambda: window._last_update is not None, qapp, timeout=15)
        qapp.processEvents()
        assert distinct_colors(window, step=13) > 10

    def test_sidebar_navigation_switches_pages(self, window, qapp):
        window.show_page("processes")
        qapp.processEvents()
        assert window.stack.currentWidget() is window.pages["processes"]
        assert window.sidebar.current_key() == "processes"
        assert "Processes" in window.windowTitle()

    def test_switching_pages_toggles_process_collection(self, window, qapp):
        window.show_page("processes")
        qapp.processEvents()
        assert window.worker.collect_processes is True
        window.show_page("dashboard")
        qapp.processEvents()
        assert window.worker.collect_processes is False

    def test_hidden_pages_are_not_updated(self, window, qapp):
        assert wait_until(lambda: window._last_update is not None, qapp, timeout=15)
        for key, _label, _icon, _cls in PAGE_DEFINITIONS:
            window.show_page(key)
            qapp.processEvents()
        window.show_page("cpu")
        qapp.processEvents()
        # Only the visible page may react to a reading.
        calls: list[str] = []
        for key, page in window.pages.items():
            page.apply_update = _recorder(page.apply_update, key, calls)  # type: ignore[method-assign]
        window._on_update(window._last_update)
        assert calls == ["cpu"]

    def test_status_bar_reflects_the_refresh_interval(self, window, qapp):
        assert wait_until(lambda: "Updated" in window.status_label.text(), qapp, timeout=15)
        assert "every" in window.status_label.text()

    def test_theme_toggle_switches_and_persists(self, window, qapp):
        assert window.settings.theme == "dark"
        window.toggle_theme()
        qapp.processEvents()
        assert window.settings.theme == "light"
        assert window.theme is LIGHT
        reloaded = SettingsManager(window.settings_manager.path).load()
        assert reloaded.theme == "light"
        window.toggle_theme()
        assert window.settings.theme == "dark"

    def test_clock_label_is_updated(self, window):
        assert len(window.clock_label.text()) == len("00:00:00")


class TestSettingsPage:
    @pytest.fixture
    def page(self, window, qapp):
        window.show_page("settings")
        qapp.processEvents()
        return window.pages["settings"]

    def test_controls_reflect_the_settings(self, window, page):
        assert page.refresh_field.value() == window.settings.refresh_interval_ms
        assert page.confirm_check.isChecked() is True
        assert page.save_button.isEnabled() is False

    def test_moving_a_slider_marks_the_form_dirty(self, window, page, qapp):
        page.refresh_field.slider.setValue(2500)
        qapp.processEvents()
        assert page.save_button.isEnabled() is True
        assert page.dirty_badge.text() == "Unsaved changes"

    def test_save_applies_and_persists(self, window, page, qapp):
        page.refresh_field.slider.setValue(2000)
        page.save_button.click()
        qapp.processEvents()

        assert window.settings.refresh_interval_ms == 2000
        assert window.worker.interval_ms == 2000
        assert page.save_button.isEnabled() is False
        assert SettingsManager(window.settings_manager.path).load().refresh_interval_ms == 2000

    def test_history_length_is_applied(self, window, page, qapp):
        page.history_field.slider.setValue(400)
        page.save_button.click()
        qapp.processEvents()
        assert window.history.capacity == 400

    def test_dashboard_visibility_follows_settings(self, window, page, qapp):
        dashboard = window.pages["dashboard"]
        page.card_checks["cpu"].setChecked(False)
        page.save_button.click()
        qapp.processEvents()
        assert window.settings.dashboard_cards["cpu"] is False
        assert dashboard.cards["cpu"].isVisibleTo(dashboard) is False
        assert dashboard.cards["memory"].isVisibleTo(dashboard) is True

    def test_restoring_defaults(self, window, page, qapp):
        page.refresh_field.slider.setValue(4000)
        page.save_button.click()
        qapp.processEvents()
        assert window.settings.refresh_interval_ms == 4000

        page.reset_button.click()
        qapp.processEvents()
        assert window.settings.refresh_interval_ms == 1000
        assert page.save_button.isEnabled() is False

    def test_unknown_theme_cannot_be_selected(self, page):
        assert page.theme_combo.count() == 2
        assert {page.theme_combo.itemData(i) for i in range(2)} == {"dark", "light"}


def _recorder(original, key: str, calls: list):
    """Wrap ``Page.apply_update`` so a test can see which pages were refreshed."""

    def wrapper(update):
        calls.append(key)
        return original(update)

    return wrapper
