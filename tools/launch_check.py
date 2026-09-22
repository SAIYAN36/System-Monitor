"""Start System Monitor for a few seconds and report whether it stayed healthy.

This is the "does it actually run?" check used after installing the
dependencies and after building the executable:

    python tools/launch_check.py                    # run from source
    python tools/launch_check.py --exe dist/SystemMonitor.exe   # check a build

It fails (exit code 1) when the application exits early, does not produce
metrics, or writes an error to its log. It also reports the application's own
CPU and memory footprint, which is the easiest way to confirm the polling stays
light.
"""

from __future__ import annotations

import argparse
import pathlib
import statistics
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psutil  # noqa: E402

from app.config import log_file_path  # noqa: E402

#: Log lines containing any of these are treated as a failed launch.
_ERROR_MARKERS = ("| ERROR ", "| CRITICAL ")
#: The monitor logs this once per successful start.
_STARTED_MARKER = "Monitor worker started"


def read_log_tail(offset: int) -> tuple:
    """Return ``(new_text, new_offset)`` for the application log."""
    path = log_file_path()
    if not path.exists():
        return "", offset
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(offset)
            text = handle.read()
            return text, handle.tell()
    except OSError as exc:
        return f"(could not read the log: {exc})", offset


#: Helper processes the application spawns for a single query. PowerShell is
#: used once by the ACPI temperature probe; counting its start-up cost would
#: misrepresent the application's own footprint.
_HELPER_NAMES = {"powershell.exe", "pwsh.exe", "conhost.exe", "cmd.exe", "wmic.exe"}


def _family(root_process) -> list:
    """The launched process tree, excluding short-lived helper processes."""
    members = [root_process]
    try:
        if root_process.is_running():
            members += root_process.children(recursive=True)
    except psutil.Error:
        pass
    return [
        member
        for member in members
        if _is_alive(member) and _name(member) not in _HELPER_NAMES
    ]


def _name(process) -> str:
    try:
        return (process.name() or "").lower()
    except psutil.Error:
        return ""


def _is_alive(process) -> bool:
    try:
        return process.is_running()
    except psutil.Error:
        return False


def _safe_cpu(process) -> float:
    """CPU percentage since the previous call, or 0 when it is gone."""
    try:
        return process.cpu_percent(interval=None)
    except psutil.Error:
        return 0.0


def _safe_rss(process) -> int:
    try:
        return process.memory_info().rss
    except psutil.Error:
        return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=12.0,
                        help="how long to observe the application (default: 12)")
    parser.add_argument("--exe", help="path to a built executable instead of running main.py")
    parser.add_argument("--minimized", action="store_true",
                        help="start the application minimized")
    parser.add_argument("--max-idle-cpu", type=float, default=20.0,
                        help="fail when the idle CPU exceeds this share of one core "
                             "(default: 20)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="print the per-second CPU and memory samples")
    args = parser.parse_args(argv)

    if args.exe:
        executable = pathlib.Path(args.exe)
        if not executable.exists():
            print(f"FAIL: {executable} does not exist")
            return 1
        command = [str(executable)]
    else:
        command = [sys.executable, str(ROOT / "main.py")]
    if args.minimized:
        command.append("--minimized")

    _, offset = read_log_tail(0)
    print(f"Launching: {' '.join(command)}")
    process = subprocess.Popen(command, cwd=str(ROOT))

    samples: list = []
    exit_code = None
    handles: dict = {}
    try:
        root_process = psutil.Process(process.pid)
        # A virtual-environment python.exe is a small launcher that re-executes
        # the real interpreter, so the whole process tree is measured.
        handles[root_process.pid] = root_process
        _safe_cpu(root_process)

        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                exit_code = process.returncode
                break
            members = _family(root_process)
            if not members:
                break
            total_cpu = 0.0
            largest_rss = 0
            for member in members:
                # psutil reports the CPU used since the previous call *on the
                # same Process object*, so handles are cached by pid. Reusing
                # the child objects returned by children() would always read
                # 0.0 and silently under-report.
                handle = handles.get(member.pid)
                if handle is None:
                    handle = psutil.Process(member.pid)
                    handles[member.pid] = handle
                    _safe_cpu(handle)  # prime: the first call is meaningless
                total_cpu += _safe_cpu(handle)
                largest_rss = max(largest_rss, _safe_rss(handle))
            samples.append((total_cpu, largest_rss))
            time.sleep(1.0)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

    text, _ = read_log_tail(offset)
    new_lines = [line for line in text.splitlines() if line.strip()]

    # The first samples include start-up work, so the idle figure is what the
    # "low CPU usage" requirement is really about.
    warmup = 3
    steady = samples[warmup:]

    print(f"\nObserved for {len(samples)} second(s)")
    idle_cpu = None
    if samples:
        peak_rss = max(rss for _, rss in samples) / (1024 * 1024)
        print(
            f"Start-up CPU:  {sum(cpu for cpu, _ in samples[:warmup]) / max(1, len(samples[:warmup])):5.1f}% of one core"
        )
        if steady:
            # The median is used rather than the mean: a virus scanner reading
            # the freshly written executable, or a log rotation, can produce a
            # single large sample that says nothing about the idle cost.
            idle_cpu = statistics.median(cpu for cpu, _ in steady)
            mean_cpu = sum(cpu for cpu, _ in steady) / len(steady)
            print(
                f"Idle CPU:      {idle_cpu:5.1f}% of one core "
                f"(median, mean {mean_cpu:.1f}%)"
            )
        print(f"Resident memory: {peak_rss:6.1f} MB (largest process in the tree)")
    else:
        print("No samples were taken")

    if args.verbose and samples:
        print("\nPer-second samples (CPU% of one core, largest process MB):")
        for index, (cpu, rss) in enumerate(samples, start=1):
            print(f"  t={index:3d}s  cpu={cpu:6.1f}%   rss={rss / (1024 * 1024):6.1f} MB")

    print(f"\nLog lines written during the run: {len(new_lines)}")
    for line in new_lines[-8:]:
        print(f"  {line}")

    failures = []
    if exit_code not in (None, 0):
        failures.append(f"the application exited early with code {exit_code}")
    if not samples:
        failures.append("the application produced no CPU samples (it may have died instantly)")
    if not any(_STARTED_MARKER in line for line in new_lines):
        # A rebuilt log may have rotated, so only warn when the file is quiet.
        if not new_lines:
            failures.append("the application wrote nothing to its log")
    errors = [line for line in new_lines if any(mark in line for mark in _ERROR_MARKERS)]
    if errors:
        failures.append(f"{len(errors)} error line(s) in the log, first: {errors[0]}")
    if idle_cpu is not None and idle_cpu > args.max_idle_cpu:
        failures.append(
            f"idle CPU was {idle_cpu:.1f}% of one core (median), above the "
            f"{args.max_idle_cpu:g}% budget"
        )

    print()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: the application started, stayed up and logged no errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
