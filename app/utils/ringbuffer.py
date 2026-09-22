"""A fixed-capacity FIFO of samples.

The live graphs use this so that memory can never grow without bound: once the
buffer is full the oldest sample is discarded to make room for the newest.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Iterator, List, Optional


class RingBuffer:
    """Bounded sequence of floats with cheap append/average/peak queries."""

    __slots__ = ("_samples", "_capacity")

    def __init__(self, capacity: int = 120) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = int(capacity)
        self._samples: deque[float] = deque(maxlen=self._capacity)

    # ------------------------------------------------------------------ basics
    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return len(self._samples)

    def __iter__(self) -> Iterator[float]:
        return iter(self._samples)

    def __bool__(self) -> bool:
        return bool(self._samples)

    @property
    def is_full(self) -> bool:
        return len(self._samples) == self._capacity

    # ------------------------------------------------------------------ writes
    def append(self, value: float) -> None:
        """Append one sample, dropping the oldest one when full."""
        try:
            self._samples.append(float(value))
        except (TypeError, ValueError):
            return

    def extend(self, values: Iterable[float]) -> None:
        for value in values:
            self.append(value)

    def clear(self) -> None:
        self._samples.clear()

    def resize(self, capacity: int) -> None:
        """Change the capacity, keeping the most recent samples."""
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        capacity = int(capacity)
        if capacity == self._capacity:
            return
        self._capacity = capacity
        self._samples = deque(self._samples, maxlen=capacity)

    # ------------------------------------------------------------------ reads
    def values(self) -> List[float]:
        """Snapshot of the buffered samples, oldest first."""
        return list(self._samples)

    def latest(self) -> Optional[float]:
        return self._samples[-1] if self._samples else None

    def average(self) -> Optional[float]:
        if not self._samples:
            return None
        return sum(self._samples) / len(self._samples)

    def peak(self) -> Optional[float]:
        return max(self._samples) if self._samples else None

    def minimum(self) -> Optional[float]:
        return min(self._samples) if self._samples else None
