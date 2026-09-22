\# 🖥️ System Monitor



A real-time system monitoring desktop application for Windows, built with \*\*Python\*\*, \*\*PySide6\*\* (Qt 6), and \*\*psutil\*\*.



Every value on every screen comes from the machine it is running on. Nothing is simulated, randomized, or hard-coded. CPU load, memory, disks, network adapters, processes, drive labels, temperatures, and Windows build numbers are all read from the operating system at runtime.



\---



```text

┌───────────────────────────────────────────────────────────────────────────┐

│  System Monitor            Dashboard                                      │

│  v1.0.0                    Live system overview, refreshed automatically.  │

│  ┌──────────────┐  ┌───────────────────────┐ ┌─────────────────────────┐   │

│  │ ▤ Dashboard  │  │ CPU usage   12.4%     │ │ RAM usage      78.2%    │   │

│  ├──────────────┤  │ 2 cores / 4 threads   │ │ 3.1 GB of 3.9 GB in use │   │

│  │ ▢ CPU        │  │ ▇▇▇▇░░░░░░░░░░░░░░░░░ │ │ ▇▇▇▇▇▇▇▇▇▇▇▇▇▇░░░░░░ │   │

│  │ ▤ Memory     │  └───────────────────────┘ └─────────────────────────┘   │

│  │ ▣ Disk       │                                                         │

│  │ ⬡ Network    │  CPU ────────────────╮                                  │

│  │ ☰ Processes  │                      ╰────╮                             │

│  │ ⓘ System     │                           ╰────────                     │

│  │ ⚙ Settings   │                                                         │

│  └──────────────┘                                                         │

└───────────────────────────────────────────────────────────────────────────┘

```



\---



\## 📋 Table of Contents



\* \[What is included](#1-what-is-included)

\* \[Project structure](#2-project-structure)

\* \[How the monitoring works](#3-how-the-monitoring-works)

\* \[Installing and running](#4-installing-and-running)

\* \[Running the tests](#5-running-the-tests)

\* \[Building a standalone Windows executable](#6-building-a-standalone-windows-executable)

\* \[Performance](#7-performance)

\* \[Features that depend on hardware or Windows](#8-features-that-depend-on-the-hardware-or-on-windows)

\* \[Extending it](#9-extending-it)



\---



\# 1. What is included



\## Dashboard



The Dashboard provides a live overview of the system, including:



\* CPU usage

\* RAM usage

\* Aggregate disk usage

\* Network upload/download speed

\* System uptime

\* CPU temperature, when available

\* Running process count

\* Current time

\* Live CPU graph

\* Live memory graph

\* Live network graph

\* Live disk graph



\---



\## CPU



The CPU page provides:



\* Overall CPU utilization

\* Per-core utilization

\* Processor model

\* Physical core count

\* Thread count

\* Current clock speed

\* Maximum clock speed

\* CPU architecture

\* Load average

\* Usage history graph

\* CPU temperature

\* Temperature sensor/provider name



\---



\## Memory



The Memory page provides:



\* Total RAM

\* Used RAM

\* Available RAM

\* Memory utilization

\* Memory usage history

\* Page file / swap information

\* Page file utilization gauge



\---



\## Disk



Every mounted volume is detected automatically.



For each volume, the application can display:



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

\* Disk activity graph



\---



\## Network



The Network page provides:



\* Upload speed

\* Download speed

\* Cumulative network totals

\* Primary IPv4 address

\* Network traffic graph

\* Adapter information

\* Link state

\* IP addresses

\* MAC address

\* Link speed

\* Adapter traffic totals



\---



\## Processes



The Processes page provides a sortable table containing:



\* Process name

\* PID

\* CPU usage

\* Memory percentage

\* Memory usage

\* Thread count

\* Process status



Additional functionality includes:



\* Process filtering

\* Process details panel

\* Confirmed \*\*End task\*\* action



Process enumeration is deliberately enabled only while the Processes page is visible because it is one of the most expensive monitoring operations.



\---



\## System Information



The System Information page provides:



\* Operating system name

\* Windows edition

\* Windows build

\* Host name

\* Architecture

\* Machine type

\* Python version

\* Qt version

\* psutil version

\* Boot time

\* System uptime

\* Installed memory

\* Page file size

\* Mounted volumes

\* Physical disks

\* Network adapters

\* Application log directory



\---



\## Settings



Configurable settings include:



\* Refresh interval

\* Graph history length

\* CPU temperature reading interval

\* Start minimized

\* Start with Windows

\* Keep running in the notification area

\* Confirm before ending a process

\* Dark/light theme

\* Dashboard cards

\* Dashboard graphs



\---



\# 2. Project structure



```text

system\_monitor/

├── main.py

├── requirements.txt

├── requirements-dev.txt

├── pyproject.toml

├── system\_monitor.spec

├── README.md

│

├── app/

│   ├── config.py

│   │

│   ├── models/

│   │   └── snapshot.py

│   │

│   ├── monitoring/

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

│   ├── services/

│   │   ├── monitor\_service.py

│   │   ├── history.py

│   │   ├── settings.py

│   │   ├── logging\_service.py

│   │   └── autostart.py

│   │

│   ├── ui/

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

├── tests/

│

├── tools/

│   ├── launch\_check.py

│   └── make\_icon.py

│

└── assets/

&#x20;   ├── icon.ico

&#x20;   └── icon.png

```



\### Architecture



The project uses a strict separation between monitoring, application services, and the Qt interface.



```text

┌─────────────────────────────────────────────────────┐

│                       UI                            │

│                    PySide6                         │

└───────────────────────┬─────────────────────────────┘

&#x20;                       │

&#x20;                       ▼

┌─────────────────────────────────────────────────────┐

│                    Services                         │

│       Worker • History • Settings • Logging         │

└───────────────────────┬─────────────────────────────┘

&#x20;                       │

&#x20;                       ▼

┌─────────────────────────────────────────────────────┐

│                   Monitoring                        │

│       CPU • RAM • Disk • Network • Processes       │

└───────────────────────┬─────────────────────────────┘

&#x20;                       │

&#x20;                       ▼

┌─────────────────────────────────────────────────────┐

│                    Windows                          │

│                 Operating System                    │

└─────────────────────────────────────────────────────┘

```



The layering is intentional:



\* `app.monitoring` does not import Qt.

\* `app.utils` does not import Qt.

\* The UI never accesses `psutil` directly.

\* The monitoring layer never accesses UI components.

\* The monitoring layer can therefore be tested without a graphical display.



\---



\# 3. How the monitoring works



\## Threading



System monitoring runs away from the GUI thread.



```text

&#x20;         GUI THREAD                         MONITOR WORKER

┌─────────────────────────┐          ┌───────────────────────────┐

│                         │          │                           │

│      MainWindow         │          │       MonitorWorker       │

│                         │          │                           │

│  ┌───────────────────┐  │          │  SystemMonitor.collect()  │

│  │     Sidebar       │  │          │            │              │

│  └───────────────────┘  │          │            ▼              │

│                         │          │  MetricHistory.append()   │

│  ┌───────────────────┐  │          │            │              │

│  │   Visible Page    │◄─┼──────────┤            ▼              │

│  └───────────────────┘  │ Metrics  │       sleep(interval)    │

│                         │ Update   │                           │

│      Status Bar         │          └───────────────────────────┘

└─────────────────────────┘

```



Every `psutil` call occurs on the worker thread.



This prevents slow system queries from freezing the graphical interface.



Each reading is delivered as one immutable `MetricsUpdate` containing:



\* A `Snapshot`

\* Graph data

\* Plain tuples rather than mutable shared objects



\### Visible-page optimization



Only the currently visible page receives updates.



Hidden pages receive no UI updates.



Pages are also created lazily when first opened.



This means that while one page is being viewed, the other screens do not continuously perform UI update work.



\---



\## Process enumeration is opt-in



Walking the Windows process table is one of the most expensive operations in the application.



Therefore:



```text

Dashboard

&#x20;  │

&#x20;  └── Process count only

&#x20;            │

&#x20;            ▼

&#x20;     Processes page

&#x20;            │

&#x20;            ▼

&#x20;  Enable process enumeration

&#x20;            │

&#x20;            ▼

&#x20;     Live process table

&#x20;            │

&#x20;            ▼

&#x20;       Leave page

&#x20;            │

&#x20;            ▼

&#x20;  Disable enumeration

```



The Dashboard therefore does not fabricate a process count when detailed enumeration is disabled.



It reports that detailed process information is available while the Processes page is open.



\### Process CPU calculation



Process CPU percentages require consecutive samples from the same `psutil.Process` object.



The collector therefore maintains a PID-based cache:



```text

PID

&#x20;│

&#x20;▼

psutil.Process object

&#x20;│

&#x20;├── Previous CPU sample

&#x20;│

&#x20;└── Current CPU sample

&#x20;         │

&#x20;         ▼

&#x20;      CPU %

```



Creating a new `Process` object on every sweep would prevent psutil from having the previous sample needed for meaningful CPU percentages.



Dead PIDs are removed from the cache after each sweep so the cache cannot grow indefinitely.



\---



\## Rates instead of counters



Windows exposes cumulative byte counters.



Network and disk throughput are calculated from consecutive samples:



```text

Current counter

&#x20;     -

Previous counter

&#x20;     │

&#x20;     ▼

&#x20;  Difference

&#x20;     │

&#x20;     ÷

Elapsed time

&#x20;     │

&#x20;     ▼

&#x20;  Throughput

```



The calculation lives in:



```text

app/monitoring/rate.py

```



\### High-resolution timing



The application uses:



```python

time.perf\_counter()

```



instead of `time.monotonic()` for rate calculations on Windows.



This provides the higher-resolution timing needed to avoid losing short intervals.



\### Counter resets



A negative counter delta indicates that the underlying counter was reset.



For example:



\* Network adapter recreation

\* Resume from sleep

\* Driver reset



Rather than displaying a huge fake spike, the sample is treated as unavailable.



The first sample for a counter is also unavailable because there is no previous value to calculate a rate from.



\---



\## Caching and cadence



Different types of information are collected at different frequencies.



| Data             |               Cadence | Reason                     |

| ---------------- | --------------------: | -------------------------- |

| CPU              |            Every poll | Cheap counter              |

| Memory           |            Every poll | Cheap counter              |

| Network counters |            Every poll | Required for rates         |

| Disk counters    |            Every poll | Required for rates         |

| Volume list      |          5–30 seconds | Changes rarely             |

| Adapter list     |          5–30 seconds | Changes rarely             |

| OS information   |                Cached | Changes rarely             |

| CPU temperature  | 30 seconds by default | Sensor queries can be slow |

| Process table    |   Processes page only | Expensive enumeration      |



The refresh interval can be configured between \*\*500 ms and 10 seconds\*\*.



\---



\## Temperature: a chain of providers



CPU temperature is hardware-dependent and Windows does not provide a universal temperature API for normal applications.



The application therefore uses a provider chain.



\### Provider order



1\. `psutil.sensors\_temperatures()`

2\. LibreHardwareMonitor / OpenHardwareMonitor through WMI

3\. ACPI thermal zone through Windows WMI



When a provider succeeds, the application remembers it.



If all providers fail, the failure is cached temporarily so the application does not repeatedly launch expensive sensor queries.



```text

&#x20;                Temperature Request

&#x20;                        │

&#x20;                        ▼

&#x20;             ┌─────────────────────┐

&#x20;             │ psutil temperature  │

&#x20;             └──────────┬──────────┘

&#x20;                        │

&#x20;                   unavailable

&#x20;                        │

&#x20;                        ▼

&#x20;             ┌─────────────────────┐

&#x20;             │ Hardware Monitor    │

&#x20;             │ WMI provider        │

&#x20;             └──────────┬──────────┘

&#x20;                        │

&#x20;                   unavailable

&#x20;                        │

&#x20;                        ▼

&#x20;             ┌─────────────────────┐

&#x20;             │ ACPI Thermal Zone   │

&#x20;             └──────────┬──────────┘

&#x20;                        │

&#x20;                        ▼

&#x20;                   Temperature

&#x20;                        │

&#x20;                        └── or ──► Unavailable

```



The ACPI provider runs in its own daemon thread because the query can block for several seconds.



The monitoring worker never waits for it.



\---



\## Never crashing



System information is inherently unreliable.



Hardware can disappear, permissions can change, processes can terminate between two reads, and individual sensors may not exist.



The application handles these situations instead of allowing one failure to terminate the entire monitoring system.



```text

System query

&#x20;    │

&#x20;    ▼

&#x20;┌─────────┐

&#x20;│ Success │──────► Value

&#x20;└────┬────┘

&#x20;     │

&#x20;   Failure

&#x20;     │

&#x20;     ▼

&#x20;┌──────────────┐

&#x20;│ safe\_call()  │

&#x20;└──────┬───────┘

&#x20;       │

&#x20;       ▼

&#x20;     None

&#x20;       │

&#x20;       ▼

&#x20;  "Unavailable"

```



Examples:



\* A missing metric becomes `None`.

\* A missing volume is skipped.

\* A process that exits during enumeration is ignored.

\* A protected process may return partially readable information.

\* A `PermissionError` is represented as access denied.

\* A failing subsystem does not terminate the entire collector.



The monitoring test suite also injects failures into CPU, memory, disk, network, and process queries to verify this behavior.



\---



\# 4. Installing and running



\## Requirements



\* Windows

\* Python \*\*3.10+\*\*

\* Python \*\*3.11.9\*\* used during development/testing



\### Clone the repository



```powershell

git clone https://github.com/SAIYAN36/System-Monitor.git

cd System-Monitor

```



\### Create a virtual environment



```powershell

python -m venv .venv

```



\### Install dependencies



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements.txt

```



\### Run the application



```powershell

.venv\\Scripts\\python.exe main.py

```



\---



\## Activating the virtual environment



PowerShell:



```powershell

.venv\\Scripts\\Activate.ps1

python main.py

```



Command Prompt:



```cmd

.venv\\Scripts\\activate

python main.py

```



\---



\## Command-line flags



| Flag               | Description                                |

| ------------------ | ------------------------------------------ |

| `--minimized`      | Start in the notification area             |

| `--debug`          | Enable DEBUG-level logging                 |

| `--reset-settings` | Ignore saved settings and restore defaults |

| `--version`        | Print the application version and exit     |



Example:



```powershell

python main.py --debug

```



\---



\## Application data



System Monitor does not write configuration files next to the source code.



User data is stored under:



```text

%APPDATA%\\SystemMonitor\\

├── settings.json

└── logs\\

&#x20;   └── system\_monitor.log

```



The log uses rotating files:



```text

1 MB × 3 backups

```



The exact locations are also shown on the \*\*System Information\*\* page.



\---



\# 5. Running the tests



Install development dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Run the complete test suite:



```powershell

.venv\\Scripts\\python.exe -m pytest

```



The project currently contains \*\*201 tests\*\*.



\## Test coverage



| Test file            | Purpose                                                  |

| -------------------- | -------------------------------------------------------- |

| `test\_formatting.py` | Formatting functions, including invalid values           |

| `test\_ringbuffer.py` | Fixed-capacity buffers and resizing                      |

| `test\_rate.py`       | Counter-to-rate conversion and reset detection           |

| `test\_settings.py`   | Defaults, validation, persistence and corrupted settings |

| `test\_history.py`    | Graph history and capacity limits                        |

| `test\_monitoring.py` | Real-machine monitoring and failure handling             |

| `test\_sensors.py`    | Temperature provider chain                               |

| `test\_processes.py`  | Process enumeration and termination safety               |

| `test\_config.py`     | Path and platform configuration                          |

| `test\_ui\_smoke.py`   | Rendering and UI smoke tests                             |



\### Headless GUI tests



Qt's `offscreen` platform plugin is used for GUI tests.



This allows the test suite to render the application's pages without opening visible windows.



Monitoring tests intentionally validate \*\*invariants\*\* instead of fixed hardware values.



For example:



```text

CPU percentage → 0–100

Memory used + available → total

CPU core count → matches detected processors

```



This allows the tests to run against different machines without pretending that every machine has identical hardware.



\### Coverage



```powershell

.venv\\Scripts\\python.exe -m pytest --cov=app --cov-report=term-missing

```



\---



\# 6. Building a standalone Windows executable



Install development dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Build using PyInstaller:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm system\_monitor.spec

```



The result will be:



```text

dist\\

└── SystemMonitor\\

&#x20;   ├── SystemMonitor.exe

&#x20;   └── \_internal\\

```



\---



\## Build verification



The project includes a launch verification tool:



```powershell

.venv\\Scripts\\python.exe tools\\launch\_check.py --exe dist\\SystemMonitor\\SystemMonitor.exe

```



The tool:



1\. Starts the executable.

2\. Monitors it for several seconds.

3\. Measures CPU usage.

4\. Measures memory usage.

5\. Checks the application log.

6\. Detects early crashes.

7\. Fails if unexpected `ERROR` entries appear.



Without `--exe`, it checks the source version of the application.



\---



\## Why a folder build?



The project intentionally uses a folder-based PyInstaller build instead of `--onefile`.



A one-file executable has to unpack the Qt runtime into a temporary directory during every launch.



That can increase startup time.



The normal build therefore produces:



```text

SystemMonitor.exe

\_internal\\

```



instead of one compressed executable.



\---



\## One-file build



If a single executable is required:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm --onefile --windowed ^

&#x20;   --name SystemMonitor ^

&#x20;   --icon assets\\icon.ico ^

&#x20;   --add-data "assets;assets" ^

&#x20;   main.py

```



\---



\## Bundle optimization



The PyInstaller specification excludes Qt modules that the application does not use, including:



\* WebEngine

\* Quick/QML

\* Multimedia

\* 3D

\* Charts

\* SQL

\* Unused sensor modules



This keeps the generated bundle significantly smaller than a generic PySide6 distribution.



\---



\## Regenerating the icon



The application icon is generated programmatically.



Run:



```powershell

.venv\\Scripts\\python.exe tools\\make\_icon.py

```



Generated files:



```text

assets/

├── icon.ico

└── icon.png

```



No image editor is required.



\---



\# 7. Performance



Performance was measured on the development machine:



```text

CPU:       Intel Core i3-1115G4

Processors: 4 logical processors

Memory:    4 GB RAM

OS:        Windows 11 25H2

Refresh:   1 second

Page:      Dashboard

```



Observed measurements:



| Metric          |                   Observed value |

| --------------- | -------------------------------: |

| Idle CPU        |              \~1.5–5% of one core |

| Startup CPU     | \~30% of one core for 2–3 seconds |

| Resident memory |                       \~50–115 MB |

| Graph memory    |                          Bounded |



These values are measurements from the development machine, not guaranteed requirements.



System load, paging, background applications, hardware, Windows configuration, and refresh interval can all change the numbers.



\---



\## Why it stays lightweight



\### 1. Only the visible page is updated



Hidden pages do not continuously redraw themselves.



\### 2. Expensive operations are conditional



Process enumeration occurs only while the Processes page is open.



\### 3. Rarely-changing information is cached



Device lists and hardware information do not need to be queried every second.



\### 4. Graphs use lightweight QPainter rendering



The graphs are implemented with a small custom rendering system instead of a large charting framework.



\### 5. History is bounded



Graph data uses fixed-capacity buffers.



Old samples are discarded automatically.



```text

New samples

&#x20;    │

&#x20;    ▼

┌───────────────────────────────┐

│ ● ● ● ● ● ● ● ● ● ● ● ● ● ● │

└───────────────────────────────┘

&#x20;               │

&#x20;               ▼

&#x20;       Oldest sample removed

```



History therefore cannot grow indefinitely.



\---



\## Making it even lighter



Open:



```text

Settings → Refresh interval

```



Increasing the interval to around \*\*2 seconds\*\* reduces monitoring frequency while remaining responsive for normal monitoring.



Dashboard graphs that are not needed can also be disabled.



\---



\# 8. Features that depend on hardware or Windows



System Monitor is designed to degrade gracefully.



If a capability is unavailable, it reports \*\*Unavailable\*\* instead of generating a fake value.



| Feature                    | Requirement                                              | If unavailable                        |

| -------------------------- | -------------------------------------------------------- | ------------------------------------- |

| CPU temperature            | Supported sensor, ACPI thermal zone, or hardware monitor | Displays `Unavailable`                |

| Process details            | Process permissions                                      | Protected fields show access denied   |

| Ending protected processes | Administrator privileges                                 | Reports access denied                 |

| Disk volume label          | Windows volume APIs                                      | Label may be unavailable              |

| Drive type                 | Windows drive APIs                                       | Type may be unavailable               |

| Physical disk names        | Windows physical-drive access                            | Section may be empty                  |

| Disk throughput            | OS disk counters                                         | Rates become unavailable              |

| Page file                  | OS-reported page file                                    | Reports no page file                  |

| Load average               | psutil/Windows support                                   | Displays `Unavailable`                |

| Adapter link speed         | Driver support                                           | Displays `Unavailable`                |

| Start with Windows         | Windows registry                                         | Option is Windows-only                |

| Notification area          | System tray support                                      | Tray functionality may be unavailable |

| Uptime                     | Operating system                                         | Normally available                    |

| Windows build              | Windows                                                  | Normally available                    |



\### CPU temperature



For better temperature support on Windows, running:



\*\*LibreHardwareMonitor\*\* or \*\*OpenHardwareMonitor\*\*



along with the optional Python `wmi` dependency can expose additional sensor information.



The application does not invent a temperature when no sensor is available.



\---



\## Design principle



The application deliberately follows one rule:



> \*\*If the operating system cannot provide a value, System Monitor reports that it is unavailable.\*\*



It does not generate random values, estimate hardware statistics without evidence, or display placeholder numbers as real measurements.



\---



\# 9. Extending it



Adding a new metric follows a predictable process.



\### 1. Add the metric to the model



Update the relevant dataclass in:



```text

app/models/snapshot.py

```



\### 2. Collect the metric



Add the collection logic to the appropriate module:



```text

app/monitoring/

```



Wrap potentially failing system calls with the project's safe error-handling helpers.



\### 3. Add formatting



If necessary, add a formatter to:



```text

app/utils/formatting.py

```



`None` values should be displayed as:



```text

Unavailable

```



\### 4. Add it to the UI



Depending on the type of metric, use:



```text

InfoGrid

MetricCard

Graph

Gauge

Table

```



\### 5. Add tests



Add tests for:



\* Normal values

\* Missing values

\* Invalid values

\* System/API failures

\* Boundary conditions



\---



\## Adding expensive metrics



If a metric is expensive to collect, do not automatically run it every polling cycle.



Consider either:



\* Adding a TTL cache

\* Running it at a slower cadence

\* Enabling it only when the relevant page is visible



The process monitor is an example of this approach.



\---



\# 🛠️ Technology Stack



| Technology             | Purpose                             |

| ---------------------- | ----------------------------------- |

| \*\*Python\*\*             | Core application language           |

| \*\*PySide6\*\*            | Qt 6 desktop interface              |

| \*\*psutil\*\*             | System and process information      |

| \*\*PyInstaller\*\*        | Windows executable packaging        |

| \*\*pytest\*\*             | Automated testing                   |

| \*\*QPainter\*\*           | Lightweight graph/icon rendering    |

| \*\*Windows APIs / WMI\*\* | Windows-specific system information |



\---



\# 📁 Core Design Principles



System Monitor is built around several principles:



```text

Real data

&#x20;  │

&#x20;  ▼

No fake metrics

&#x20;  │

&#x20;  ▼

Safe collection

&#x20;  │

&#x20;  ▼

Isolated failures

&#x20;  │

&#x20;  ▼

Background monitoring

&#x20;  │

&#x20;  ▼

Responsive UI

&#x20;  │

&#x20;  ▼

Testable architecture

```



\### The project prioritizes:



\* Real machine data

\* No simulated statistics

\* Graceful hardware limitations

\* Responsive UI

\* Low background overhead

\* Modular architecture

\* Testability

\* Explicit error handling

\* Windows-native behavior where appropriate



\---



\# 📜 License



This project is open source.



See the repository license for the applicable terms.



\---



\# 👤 Author



Built by \*\*SAIYAN36\*\*.



GitHub:



\*\*https://github.com/SAIYAN36/System-Monitor\*\*



\---



<p align="center">

&#x20; <b>System Monitor</b><br>

&#x20; Real-time Windows monitoring without fake numbers.

</p>



