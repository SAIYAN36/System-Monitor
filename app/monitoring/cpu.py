"""Processor metrics: utilisation (total and per core), frequency and model."""

from __future__ import annotations

import logging
import platform
from typing import Optional

import psutil

from app.config import is_windows
from app.models.snapshot import CpuInfo, CpuStats
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)


class CpuCollector:
    """Reads CPU utilisation and the static description of the processor."""

    def __init__(self) -> None:
        self._info: Optional[CpuInfo] = None

    def prime(self) -> None:
        """Warm up psutil's percentage counters.

        ``psutil.cpu_percent()`` compares against the previous call, so the
        first value is always 0.0. Calling it once at start-up means the very
        first snapshot already shows a real number.
        """
        safe_call(psutil.cpu_percent, default=None, interval=None, context="cpu_percent.prime")
        safe_call(
            psutil.cpu_percent,
            default=None,
            interval=None,
            percpu=True,
            context="cpu_percent.percpu.prime",
        )

    # ------------------------------------------------------------------ static
    @property
    def info(self) -> CpuInfo:
        """Static CPU details, resolved once and cached."""
        if self._info is None:
            logical = safe_call(psutil.cpu_count, default=None, logical=True, context="cpu_count")
            physical = safe_call(psutil.cpu_count, default=None, logical=False, context="cpu_count")
            frequency = safe_call(psutil.cpu_freq, default=None, context="cpu_freq")
            self._info = CpuInfo(
                name=_processor_name(),
                physical_cores=physical,
                logical_cores=logical,
                max_frequency_mhz=getattr(frequency, "max", None),
                architecture=safe_call(platform.machine, default="", context="platform.machine"),
            )
        return self._info

    # -------------------------------------------------------------------- live
    def collect(self, temperature_c: Optional[float] = None) -> CpuStats:
        overall = safe_call(
            psutil.cpu_percent, default=None, interval=None, context="cpu_percent"
        )
        per_core = safe_call(
            psutil.cpu_percent,
            default=None,
            interval=None,
            percpu=True,
            context="cpu_percent.percpu",
        )
        frequency = safe_call(psutil.cpu_freq, default=None, context="cpu_freq")
        current_mhz = getattr(frequency, "current", None) if frequency else None
        if not current_mhz:
            # cpu_freq() is unavailable on some virtual machines; fall back to
            # the processor's nominal clock speed so the field stays populated.
            current_mhz = self.info.max_frequency_mhz

        load = safe_call(psutil.getloadavg, default=None, context="getloadavg")

        return CpuStats(
            percent=overall,
            per_core=tuple(per_core or ()),
            frequency_mhz=current_mhz,
            temperature_c=temperature_c,
            load_average=tuple(load) if load else None,
        )


def _processor_name() -> str:
    """Best available marketing name for the installed processor.

    ``platform.processor()`` returns a CPUID family string on Windows
    ("Intel64 Family 6 Model 158 Stepping 10"), so the registry value is
    preferred: it holds the real marketing name.
    """
    if is_windows():
        name = safe_call(_windows_processor_name, default=None, context="cpu.registry")
        if name:
            return name
    name = safe_call(platform.processor, default="", context="platform.processor") or ""
    return name.strip() or "Unknown CPU"


def _windows_processor_name() -> Optional[str]:
    """Read ``ProcessorNameString`` from the Windows registry."""
    import winreg  # noqa: PLC0415 - Windows-only import, kept local

    key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
        value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
    return str(value).strip() or None
