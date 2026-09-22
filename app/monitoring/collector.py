"""The aggregator that produces complete metrics snapshots.

This is the single entry point the rest of the application uses. Keeping it
separate from the individual collectors means the polling thread never has to
know which subsystem is expensive on which machine.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from app.config import DEFAULT_TEMPERATURE_INTERVAL_S
from app.models.snapshot import CpuInfo, Snapshot, SystemInfo
from app.monitoring.cpu import CpuCollector
from app.monitoring.disk import DiskCollector
from app.monitoring.memory import MemoryCollector
from app.monitoring.network import NetworkCollector
from app.monitoring.processes import ProcessCollector
from app.monitoring.rate import monotonic_time
from app.monitoring.sensors import SensorReader
from app.monitoring.system import SystemInfoCollector

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Collects every metric group into a single :class:`Snapshot`."""

    def __init__(
        self,
        *,
        temperature_enabled: bool = True,
        temperature_interval_s: float = DEFAULT_TEMPERATURE_INTERVAL_S,
    ) -> None:
        self.cpu = CpuCollector()
        self.memory = MemoryCollector()
        self.disk = DiskCollector()
        self.network = NetworkCollector()
        self.processes = ProcessCollector()
        self.sensors = SensorReader(
            enabled=temperature_enabled, interval_seconds=temperature_interval_s
        )
        self.system = SystemInfoCollector(cpu_info_provider=lambda: self.cpu.info)

    # -------------------------------------------------------------------- api
    def prime(self) -> None:
        """Warm up the delta-based counters so the first poll is meaningful."""
        self.cpu.prime()

    @property
    def cpu_info(self) -> CpuInfo:
        return self.cpu.info

    def collect(
        self,
        *,
        include_processes: bool = False,
        now: Optional[float] = None,
    ) -> Snapshot:
        """Build one snapshot.

        ``include_processes`` is the only expensive switch; the process table is
        therefore only collected while the Processes page is on screen.
        """
        moment = time.time() if now is None else float(now)
        monotonic_now = monotonic_time()

        temperature = self.sensors.read()
        cpu_stats = self.cpu.collect(temperature_c=temperature)
        memory_stats = self.memory.collect()
        disk_stats = self.disk.collect(now=monotonic_now)
        network_stats = self.network.collect(now=monotonic_now)
        system_info: SystemInfo = self.system.collect(now=monotonic_now)

        process_rows = None
        if include_processes:
            process_rows = self.processes.collect()

        return Snapshot(
            timestamp=moment,
            cpu=cpu_stats,
            memory=memory_stats,
            disk=disk_stats,
            network=network_stats,
            system=system_info,
            processes=process_rows,
        )

    # -------------------------------------------------------------- settings
    def set_temperature_enabled(self, enabled: bool) -> None:
        self.sensors.set_enabled(enabled)

    def set_temperature_interval(self, seconds: float) -> None:
        self.sensors.set_interval(seconds)

    def refresh_static(self) -> None:
        """Drop cached device lists (used when the Settings page is saved)."""
        self.disk.invalidate()
        self.network.invalidate()
        self.system.invalidate()
