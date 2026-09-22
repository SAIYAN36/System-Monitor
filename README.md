\# System Monitor



> A real-time system monitoring desktop application for Windows, built with Python, \*\*PySide6\*\* (Qt 6) and \*\*psutil\*\*.



System Monitor provides live information about your CPU, memory, disks, network adapters, processes, temperatures and Windows system information.



Every value comes from the machine it is running on. Nothing is simulated, randomised or hard-coded. If the operating system or hardware does not expose a value, System Monitor reports it as \*\*Unavailable\*\* instead of fabricating a plausible number.



\---



\## 📸 Application Output



```text

┌──────────────────────────────────────────────────────────────────────────────┐

│  System Monitor                                      Dashboard              │

│  v1.0.0                         Live system overview, refreshed automatically │

│                                                                              │

├────────────────┬─────────────────────────────────────────────────────────────┤

│                │                                                             │

│  ◈ Dashboard   │  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │

│                │  │ CPU            │  │ MEMORY         │  │ DISK         │ │

│  ◉ CPU         │  │                │  │                │  │              │ │

│                │  │    12.4%       │  │  3.1 / 3.9 GB  │  │    41.7%     │ │

│  ▣ Memory      │  │  ▂▃▅▃▂▂▃       │  │  ▆▇▆▅▇▆▅       │  │   ▂▃▄▅▃▂     │ │

│                │  └────────────────┘  └────────────────┘  └──────────────┘ │

│  ◫ Disk        │                                                             │

│                │  CPU HISTORY                                               │

│  ◇ Network     │ 100% ┤                                                     │

│                │  75% ┤       ╭╮                                            │

│  ☰ Processes   │  50% ┤  ╭────╯╰──╮       ╭──╮                             │

│                │  25% ┤──╯          ╰─────╯  ╰──                           │

│  ⓘ System      │   0% └──────────────────────────────────                  │

│                │                                                             │

│  ⚙ Settings    │  NETWORK                         UPTIME                    │

│                │  ↓ 2.4 MB/s                      04:32:17                  │

│                │  ↑ 512 KB/s                                                │

└────────────────┴─────────────────────────────────────────────────────────────┘

```



\---



\# 1. What is included



\### Dashboard



CPU %, RAM %, aggregate disk usage %, network upload/download speed, system uptime, CPU temperature when the machine exposes one, running process count and the current time, plus four live graphs:



\* CPU

\* Memory

\* Network

\* Disk



\### CPU



\* Overall and per-core utilisation

\* Processor model

\* Physical core count

\* Thread count

\* Current and maximum clock speed

\* Architecture

\* Load average

\* Usage history graph

\* CPU temperature

\* Temperature sensor source



\### Memory



\* Total RAM

\* Used RAM

\* Available RAM

\* Utilisation

\* Usage history graph

\* Page file / swap figures

\* Page file gauge



\### Disk



Every mounted volume is detected automatically.



For each volume:



\* Capacity

\* Used space

\* Free space

\* Usage percentage

\* File system

\* Drive type

\* Windows volume label



Disk monitoring also provides:



\* Read throughput

\* Write throughput

\* Cumulative read/write counters

\* Activity graph



\### Network



\* Upload/download speed

\* Cumulative totals

\* Primary IPv4 address

\* Traffic graph

\* Network adapter table

\* Link state

\* IPv4/IPv6 addresses

\* MAC address

\* Link speed

\* Per-adapter traffic totals



\### Processes



A sortable table of running processes containing:



\* Name

\* PID

\* CPU %

\* Memory %

\* Memory usage

\* Thread count

\* Status



Also includes:



\* Process filter

\* Process details panel

\* Confirmed \*\*End Task\*\* action



\### System Information



Displays:



\* OS name

\* Windows edition

\* Windows build

\* Host name

\* Architecture

\* Machine type

\* Python version

\* Qt version

\* psutil version

\* Boot time

\* Uptime

\* Installed memory

\* Page file size

\* Volumes

\* Physical disks

\* Network adapters

\* Application log directory



\### Settings



Configurable options include:



\* Refresh interval

\* Graph history length

\* CPU temperature reading

\* Temperature interval

\* Start minimized

\* Start with Windows

\* Keep running in notification area

\* Confirm before ending a process

\* Dark/light theme

\* Dashboard cards

\* Dashboard graphs



\---



\# 2. Project structure



```text

System-Monitor/

│

├── main.py                     # Entry point

├── requirements.txt            # Runtime dependencies

├── requirements-dev.txt        # Test and packaging dependencies

├── pyproject.toml              # Pytest configuration

├── system\_monitor.spec         # PyInstaller configuration

├── README.md

│

├── app/

│   ├── config.py               # Paths, constants, refresh bounds

│   │

│   ├── models/

│   │   └── snapshot.py         # Immutable metric dataclasses

│   │

│   ├── monitoring/             # System data collection

│   │   ├── collector.py

│   │   ├── cpu.py

│   │   ├── memory.py

│   │   ├── disk.py

│   │   ├── network.py

│   │   ├── processes.py

│   │   ├── system.py

│   │   ├── sensors.py

│   │   └── rate.py

│   │

│   ├── services/               # Application behaviour

│   │   ├── monitor\_service.py

│   │   ├── history.py

│   │   ├── settings.py

│   │   ├── logging\_service.py

│   │   └── autostart.py

│   │

│   ├── ui/                     # PySide6 interface

│   │   ├── main\_window.py

│   │   ├── context.py

│   │   ├── theme.py

│   │   ├── icons.py

│   │   │

│   │   ├── widgets/

│   │   │   ├── cards.py

│   │   │   ├── graph.py

│   │   │   ├── gauge.py

│   │   │   ├── table.py

│   │   │   ├── sidebar.py

│   │   │   └── common.py

│   │   │

│   │   └── pages/

│   │       ├── base.py

│   │       ├── dashboard.py

│   │       ├── cpu.py

│   │       ├── memory.py

│   │       ├── disk.py

│   │       ├── network.py

│   │       ├── processes.py

│   │       ├── system\_info.py

│   │       └── settings.py

│   │

│   └── utils/

│       ├── formatting.py

│       ├── ringbuffer.py

│       └── errors.py

│

├── tests/                      # 201 pytest tests

│

├── tools/

│   ├── launch\_check.py

│   └── make\_icon.py

│

├── assets/

│   ├── icon.ico

│   └── icon.png

│

└── SystemMonitor-v1.0.0-Windows-x64.zip

```



The layering is intentional:



```text

app.monitoring ──────► system data

&#x20;      │

&#x20;      │

&#x20;      ▼

app.services ────────► application behaviour

&#x20;      │

&#x20;      │

&#x20;      ▼

app.ui ──────────────► presentation

```



The monitoring and utility layers do not import Qt widgets.



The UI never accesses psutil directly.



This separation keeps the data layer independently testable.



\---



\# 3. How the monitoring works



\## Threading



```text

&#x20;            GUI THREAD                         MONITOR WORKER

┌────────────────────────────┐          ┌──────────────────────────────┐

│                            │          │                              │

│ MainWindow                 │          │ QThread                      │

│                            │          │                              │

│ ├── Sidebar                │          │ SystemMonitor.collect()      │

│ ├── Visible Page           │◄─────────│ MetricHistory.append()       │

│ └── Status Bar             │ Signal   │ sleep(interval - work time)  │

│                            │          │                              │

└────────────────────────────┘          └──────────────────────────────┘

```



Every psutil call happens on the worker thread rather than the GUI thread.



This means a slow system query cannot freeze the interface.



Each reading is delivered as one immutable `MetricsUpdate` containing:



\* A `Snapshot`

\* Graph series

\* Plain tuples rather than mutable shared state



\### Visible-page updates



Only the visible page is updated.



Hidden pages receive no UI updates.



Pages are also created lazily when first visited, reducing startup work.



\### Polling cadence



The worker accounts for collection time:



```text

sleep\_time = interval - collection\_time

```



This prevents the monitoring cadence from continuously drifting.



If a poll repeatedly fails, the worker backs off up to 5× instead of repeatedly hammering a broken query.



\---



\## Process enumeration is opt-in



Walking the process table is one of the most expensive monitoring operations.



Therefore, process enumeration only occurs while the \*\*Processes\*\* page is visible.



```text

Dashboard

&#x20;  │

&#x20;  └── Process table disabled

&#x20;          │

&#x20;          ▼

Processes page opened

&#x20;          │

&#x20;          ▼

Process enumeration enabled

&#x20;          │

&#x20;          ▼

Processes page closed

&#x20;          │

&#x20;          ▼

Process enumeration disabled

```



This means the Dashboard does not continuously pay the cost of collecting the entire process table.



\### Process CPU percentages



psutil calculates process CPU usage from the difference between previous and current readings on the same `Process` object.



System Monitor therefore maintains a cache of `psutil.Process` objects keyed by PID.



Creating a fresh object on every sweep would cause process CPU measurements to remain at or near zero because there would be no previous sample associated with the new object.



Dead PIDs are removed from the cache after each sweep so the cache cannot grow indefinitely.



\---



\## Rates instead of counters



Windows exposes cumulative byte counters.



Network and disk throughput are calculated as:



```text

rate = counter\_difference / elapsed\_time

```



The implementation uses:



```python

time.perf\_counter()

```



rather than `time.monotonic()` for interval measurement.



A negative counter difference indicates that the counter was reset, for example after an adapter was recreated or the machine resumed from sleep.



Such a sample is treated as unavailable rather than creating a fake traffic spike.



The first sample for a counter therefore displays:



> \*\*Unavailable\*\*



The next sample provides the first valid rate.



\---



\## Caching and cadence



| Work             | Cadence             | Reason              |

| ---------------- | ------------------- | ------------------- |

| CPU              | Every poll          | Cheap               |

| RAM              | Every poll          | Cheap               |

| Network counters | Every poll          | Cheap               |

| Disk counters    | Every poll          | Cheap               |

| Volume list      | 5–30 seconds        | Changes rarely      |

| Adapter list     | 5–30 seconds        | Changes rarely      |

| OS details       | Cached              | Changes rarely      |

| CPU temperature  | \~30 seconds         | Sensors can be slow |

| Process table    | Processes page only | Expensive           |



\---



\## Temperature: provider chain



There is no universal Windows API that provides CPU temperature to a normal user application.



System Monitor therefore attempts multiple providers.



```text

&#x20;                CPU Temperature

&#x20;                       │

&#x20;                       ▼

&#x20;         ┌─────────────────────────┐

&#x20;         │ psutil.sensors\_temperatures()

&#x20;         └────────────┬────────────┘

&#x20;                      │ unavailable

&#x20;                      ▼

&#x20;         ┌─────────────────────────┐

&#x20;         │ LibreHardwareMonitor /  │

&#x20;         │ OpenHardwareMonitor     │

&#x20;         └────────────┬────────────┘

&#x20;                      │ unavailable

&#x20;                      ▼

&#x20;         ┌─────────────────────────┐

&#x20;         │ Windows ACPI thermal    │

&#x20;         │ zone                    │

&#x20;         └────────────┬────────────┘

&#x20;                      │ unavailable

&#x20;                      ▼

&#x20;                 Unavailable

```



`psutil.sensors\_temperatures()` works on Linux and some supported systems, but psutil does not implement it on Windows.



LibreHardwareMonitor and OpenHardwareMonitor can provide temperature data through their WMI interfaces.



The ACPI provider uses:



```text

root/wmi:MSAcpi\_ThermalZoneTemperature

```



Because the ACPI query can block for seconds, temperature reading runs in its own daemon thread.



The UI receives the most recently cached result rather than waiting for the sensor query.



When all providers fail, the failure is cached for 15 minutes to avoid repeatedly launching PowerShell processes for the same unavailable sensor.



\---



\## Never crashing



The monitoring layer is designed around graceful failure.



A metric that cannot be read becomes:



```text

None

```



The formatter then displays:



```text

Unavailable

```



Examples:



```text

CPU sensor fails

&#x20;     ↓

temperature = None

&#x20;     ↓

UI = "Unavailable"

```



A volume disappearing during a scan is skipped.



A process exiting while being read is dropped.



A protected process can leave some fields readable while others are marked:



```text

Access denied

```



A failure in one subsystem does not take down the collector.



\---



\# 4. Installing and running



\## Requirements



\* Windows

\* Python 3.10+

\* Python 3.11.9 recommended for development



Clone the repository:



```powershell

git clone https://github.com/SAIYAN36/System-Monitor.git

cd System-Monitor

```



Create a virtual environment:



```powershell

python -m venv .venv

```



Install dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements.txt

```



Run the application:



```powershell

.venv\\Scripts\\python.exe main.py

```



\### Optional activation



```powershell

.venv\\Scripts\\Activate.ps1

python main.py

```



\---



\## Command-line flags



| Flag               | Effect                         |

| ------------------ | ------------------------------ |

| `--minimized`      | Start in the notification area |

| `--debug`          | Enable DEBUG logging           |

| `--reset-settings` | Restore default settings       |

| `--version`        | Print the version and exit     |



Example:



```powershell

python main.py --debug

```



\---



\## Where the application keeps its files



Nothing is written next to the source code.



Application data is stored in the user's profile:



```text

%APPDATA%\\SystemMonitor\\

│

├── settings.json

│

└── logs\\

&#x20;   └── system\_monitor.log

```



The log uses rotating files:



```text

1 MB × 3 backups

```



The exact paths are shown on the \*\*System Information\*\* page.



\---



\# 5. Running the tests



Install development dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Run:



```powershell

.venv\\Scripts\\python.exe -m pytest

```



Current test count:



> \*\*201 tests\*\*



| File                 | Covers                                              |

| -------------------- | --------------------------------------------------- |

| `test\_formatting.py` | Formatters, `None`, NaN and infinity                |

| `test\_ringbuffer.py` | Bounded memory, resizing and statistics             |

| `test\_rate.py`       | Counter → rate conversion, resets and TTL cache     |

| `test\_settings.py`   | Defaults, validation, atomic save and corrupt files |

| `test\_history.py`    | Graph series and capacity limits                    |

| `test\_monitoring.py` | Real machine monitoring and psutil failures         |

| `test\_sensors.py`    | Temperature provider chain                          |

| `test\_processes.py`  | Enumeration, termination and child processes        |

| `test\_config.py`     | Paths and platform detection                        |

| `test\_ui\_smoke.py`   | All eight pages, rendering, themes and settings     |



The monitoring tests run against the real machine but test \*\*properties and invariants\*\*, not fixed hardware values.



For example:



```text

0 ≤ CPU usage ≤ 100

used + free ≈ total

one entry per logical processor

```



The tests also inject failures into psutil to verify that monitoring continues safely.



The GUI tests use Qt's `offscreen` platform, so they can render the interface without opening a desktop window.



\### Coverage



```powershell

.venv\\Scripts\\python.exe -m pytest --cov=app --cov-report=term-missing

```



\---



\# 6. Building a standalone Windows executable



Install packaging dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Build:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm system\_monitor.spec

```



The output is:



```text

dist\\

└── SystemMonitor\\

&#x20;   ├── SystemMonitor.exe

&#x20;   └── \_internal\\

```



Run:



```powershell

dist\\SystemMonitor\\SystemMonitor.exe

```



Verify the packaged executable:



```powershell

.venv\\Scripts\\python.exe tools\\launch\_check.py --exe dist\\SystemMonitor\\SystemMonitor.exe

```



The launch check:



\* Starts the executable

\* Monitors it for several seconds

\* Measures CPU and memory usage

\* Checks the application log

\* Fails if the process exits early

\* Fails if an `ERROR` entry is written



\---



\## Folder build vs. one-file build



The default build is a folder-based PyInstaller application.



This is intentional.



A single-file executable has to extract the complete Qt runtime into a temporary directory every time it starts.



The folder build avoids that extraction step and provides faster startup.



If a single executable is required:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm --onefile --windowed `

&#x20;   --name SystemMonitor `

&#x20;   --icon assets\\icon.ico `

&#x20;   --add-data "assets;assets" `

&#x20;   main.py

```



The PyInstaller specification also excludes large Qt modules that the application does not use, including:



\* WebEngine

\* Quick/QML

\* Multimedia

\* 3D

\* Charts

\* SQL

\* Sensors



This keeps the packaged application substantially smaller.



\---



\## Regenerating the icon



The application icon is generated from the same vector artwork used by the interface.



No image editor is required.



```powershell

.venv\\Scripts\\python.exe tools\\make\_icon.py

```



Output:



```text

assets/icon.ico

assets/icon.png

```



\---



\# 7. Performance



Performance was measured on the development machine:



\*\*Intel Core i3-1115G4 · 4 logical processors · 4 GB RAM · Windows 11 25H2\*\*



Configuration:



\* Dashboard open

\* 1-second refresh interval

\* Normal background activity



Observed values:



| Metric          |                               Observed |

| --------------- | -------------------------------------: |

| Idle CPU        |                    \~1.5–5% of one core |

| Startup CPU     | \~30% of one core for first 2–3 seconds |

| Resident memory |                             \~50–115 MB |

| Graph memory    |                                Bounded |



CPU is measured using process CPU time over a 20-second window rather than relying only on instantaneous snapshots.



Actual values depend heavily on the machine's workload.



The development machine is a small laptop with limited RAM, so these values should not be treated as universal performance guarantees.



\---



\## Why the application stays lightweight



\### 1. Only visible UI is updated



Hidden pages do not continuously redraw.



\### 2. Pages are created lazily



Unused pages do not contribute their full UI cost during startup.



\### 3. Process enumeration is opt-in



The expensive process table is only collected while it is visible.



\### 4. Different data uses different cadences



Expensive information is not polled as frequently as cheap counters.



\### 5. Graphs use QPainter



The graphs are lightweight custom QPainter-based components rather than a large charting framework.



\### 6. History is bounded



Fixed-capacity ring buffers prevent unlimited memory growth.



\---



\# 8. Features that depend on hardware or Windows



System Monitor deliberately degrades to \*\*Unavailable\*\* when a feature cannot be provided.



| Feature                       | Requirement                    | If unavailable                            |

| ----------------------------- | ------------------------------ | ----------------------------------------- |

| CPU temperature               | Supported sensor               | Shows `Unavailable`                       |

| Per-process user/command line | Process permissions            | Restricted fields show `Access denied`    |

| Ending protected process      | Administrator rights           | Windows access error is reported          |

| Disk volume label             | Windows API                    | Field remains unavailable                 |

| Physical disk names           | Windows physical-drive handles | Section remains empty                     |

| Disk throughput               | OS I/O counters                | Rates show `Unavailable`                  |

| Page file                     | OS reports it                  | Shows no page file reported               |

| Load average                  | psutil support                 | Shows `Unavailable`                       |

| Adapter link speed            | Driver support                 | Shows `Unavailable`                       |

| Start with Windows            | Windows registry               | Option unavailable on unsupported systems |

| System tray                   | System tray support            | Tray option unavailable                   |

| Uptime / boot time            | Windows                        | Normally available                        |



\---



\## Deliberately not included



System Monitor does \*\*not\*\* generate:



\* Fake CPU temperatures

\* Random network speeds

\* Fake disk activity

\* Hard-coded hardware information

\* Simulated process data



If the machine does not expose a metric, the application says so.



\---



\# 9. Extending it



Adding a new metric follows a predictable process.



\### Step 1 — Add the model field



Add the field to the appropriate dataclass:



```text

app/models/snapshot.py

```



\### Step 2 — Collect the value



Implement collection inside the appropriate module:



```text

app/monitoring/

```



\### Step 3 — Handle errors



Wrap potentially failing calls with the existing safe-call helpers.



A failure should result in:



```text

None

```



rather than crashing the collector.



\### Step 4 — Add formatting



If necessary, add a formatter:



```text

app/utils/formatting.py

```



\### Step 5 — Add it to the UI



Use:



```text

InfoGrid

MetricCard

Graph

Table

```



depending on the type of metric.



\### Step 6 — Add tests



Test:



\* Normal collection

\* Missing values

\* Invalid values

\* Provider failures

\* UI display



For expensive metrics, use the existing TTL cache or page-activation mechanism.



\---



\# 📥 Download



\## Windows — v1.0.0



The easiest way to use System Monitor is to download the packaged Windows release.



\*\*\[Download System Monitor v1.0.0 →](https://github.com/SAIYAN36/System-Monitor/releases/tag/v1.0.0)\*\*



The release contains:



```text

SystemMonitor-v1.0.0-Windows-x64.zip

```



Extract the ZIP and run:



```text

SystemMonitor\\SystemMonitor.exe

```



No Python installation is required for the packaged version.



\---



\# 🤝 Contributing



Contributions are welcome.



Before submitting a change:



1\. Create a branch.

2\. Keep changes focused.

3\. Add tests for new functionality.

4\. Run the complete test suite.

5\. Verify the application manually when changing UI behavior.

6\. Document significant architectural changes.



Run the tests with:



```powershell

python -m pytest

```



\---



\# 🐛 Bug Reports



When reporting an issue, include:



\* System Monitor version

\* Windows version/build

\* Python version if running from source

\* Steps to reproduce

\* Relevant log output

\* Screenshots where useful



Please avoid posting sensitive system information.



\---



\# 📜 License



This project is released under the \*\*MIT License\*\*.



See \[`LICENSE`](LICENSE) for the complete license text.



\---



\# ⭐ System Monitor



Built with:



\*\*Python · PySide6 · psutil · PyInstaller\*\*



Real-time monitoring.



Real machine data.



No fabricated numbers.



