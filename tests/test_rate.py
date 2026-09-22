"""Tests for :mod:`app.monitoring.rate`."""

from __future__ import annotations

from app.monitoring.rate import RateTracker, TTLCache


class TestRateTracker:
    def test_first_sample_has_no_rate(self):
        tracker = RateTracker()
        assert tracker.update("nic", 1_000, now=100.0) is None

    def test_second_sample_produces_a_rate(self):
        tracker = RateTracker()
        tracker.update("nic", 1_000, now=100.0)
        # 2048 bytes in 2 seconds -> 1024 bytes/second.
        assert tracker.update("nic", 3_048, now=102.0) == 1024.0

    def test_prime_does_not_produce_a_rate(self):
        tracker = RateTracker()
        tracker.prime("nic", 500, now=10.0)
        assert tracker.update("nic", 1_500, now=11.0) == 1000.0

    def test_counter_reset_is_not_reported_as_a_spike(self):
        tracker = RateTracker()
        tracker.update("nic", 5_000, now=1.0)
        assert tracker.update("nic", 10, now=2.0) is None

    def test_zero_elapsed_time_is_ignored(self):
        tracker = RateTracker()
        tracker.update("nic", 100, now=5.0)
        assert tracker.update("nic", 200, now=5.0) is None

    def test_keys_are_tracked_independently(self):
        tracker = RateTracker()
        tracker.update("a", 0, now=0.0)
        tracker.update("b", 0, now=0.0)
        assert tracker.update("a", 100, now=1.0) == 100.0
        assert tracker.update("b", 50, now=1.0) == 50.0

    def test_retain_forgets_missing_devices(self):
        tracker = RateTracker()
        tracker.update("keep", 1, now=0.0)
        tracker.update("drop", 1, now=0.0)
        tracker.retain(["keep"])
        # "drop" starts over, so its next update has no previous sample.
        assert tracker.update("drop", 10, now=1.0) is None
        assert tracker.update("keep", 11, now=1.0) == 10.0

    def test_drop_and_clear(self):
        tracker = RateTracker()
        tracker.update("a", 1, now=0.0)
        tracker.drop("a")
        assert tracker.update("a", 5, now=1.0) is None
        tracker.clear()
        tracker.update("b", 1, now=0.0)
        assert tracker.update("b", 2, now=1.0) == 1.0


class TestTTLCache:
    def test_value_is_reused_before_expiry(self):
        calls = []

        def factory():
            calls.append(1)
            return len(calls)

        cache = TTLCache(5.0)
        assert cache.get(factory, now=100.0) == 1
        assert cache.get(factory, now=101.0) == 1
        assert len(calls) == 1

    def test_value_is_rebuilt_after_expiry(self):
        calls = []

        def factory():
            calls.append(1)
            return len(calls)

        cache = TTLCache(5.0)
        assert cache.get(factory, now=100.0) == 1
        assert cache.get(factory, now=106.0) == 2
        assert len(calls) == 2

    def test_invalidate_forces_a_rebuild(self):
        calls = []

        def factory():
            calls.append(1)
            return len(calls)

        cache = TTLCache(60.0)
        cache.get(factory, now=0.0)
        cache.invalidate()
        cache.get(factory, now=0.5)
        assert len(calls) == 2

    def test_ttl_is_exposed(self):
        assert TTLCache(2.5).ttl == 2.5
