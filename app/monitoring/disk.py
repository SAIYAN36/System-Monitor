"""Disk metrics: mounted volumes, their usage, and read/write throughput."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import psutil

from app.config import is_windows
from app.models.snapshot import DiskIO, DiskStats, PartitionInfo
from app.monitoring.rate import RateTracker, TTLCache
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)

#: Windows drive types returned by ``GetDriveTypeW``.
_DRIVE_TYPES = {
    0: "Unknown",
    1: "No root directory",
    2: "Removable",
    3: "Fixed",
    4: "Network",
    5: "Optical",
    6: "RAM disk",
}

#: Partitions are re-enumerated at most this often (drives appear/disappear).
_PARTITION_TTL_SECONDS = 5.0


class DiskCollector:
    """Enumerates volumes and converts disk counters into throughput."""

    def __init__(self) -> None:
        self._rates = RateTracker()
        self._partitions = TTLCache(_PARTITION_TTL_SECONDS)
        self._volume_cache: Dict[str, Tuple[Optional[str], str]] = {}
        self._io_available: Optional[bool] = None

    # -------------------------------------------------------------------- live
    def collect(self, now: Optional[float] = None) -> DiskStats:
        partitions = self.partitions(now=now)
        return DiskStats(partitions=partitions, io=self.io_counters(now=now))

    def partitions(self, now: Optional[float] = None) -> Tuple[PartitionInfo, ...]:
        """All currently mounted volumes with usage figures.

        A volume that vanishes between enumeration and the usage query (removed
        USB stick, unmounted share) is skipped rather than aborting the sweep.
        """
        entries = self._partitions.get(self._list_partitions, now=now)
        result: List[PartitionInfo] = []
        for entry in entries:
            usage = safe_call(
                psutil.disk_usage,
                entry.mountpoint,
                default=None,
                context=f"disk_usage({entry.mountpoint})",
            )
            if usage is None:
                # The drive went away or is not ready (empty card reader).
                logger.debug("Skipping unreadable volume %s", entry.mountpoint)
                continue
            label, drive_type = self._volume_details(entry.mountpoint)
            result.append(
                PartitionInfo(
                    device=entry.device,
                    mountpoint=entry.mountpoint,
                    fstype=entry.fstype or "",
                    total=usage.total,
                    used=usage.used,
                    free=usage.free,
                    percent=usage.percent,
                    label=label,
                    drive_type=drive_type,
                )
            )
        return tuple(result)

    def io_counters(self, now: Optional[float] = None) -> Optional[DiskIO]:
        """Aggregate disk throughput, or ``None`` when the OS does not expose it."""
        counters = safe_call(psutil.disk_io_counters, default=None, context="disk_io_counters")
        if counters is None:
            if self._io_available is not False:
                logger.info("Disk I/O counters are not available on this system")
                self._io_available = False
            return None
        self._io_available = True

        read_rate = self._rates.update("read", counters.read_bytes, now)
        write_rate = self._rates.update("write", counters.write_bytes, now)
        return DiskIO(
            read_bytes=counters.read_bytes,
            write_bytes=counters.write_bytes,
            read_rate=read_rate,
            write_rate=write_rate,
            read_count=getattr(counters, "read_count", None),
            write_count=getattr(counters, "write_count", None),
        )

    @property
    def io_supported(self) -> Optional[bool]:
        """``None`` until the first probe, then whether I/O counters work."""
        return self._io_available

    # ------------------------------------------------------------------ static
    def drive_roots(self) -> Tuple[str, ...]:
        """Mount points of the volumes visible right now."""
        return tuple(part.mountpoint for part in self.partitions())

    @staticmethod
    def _list_partitions():
        """Raw partition enumeration, tolerating a total failure."""
        partitions = safe_call(
            psutil.disk_partitions, default=None, all=False, context="disk_partitions"
        )
        if partitions:
            return partitions
        # ``all=False`` filters out unready/optical media; retry with everything
        # so an exotic mount layout still shows up.
        return safe_call(
            psutil.disk_partitions, default=[], all=True, context="disk_partitions(all)"
        )

    def _volume_details(self, mountpoint: str) -> Tuple[Optional[str], str]:
        """Volume label and drive type for a mount point (cached)."""
        cached = self._volume_cache.get(mountpoint)
        if cached is not None:
            return cached
        details: Tuple[Optional[str], str] = (None, "")
        if is_windows():
            details = (_windows_volume_label(mountpoint), _windows_drive_type(mountpoint))
        self._volume_cache[mountpoint] = details
        return details

    def invalidate(self) -> None:
        """Force re-enumeration (used after the volume list changes)."""
        self._partitions.invalidate()
        self._volume_cache.clear()


def _windows_volume_label(mountpoint: str) -> Optional[str]:
    """Read the volume label through ``GetVolumeInformationW``."""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.GetVolumeInformationW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPWSTR,
            wintypes.DWORD,
        ]
        kernel32.GetVolumeInformationW.restype = wintypes.BOOL

        name_buffer = ctypes.create_unicode_buffer(261)
        ok = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(mountpoint),
            name_buffer,
            len(name_buffer),
            None,
            None,
            None,
            None,
            0,
        )
        if ok and name_buffer.value:
            return name_buffer.value
    except Exception as exc:  # noqa: BLE001 - optional enrichment only
        logger.debug("Volume label lookup failed for %s: %r", mountpoint, exc)
    return None


def _windows_drive_type(mountpoint: str) -> str:
    """Map a Windows drive letter to a human readable type."""
    if not mountpoint:
        return ""
    try:
        import ctypes

        root = mountpoint.rstrip("\\/") + "\\"
        kind = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))  # type: ignore[attr-defined]
        return _DRIVE_TYPES.get(int(kind), "Unknown")
    except Exception as exc:  # noqa: BLE001 - optional enrichment only
        logger.debug("Drive type lookup failed for %s: %r", mountpoint, exc)
        return ""


def physical_disk_names() -> Tuple[str, ...]:
    """Names of the physical disks, when the platform exposes them.

    Windows keeps one device object per physical drive under ``\\\\.\\``.
    """
    if not is_windows():
        return ()
    names: List[str] = []
    for index in range(16):
        path = f"\\\\.\\PHYSICALDRIVE{index}"
        try:
            import ctypes

            handle = ctypes.windll.kernel32.CreateFileW(  # type: ignore[attr-defined]
                ctypes.c_wchar_p(path),
                0,  # query metadata only
                0x00000001 | 0x00000002,  # share read + write
                None,
                3,  # OPEN_EXISTING
                0,
                None,
            )
            if handle not in (0, -1):
                names.append(path)
                ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - best effort enumeration
            break
    return tuple(names)
