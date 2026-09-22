"""Tests for :mod:`app.monitoring.processes`.

Termination is exercised against a throwaway child process that this test
starts itself, so nothing belonging to the machine is ever touched.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import psutil
import pytest

from app.monitoring.processes import (
    CRITICAL_NAMES,
    ProcessCollector,
    ProcessTerminationError,
)


@pytest.fixture
def collector() -> ProcessCollector:
    return ProcessCollector()


class TestCriticalClassification:
    @pytest.mark.parametrize("name", ["lsass.exe", "LSASS.EXE", " csrss.exe ", "System"])
    def test_known_system_processes_are_critical(self, collector, name):
        assert collector.is_critical(name) is True

    @pytest.mark.parametrize("name", ["notepad.exe", "chrome", "python.exe", ""])
    def test_ordinary_processes_are_not_critical(self, collector, name):
        assert collector.is_critical(name) is False

    def test_list_is_not_empty(self):
        assert CRITICAL_NAMES


class TestSafetyGuards:
    def test_pid_zero_is_refused(self, collector):
        with pytest.raises(ProcessTerminationError):
            collector.terminate(0)

    def test_negative_pid_is_refused(self, collector):
        with pytest.raises(ProcessTerminationError):
            collector.terminate(-1)

    def test_missing_process_reports_a_readable_error(self, collector, monkeypatch):
        def missing(pid):
            raise psutil.NoSuchProcess(pid)

        monkeypatch.setattr(psutil, "Process", missing)
        with pytest.raises(ProcessTerminationError, match="no longer running"):
            collector.terminate(4242)

    def test_access_denied_is_explained(self, collector):
        class Denied:
            pid = 1
            name = "protected.exe"

            def terminate(self):
                raise psutil.AccessDenied(1)

            def kill(self):
                raise psutil.AccessDenied(1)

            def wait(self, timeout=None):
                return 0

        collector._cache[1] = Denied()  # noqa: SLF001 - simulating a protected process
        with pytest.raises(ProcessTerminationError, match="Access denied"):
            collector.terminate(1)


class TestTermination:
    def test_a_child_process_can_be_stopped(self, collector):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
        )
        try:
            # Wait until the child is really up before terminating it.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if psutil.pid_exists(child.pid):
                    break
                time.sleep(0.05)

            collector.terminate(child.pid)
            assert child.wait(timeout=10) is not None
            assert not psutil.pid_exists(child.pid)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)


class TestEnumeration:
    def test_first_sweep_lists_processes(self, collector):
        rows = collector.collect()
        assert rows
        assert all(row.pid > 0 for row in rows)
        assert all(row.name for row in rows)

    def test_our_own_process_is_in_the_list(self, collector):
        collector.collect()
        time.sleep(0.2)
        rows = collector.collect()
        assert any(row.pid == os.getpid() for row in rows)

    def test_dead_processes_are_forgotten(self, collector):
        collector.collect()
        before = set(collector._cache)  # noqa: SLF001 - cache behaviour under test
        assert before

        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait(timeout=10)
        time.sleep(0.2)
        collector.collect()
        after = set(collector._cache)  # noqa: SLF001
        assert child.pid not in after

    def test_detail_returns_information_about_our_own_process(self, collector):
        detail = collector.detail(os.getpid())
        assert detail is not None
        assert isinstance(detail["threads"], int)
        assert detail["threads"] > 0

    def test_detail_of_a_missing_process_is_none(self, collector, monkeypatch):
        def missing(pid):
            raise psutil.NoSuchProcess(pid)

        monkeypatch.setattr(psutil, "Process", missing)
        assert collector.detail(4242) is None
