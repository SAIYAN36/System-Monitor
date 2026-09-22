"""Network metrics: adapters, addresses, throughput and totals."""

from __future__ import annotations

import logging
import socket
from typing import Dict, List, Optional, Tuple

import psutil

from app.models.snapshot import NetworkInterface, NetworkStats
from app.monitoring.rate import RateTracker, TTLCache
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)

#: Adapter metadata (names, addresses, link state) changes rarely; cache it.
_ADAPTER_TTL_SECONDS = 5.0

#: Suffixes used by Windows pseudo-adapters that carry no real traffic.
_VIRTUAL_HINTS = ("loopback", "isatap", "teredo", "6to4", "vethernet (", "pseudo")


class NetworkCollector:
    """Aggregates per-adapter counters into system-wide throughput."""

    def __init__(self) -> None:
        self._rates = RateTracker()
        self._adapters = TTLCache(_ADAPTER_TTL_SECONDS)

    def collect(self, now: Optional[float] = None) -> NetworkStats:
        counters = safe_call(
            psutil.net_io_counters,
            default=None,
            pernic=True,
            context="net_io_counters",
        )
        if not counters:
            return NetworkStats()

        details = self._adapters.get(self._adapter_details, now=now)

        interfaces: List[NetworkInterface] = []
        total_sent = total_recv = 0
        upload_rate: Optional[float] = None
        download_rate: Optional[float] = None
        primary_ipv4: Optional[str] = None

        for name, counter in counters.items():
            info = details.get(name)
            is_loopback = _is_loopback(name, info)
            sent = int(getattr(counter, "bytes_sent", 0) or 0)
            recv = int(getattr(counter, "bytes_recv", 0) or 0)

            # Rate for this adapter, then add it to the system-wide totals.
            nic_upload = self._rates.update(name, sent, now)
            nic_download = self._rates.update(f"{name}#recv", recv, now)

            if not is_loopback:
                total_sent += sent
                total_recv += recv
                upload_rate = _add(upload_rate, nic_upload)
                download_rate = _add(download_rate, nic_download)
                if primary_ipv4 is None and info and info["ipv4"] and info["is_up"]:
                    primary_ipv4 = info["ipv4"]

            interfaces.append(
                NetworkInterface(
                    name=name,
                    is_up=bool(info["is_up"]) if info else False,
                    speed_mbps=info["speed_mbps"] if info else None,
                    ipv4=info["ipv4"] if info else None,
                    ipv6=info["ipv6"] if info else None,
                    mac=info["mac"] if info else None,
                    mtu=info["mtu"] if info else None,
                    bytes_sent=sent,
                    bytes_recv=recv,
                    upload_rate=nic_upload,
                    download_rate=nic_download,
                    is_loopback=is_loopback,
                )
            )

        # Drop cached counters for adapters that have been disconnected.
        self._rates.retain(list(counters) + [f"{name}#recv" for name in counters])

        interfaces.sort(key=lambda nic: (nic.is_loopback, not nic.is_up, nic.name.lower()))

        return NetworkStats(
            interfaces=tuple(interfaces),
            total_sent=total_sent,
            total_recv=total_recv,
            upload_rate=upload_rate,
            download_rate=download_rate,
            primary_ipv4=primary_ipv4,
        )

    # ------------------------------------------------------------------ static
    def adapter_names(self) -> Tuple[str, ...]:
        """Names of every adapter psutil can see."""
        addresses = safe_call(
            psutil.net_if_addrs, default={}, context="net_if_addrs"
        )
        return tuple(sorted(addresses)) if addresses else ()

    def invalidate(self) -> None:
        self._adapters.invalidate()

    # ----------------------------------------------------------------- private
    @staticmethod
    def _adapter_details() -> Dict[str, Dict[str, object]]:
        """Combine address and link-state queries into one lookup table."""
        details: Dict[str, Dict[str, object]] = {}
        addresses = safe_call(psutil.net_if_addrs, default={}, context="net_if_addrs") or {}
        for name, entries in addresses.items():
            record: Dict[str, object] = {
                "ipv4": None,
                "ipv6": None,
                "mac": None,
                "mtu": None,
                "is_up": False,
                "speed_mbps": None,
            }
            for entry in entries:
                family = getattr(entry, "family", None)
                address = getattr(entry, "address", "") or ""
                if family == psutil.AF_LINK:
                    record["mac"] = address
                elif family == socket.AF_INET:
                    record["ipv4"] = address
                elif family == socket.AF_INET6:
                    # Strip the IPv6 scope/zone suffix for readability.
                    record["ipv6"] = address.split("%")[0]
            details[name] = record

        stats = safe_call(psutil.net_if_stats, default={}, context="net_if_stats") or {}
        for name, stat in stats.items():
            record = details.setdefault(
                name,
                {"ipv4": None, "ipv6": None, "mac": None, "mtu": None, "is_up": False,
                 "speed_mbps": None},
            )
            record["is_up"] = bool(getattr(stat, "isup", False))
            speed = getattr(stat, "speed", None)
            record["speed_mbps"] = float(speed) if speed else None
            record["mtu"] = getattr(stat, "mtu", None) or record.get("mtu")
        return details


def _is_loopback(name: str, info: Optional[Dict[str, object]]) -> bool:
    """True for loopback/tunnel adapters that should not count as traffic."""
    lowered = name.lower()
    if any(hint in lowered for hint in _VIRTUAL_HINTS):
        return True
    if info and info.get("ipv4") in ("127.0.0.1",):
        return True
    return False


def _add(total: Optional[float], value: Optional[float]) -> Optional[float]:
    """Add a sample to a running total, ignoring missing samples."""
    if value is None:
        return total
    return (total or 0.0) + value
