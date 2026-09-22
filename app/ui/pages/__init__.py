"""All application pages, in sidebar order."""

from app.ui.pages.base import Page, ScrollPage
from app.ui.pages.cpu import CpuPage
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.disk import DiskPage
from app.ui.pages.memory import MemoryPage
from app.ui.pages.network import NetworkPage
from app.ui.pages.processes import ProcessesPage
from app.ui.pages.settings import SettingsPage
from app.ui.pages.system_info import SystemInfoPage

#: (key, label, icon, page class) in the order they appear in the sidebar.
PAGE_DEFINITIONS = (
    ("dashboard", "Dashboard", "dashboard", DashboardPage),
    ("cpu", "CPU", "cpu", CpuPage),
    ("memory", "Memory", "memory", MemoryPage),
    ("disk", "Disk", "disk", DiskPage),
    ("network", "Network", "network", NetworkPage),
    ("processes", "Processes", "processes", ProcessesPage),
    ("system", "System Information", "info", SystemInfoPage),
    ("settings", "Settings", "settings", SettingsPage),
)

__all__ = [
    "PAGE_DEFINITIONS",
    "CpuPage",
    "DashboardPage",
    "DiskPage",
    "MemoryPage",
    "NetworkPage",
    "Page",
    "ProcessesPage",
    "ScrollPage",
    "SettingsPage",
    "SystemInfoPage",
]
