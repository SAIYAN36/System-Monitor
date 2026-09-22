"""Human-readable formatting helpers.

Every formatter tolerates ``None`` (and non-numeric input) by returning
:data:`UNAVAILABLE`, so a page can render a metric that this machine does not
expose without any special-case branching.
"""

from __future__ import annotations

import datetime as _dt
import math
from typing import Any, Optional

#: Text shown whenever a metric is not available on this machine.
UNAVAILABLE = "Unavailable"

_BYTE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB", "EB")


def _as_float(value: Any) -> Optional[float]:
    """Return ``value`` as a finite float, or ``None`` when that is impossible."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def format_bytes(value: Any, *, precision: int = 1, per_second: bool = False) -> str:
    """Format a byte count using binary (1024-based) units, e.g. ``1.4 GB``."""
    number = _as_float(value)
    if number is None:
        return UNAVAILABLE

    sign = "-" if number < 0 else ""
    number = abs(number)
    index = 0
    while number >= 1024.0 and index < len(_BYTE_UNITS) - 1:
        number /= 1024.0
        index += 1

    if index == 0:
        text = f"{sign}{int(round(number))} {_BYTE_UNITS[index]}"
    else:
        text = f"{sign}{number:.{precision}f} {_BYTE_UNITS[index]}"
    return f"{text}/s" if per_second else text


def format_rate(bytes_per_second: Any, *, precision: int = 1) -> str:
    """Format a transfer rate, e.g. ``2.5 MB/s``."""
    return format_bytes(bytes_per_second, precision=precision, per_second=True)


def format_percent(value: Any, *, precision: int = 1) -> str:
    """Format a 0-100 value, e.g. ``37.4%``."""
    number = _as_float(value)
    if number is None:
        return UNAVAILABLE
    return f"{number:.{precision}f}%"


def format_duration(seconds: Any) -> str:
    """Format a span of seconds as ``2d 4h 11m`` / ``11m 3s`` / ``42s``."""
    number = _as_float(seconds)
    if number is None:
        return UNAVAILABLE
    total = int(max(0, number))
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_frequency(mhz: Any, *, precision: int = 2) -> str:
    """Format a clock speed given in MHz, e.g. ``3.60 GHz``."""
    number = _as_float(mhz)
    if number is None or number <= 0:
        return UNAVAILABLE
    if number >= 1000.0:
        return f"{number / 1000.0:.{precision}f} GHz"
    return f"{number:.0f} MHz"


def format_temperature(celsius: Any, *, precision: int = 1) -> str:
    """Format a temperature in degrees Celsius."""
    number = _as_float(celsius)
    if number is None:
        return UNAVAILABLE
    return f"{number:.{precision}f} °C"


def format_link_speed(mbps: Any) -> str:
    """Format a NIC link speed given in megabits per second."""
    number = _as_float(mbps)
    if number is None or number <= 0:
        return UNAVAILABLE
    if number >= 1000.0:
        return f"{number / 1000.0:.1f} Gbps"
    return f"{number:.0f} Mbps"


def format_count(value: Any) -> str:
    """Format an integer with thousands separators."""
    number = _as_float(value)
    if number is None:
        return UNAVAILABLE
    return f"{int(round(number)):,}"


def format_text(value: Any, *, fallback: str = UNAVAILABLE) -> str:
    """Return ``str(value)`` unless it is empty/None, then the fallback."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def format_timestamp(value: Any) -> str:
    """Format a UNIX timestamp as a local date and time."""
    number = _as_float(value)
    if number is None:
        return UNAVAILABLE
    try:
        return _dt.datetime.fromtimestamp(number).strftime("%Y-%m-%d %H:%M:%S")
    except (OverflowError, OSError, ValueError):
        return UNAVAILABLE


def format_clock(value: Optional[_dt.datetime] = None, *, with_seconds: bool = True) -> str:
    """Format a local time for the header clock."""
    moment = value or _dt.datetime.now()
    fmt = "%H:%M:%S" if with_seconds else "%H:%M"
    return moment.strftime(fmt)
