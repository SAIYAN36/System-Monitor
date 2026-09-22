"""Immutable data models describing one system-metrics snapshot.

Keeping these as plain dataclasses means the polling thread and the GUI only
ever exchange inert value objects, which is safe to pass across Qt's queued
signal connections. Fields whose metric is unavailable on a machine are left as
``None`` and rendered as "Unavailable" by the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

__all__ = [
    "CpuInfo",
    "CpuStats",
    "MemoryStats",
    "PartitionInfo",
    "DiskIO",
    "DiskStats",
    "NetworkInterface",
    "NetworkStats",
    "ProcessInfo",
    "SystemInfo",
    "Snapshot",
]


@dataclass(frozen=True)
class CpuInfo:
    """Static information about the installed processor."""

    name: str = "Unknown CPU"
    physical_cores: Optional[int] = None
    logical_cores: Optional[int] = None
    max_frequency_mhz: Optional[float] = None
    architecture: str = ""


@dataclass(frozen=True)
class CpuStats:
    """Live processor metrics."""

    percent: Optional[float] = None
    per_core: Tuple[float, ...] = ()
    frequency_mhz: Optional[float] = None
    temperature_c: Optional[float] = None
    load_average: Optional[Tuple[float, float, float]] = None

    @property
    def core_count(self) -> int:
        return len(self.per_core)


@dataclass(frozen=True)
class MemoryStats:
    """Physical memory and page-file/swap metrics, all in bytes."""

    total: Optional[int] = None
    used: Optional[int] = None
    available: Optional[int] = None
    percent: Optional[float] = None
    swap_total: Optional[int] = None
    swap_used: Optional[int] = None
    swap_free: Optional[int] = None
    swap_percent: Optional[float] = None


@dataclass(frozen=True)
class PartitionInfo:
    """One mounted volume."""

    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total: Optional[int] = None
    used: Optional[int] = None
    free: Optional[int] = None
    percent: Optional[float] = None
    #: Volume label as reported by the OS, when one is set.
    label: Optional[str] = None
    #: Fixed / Removable / Network / Optical on Windows, empty elsewhere.
    drive_type: str = ""

    @property
    def display_name(self) -> str:
        """Mount point plus volume label, e.g. ``C:\ (Windows)``."""
        base = self.mountpoint or self.device or "Unknown"
        return f"{base} ({self.label})" if self.label else base


@dataclass(frozen=True)
class DiskIO:
    """Cumulative and instantaneous disk throughput, in bytes and bytes/second."""

    read_bytes: Optional[int] = None
    write_bytes: Optional[int] = None
    read_rate: Optional[float] = None
    write_rate: Optional[float] = None
    read_count: Optional[int] = None
    write_count: Optional[int] = None


@dataclass(frozen=True)
class DiskStats:
    partitions: Tuple[PartitionInfo, ...] = ()
    io: Optional[DiskIO] = None


@dataclass(frozen=True)
class NetworkInterface:
    """One network adapter with its counters and addresses."""

    name: str = ""
    is_up: bool = False
    speed_mbps: Optional[float] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = None
    mtu: Optional[int] = None
    bytes_sent: int = 0
    bytes_recv: int = 0
    upload_rate: Optional[float] = None
    download_rate: Optional[float] = None
    is_loopback: bool = False


@dataclass(frozen=True)
class NetworkStats:
    """Aggregate network throughput plus the per-adapter detail."""

    interfaces: Tuple[NetworkInterface, ...] = ()
    total_sent: int = 0
    total_recv: int = 0
    upload_rate: Optional[float] = None
    download_rate: Optional[float] = None
    primary_ipv4: Optional[str] = None


@dataclass(frozen=True)
class ProcessInfo:
    """A single running process."""

    pid: int = 0
    name: str = ""
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_rss: Optional[int] = None
    status: str = ""
    username: Optional[str] = None
    exe: Optional[str] = None
    threads: Optional[int] = None
    create_time: Optional[float] = None


@dataclass(frozen=True)
class SystemInfo:
    """Static/mostly-static machine description, refreshed rarely."""

    hostname: str = ""
    os_name: str = ""
    os_version: str = ""
    os_build: str = ""
    os_edition: str = ""
    architecture: str = ""
    machine: str = ""
    python_version: str = ""
    boot_time: Optional[float] = None
    cpu: CpuInfo = field(default_factory=CpuInfo)
    total_memory: Optional[int] = None
    drives: Tuple[str, ...] = ()
    network_adapters: Tuple[str, ...] = ()
    physical_disks: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Snapshot:
    """One complete metrics reading.

    ``processes`` and ``system`` are only populated when the corresponding
    collector was asked for them, which keeps the common dashboard poll cheap.
    """

    timestamp: float = 0.0
    cpu: CpuStats = field(default_factory=CpuStats)
    memory: MemoryStats = field(default_factory=MemoryStats)
    disk: DiskStats = field(default_factory=DiskStats)
    network: NetworkStats = field(default_factory=NetworkStats)
    system: Optional[SystemInfo] = None
    processes: Optional[Tuple[ProcessInfo, ...]] = None

    @property
    def uptime(self) -> Optional[float]:
        """Seconds since the machine booted, or ``None`` when unknown."""
        if self.system is None or self.system.boot_time is None:
            return None
        return max(0.0, self.timestamp - self.system.boot_time)

    @property
    def process_count(self) -> Optional[int]:
        return len(self.processes) if self.processes is not None else None
