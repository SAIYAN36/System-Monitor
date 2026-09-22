"""CPU temperature reading.

Temperature is the least portable metric on Windows. There is no supported API
that a plain user process can call, so several sources are tried in order and
the first one that produces a value is remembered:

1. ``psutil.sensors_temperatures()`` (Linux, and some laptops via firmware).
2. LibreHardwareMonitor / OpenHardwareMonitor, if the user runs one of them -
   it publishes temperatures through its own WMI namespace.
3. The ACPI thermal zone that Windows exposes at ``root/wmi``.

Reading a temperature can take seconds (the ACPI query spawns a process), so
:class:`SensorReader` owns a dedicated daemon thread and :meth:`SensorReader.read`
only ever returns the last cached value. That keeps the UI polling loop fast no
matter how slow the underlying sensor is. When nothing works the UI shows
"Unavailable"; nothing here ever raises.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from typing import Callable, Dict, List, Optional, Tuple

from app.config import (
    DEFAULT_TEMPERATURE_INTERVAL_S,
    MAX_TEMPERATURE_INTERVAL_S,
    MIN_TEMPERATURE_INTERVAL_S,
    is_windows,
)
from app.monitoring.rate import monotonic_time
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)

#: Keys of psutil temperature sensors that represent the CPU.
_CPU_SENSOR_HINTS = ("coretemp", "k10temp", "zenpower", "cpu", "acpitz", "pch")

#: Vendor WMI namespaces published by hardware monitor tools, if installed.
_HARDWARE_MONITOR_NAMESPACES = (
    r"root\LibreHardwareMonitor",
    r"root\OpenHardwareMonitor",
)

#: How long to wait before retrying a provider that just failed. The ACPI query
#: is expensive, so a machine without usable sensors is probed rarely.
_FAILURE_COOLDOWN_SECONDS = 900.0

#: Upper bound for the PowerShell helper process.
_ACPI_TIMEOUT_SECONDS = 10.0


class SensorUnavailable(RuntimeError):
    """Raised by a provider when the machine simply cannot supply a reading."""


Provider = Tuple[str, Callable[[], Optional[float]]]


class SensorReader:
    """Keeps the last CPU temperature in memory, refreshed by a worker thread."""

    def __init__(
        self,
        enabled: bool = True,
        interval_seconds: float = DEFAULT_TEMPERATURE_INTERVAL_S,
        *,
        start_thread: bool = True,
        providers: Optional[List[Provider]] = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.interval_seconds = _clamp_interval(interval_seconds)
        self._lock = threading.Lock()
        self._value: Optional[float] = None
        self._provider: Optional[str] = None
        self._last_error: Optional[str] = None
        self._probed = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._providers = providers
        self._acpi_blocked_until = 0.0
        if start_thread and self.enabled:
            self.start()

    # -------------------------------------------------------------------- read
    def read(self) -> Optional[float]:
        """Last known temperature in degrees Celsius; never blocks."""
        with self._lock:
            return self._value

    @property
    def provider_name(self) -> Optional[str]:
        """Name of the provider that supplied the current reading, if any."""
        with self._lock:
            return self._provider

    @property
    def last_error(self) -> Optional[str]:
        """Why the last refresh produced no value (empty when it succeeded)."""
        with self._lock:
            return self._last_error

    @property
    def probed(self) -> bool:
        """True once at least one refresh attempt has finished."""
        with self._lock:
            return self._probed

    def status(self) -> Dict[str, object]:
        """Everything the Settings and CPU pages need, in one locked read."""
        with self._lock:
            return {
                "value": self._value,
                "provider": self._provider,
                "error": self._last_error,
                "probed": self._probed,
                "enabled": self.enabled,
                "interval": self.interval_seconds,
            }

    # ------------------------------------------------------------------ thread
    def start(self) -> None:
        """Begin refreshing in the background (no-op if already running)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="sensor-reader", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        """Stop the background refresh thread."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            if self.enabled:
                self.refresh_now()
            # Waiting on the event means stop() returns immediately.
            self._stop_event.wait(self.interval_seconds)

    # ----------------------------------------------------------------- control
    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        if not enabled:
            with self._lock:
                self._value = None
                self._provider = None
                self._last_error = None
        else:
            self.start()

    def set_interval(self, seconds: float) -> None:
        self.interval_seconds = _clamp_interval(seconds)

    def refresh_now(self) -> Optional[float]:
        """Perform one blocking refresh; used by the worker thread and tests."""
        if not self.enabled:
            # A disabled reader must not touch the sensor bus at all.
            return None
        value, provider, error = self._query()
        with self._lock:
            self._value = value
            self._provider = provider
            self._last_error = error
            self._probed = True
        return value

    def available_providers(self) -> List[str]:
        """Names of providers that look usable on this machine.

        This probes WMI, so it is meant for the Settings/System pages rather
        than the polling loop.
        """
        if self._providers is not None:
            # An injected chain is reported verbatim: it is already known good.
            return [name for name, _provider in self._providers]

        names: List[str] = []
        for name, provider in self._build_providers():
            if name == "ACPI thermal zone" and monotonic_time() < self._acpi_blocked_until:
                continue
            if name == "Hardware Monitor WMI" and _hardware_monitor_namespace() is None:
                continue
            if name == "psutil sensors" and not hasattr(psutil_module(), "sensors_temperatures"):
                continue
            names.append(name)
        return names

    # --------------------------------------------------------------- internal
    def _build_providers(self) -> List[Provider]:
        if self._providers is not None:
            return self._providers
        chain: List[Provider] = [("psutil sensors", _from_psutil_sensors)]
        if is_windows():
            chain.append(("Hardware Monitor WMI", _from_hardware_monitor))
            chain.append(("ACPI thermal zone", self._from_acpi_thermal_zone))
        return chain

    def _query(self) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Walk the provider chain, returning the first usable reading."""
        errors: List[str] = []
        for name, provider in self._build_providers():
            if name == "ACPI thermal zone" and monotonic_time() < self._acpi_blocked_until:
                continue
            try:
                value = provider()
            except Exception as exc:  # noqa: BLE001 - try the next provider
                errors.append(f"{name}: {exc}")
                logger.debug("Temperature provider %s failed: %r", name, exc)
                continue
            if value is not None and -50.0 < value < 200.0:
                return float(value), name, None
            errors.append(f"{name}: no reading")
        return None, None, ("; ".join(errors) if errors else "no supported sensor")

    def _from_acpi_thermal_zone(self) -> Optional[float]:
        """Query the ACPI thermal zone, respecting the failure cooldown."""
        value = _from_acpi_thermal_zone()
        if value is None:
            # Nothing to gain from re-spawning PowerShell on every refresh.
            self._acpi_blocked_until = monotonic_time() + _FAILURE_COOLDOWN_SECONDS
        return value


def psutil_module():
    """Import psutil lazily so this module stays import-cheap."""
    import psutil

    return psutil


def _clamp_interval(seconds: float) -> float:
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return float(DEFAULT_TEMPERATURE_INTERVAL_S)
    return float(min(max(value, MIN_TEMPERATURE_INTERVAL_S), MAX_TEMPERATURE_INTERVAL_S))


def _from_psutil_sensors() -> Optional[float]:
    """Read the CPU temperature through psutil's sensor support."""
    psutil = psutil_module()
    reader = getattr(psutil, "sensors_temperatures", None)
    if reader is None:
        # psutil only implements this on platforms with a sensor subsystem.
        raise SensorUnavailable("temperature sensors are not supported here")

    sensors = reader(fahrenheit=False)
    if not sensors:
        raise SensorUnavailable("the OS reported no temperature sensors")

    readings: List[float] = []
    for key, entries in sensors.items():
        if not entries:
            continue
        key_is_cpu = any(hint in key.lower() for hint in _CPU_SENSOR_HINTS)
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is None:
                continue
            label = (getattr(entry, "label", "") or "").lower()
            if not key_is_cpu and "package" not in label and "cpu" not in label:
                continue
            readings.append(float(current))
    if not readings:
        raise SensorUnavailable("no CPU sensor was found")
    # The package/die temperature is the hottest of the CPU sensors.
    return max(readings)


def _hardware_monitor_namespace() -> Optional[str]:
    """Find a running hardware-monitor WMI namespace, if one exists.

    Requires the optional ``wmi`` package; without it this returns ``None`` and
    the caller falls through to the ACPI provider.
    """
    if not is_windows():
        return None
    if safe_call(__import__, default=None, name="wmi") is None:
        return None

    for candidate in _HARDWARE_MONITOR_NAMESPACES:
        if safe_call(_query_wmi_temperature, candidate, default=None) is not None:
            return candidate
    return None


def _from_hardware_monitor() -> Optional[float]:
    """Read the CPU package temperature from LibreHardwareMonitor/OHM."""
    namespace = _hardware_monitor_namespace()
    if namespace is None:
        raise SensorUnavailable("no hardware monitor is running")
    value = _query_wmi_temperature(namespace)
    if value is None:
        raise SensorUnavailable("no CPU temperature sensor was exposed")
    return value


def _query_wmi_temperature(namespace: str) -> Optional[float]:
    """Read ``Sensor`` entries from a hardware-monitor WMI namespace."""
    import wmi  # noqa: PLC0415 - optional dependency

    client = wmi.WMI(namespace=namespace)
    readings: List[float] = []
    for sensor in client.Sensor():
        if (getattr(sensor, "SensorType", "") or "").lower() != "temperature":
            continue
        name = (getattr(sensor, "Name", "") or "").lower()
        if "cpu" not in name and "package" not in name and "core" not in name:
            continue
        value = getattr(sensor, "Value", None)
        if value is None:
            continue
        readings.append(float(value))
    return max(readings) if readings else None


def _from_acpi_thermal_zone() -> Optional[float]:
    """Read the ACPI thermal zone temperature via PowerShell.

    ``MSAcpi_ThermalZoneTemperature`` reports tenths of a Kelvin. This only
    works when the firmware publishes the zone and the process may read
    ``root\\wmi`` - frequently it does not, which is why it is last in line.
    """
    if not is_windows():
        return None

    command = (
        "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature"
        " -ErrorAction SilentlyContinue | Select-Object -First 1"
        " -ExpandProperty CurrentTemperature"
    )
    # Keep a console window from flashing up on every refresh.
    creation_flags = 0x08000000 if sys.platform == "win32" else 0
    for executable in ("powershell", "pwsh"):
        try:
            completed = subprocess.run(
                [executable, "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=_ACPI_TIMEOUT_SECONDS,
                creationflags=creation_flags,
            )
        except FileNotFoundError:
            continue
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug("ACPI temperature query could not run: %r", exc)
            return None

        output = (completed.stdout or "").strip()
        if not output:
            continue
        try:
            tenths_kelvin = float(output.splitlines()[0].strip())
        except (ValueError, IndexError):
            continue
        if tenths_kelvin <= 0:
            continue
        return tenths_kelvin / 10.0 - 273.15
    return None
