"""Tests for :mod:`app.monitoring.sensors`.

The provider chain is injected so these tests never depend on the machine
actually having a readable temperature sensor.
"""

from __future__ import annotations

import time

import pytest

from app.config import DEFAULT_TEMPERATURE_INTERVAL_S
from app.monitoring.sensors import SensorReader, SensorUnavailable


def reader(providers, *, enabled=True) -> SensorReader:
    return SensorReader(
        enabled=enabled, interval_seconds=30, start_thread=False, providers=providers
    )


def test_first_working_provider_wins():
    sensor = reader([("good", lambda: 55.5), ("never", lambda: 99.0)])
    assert sensor.refresh_now() == 55.5
    assert sensor.provider_name == "good"
    assert sensor.last_error is None


def test_a_failing_provider_falls_through_to_the_next():
    def broken():
        raise RuntimeError("sensor bus error")

    sensor = reader([("broken", broken), ("good", lambda: 42.0)])
    assert sensor.refresh_now() == 42.0
    assert sensor.provider_name == "good"
    assert sensor.last_error is None


def test_all_providers_failing_reports_a_reason():
    def broken():
        raise SensorUnavailable("no sensor")

    sensor = reader([("a", broken), ("b", broken)])
    assert sensor.refresh_now() is None
    assert sensor.provider_name is None
    assert "a: no sensor" in sensor.last_error
    assert "b: no sensor" in sensor.last_error


def test_providers_returning_nothing_are_recorded():
    sensor = reader([("empty", lambda: None)])
    assert sensor.refresh_now() is None
    assert "no reading" in sensor.last_error


@pytest.mark.parametrize("bad", [-500.0, 400.0, 273.15 + 1000])
def test_implausible_readings_are_rejected(bad):
    sensor = reader([("silly", lambda: bad), ("good", lambda: 30.0)])
    assert sensor.refresh_now() == 30.0
    assert sensor.provider_name == "good"


def test_disabled_reader_never_queries():
    calls = []

    def provider():
        calls.append(1)
        return 50.0

    sensor = reader([("counting", provider)], enabled=False)
    assert sensor.read() is None
    assert sensor.refresh_now() is None
    assert calls == []


def test_enabling_and_disabling_the_reader():
    sensor = reader([("good", lambda: 44.0)], enabled=False)
    assert sensor.read() is None

    sensor.set_enabled(True)
    sensor.refresh_now()
    assert sensor.read() == 44.0

    sensor.set_enabled(False)
    assert sensor.read() is None
    assert sensor.provider_name is None


def test_read_does_not_block_before_a_probe():
    calls = []

    def slow():
        calls.append(1)
        time.sleep(0.2)
        return 60.0

    sensor = reader([("slow", slow)])
    started = time.perf_counter()
    assert sensor.read() is None
    assert time.perf_counter() - started < 0.05
    assert calls == []


def test_probed_flag_reflects_a_completed_refresh():
    sensor = reader([("good", lambda: 20.0)])
    assert sensor.probed is False
    sensor.refresh_now()
    assert sensor.probed is True


def test_background_thread_refreshes_and_stops():
    sensor = SensorReader(
        enabled=True, interval_seconds=5, start_thread=False, providers=[("good", lambda: 61.0)]
    )
    assert sensor._thread is None  # noqa: SLF001 - lifecycle assertion
    sensor.start()
    try:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and not sensor.probed:
            time.sleep(0.02)
        assert sensor.probed
        assert sensor.read() == 61.0
    finally:
        sensor.stop()
    assert sensor._thread is None  # noqa: SLF001


def test_interval_is_clamped():
    assert reader([("x", lambda: 1.0)]).interval_seconds == 30
    sensor = reader([("x", lambda: 1.0)])
    sensor.set_interval(0.001)
    assert sensor.interval_seconds >= 5
    sensor.set_interval(10_000)
    assert sensor.interval_seconds <= 300
    assert DEFAULT_TEMPERATURE_INTERVAL_S == 30


def test_status_snapshot_is_complete():
    sensor = reader([("good", lambda: 33.0)])
    sensor.refresh_now()
    status = sensor.status()
    assert status["value"] == 33.0
    assert status["provider"] == "good"
    assert status["probed"] is True
    assert status["enabled"] is True
    assert status["interval"] == 30


def test_available_providers_uses_the_injected_chain():
    # The injected chain bypasses the WMI probe, so this stays fast and
    # deterministic while still exercising the label list.
    sensor = reader([("psutil sensors", lambda: 30.0)])
    assert sensor.available_providers() == ["psutil sensors"]
