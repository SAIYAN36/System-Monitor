"""Process enumeration and termination."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import psutil

from app.models.snapshot import ProcessInfo
from app.utils.errors import safe_call

logger = logging.getLogger(__name__)

#: Terminating these would take Windows down with it; the UI warns harder.
CRITICAL_NAMES = {
    "system",
    "system idle process",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "explorer.exe",
    "dwm.exe",
    "fontdrvhost.exe",
    "audiodg.exe",
    "ntoskrnl.exe",
    "memcompression",
    "idle",
}


class ProcessTerminationError(RuntimeError):
    """Raised when a process could not be stopped."""


class ProcessCollector:
    """Enumerates processes, reusing ``psutil.Process`` objects over time.

    psutil measures per-process CPU as the delta since the previous call *on
    that same object*, so the objects are cached between polls. Percentages are
    divided by the logical core count to match the system-wide CPU figure the
    Task Manager reports.
    """

    def __init__(self) -> None:
        self._cache: Dict[int, psutil.Process] = {}
        self._cpu_divisor = max(1, psutil.cpu_count(logical=True) or 1)

    def collect(self) -> Tuple[ProcessInfo, ...]:
        """One row per visible process, sorted by CPU usage."""
        alive: set[int] = set()
        rows: List[ProcessInfo] = []

        for pid in safe_call(psutil.pids, default=[], context="pids") or []:
            if pid == 0:
                # PID 0 is the kernel idle task and cannot be inspected.
                continue
            process = self._cache.get(pid)
            if process is None:
                process = safe_call(psutil.Process, pid, default=None, context="Process")
                if process is None:
                    continue
                # Cache it so the next poll can compute a real CPU delta. The
                # reading taken now is 0.0 for a freshly created handle, which
                # is why processes are listed (at 0%) rather than skipped.
                self._cache[pid] = process

            info = self._read(process)
            if info is None:
                self._cache.pop(pid, None)
                continue
            alive.add(pid)
            rows.append(info)

        # Forget processes that no longer exist.
        for pid in list(self._cache):
            if pid not in alive:
                self._cache.pop(pid, None)

        rows.sort(key=lambda row: (row.cpu_percent or 0.0, row.memory_rss or 0), reverse=True)
        return tuple(rows)

    def detail(self, pid: int) -> Optional[Dict[str, object]]:
        """Extra, more expensive facts about one process (for the detail panel)."""
        process = self._cache.get(pid)
        if process is None:
            process = safe_call(psutil.Process, pid, default=None, context="Process.detail")
            if process is None:
                return None
        return {
            "username": safe_call(process.username, default=None, context="username"),
            "exe": safe_call(process.exe, default=None, context="exe"),
            "cwd": safe_call(process.cwd, default=None, context="cwd"),
            "cmdline": safe_call(process.cmdline, default=None, context="cmdline"),
            "create_time": safe_call(process.create_time, default=None, context="create_time"),
            "threads": safe_call(process.num_threads, default=None, context="num_threads"),
            "nice": safe_call(process.nice, default=None, context="nice"),
        }

    def terminate(self, pid: int, *, force: bool = False) -> None:
        """Stop a process, translating psutil errors into readable messages."""
        if pid <= 0:
            raise ProcessTerminationError("Cannot terminate a system process.")
        process = self._cache.get(pid)
        if process is None:
            process = safe_call(psutil.Process, pid, default=None, context="Process.terminate")
            if process is None:
                raise ProcessTerminationError("That process is no longer running.")

        action = process.kill if force else process.terminate
        try:
            action()
            process.wait(timeout=3)
        except psutil.NoSuchProcess:
            # Already gone: the desired end state, so this is a success.
            logger.info("Process %s exited before it could be stopped", pid)
        except psutil.AccessDenied as exc:
            raise ProcessTerminationError(
                "Access denied. Try running System Monitor as administrator."
            ) from exc
        except psutil.TimeoutExpired:
            if force:
                raise ProcessTerminationError(
                    "The process did not exit within the timeout."
                ) from None
            # Escalate to a forceful kill only when the polite request failed.
            self.terminate(pid, force=True)
            return
        except Exception as exc:  # noqa: BLE001 - surfaced in the dialog
            raise ProcessTerminationError(f"Could not terminate the process: {exc}") from exc
        finally:
            self._cache.pop(pid, None)

    def is_critical(self, name: str) -> bool:
        return (name or "").strip().lower() in CRITICAL_NAMES

    # ----------------------------------------------------------------- private
    def _read(self, process: psutil.Process) -> Optional[ProcessInfo]:
        """Build one row, or ``None`` if the process vanished mid-read."""
        raw_name = ""
        try:
            raw_cpu = process.cpu_percent(interval=None)
            with process.oneshot():
                memory = process.memory_info()
                memory_percent = process.memory_percent()
                status = process.status()
                raw_name = safe_call(process.name, default="")
                threads = process.num_threads()
        except psutil.NoSuchProcess:
            return None
        except psutil.AccessDenied:
            # System processes deny some queries; report what is known.
            return ProcessInfo(
                pid=process.pid,
                name=_display_name(raw_name, process.pid),
                status="access denied",
            )
        except Exception as exc:  # noqa: BLE001 - never break the sweep
            logger.debug("Process %s could not be read: %r", process.pid, exc)
            return None

        return ProcessInfo(
            pid=process.pid,
            name=_display_name(raw_name, process.pid),
            cpu_percent=(raw_cpu or 0.0) / self._cpu_divisor,
            memory_percent=memory_percent,
            memory_rss=memory.rss,
            status=status,
            threads=threads,
        )


def _display_name(raw_name: Optional[str], pid: int) -> str:
    """A process name is occasionally blank (protected or exiting processes).

    Showing an empty cell would look like a bug, so fall back to the PID.
    """
    name = (raw_name or "").strip()
    return name or f"PID {pid}"
