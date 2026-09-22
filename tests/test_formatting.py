"""Tests for :mod:`app.utils.formatting`."""

from __future__ import annotations

import datetime as dt
import math

import pytest

from app.utils.formatting import (
    UNAVAILABLE,
    format_bytes,
    format_clock,
    format_count,
    format_duration,
    format_frequency,
    format_link_speed,
    format_percent,
    format_rate,
    format_temperature,
    format_text,
    format_timestamp,
)


class TestFormatBytes:
    def test_zero(self):
        assert format_bytes(0) == "0 B"

    def test_below_one_kilobyte_stays_in_bytes(self):
        assert format_bytes(1023) == "1023 B"

    def test_kilobytes(self):
        assert format_bytes(1024) == "1.0 KB"

    def test_fractional_value(self):
        assert format_bytes(1536) == "1.5 KB"

    def test_gigabytes(self):
        assert format_bytes(1024**3) == "1.0 GB"

    def test_terabytes(self):
        assert format_bytes(1024**4 * 2.5) == "2.5 TB"

    def test_negative_sign_is_preserved(self):
        assert format_bytes(-2048) == "-2.0 KB"

    def test_precision_is_configurable(self):
        assert format_bytes(1500, precision=2) == "1.46 KB"

    def test_rate_suffix(self):
        assert format_rate(1024) == "1.0 KB/s"

    @pytest.mark.parametrize("value", [None, "abc", float("nan"), float("inf")])
    def test_unavailable_values(self, value):
        assert format_bytes(value) == UNAVAILABLE
        assert format_rate(value) == UNAVAILABLE

    def test_booleans_are_not_treated_as_numbers(self):
        assert format_bytes(True) == UNAVAILABLE


class TestFormatPercent:
    def test_basic(self):
        assert format_percent(0) == "0.0%"

    def test_precision(self):
        assert format_percent(42.26) == "42.3%"
        assert format_percent(42.26, precision=0) == "42%"

    def test_unavailable(self):
        assert format_percent(None) == UNAVAILABLE


class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration(42) == "42s"

    def test_minutes_and_seconds(self):
        assert format_duration(63) == "1m 3s"

    def test_hours(self):
        assert format_duration(3725) == "1h 2m 5s"

    def test_days(self):
        assert format_duration(86_400 + 3_600 * 2 + 180) == "1d 2h 3m"

    def test_negative_clamps_to_zero(self):
        assert format_duration(-10) == "0s"

    def test_unavailable(self):
        assert format_duration(None) == UNAVAILABLE


class TestFormatFrequency:
    def test_gigahertz(self):
        assert format_frequency(3000) == "3.00 GHz"

    def test_megahertz(self):
        assert format_frequency(800) == "800 MHz"

    @pytest.mark.parametrize("value", [None, 0, -5])
    def test_unavailable(self, value):
        assert format_frequency(value) == UNAVAILABLE


class TestOtherFormatters:
    def test_temperature(self):
        assert format_temperature(58.0) == "58.0 °C"
        assert format_temperature(None) == UNAVAILABLE

    def test_link_speed(self):
        assert format_link_speed(1000) == "1.0 Gbps"
        assert format_link_speed(100) == "100 Mbps"
        assert format_link_speed(0) == UNAVAILABLE

    def test_count(self):
        assert format_count(1234) == "1,234"
        assert format_count(None) == UNAVAILABLE

    def test_text(self):
        assert format_text("hello") == "hello"
        assert format_text("   ") == UNAVAILABLE
        assert format_text(None) == UNAVAILABLE
        assert format_text(None, fallback="n/a") == "n/a"

    def test_timestamp(self):
        assert format_timestamp(0) != UNAVAILABLE
        assert format_timestamp(None) == UNAVAILABLE
        assert format_timestamp("nonsense") == UNAVAILABLE

    def test_clock(self):
        text = format_clock(dt.datetime(2024, 5, 6, 7, 8, 9))
        assert text == "07:08:09"
        assert len(format_clock()) == len("00:00:00")

    def test_nan_and_infinity_are_unavailable(self):
        assert format_percent(math.nan) == UNAVAILABLE
        assert format_temperature(math.inf) == UNAVAILABLE
