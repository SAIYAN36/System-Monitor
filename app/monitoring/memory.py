"""Physical memory and page-file/swap metrics."""

from __future__ import annotations

import logging

import psutil

from app.models.snapshot import MemoryStats
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)


class MemoryCollector:
    """Reads RAM and swap (page file on Windows) usage in bytes."""

    def collect(self) -> MemoryStats:
        virtual = safe_call(psutil.virtual_memory, default=None, context="virtual_memory")
        swap = safe_call(psutil.swap_memory, default=None, context="swap_memory")

        if virtual is None and swap is None:
            return MemoryStats()

        return MemoryStats(
            total=getattr(virtual, "total", None),
            used=getattr(virtual, "used", None),
            available=getattr(virtual, "available", None),
            percent=getattr(virtual, "percent", None),
            swap_total=getattr(swap, "total", None) or None,
            swap_used=getattr(swap, "used", None) if swap else None,
            swap_free=getattr(swap, "free", None) if swap else None,
            swap_percent=getattr(swap, "percent", None) if swap else None,
        )
