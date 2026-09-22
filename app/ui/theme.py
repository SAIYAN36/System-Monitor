"""Application theming.

Two complete themes are provided. Each one supplies both a
:class:`QPalette` (so native dialogs, menus and message boxes match) and a
stylesheet for the custom dashboard widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class Theme:
    """One colour scheme."""

    name: str
    bg: str
    sidebar: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_soft: str
    success: str
    warning: str
    danger: str
    purple: str
    cyan: str
    grid: str

    def color(self, key: str) -> str:
        return getattr(self, key, self.accent)

    def stylesheet(self) -> str:
        """The application stylesheet for this theme."""
        t = self
        return f"""
QWidget {{
    color: {t.text};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{ background: {t.bg}; }}
#Sidebar {{ background: {t.sidebar}; border-right: 1px solid {t.border}; }}
#SidebarTitle {{ font-size: 15px; font-weight: 700; color: {t.text}; }}
#SidebarSubtitle {{ font-size: 11px; color: {t.muted}; }}
#NavButton {{
    text-align: left;
    padding: 9px 12px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: {t.muted};
    font-size: 13px;
}}
#NavButton:hover {{ background: {t.surface_alt}; color: {t.text}; }}
#NavButton:checked {{
    background: {t.accent_soft};
    color: {t.accent};
    border-color: {t.accent};
    font-weight: 600;
}}
#Card {{
    background: {t.surface};
    border: 1px solid {t.border};
    border-radius: 12px;
}}
#CardTitle {{ color: {t.muted}; font-size: 11px; font-weight: 700; }}
#CardIconChip {{
    background: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: 8px;
}}
#MetricValue {{ color: {t.text}; font-size: 25px; font-weight: 600; }}
#MetricCaption {{ color: {t.muted}; font-size: 12px; }}
#PageTitle {{ font-size: 21px; font-weight: 600; color: {t.text}; }}
#PageSubtitle {{ color: {t.muted}; font-size: 13px; }}
#SectionTitle {{ color: {t.muted}; font-size: 11px; font-weight: 700; }}
#InfoLabel {{ color: {t.muted}; }}
#InfoValue {{ color: {t.text}; font-weight: 600; }}
#HeaderClock {{ font-size: 13px; font-weight: 600; color: {t.text}; }}
#HeaderMeta {{ color: {t.muted}; font-size: 12px; }}
#Badge {{
    background: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: 9px;
    padding: 2px 8px;
    color: {t.muted};
    font-size: 11px;
}}
QScrollArea {{ border: none; background: transparent; }}
#PageScroll > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle {{ background: {t.border}; border-radius: 5px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {t.muted}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QPushButton {{
    background: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: 8px;
    padding: 7px 14px;
    color: {t.text};
}}
QPushButton:hover {{ border-color: {t.accent}; }}
QPushButton:pressed {{ background: {t.border}; }}
QPushButton:disabled {{ color: {t.muted}; border-color: {t.border}; }}
QPushButton#PrimaryButton {{
    background: {t.accent}; border-color: {t.accent}; color: #ffffff; font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{ background: {t.accent}; }}
QPushButton#DangerButton {{
    background: {t.danger}; border-color: {t.danger}; color: #ffffff; font-weight: 600;
}}
QPushButton#DangerButton:disabled {{ background: {t.surface_alt}; color: {t.muted}; border-color: {t.border}; }}
QLineEdit, QComboBox, QSpinBox {{
    background: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: 8px;
    padding: 6px 10px;
    color: {t.text};
    selection-background-color: {t.accent};
    selection-color: #ffffff;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {t.accent}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background: {t.surface};
    border: 1px solid {t.border};
    selection-background-color: {t.accent_soft};
    selection-color: {t.text};
    outline: none;
}}
QCheckBox {{ color: {t.text}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border: 1px solid {t.border};
    border-radius: 4px; background: {t.surface_alt};
}}
QCheckBox::indicator:hover {{ border-color: {t.accent}; }}
QCheckBox::indicator:checked {{ background: {t.accent}; border-color: {t.accent}; }}
QSlider::groove:horizontal {{ height: 4px; background: {t.border}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {t.accent}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
}}
QTableView {{
    background: {t.surface};
    alternate-background-color: {t.surface_alt};
    gridline-color: {t.border};
    border: 1px solid {t.border};
    border-radius: 10px;
    selection-background-color: {t.accent_soft};
    selection-color: {t.text};
    outline: none;
}}
QTableView::item:selected {{ color: {t.text}; }}
QHeaderView::section {{
    background: {t.surface_alt};
    color: {t.muted};
    padding: 7px 6px;
    border: none;
    border-bottom: 1px solid {t.border};
    font-weight: 600;
}}
QTableCornerButton::section {{ background: {t.surface_alt}; border: none; }}
QProgressBar {{
    border: none; border-radius: 4px; background: {t.border};
    min-height: 8px; max-height: 8px; color: transparent;
}}
QProgressBar::chunk {{ background: {t.accent}; border-radius: 4px; }}
QStatusBar {{ background: {t.sidebar}; color: {t.muted}; border-top: 1px solid {t.border}; }}
QStatusBar::item {{ border: none; }}
QToolTip {{
    background: {t.surface_alt}; color: {t.text};
    border: 1px solid {t.border}; padding: 5px; border-radius: 6px;
}}
QSplitter::handle {{ background: {t.border}; }}
QMessageBox {{ background: {t.surface}; }}
"""


DARK = Theme(
    name="dark",
    bg="#0e1116",
    sidebar="#12161d",
    surface="#171d26",
    surface_alt="#1e2632",
    border="#28323f",
    text="#e9eff7",
    muted="#93a1b5",
    accent="#4c8dff",
    accent_soft="#1b2a44",
    success="#35c98a",
    warning="#f0a63c",
    danger="#f2565b",
    purple="#a877ff",
    cyan="#35c4d8",
    grid="#222c39",
)

LIGHT = Theme(
    name="light",
    bg="#f3f5f9",
    sidebar="#ffffff",
    surface="#ffffff",
    surface_alt="#eef2f8",
    border="#d7dee9",
    text="#111823",
    muted="#5d6b80",
    accent="#2563eb",
    accent_soft="#dbe7ff",
    success="#12a05f",
    warning="#c47d09",
    danger="#d93a3f",
    purple="#7c3aed",
    cyan="#0b8fa8",
    grid="#e3e9f2",
)

THEMES: Dict[str, Theme] = {"dark": DARK, "light": LIGHT}


def get_theme(name: str) -> Theme:
    """Look up a theme by name, defaulting to dark."""
    return THEMES.get(name, DARK)


def usage_color(theme: Theme, percent: float | None) -> str:
    """Green/amber/red accent for a utilisation figure."""
    if percent is None:
        return theme.muted
    if percent >= 90:
        return theme.danger
    if percent >= 75:
        return theme.warning
    return theme.success


def apply_theme(app: QApplication, name: str) -> Theme:
    """Apply the named theme to the whole application."""
    theme = get_theme(name)
    app.setStyleSheet(theme.stylesheet())
    app.setPalette(_palette(theme))
    return theme


def _palette(theme: Theme) -> QPalette:
    """A matching QPalette so native dialogs follow the theme too."""
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: theme.bg,
        QPalette.ColorRole.WindowText: theme.text,
        QPalette.ColorRole.Base: theme.surface,
        QPalette.ColorRole.AlternateBase: theme.surface_alt,
        QPalette.ColorRole.Text: theme.text,
        QPalette.ColorRole.Button: theme.surface_alt,
        QPalette.ColorRole.ButtonText: theme.text,
        QPalette.ColorRole.Highlight: theme.accent,
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: theme.surface_alt,
        QPalette.ColorRole.ToolTipText: theme.text,
        QPalette.ColorRole.PlaceholderText: theme.muted,
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    disabled = QColor(theme.muted)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
    return palette
