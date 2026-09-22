"""Bounded metric history backing the live graphs.

History is recorded by the polling thread and consumed by the GUI thread. To
avoid sharing mutable buffers between threads, the worker hands the UI an
immutable :class:`MetricsUpdate` containing plain tuples.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple

from app.config import DEFAULT_HISTORY_SAMPLES
from app.models.snapshot import Snapshot
from app.utils.ringbuffer import RingBuffer

#: Series recorded for the graphs. Disk and network values are bytes/second.
SERIES_NAMES: Tuple[str, ...] = (
    "cpu",
    "memory",
    "net_upload",
    "net_download",
    "disk_read",
    "disk_write",
    "cpu_temp",
    "processes",
)


@dataclass(frozen=True)
class MetricsUpdate:
    """A snapshot plus the current graph series, safe to pass between threads."""

    snapshot: Snapshot
    series: Mapping[str, Tuple[float, ...]]

    def values(self, name: str) -> Tuple[float, ...]:
        return self.series.get(name, ())


class MetricHistory:
    """Fixed-capacity series for the live graphs."""

    def __init__(self, capacity: int = DEFAULT_HISTORY_SAMPLES) -> None:
        self._capacity = max(2, int(capacity))
        self._buffers: Dict[str, RingBuffer] = {
            name: RingBuffer(self._capacity) for name in SERIES_NAMES
        }

    @property
    def capacity(self) -> int:
        return self._capacity

    def set_capacity(self, capacity: int) -> None:
        """Resize every series, keeping the most recent samples."""
        self._capacity = max(2, int(capacity))
        for buffer in self._buffers.values():
            buffer.resize(self._capacity)

    def clear(self) -> None:
        for buffer in self._buffers.values():
            buffer.clear()

    def append_snapshot(self, snapshot: Snapshot) -> MetricsUpdate:
        """Record one snapshot and return it bundled with the series."""
        samples = {
            "cpu": snapshot.cpu.percent,
            "memory": snapshot.memory.percent,
            "net_upload": snapshot.network.upload_rate,
            "net_download": snapshot.network.download_rate,
            "disk_read": snapshot.disk.io.read_rate if snapshot.disk.io else None,
            "disk_write": snapshot.disk.io.write_rate if snapshot.disk.io else None,
            "cpu_temp": snapshot.cpu.temperature_c,
            "processes": snapshot.process_count,
        }
        for name, value in samples.items():
            # An unavailable sample is recorded as zero so the graphs keep a
            # continuous shape instead of showing a hole.
            self._buffers[name].append(0.0 if value is None else value)
        return MetricsUpdate(snapshot=snapshot, series=self.bundle())

    def series(self, name: str) -> Tuple[float, ...]:
        buffer = self._buffers.get(name)
        return tuple(buffer.values()) if buffer else ()

    def bundle(self) -> Dict[str, Tuple[float, ...]]:
        return {name: tuple(buffer.values()) for name, buffer in self._buffers.items()}

    def latest(self, name: str) -> Optional[float]:
        buffer = self._buffers.get(name)
        return buffer.latest() if buffer else None

    def stats(self, name: str) -> Tuple[Optional[float], Optional[float]]:
        """``(average, peak)`` for a series, for the graph captions."""
        buffer = self._buffers.get(name)
        if buffer is None:
            return None, None
        return buffer.average(), buffer.peak()
