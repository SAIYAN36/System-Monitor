"""Static system information: OS, machine, boot time, drives and adapters."""

from __future__ import annotations

import logging
import platform
import socket
from typing import Dict, Optional, Tuple

import psutil

from app.config import APP_VERSION, is_windows
from app.monitoring.disk import physical_disk_names
from app.models.snapshot import CpuInfo, SystemInfo
from app.monitoring.rate import TTLCache
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)

#: The machine description changes rarely; re-read it a few times a minute.
_INFO_TTL_SECONDS = 30.0


class SystemInfoCollector:
    """Produces the :class:`SystemInfo` block, cached for a short interval."""

    def __init__(self, cpu_info_provider=None) -> None:
        self._cache: TTLCache = TTLCache(_INFO_TTL_SECONDS)
        self._cpu_info_provider = cpu_info_provider

    def collect(self, now: Optional[float] = None) -> SystemInfo:
        return self._cache.get(self._build, now=now)

    def invalidate(self) -> None:
        self._cache.invalidate()

    # ----------------------------------------------------------------- private
    def _build(self) -> SystemInfo:
        os_name, os_version, os_build, os_edition = _os_details()
        cpu_info: CpuInfo = (
            self._cpu_info_provider() if self._cpu_info_provider else CpuInfo()
        )
        drives = safe_call(psutil.disk_partitions, default=[], context="disk_partitions")
        adapters = safe_call(psutil.net_if_addrs, default={}, context="net_if_addrs")

        return SystemInfo(
            hostname=safe_call(socket.gethostname, default="Unknown"),
            os_name=os_name,
            os_version=os_version,
            os_build=os_build,
            os_edition=os_edition,
            architecture=safe_call(platform.architecture, default=("", ""))[0] or "",
            machine=safe_call(platform.machine, default=""),
            python_version=platform.python_version(),
            boot_time=safe_call(psutil.boot_time, default=None, context="boot_time"),
            cpu=cpu_info,
            total_memory=_total_memory(),
            drives=tuple(part.mountpoint for part in drives or ()),
            network_adapters=tuple(sorted(adapters)) if adapters else (),
            physical_disks=physical_disk_names(),
        )


def _total_memory() -> Optional[int]:
    memory = safe_call(psutil.virtual_memory, default=None, context="virtual_memory")
    return getattr(memory, "total", None)


def _os_details() -> Tuple[str, str, str, str]:
    """Return ``(os name, version, build, edition)``.

    On Windows the registry holds the marketing build information. Note that
    ``ProductName`` still says "Windows 10" on Windows 11, so the build number
    decides which of the two it actually is.
    """
    system = safe_call(platform.system, default="") or ""
    release = safe_call(platform.release, default="") or ""
    version = safe_call(platform.version, default="") or ""

    if not is_windows():
        return system or "Unknown", release, version, ""

    registry = _windows_registry_details()
    build_number = registry.get("CurrentBuildNumber") or ""
    display_version = registry.get("DisplayVersion") or registry.get("ReleaseId") or ""
    revision = registry.get("UBR") or ""

    product = registry.get("ProductName") or "Windows"
    major_build = _to_int(build_number)
    if major_build is not None and major_build >= 22000 and "11" not in product:
        # Same registry string, different OS: relabel for correctness.
        product = product.replace("Windows 10", "Windows 11")

    build = build_number
    if revision:
        build = f"{build_number}.{revision}"
    if not build:
        build = version

    edition = product
    if display_version:
        edition = f"{product} {display_version}"

    return "Windows", release or "10", build, edition


def _windows_registry_details() -> Dict[str, str]:
    """Read the Windows version key from the registry (best effort)."""
    details: Dict[str, str] = {}
    try:
        import winreg  # noqa: PLC0415 - Windows-only import, kept local

        path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            for value_name in (
                "ProductName",
                "DisplayVersion",
                "ReleaseId",
                "CurrentBuildNumber",
                "CurrentBuild",
                "UBR",
            ):
                try:
                    value, _ = winreg.QueryValueEx(key, value_name)
                except OSError:
                    continue
                details[value_name] = str(value)
    except Exception as exc:  # noqa: BLE001 - falls back to platform module data
        logger.debug("Windows registry version lookup failed: %r", exc)
    return details


def _to_int(value: str) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


__all__ = ["SystemInfoCollector", "APP_VERSION"]
