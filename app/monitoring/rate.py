"""Helpers shared by the collectors: counter deltas and short-lived caches."""

from __future__ import annotations

import time
from typing import Callable, Dict, Optional, Tuple, TypeVar

T = TypeVar("T")


def monotonic_time() -> float:
    """High-resolution monotonic clock for interval measurements.

    ``time.monotonic()`` is only accurate to about 16 ms on Windows
    (``GetTickCount64``), so two readings taken inside the same tick appear to
    have happened at the same instant and the throughput sample is lost.
    ``perf_counter`` has sub-microsecond resolution and is monotonic, so every
    interval in the monitoring layer is measured with it.
    """
    return time.perf_counter()


class RateTracker:
    """Turns monotonically increasing counters into a per-second rate.

    Used for network and disk throughput. The first reading for a key has no
    previous sample to compare against, so it yields ``None`` (shown as
    "Unavailable") instead of a meaningless value.
    """

    __slots__ = ("_samples",)

    def __init__(self) -> None:
        self._samples: Dict[str, Tuple[float, float]] = {}

    def prime(self, key: str, value: float, now: Optional[float] = None) -> None:
        """Seed a counter without producing a rate."""
        self._samples[key] = (float(value), monotonic_time() if now is None else float(now))

    def update(self, key: str, value: float, now: Optional[float] = None) -> Optional[float]:
        """Record ``value`` and return the rate since the previous sample."""
        moment = monotonic_time() if now is None else float(now)
        previous = self._samples.get(key)
        self._samples[key] = (float(value), moment)
        if previous is None:
            return None
        previous_value, previous_moment = previous
        elapsed = moment - previous_moment
        if elapsed <= 0:
            return None
        delta = float(value) - previous_value
        # A negative delta means the counter was reset (adapter re-created,
        # machine resumed from sleep); report nothing rather than a bogus spike.
        if delta < 0:
            return None
        return delta / elapsed

    def drop(self, key: str) -> None:
        self._samples.pop(key, None)

    def retain(self, keys) -> None:
        """Forget counters for devices that no longer exist."""
        keep = set(keys)
        for key in list(self._samples):
            if key not in keep:
                del self._samples[key]

    def clear(self) -> None:
        self._samples.clear()


class TTLCache:
    """Memoises an expensive query for a short while.

    Enumerating partitions or network adapters is far costlier than reading the
    counters, and neither changes from one second to the next.
    """

    __slots__ = ("_ttl", "_value", "_expires", "_has_value")

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = float(ttl_seconds)
        self._value: object = None
        self._expires = 0.0
        self._has_value = False

    def get(self, factory: Callable[[], T], now: Optional[float] = None) -> T:
        moment = monotonic_time() if now is None else float(now)
        if not self._has_value or moment >= self._expires:
            self._value = factory()
            self._expires = moment + self._ttl
            self._has_value = True
        return self._value  # type: ignore[return-value]

    def invalidate(self) -> None:
        self._has_value = False

    @property
    def ttl(self) -> float:
        return self._ttl
