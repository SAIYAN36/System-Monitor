# System Monitor

A real-time system monitoring desktop application for Windows, built with Python,
**PySide6** (Qt 6) and **psutil**.

Every value on every screen comes from the machine it is running on. Nothing is
simulated, randomised or hard-coded: CPU load, memory, disks, network adapters,
processes, drive labels, temperatures and Windows build numbers are all read
from the operating system at runtime.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  System Monitor            Dashboard                                      │
│  v1.0.0                    Live system overview, refreshed automatically.  │
│  ┌──────────────┐  ┌───────────────────────┐ ┌─────────────────────────┐   │
│  │ ▤ Dashboard  │  │ CPU usage   12.4%     │ │ RAM usage      78.2%    │   │
│  ├──────────────┤  │ 2 cores / 4 threads   │ │ 3.1 GB of 3.9 GB in use │   │
│  │ ▢ CPU        │  │ ▇▇▇▇░░░░░░░░░░░░░░░░░ │ │ ▇▇▇▇▇▇▇▇▇▇▇▇▇▇░░░░░░ │   │
│  │ ▤ Memory     │  └───────────────────────┘ └─────────────────────────┘   │
│  │ ▣ Disk       │  ...                                                      │
│  │ ⬡ Network    │                                                           │
│  │ ☰ Processes  │                                                           │
│  │ ⓘ System     │                                                           │
│  │ ⚙ Settings   │                                                           │
│  └──────────────┘                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 1. What is included

**Dashboard** — CPU %, RAM %, aggregate disk usage %, network up/down speed,
system uptime, CPU temperature (when the machine exposes one), running process
count and the current time, plus four live graphs (CPU, memory, network, disk).

**CPU** — overall and per-core utilisation, processor model, physical core count,
thread count, current and maximum clock speed, architecture, load average,
a usage history graph and the temperature with the name of the sensor source.

**Memory** — total, used and available RAM, utilisation, a usage history graph,
and the page file / swap figures with their own gauge.

**Disk** — every mounted volume detected automatically, with capacity, used and
free space, usage percentage, file system, drive type and (on Windows) the volume
label; plus read/write throughput, cumulative counters since boot, and an
activity graph.

**Network** — per-interval upload and download speed, cumulative totals, primary
IPv4 address, a traffic graph, and a table of every adapter with its link state,
addresses, MAC, link speed and traffic totals.

**Processes** — a sortable table of every running process (name, PID, CPU %,
memory %, memory, threads, status) with a filter box, a details panel for the
selected process, and a confirmed *End task* action.

**System Information** — OS name, edition and build, host name, architecture,
machine type, Python/Qt/psutil versions, boot time, uptime, installed memory,
page file size, volumes, physical disks and network adapters, plus the path of
the application's log directory.

**Settings** — refresh interval, graph history length, CPU temperature reading
and its interval, start minimized, start with Windows, keep running in the
notification area, confirm before ending a process, dark/light theme, and which
dashboard cards and graphs are shown.

---

## 2. Project structure

```
system_monitor/
├── main.py                     # Entry point: CLI flags, logging, theme, window
├── requirements.txt            # Runtime dependencies (PySide6, psutil)
├── requirements-dev.txt        # Test and packaging dependencies
├── pyproject.toml              # Pytest configuration
├── system_monitor.spec         # PyInstaller build configuration
├── README.md
├── app/
│   ├── config.py               # Paths, constants, refresh bounds
│   ├── models/
│   │   └── snapshot.py         # Immutable dataclasses for every metric group
│   ├── monitoring/             # Data collection - no Qt, no UI
│   │   ├── collector.py        # SystemMonitor: builds a Snapshot from all sources
│   │   ├── cpu.py              # Utilisation, per-core load, clock speed, model
│   │   ├── memory.py           # RAM and page file / swap
│   │   ├── disk.py             # Volumes, labels, drive types, I/O throughput
│   │   ├── network.py          # Adapters, addresses, throughput, totals
│   │   ├── processes.py        # Process enumeration and termination
│   │   ├── system.py           # OS/machine details, boot time, device lists
│   │   ├── sensors.py          # CPU temperature provider chain
│   │   └── rate.py             # Counter→rate conversion, short-lived cache, clock
│   ├── services/               # Application behaviour
│   │   ├── monitor_service.py  # MonitorWorker: the QThread that polls
│   │   ├── history.py          # Bounded graph history + thread-safe update bundle
│   │   ├── settings.py         # Settings dataclass, validation, JSON persistence
│   │   ├── logging_service.py  # Rotating file + console logging, crash hooks
│   │   └── autostart.py        # Windows "Start with Windows" registry entry
│   ├── ui/                     # Everything PySide6
│   │   ├── main_window.py      # Window, sidebar, page stack, tray, status bar
│   │   ├── context.py          # Shared state handed to the pages
│   │   ├── theme.py            # Dark and light palettes + stylesheets
│   │   ├── icons.py            # Vector icons drawn with QPainter
│   │   ├── widgets/            # Reusable building blocks
│   │   │   ├── cards.py        # Card, MetricCard, InfoGrid
│   │   │   ├── graph.py        # Lightweight multi-series line graph
│   │   │   ├── gauge.py        # Ring gauge, per-core usage bars
│   │   │   ├── table.py        # Rebuildable device table (drives, adapters)
│   │   │   ├── sidebar.py      # Navigation rail
│   │   │   └── common.py       # Usage bar, section titles, badges
│   │   └── pages/              # One module per screen
│   │       ├── base.py         # Page / ScrollPage base classes
│   │       ├── dashboard.py    ├── network.py
│   │       ├── cpu.py          ├── processes.py
│   │       ├── memory.py       ├── system_info.py
│   │       ├── disk.py         └── settings.py
│   └── utils/
│       ├── formatting.py       # Byte/rate/duration/temperature formatting
│       ├── ringbuffer.py       # Fixed-capacity sample buffer
│       └── errors.py           # safe_call / safe / ignore_errors helpers
├── tests/                      # 201 pytest tests
├── tools/
│   ├── launch_check.py         # Runs the app, measures it, checks the log
│   └── make_icon.py            # Generates assets/icon.ico and icon.png
└── assets/
    ├── icon.ico                # Multi-size application icon (7 sizes)
    └── icon.png                # 256×256 badge
```

The layering is strict: `app.monitoring` and `app.utils` import neither Qt nor any
widget, which is why the entire data layer is testable without a display. The UI
never touches psutil directly, and the monitoring layer never touches the UI.

---

## 3. How the monitoring works

### Threading

```
        GUI thread                        MonitorWorker (QThread)
  ┌───────────────────┐                ┌──────────────────────────┐
  │ MainWindow        │  MetricsUpdate │ loop:                    │
  │  ├ sidebar        │ ◄──────────────│   SystemMonitor.collect  │
  │  ├ visible page   │   (Qt signal)  │   MetricHistory.append   │
  │  └ status bar     │                │   sleep(interval − work) │
  └───────────────────┘                └──────────────────────────┘
```

* Every psutil call happens on the worker thread, never on the GUI thread, so the
  interface cannot freeze even if a query stalls.
* Each reading is delivered as one immutable `MetricsUpdate` (a `Snapshot` plus
  the graph series as plain tuples). Nothing mutable is shared between threads.
* **Only the visible page is updated.** Hidden pages receive nothing at all, so
  seven of the eight screens cost zero CPU while you are looking at the eighth.
  Pages are also *created* lazily on first visit, which keeps start-up fast.
* The loop subtracts the time the collection itself took, so the cadence stays
  accurate instead of drifting, and it backs off (up to 5×) if a poll fails
  repeatedly rather than hammering a broken query.

### Process enumeration is opt-in

Walking the process table is by far the most expensive operation, so it only runs
while the **Processes** page is visible. The page asks the worker to enable it on
activation and disable it on the way out. On the Dashboard the process *count* is
therefore shown as "Unavailable — detailed while the Processes page is open",
which is honest rather than a fabricated number.

While the page *is* open the table is collected on every poll, because that is
exactly the screen where you want current numbers; the cost is only paid while
you are looking at it.

Process CPU percentages need one more trick. psutil computes a process's CPU as
the delta since the previous read **on that same `Process` object**, so the
collector keeps its `psutil.Process` handles in a cache keyed by PID and re-reads
those same objects each sweep. Creating a fresh handle every time — the obvious
implementation — makes the CPU column permanently read 0 %, because a new handle
has no previous sample to compare against. Dead PIDs are dropped from the cache
on every sweep so it cannot grow.

### Rates instead of counters

Windows reports cumulative byte counters. Network and disk throughput are
derived from the difference between consecutive samples divided by the elapsed
time (`app/monitoring/rate.py`). Two details matter:

* The clock is `time.perf_counter()`, not `time.monotonic()`. On Windows
  `monotonic()` is only accurate to ~16 ms (`GetTickCount64`), so two readings
  taken in the same tick look simultaneous and the sample is lost.
* A *negative* delta means the counter was reset (an adapter was re-created, the
  machine resumed from sleep). That is reported as "no sample" rather than as a
  spectacular fake spike.

The first sample for any counter therefore shows "Unavailable" and correct values
appear one interval later. That is expected, not a bug.

### Caching and cadence

Three different cadences keep the application light:

| Work | Cadence | Why |
|---|---|---|
| CPU, RAM, network, disk counters | every poll (default 1 s) | cheap counter reads |
| Volume list, adapter list, OS details | 5–30 s (TTL cache) | changes rarely, costly to enumerate |
| CPU temperature | 30 s (configurable) | sensors are slow; see below |
| Full process table | only while the Processes page is open | most expensive query; costs nothing when the page is closed |

### Temperature: a chain of providers

There is no supported Windows API that gives a plain user process the CPU
temperature, so `app/monitoring/sensors.py` tries several sources in order and
remembers the first one that works:

1. `psutil.sensors_temperatures()` — works on Linux and on some laptops. (psutil
   does not implement it on Windows at all, which is detected and reported.)
2. **LibreHardwareMonitor / OpenHardwareMonitor** — if the user runs one of them,
   it publishes temperatures through its own WMI namespace. Requires the optional
   `wmi` package; nothing else depends on it.
3. **The ACPI thermal zone** (`root/wmi:MSAcpi_ThermalZoneTemperature`) — queried
   through a hidden PowerShell process.

Because the ACPI query can block for seconds, it never runs on the polling
thread: `SensorReader` owns its own daemon thread and `read()` only ever returns
the last cached value. When every provider fails, the answer is remembered for
15 minutes so the application does not spawn a PowerShell process every 30
seconds to learn the same thing twice. The UI shows "Unavailable" together with
the reason, and the CPU/Settings pages name the provider that is supplying the
value when one exists.

### Never crashing

`app/utils/errors.py` wraps every probe. A metric that cannot be read becomes
`None`, which every formatter renders as **Unavailable**; a volume that vanished
mid-sweep is skipped; a process that exits while being read is dropped; a
`PermissionError` from a protected process leaves that row with the data that
*was* readable and marks it "access denied". A whole failing subsystem cannot
take the collector down, and `tests/test_monitoring.py` proves it by making
psutil raise for CPU, memory, disks, networks and processes — including all of
them at once.

---

## 4. Installing and running

Requires **Python 3.10+** (developed and tested on 3.11.9) on Windows.

```bash
cd system_monitor

# 1. Create a virtual environment
python -m venv .venv

# 2. Install the dependencies
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Run it
.venv\Scripts\python.exe main.py
```

In PowerShell or cmd, activate first if you prefer:

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

### Command line flags

| Flag | Effect |
|---|---|
| `--minimized` | start in the notification area without showing the window |
| `--debug` | log at DEBUG level |
| `--reset-settings` | ignore the saved settings and restore the defaults |
| `--version` | print the version and exit |

### Where the application keeps its files

Nothing is written next to the source. Everything lives in the per-user profile:

```
%APPDATA%\SystemMonitor\
├── settings.json               # your configuration
└── logs\
    └── system_monitor.log      # rotating, 1 MB × 3 backups
```

The exact paths are shown on the **System Information** page, and the **Open log
folder** button takes you straight there.

---

## 5. Running the tests

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
```

201 tests, roughly half a minute:

| File | Covers |
|---|---|
| `test_formatting.py` | every formatter, including `None`, NaN and infinity |
| `test_ringbuffer.py` | bounded memory, resize, statistics |
| `test_rate.py` | counter→rate conversion, reset detection, TTL cache |
| `test_settings.py` | defaults, clamping of bad input, atomic save, corrupt files |
| `test_history.py` | graph series, missing values, capacity limits |
| `test_monitoring.py` | the collectors **against the real machine**, plus injection of failing psutil calls |
| `test_sensors.py` | the temperature provider chain with injected providers |
| `test_processes.py` | termination safety, enumeration, starting and stopping a real child process |
| `test_config.py` | path layout and platform detection |
| `test_ui_smoke.py` | builds and *renders* all eight pages offscreen, checks that no page is blank, plus the process table model, theming and the settings round trip |

The GUI tests use Qt's `offscreen` platform plugin, so they run headless and never
open a window on your desktop. The monitoring tests assert *shapes and
invariants* (a percentage is between 0 and 100, `used + free == total`, one
entry per logical processor) rather than fixed values — they exercise the real
machine but do not pretend to know what it will report.

Add `--cov=app --cov-report=term-missing` for coverage.

---

## 6. Building a standalone Windows executable

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m PyInstaller --noconfirm system_monitor.spec
```

The result is:

```
dist\SystemMonitor\SystemMonitor.exe      (plus the _internal folder beside it)
```

Verify the build actually runs:

```bash
.venv\Scripts\python.exe tools\launch_check.py --exe dist\SystemMonitor\SystemMonitor.exe
```

That starts the executable, watches it for a few seconds, reports its CPU and
memory usage, and fails if it exits early or writes anything at ERROR level to
its log. The same script without `--exe` checks the application running from
source.

**A folder build rather than `--onefile`.** A single-file executable has to unpack
the entire Qt runtime into a temporary directory on every launch, which costs
several seconds of start-up time. If you need one file anyway:

```bash
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed ^
    --name SystemMonitor --icon assets\icon.ico --add-data "assets;assets" main.py
```

The spec excludes the large Qt modules this application never imports
(WebEngine, Quick/QML, Multimedia, 3D, Charts, SQL, sensors, …), which is what
keeps the bundle at ~117 MB instead of several hundred.

### Regenerating the icon

`assets/icon.ico` is generated from the same vector artwork that draws the
interface icons, so you never need an image editor:

```bash
.venv\Scripts\python.exe tools\make_icon.py
```

---

## 7. Performance

Measured on the development machine (Intel i3-1115G4, 4 logical processors,
4 GB RAM, Windows 11 25H2) with `tools/launch_check.py`, 1 s refresh interval,
Dashboard open. Note that this machine is a small laptop that is usually loaded,
which is worth knowing when reading the ranges below:

| Metric | Value |
|---|---|
| Idle CPU | **1.5 – 5 % of one core** (1.5 % on a quiet machine, ~5 % when it is busy; see the note below) |
| Start-up CPU | ~30 % of one core for the first 2–3 seconds |
| Resident memory | **50 – 115 MB**, stable — it does not grow over time, and settles as Qt's caches fill |
| Graph memory | bounded by design: the oldest samples are dropped from fixed-capacity ring buffers, so history can never grow without limit |

Measured as CPU *time* consumed over a 20-second window (`process.cpu_times()`),
which is reliable where snapshot percentages are not. Expect the figure to move
with the state of the machine: on a box already at 90 % memory utilisation and
40 % CPU — the state of the development machine during much of this work — the
same application reports 5–11 %, because CPU accounting under contention and
paging inflates every process's share. Re-measure on your own hardware before
treating any of these numbers as a promise.

The three ways this stays low:

1. **Nothing hidden costs anything.** Only the visible page is updated, pages are
   built on first visit, and the process table is only walked while its page is
   open.
2. **Nothing is polled faster than it changes.** Device lists are cached for
   5–30 s, temperatures for 30 s, and everything else at the configurable refresh
   interval (500 ms – 10 s).
3. **The graphs are 30 lines of QPainter**, not a charting library: a fixed
   number of points, no animation, no per-frame allocations.

If you want it even lighter, raise the refresh interval in **Settings** — 2
seconds halves the cost and is still perfectly responsive — or hide the
dashboard graphs you do not read, since each visible graph is redrawn every
interval.

---

## 8. Features that depend on the hardware or on Windows

These degrade to "Unavailable" instead of failing. The right-hand column says what
you can do about it.

| Feature | Requirement | If it is missing |
|---|---|---|
| **CPU temperature** | Firmware publishing an ACPI thermal zone, a readable `coretemp`/`k10temp` sensor, or LibreHardwareMonitor/OpenHardwareMonitor running | Shows "Unavailable" with the reason. Running [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) plus `pip install wmi` makes it work on most desktops |
| **Per-process user, executable, command line, priority** | The process must be owned by you | Protected/system processes show the fields that are readable and are marked "access denied" |
| **Ending a protected process** | Administrator rights | Reports "Access denied. Try running System Monitor as administrator" |
| **Disk volume label and drive type** | Windows (`GetVolumeInformationW` / `GetDriveTypeW`) | Left blank on other platforms |
| **Physical disk names** | Windows (`\\.\PHYSICALDRIVE*` handles) | The section is empty |
| **Disk read/write throughput** | OS-level disk I/O counters | The activity graph and rates show "Unavailable" while the rest of the page keeps working |
| **Page file / swap** | The OS reports it | The page-file card shows "No page file reported" |
| **Load average (1/5/15 min)** | psutil can emulate it on Windows; unavailable in some sandboxes | Shows "Unavailable" |
| **Adapter link speed** | The driver reports it | Shows "Unavailable" |
| **Start with Windows** | Windows; writes to `HKCU\...\CurrentVersion\Run` (no admin needed) | The checkbox is disabled with an explanation |
| **Minimize to the notification area** | A system tray exists | The checkbox is disabled and the window simply closes |
| **Uptime, boot time, OS edition/build** | Always available | — |

Deliberately **not** included: fake or randomly generated values. A metric that
this machine does not expose is reported as unavailable, with the reason, rather
than replaced by something that looks plausible.

---

## 9. Extending it

To add a new metric:

1. Add the field to the relevant dataclass in `app/models/snapshot.py`.
2. Read it in the matching collector under `app/monitoring/` (wrap the call in
   `safe_call` so a failure yields `None`).
3. Add a formatter in `app/utils/formatting.py` if you need one, and return
   `UNAVAILABLE` for `None`.
4. Surface it in a page: `InfoGrid.add_row` + `set_value` for a label/value pair,
   or `MetricCard.set_value` for a headline number.
5. Add a test. Collectors are tested against the real machine for shape, and
   error handling is tested by making psutil raise.

If the metric is expensive, add it to the TTL-cached path or gate it behind a
page's `on_activated`, as the process table does.
