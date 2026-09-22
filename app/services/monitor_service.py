"""The background polling thread.

Everything that touches psutil runs here, never on the GUI thread, so the
interface stays responsive even when a collector stalls. Completed readings are
delivered to the UI as immutable :class:`MetricsUpdate` objects.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from PySide6.QtCore import QThread, Signal

from app.config import DEFAULT_REFRESH_MS, MAX_REFRESH_MS, MIN_REFRESH_MS
from app.monitoring.collector import SystemMonitor
from app.services.history import MetricHistory, MetricsUpdate

logger = logging.getLogger(__name__)

#: After a failure the cadence is stretched, up to this multiple of the interval.
_MAX_BACKOFF_FACTOR = 5


class MonitorWorker(QThread):
    """Polls the collectors and emits one update per refresh interval."""

    #: Emitted with a :class:`MetricsUpdate` on every successful poll.
    updateReady = Signal(object)
    #: Emitted with a message when a poll raised; the worker keeps going.
    pollFailed = Signal(str)

    def __init__(
        self,
        monitor: SystemMonitor,
        history: MetricHistory,
        interval_ms: int = DEFAULT_REFRESH_MS,
        *,
        collect_processes: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._monitor = monitor
        self._history = history
        self._interval_ms = _clamp_interval(interval_ms)
        self._collect_processes = bool(collect_processes)
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._last_error: Optional[str] = None

    # ------------------------------------------------------------------ config
    @property
    def interval_ms(self) -> int:
        return self._interval_ms

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def set_interval_ms(self, interval_ms: int) -> None:
        """Change the cadence; the current wait is cut short so it applies now."""
        self._interval_ms = _clamp_interval(interval_ms)
        self._wake_event.set()

    def set_collect_processes(self, enabled: bool) -> None:
        """Enable process enumeration only while the Processes page is visible."""
        enabled = bool(enabled)
        if enabled == self._collect_processes:
            return
        self._collect_processes = enabled
        # Poll at once so the page does not sit empty for a whole interval.
        self._wake_event.set()

    @property
    def collect_processes(self) -> bool:
        return self._collect_processes

    # ----------------------------------------------------------------- control
    def wake(self) -> None:
        """Poll immediately instead of waiting for the next interval."""
        self._wake_event.set()

    def request_stop(self) -> None:
        """Ask the loop to finish promptly."""
        self._stop_event.set()
        self._wake_event.set()

    def run(self) -> None:  # noqa: D102 - QThread entry point
        logger.info(
            "Monitor worker started (interval %d ms, processes=%s)",
            self._interval_ms,
            self._collect_processes,
        )
        failures = 0
        try:
            self._monitor.prime()
            while not self._stop_event.is_set():
                started = time.monotonic()
                update = self._poll()
                if update is None:
                    failures += 1
                else:
                    failures = 0

                elapsed = time.monotonic() - started
                delay = max(0.05, self._interval_ms / 1000.0 - elapsed)
                if failures:
                    # Slow down when something is persistently unhappy instead
                    # of retrying at full rate forever.
                    delay *= min(1 + failures, _MAX_BACKOFF_FACTOR)
                self._wake_event.wait(delay)
                self._wake_event.clear()
        finally:
            logger.info("Monitor worker stopped")

    # ---------------------------------------------------------------- internal
    def _poll(self) -> Optional[MetricsUpdate]:
        try:
            snapshot = self._monitor.collect(include_processes=self._collect_processes)
        except Exception as exc:  # noqa: BLE001 - a bad poll must not kill the thread
            self._last_error = str(exc)
            logger.exception("Metric collection failed")
            self.pollFailed.emit(str(exc))
            return None

        self._last_error = None
        update = self._history.append_snapshot(snapshot)
        self.updateReady.emit(update)
        return update


def _clamp_interval(value: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REFRESH_MS
    return max(MIN_REFRESH_MS, min(MAX_REFRESH_MS, number))
