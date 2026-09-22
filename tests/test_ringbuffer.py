"""Tests for :mod:`app.utils.ringbuffer`."""

from __future__ import annotations

import pytest

from app.utils.ringbuffer import RingBuffer


def test_starts_empty():
    buffer = RingBuffer(5)
    assert len(buffer) == 0
    assert buffer.values() == []
    assert buffer.latest() is None
    assert buffer.average() is None
    assert not buffer


def test_keeps_insertion_order():
    buffer = RingBuffer(5)
    buffer.extend([1, 2, 3])
    assert buffer.values() == [1.0, 2.0, 3.0]


def test_oldest_sample_is_dropped_when_full():
    buffer = RingBuffer(3)
    buffer.extend([1, 2, 3, 4, 5])
    assert buffer.values() == [3.0, 4.0, 5.0]
    assert len(buffer) == 3


def test_memory_stays_bounded_over_many_appends():
    buffer = RingBuffer(10)
    for value in range(5_000):
        buffer.append(value)
    assert len(buffer) == 10
    assert buffer.values() == [float(v) for v in range(4_990, 5_000)]


def test_statistics():
    buffer = RingBuffer(4)
    buffer.extend([2, 4, 6])
    assert buffer.latest() == 6.0
    assert buffer.average() == 4.0
    assert buffer.peak() == 6.0
    assert buffer.minimum() == 2.0


def test_is_full():
    buffer = RingBuffer(2)
    buffer.append(1)
    assert not buffer.is_full
    buffer.append(2)
    assert buffer.is_full


def test_resize_smaller_keeps_most_recent():
    buffer = RingBuffer(5)
    buffer.extend(range(5))
    buffer.resize(2)
    assert buffer.values() == [3.0, 4.0]
    assert buffer.capacity == 2


def test_resize_larger_keeps_everything():
    buffer = RingBuffer(2)
    buffer.extend([1, 2])
    buffer.resize(10)
    assert buffer.values() == [1.0, 2.0]
    assert len(buffer) == 2


def test_clear():
    buffer = RingBuffer(3)
    buffer.extend([1, 2, 3])
    buffer.clear()
    assert buffer.values() == []


def test_non_numeric_samples_are_ignored():
    buffer = RingBuffer(3)
    buffer.append("not a number")
    buffer.append(None)
    buffer.append(7)
    assert buffer.values() == [7.0]


def test_invalid_capacity_rejected():
    with pytest.raises(ValueError):
        RingBuffer(0)
    with pytest.raises(ValueError):
        RingBuffer(5).resize(0)


def test_iteration():
    buffer = RingBuffer(3)
    buffer.extend([1, 2])
    assert list(buffer) == [1.0, 2.0]
