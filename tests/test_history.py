"""Tests for :mod:`app.services.history`."""

from __future__ import annotations

from app.models.snapshot import CpuStats, DiskIO, DiskStats, MemoryStats, NetworkStats, Snapshot
from app.services.history import SERIES_NAMES, MetricHistory, MetricsUpdate


def make_snapshot(
    *,
    timestamp: float = 1_000.0,
    cpu: float | None = 10.0,
    memory: float | None = 40.0,
    upload: float | None = 100.0,
    download: float | None = 200.0,
    read: float | None = 300.0,
    write: float | None = 400.0,
    temperature: float | None = 50.0,
    processes: tuple = (),
) -> Snapshot:
    return Snapshot(
        timestamp=timestamp,
        cpu=CpuStats(percent=cpu, per_core=(cpu or 0.0,), temperature_c=temperature),
        memory=MemoryStats(total=8, used=4, percent=memory),
        disk=DiskStats(io=DiskIO(read_rate=read, write_rate=write)),
        network=NetworkStats(upload_rate=upload, download_rate=download),
        processes=processes,
    )


def test_series_names_are_all_present():
    history = MetricHistory(10)
    assert set(history.bundle()) == set(SERIES_NAMES)


def test_append_returns_an_update_bundle():
    history = MetricHistory(10)
    snapshot = make_snapshot()
    update = history.append_snapshot(snapshot)
    assert isinstance(update, MetricsUpdate)
    assert update.snapshot is snapshot
    assert update.values("cpu") == (10.0,)


def test_series_values_are_tuples_of_floats():
    history = MetricHistory(3)
    for index in range(5):
        history.append_snapshot(make_snapshot(cpu=float(index)))
    values = history.series("cpu")
    assert isinstance(values, tuple)
    assert values == (2.0, 3.0, 4.0)


def test_all_recorded_series():
    history = MetricHistory(5)
    history.append_snapshot(make_snapshot())
    assert history.series("cpu") == (10.0,)
    assert history.series("memory") == (40.0,)
    assert history.series("net_upload") == (100.0,)
    assert history.series("net_download") == (200.0,)
    assert history.series("disk_read") == (300.0,)
    assert history.series("disk_write") == (400.0,)
    assert history.series("cpu_temp") == (50.0,)


def test_missing_values_are_recorded_as_zero():
    history = MetricHistory(5)
    history.append_snapshot(
        make_snapshot(cpu=None, memory=None, upload=None, download=None, temperature=None)
    )
    assert history.series("cpu") == (0.0,)
    assert history.series("memory") == (0.0,)
    assert history.series("net_upload") == (0.0,)
    assert history.series("cpu_temp") == (0.0,)


def test_missing_disk_io_is_tolerated():
    history = MetricHistory(5)
    history.append_snapshot(Snapshot(timestamp=1.0, disk=DiskStats(io=None)))
    assert history.series("disk_read") == (0.0,)


def test_history_is_bounded():
    history = MetricHistory(4)
    for index in range(100):
        history.append_snapshot(make_snapshot(cpu=float(index)))
    assert len(history.series("cpu")) == 4
    assert history.series("cpu") == (96.0, 97.0, 98.0, 99.0)


def test_set_capacity_resizes_buffers():
    history = MetricHistory(10)
    for index in range(10):
        history.append_snapshot(make_snapshot(cpu=float(index)))
    history.set_capacity(3)
    assert history.capacity == 3
    assert history.series("cpu") == (7.0, 8.0, 9.0)


def test_clear_empties_every_series():
    history = MetricHistory(5)
    history.append_snapshot(make_snapshot())
    history.clear()
    assert all(values == () for values in history.bundle().values())


def test_stats_report_average_and_peak():
    history = MetricHistory(5)
    for value in (10.0, 20.0, 30.0):
        history.append_snapshot(make_snapshot(cpu=value))
    average, peak = history.stats("cpu")
    assert average == 20.0
    assert peak == 30.0


def test_latest_of_unknown_series_is_none():
    history = MetricHistory(5)
    assert history.latest("nope") is None
    assert history.series("nope") == ()
