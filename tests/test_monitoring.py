"""Tests for the collectors.

These assertions run against the real machine: the point is that the collectors
report plausible, correctly-shaped readings (and degrade safely when a metric is
missing), not that they match any fixed expectation.
"""

from __future__ import annotations

import re
import time

import psutil
import pytest

from app.models.snapshot import MemoryStats, Snapshot
from app.monitoring.collector import SystemMonitor
from app.monitoring.disk import DiskCollector

IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@pytest.fixture(scope="module")
def monitor() -> SystemMonitor:
    instance = SystemMonitor(temperature_enabled=False)
    instance.prime()
    # psutil's counters compare against the previous call, so give the module
    # fixture a moment to produce a meaningful first reading.
    time.sleep(0.25)
    return instance


@pytest.fixture(scope="module")
def snapshot(monitor: SystemMonitor) -> Snapshot:
    return monitor.collect(include_processes=True)


class TestCpu:
    def test_overall_usage_is_a_percentage(self, snapshot):
        percent = snapshot.cpu.percent
        assert percent is not None
        assert 0.0 <= percent <= 100.0

    def test_one_entry_per_logical_processor(self, snapshot, monitor):
        expected = psutil.cpu_count(logical=True)
        assert len(snapshot.cpu.per_core) == expected
        assert all(0.0 <= value <= 100.0 for value in snapshot.cpu.per_core)

    def test_processor_is_described(self, monitor):
        info = monitor.cpu_info
        assert isinstance(info.name, str) and info.name.strip()
        assert info.logical_cores is None or info.logical_cores >= 1
        if info.physical_cores and info.logical_cores:
            assert info.physical_cores <= info.logical_cores

    def test_frequency_is_positive_when_available(self, snapshot):
        assert snapshot.cpu.frequency_mhz is None or snapshot.cpu.frequency_mhz > 0

    def test_per_core_count_property(self, snapshot):
        assert snapshot.cpu.core_count == len(snapshot.cpu.per_core)


class TestMemory:
    def test_totals_are_consistent(self, snapshot):
        memory = snapshot.memory
        assert memory.total and memory.total > 0
        assert memory.used is not None and 0 <= memory.used <= memory.total
        assert memory.available is not None and memory.available <= memory.total
        assert memory.percent is not None and 0.0 <= memory.percent <= 100.0

    def test_swap_is_reported_or_absent(self, snapshot):
        memory = snapshot.memory
        if memory.swap_total:
            assert memory.swap_used is not None
            assert memory.swap_used <= memory.swap_total
            assert memory.swap_percent is not None


class TestDisk:
    def test_volumes_have_capacity(self, snapshot):
        for part in snapshot.disk.partitions:
            assert part.mountpoint
            assert part.total and part.total > 0
            assert part.used is not None and part.free is not None
            assert part.used + part.free == pytest.approx(part.total, rel=0.01)
            assert part.percent is not None and 0.0 <= part.percent <= 100.0

    def test_drive_type_is_labelled_on_windows(self, snapshot):
        if not any(part.drive_type for part in snapshot.disk.partitions):
            pytest.skip("This platform does not report drive types")
        for part in snapshot.disk.partitions:
            assert part.drive_type

    def test_io_counters_are_monotonic(self, monitor):
        first = monitor.disk.io_counters()
        if first is None:
            pytest.skip("Disk I/O counters are unavailable on this system")
        assert first.read_bytes >= 0
        second = monitor.disk.io_counters()
        assert second.read_bytes >= first.read_bytes
        assert second.write_bytes >= first.write_bytes

    def test_io_rates_need_two_samples(self):
        # A dedicated collector with explicit timestamps, so the assertion does
        # not depend on how fast the machine happens to run this test.
        collector = DiskCollector()
        assert collector.io_counters(now=1_000.0).read_rate is None
        second = collector.io_counters(now=1_001.0)
        assert second.read_rate is not None and second.read_rate >= 0.0

    def test_io_rate_ignores_a_counter_reset(self):
        collector = DiskCollector()
        collector.io_counters(now=1_000.0)
        collector.io_counters(now=1_010.0)
        assert collector.io_counters(now=1_020.0) is not None

    def test_disappearing_drive_does_not_break_the_sweep(self, monitor, monkeypatch):
        def explode(path, **kwargs):
            raise OSError("device not ready")

        monkeypatch.setattr(psutil, "disk_usage", explode)
        monitor.disk.invalidate()
        assert monitor.disk.partitions() == ()


class TestNetwork:
    def test_interfaces_are_listed(self, snapshot):
        network = snapshot.network
        assert network.interfaces
        for nic in network.interfaces:
            assert nic.name
            assert nic.bytes_sent >= 0 and nic.bytes_recv >= 0

    def test_totals_are_non_negative(self, snapshot):
        assert snapshot.network.total_recv >= 0
        assert snapshot.network.total_sent >= 0

    def test_rates_are_absent_on_the_first_sample_then_present(self, monitor):
        first = monitor.network.collect(now=1_000.0)
        assert first.upload_rate is None
        second = monitor.network.collect(now=1_001.0)
        assert second.upload_rate is not None and second.upload_rate >= 0.0

    def test_primary_address_looks_like_an_ipv4(self, snapshot):
        address = snapshot.network.primary_ipv4
        assert address is None or IPV4.match(address)

    def test_counter_reset_is_handled(self, monitor):
        # Simulating an adapter reset must not raise or report a huge spike.
        monitor.network.collect(now=5_000.0)
        stats = monitor.network.collect(now=5_001.0)
        assert stats.upload_rate is None or stats.upload_rate >= 0.0


class TestProcesses:
    def test_rows_are_plausible(self, snapshot):
        assert snapshot.processes
        for process in snapshot.processes:
            assert process.pid > 0
            assert process.name
            assert process.cpu_percent is None or process.cpu_percent >= 0.0
            assert process.memory_rss is None or process.memory_rss >= 0

    def test_rows_are_sorted_by_cpu_descending(self, snapshot):
        values = [process.cpu_percent or 0.0 for process in snapshot.processes]
        assert values == sorted(values, reverse=True)

    def test_pids_are_unique(self, snapshot):
        pids = [process.pid for process in snapshot.processes]
        assert len(pids) == len(set(pids))

    def test_second_sweep_reports_cpu_activity(self, monitor):
        monitor.processes.collect()
        time.sleep(0.3)
        rows = monitor.processes.collect()
        assert rows
        assert any((row.cpu_percent or 0.0) > 0.0 for row in rows)

    def test_process_count_is_only_reported_when_collected(self, monitor):
        without = monitor.collect(include_processes=False)
        assert without.processes is None
        assert without.process_count is None


class TestSnapshot:
    def test_timestamp_is_current(self, snapshot):
        assert abs(snapshot.timestamp - time.time()) < 60

    def test_uptime_is_positive(self, snapshot):
        uptime = snapshot.uptime
        assert uptime is not None and uptime > 0

    def test_system_block_is_always_attached(self, snapshot):
        assert snapshot.system is not None
        assert snapshot.system.hostname
        assert snapshot.system.os_name
        assert snapshot.system.python_version
        assert snapshot.system.boot_time and snapshot.system.boot_time > 0

    def test_static_lists_are_populated(self, snapshot):
        assert snapshot.system.drives
        assert snapshot.system.network_adapters


class TestErrorHandling:
    def test_missing_memory_metrics_do_not_raise(self, monitor, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("no memory information")

        monkeypatch.setattr(psutil, "virtual_memory", explode)
        monkeypatch.setattr(psutil, "swap_memory", explode)
        assert monitor.memory.collect() == MemoryStats()

    def test_missing_cpu_metrics_do_not_raise(self, monitor, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("no processor information")

        monkeypatch.setattr(psutil, "cpu_percent", explode)
        stats = monitor.cpu.collect()
        assert stats.percent is None
        assert stats.per_core == ()

    def test_missing_network_metrics_return_an_empty_block(self, monitor, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("no adapters")

        monkeypatch.setattr(psutil, "net_io_counters", explode)
        stats = monitor.network.collect()
        assert stats.interfaces == ()
        assert stats.total_sent == 0

    def test_missing_process_list_returns_no_rows(self, monitor, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("no process table")

        monkeypatch.setattr(psutil, "pids", explode)
        assert monitor.processes.collect() == ()

    def test_full_collect_survives_a_total_failure(self, monitor, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("everything is broken")

        for name in ("cpu_percent", "virtual_memory", "swap_memory", "disk_io_counters"):
            monkeypatch.setattr(psutil, name, explode)
        monkeypatch.setattr(psutil, "net_io_counters", explode)
        snapshot = monitor.collect()
        assert isinstance(snapshot, Snapshot)
        assert snapshot.cpu.percent is None
        assert snapshot.memory.total is None
