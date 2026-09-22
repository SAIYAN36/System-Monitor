\# 🖥️ System Monitor



> \*\*Real-time Windows system monitoring, built with Python, PySide6, and psutil.\*\*



System Monitor is a Windows desktop application that provides live information about CPU, memory, storage, network activity, processes, temperatures, and system configuration.



The application is designed around a simple principle:



> \*\*Real system data only. If the operating system cannot provide a value, System Monitor reports it as unavailable instead of fabricating one.\*\*



\---



<p align="center">



\*\*\[⬇️ Download](https://github.com/SAIYAN36/System-Monitor/releases/tag/v1.0.0)\*\* •

\*\*\[🐛 Report a Bug](https://github.com/SAIYAN36/System-Monitor/issues)\*\* •

\*\*\[💡 Request a Feature](https://github.com/SAIYAN36/System-Monitor/issues)\*\*



</p>



\---



\## 📸 Application Preview



<!--

Replace this diagram with a real screenshot when available:



!\[System Monitor Dashboard](assets/screenshots/dashboard.png)

\-->



```text

┌──────────────────────────────────────────────────────────────────────────────┐

│ SYSTEM MONITOR                                              ● Monitoring     │

│ v1.0.0                                                                        │

├────────────────┬─────────────────────────────────────────────────────────────┤

│                │  Dashboard                                                   │

│  ◈ Dashboard   │                                                              │

│                │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │

│  ◉ CPU         │  │ CPU USAGE      │ │ MEMORY         │ │ DISK           │  │

│                │  │                │ │                │ │                │  │

│  ▣ Memory      │  │    12.4%       │ │   3.1 / 3.9 GB │ │     41.7%      │  │

│                │  │   ▂▃▅▃▂▂▃      │ │   ▆▇▆▅▇▆▅      │ │    ▂▃▄▅▃▂      │  │

│  ◫ Disk        │  └────────────────┘ └────────────────┘ └────────────────┘  │

│                │                                                              │

│  ◇ Network     │  CPU HISTORY                                                │

│                │  100% ┤                                                     │

│  ☰ Processes   │   75% ┤       ╭╮                                            │

│                │   50% ┤  ╭────╯╰──╮       ╭──╮                             │

│  ⓘ System      │   25% ┤──╯          ╰─────╯  ╰──                           │

│                │    0% └──────────────────────────────────                   │

│  ⚙ Settings    │                                                              │

│                │  NETWORK                         SYSTEM UPTIME               │

│                │  ↓ 2.4 MB/s                      04:32:17                    │

│                │  ↑ 512 KB/s                                                  │

└────────────────┴─────────────────────────────────────────────────────────────┘

```



\---



\# ✨ Features



System Monitor contains eight dedicated monitoring pages.



| Page                | What it provides                                        |

| ------------------- | ------------------------------------------------------- |

| 📊 \*\*Dashboard\*\*    | Live overview of the entire system                      |

| 🧠 \*\*CPU\*\*          | CPU utilization, cores, threads, clocks and temperature |

| 💾 \*\*Memory\*\*       | RAM and page-file statistics                            |

| 💿 \*\*Disk\*\*         | Volumes, capacity and I/O activity                      |

| 🌐 \*\*Network\*\*      | Adapter information and network traffic                 |

| ⚙️ \*\*Processes\*\*    | Running processes and resource usage                    |

| 🖥️ \*\*System Info\*\* | Windows and hardware information                        |

| 🎨 \*\*Settings\*\*     | Monitoring and application configuration                |



\---



\## 📊 Dashboard



The Dashboard provides a live overview of the machine.



\### Metrics



\* CPU utilization

\* RAM utilization

\* Aggregate disk utilization

\* Network upload speed

\* Network download speed

\* System uptime

\* CPU temperature when available

\* Running process information

\* Current time



\### Live graphs



\* CPU usage

\* Memory usage

\* Network traffic

\* Disk activity



The Dashboard is designed to provide useful information without requiring the user to navigate through multiple pages.



\---



\# 🧠 CPU Monitoring



The CPU page provides detailed processor information.



\### Information available



\* Overall CPU utilization

\* Per-core utilization

\* Processor model

\* Physical core count

\* Logical processor count

\* Current clock speed

\* Maximum clock speed

\* CPU architecture

\* Load average

\* CPU temperature

\* Temperature sensor provider

\* CPU usage history



CPU data is collected independently from the UI thread.



\---



\# 💾 Memory Monitoring



The Memory page displays:



\* Total physical memory

\* Used memory

\* Available memory

\* Memory utilization

\* Page-file size

\* Page-file usage

\* Memory history



All values are collected from the operating system at runtime.



\---



\# 💿 Disk Monitoring



System Monitor automatically discovers mounted volumes.



For each volume it can display:



\* Drive name

\* Volume label

\* Capacity

\* Used space

\* Free space

\* Usage percentage

\* File system

\* Drive type



\### I/O monitoring



The application also tracks:



\* Read throughput

\* Write throughput

\* Cumulative read counters

\* Cumulative write counters

\* Disk activity history



Counter values are converted into rates using elapsed time between samples.



\---



\# 🌐 Network Monitoring



The Network page provides both traffic information and adapter details.



\### Traffic



\* Download speed

\* Upload speed

\* Total downloaded

\* Total uploaded

\* Traffic history



\### Adapter information



\* Adapter name

\* Link state

\* IPv4 address

\* IPv6 address

\* MAC address

\* Link speed

\* Per-adapter traffic



\---



\# ⚙️ Process Monitoring



The Processes page provides a sortable table of running processes.



\### Process information



\* Process name

\* PID

\* CPU usage

\* Memory percentage

\* Memory usage

\* Thread count

\* Process status

\* User information where permitted

\* Executable information where permitted

\* Command line where permitted



A search/filter field makes it easier to locate individual processes.



\### Process termination



The application provides a confirmed \*\*End Task\*\* operation.



Protected processes are handled gracefully. If Windows denies access, System Monitor reports the permission problem rather than crashing.



\### Performance consideration



Process enumeration is one of the most expensive monitoring operations.



For this reason:



> \*\*The process table is collected only while the Processes page is open.\*\*



When the page is closed, the process enumeration work stops.



\---



\# 🖥️ System Information



The System Information page displays:



\### Operating system



\* OS name

\* Windows edition

\* Windows build

\* Host name

\* Architecture

\* Machine type



\### Software



\* Python version

\* Qt version

\* psutil version



\### System state



\* Boot time

\* Uptime

\* Installed memory

\* Page-file size



\### Hardware



\* Volumes

\* Physical disks

\* Network adapters



\### Application



\* Log directory

\* Configuration location



\---



\# 🎨 Settings



System Monitor provides configurable application behavior.



\### Monitoring



\* Refresh interval

\* Graph history length

\* CPU temperature interval



\### Startup



\* Start with Windows

\* Start minimized



\### Tray



\* Keep running in notification area



\### Process management



\* Confirm before ending a process



\### Appearance



\* Dark theme

\* Light theme



\### Dashboard



\* Enable/disable dashboard cards

\* Enable/disable dashboard graphs



\---



\# 🏗️ Architecture



System Monitor separates monitoring, services, and UI responsibilities.



```text

&#x20;                        ┌───────────────────────┐

&#x20;                        │      PySide6 UI       │

&#x20;                        │                       │

&#x20;                        │ Dashboard             │

&#x20;                        │ CPU                   │

&#x20;                        │ Memory                │

&#x20;                        │ Disk                  │

&#x20;                        │ Network               │

&#x20;                        │ Processes             │

&#x20;                        │ System Info           │

&#x20;                        │ Settings              │

&#x20;                        └───────────┬───────────┘

&#x20;                                    │

&#x20;                             MetricsUpdate

&#x20;                                    │

&#x20;                                    ▼

&#x20;                        ┌───────────────────────┐

&#x20;                        │    MonitorWorker      │

&#x20;                        │       QThread         │

&#x20;                        └───────────┬───────────┘

&#x20;                                    │

&#x20;                                    ▼

&#x20;                        ┌───────────────────────┐

&#x20;                        │    SystemMonitor      │

&#x20;                        │                       │

&#x20;                        │ CPU                   │

&#x20;                        │ Memory                │

&#x20;                        │ Disk                  │

&#x20;                        │ Network               │

&#x20;                        │ Processes             │

&#x20;                        │ System                │

&#x20;                        │ Sensors               │

&#x20;                        └───────────┬───────────┘

&#x20;                                    │

&#x20;                        ┌───────────▼───────────┐

&#x20;                        │        psutil         │

&#x20;                        │    Windows APIs       │

&#x20;                        │       Sensors         │

&#x20;                        └───────────────────────┘

```



\### Separation of responsibilities



```text

app.monitoring

&#x20;     │

&#x20;     ├── Collects system data

&#x20;     ├── No Qt widgets

&#x20;     └── Independently testable



app.services

&#x20;     │

&#x20;     ├── Background monitoring

&#x20;     ├── Settings

&#x20;     ├── Logging

&#x20;     ├── History

&#x20;     └── Windows startup



app.ui

&#x20;     │

&#x20;     ├── PySide6 interface

&#x20;     ├── Pages

&#x20;     ├── Widgets

&#x20;     ├── Themes

&#x20;     └── Navigation

```



The monitoring layer never directly manipulates the UI.



The UI never calls psutil directly.



\---



\# 🧵 Threading Model



System monitoring runs in a dedicated worker thread.



```text

&#x20;             GUI THREAD

┌──────────────────────────────────┐

│                                  │

│ MainWindow                       │

│ ├── Sidebar                      │

│ ├── Visible Page                 │

│ └── Status Bar                   │

│                                  │

└───────────────▲──────────────────┘

&#x20;               │

&#x20;         Qt Signal

&#x20;      MetricsUpdate

&#x20;               │

┌───────────────┴──────────────────┐

│        MONITOR WORKER            │

│            QThread               │

│                                  │

│  SystemMonitor.collect()         │

│            ↓                     │

│  MetricHistory.append()          │

│            ↓                     │

│  sleep(interval - work\_time)     │

│                                  │

└──────────────────────────────────┘

```



This prevents slow system queries from blocking the GUI.



Each update is represented as an immutable `MetricsUpdate` containing the current snapshot and graph data.



\---



\# ⚡ Performance Design



Performance is part of the architecture.



\## Visible-page updates



Only the currently visible page receives UI updates.



Hidden pages do not continuously redraw.



\## Lazy page creation



Pages are created when first visited rather than constructing all eight screens during startup.



\## Process enumeration



The process table is collected only when its page is active.



\## Cached information



Information that rarely changes is cached using TTL-based caching.



Examples:



\* Volume lists

\* Network adapter lists

\* Operating system information

\* Temperature readings



\## Bounded graph history



Graphs use fixed-capacity buffers.



Old samples are discarded automatically.



This prevents graph history from growing indefinitely.



\---



\# 📈 Monitoring Cadence



Different data is collected at different frequencies.



| Data                |             Cadence | Reason                         |

| ------------------- | ------------------: | ------------------------------ |

| CPU usage           |          Every poll | Cheap                          |

| Memory              |          Every poll | Cheap                          |

| Network counters    |          Every poll | Cheap                          |

| Disk counters       |          Every poll | Cheap                          |

| Volume information  |        5–30 seconds | Rarely changes                 |

| Adapter information |        5–30 seconds | Rarely changes                 |

| OS information      |              Cached | Rarely changes                 |

| Temperature         |         \~30 seconds | Sensor access can be expensive |

| Processes           | Processes page only | Most expensive operation       |



The default monitoring interval is configurable between \*\*500 ms and 10 seconds\*\*.



\---



\# 📡 Rates Instead of Counters



Windows exposes cumulative network and disk byte counters.



System Monitor converts these counters into rates:



```text

rate = counter\_difference / elapsed\_time

```



The implementation uses `time.perf\_counter()` for accurate interval measurements.



If a counter decreases, the application treats it as a reset instead of generating a false traffic spike.



The first reading of a counter is therefore reported as:



> \*\*Unavailable\*\*



A valid rate becomes available after the next sample.



\---



\# 🌡️ Temperature Monitoring



CPU temperature is hardware-dependent.



System Monitor uses a provider chain:



```text

&#x20;            Temperature Request

&#x20;                     │

&#x20;                     ▼

&#x20;         ┌─────────────────────┐

&#x20;         │ psutil sensors      │

&#x20;         └──────────┬──────────┘

&#x20;                    │ unavailable

&#x20;                    ▼

&#x20;         ┌─────────────────────┐

&#x20;         │ LibreHardwareMonitor│

&#x20;         │ OpenHardwareMonitor │

&#x20;         └──────────┬──────────┘

&#x20;                    │ unavailable

&#x20;                    ▼

&#x20;         ┌─────────────────────┐

&#x20;         │ Windows ACPI        │

&#x20;         │ Thermal Zone        │

&#x20;         └──────────┬──────────┘

&#x20;                    │ unavailable

&#x20;                    ▼

&#x20;               Unavailable

```



The application never invents a temperature.



If no provider works, the UI displays the reason.



Because ACPI queries can block, temperature reading is isolated from the main monitoring thread.



\---



\# 🛡️ Error Handling



Monitoring applications interact with hardware and operating-system APIs that can fail.



System Monitor treats individual failures as isolated events.



Examples:



```text

Sensor unavailable

&#x20;      ↓

CPU temperature = None

&#x20;      ↓

UI displays "Unavailable"

```



A disappearing drive:



```text

Volume disappears

&#x20;      ↓

Collector skips the volume

&#x20;      ↓

Other volumes continue working

```



A protected process:



```text

PermissionError

&#x20;      ↓

Readable fields remain

&#x20;      ↓

Restricted fields marked "Access denied"

```



A failed subsystem should never bring down the entire monitoring application.



\---



\# 🧪 Testing



The project currently contains:



> \*\*201 tests\*\*



Run the complete test suite:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

.venv\\Scripts\\python.exe -m pytest

```



\## Test coverage



| Test module          | Purpose                                      |

| -------------------- | -------------------------------------------- |

| `test\_formatting.py` | Formatting and edge cases                    |

| `test\_ringbuffer.py` | Fixed-capacity buffers                       |

| `test\_rate.py`       | Counter → rate conversion                    |

| `test\_settings.py`   | Settings and persistence                     |

| `test\_history.py`    | Graph history                                |

| `test\_monitoring.py` | Real-machine monitoring and failure handling |

| `test\_sensors.py`    | Temperature provider chain                   |

| `test\_processes.py`  | Process enumeration and termination          |

| `test\_config.py`     | Paths and platform detection                 |

| `test\_ui\_smoke.py`   | UI rendering and page checks                 |



The monitoring tests verify invariants rather than hard-coded hardware values.



For example:



\* CPU percentages remain within valid bounds

\* Memory values remain consistent

\* Every logical processor is represented

\* Failed psutil calls are handled safely



The GUI tests use Qt's offscreen platform and therefore do not require an interactive desktop window.



\---



\# 📦 Building the Windows Executable



Install development dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Build with PyInstaller:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm system\_monitor.spec

```



Output:



```text

dist/

└── SystemMonitor/

&#x20;   ├── SystemMonitor.exe

&#x20;   └── \_internal/

```



Verify the packaged application:



```powershell

.venv\\Scripts\\python.exe tools\\launch\_check.py --exe dist\\SystemMonitor\\SystemMonitor.exe

```



The launcher check verifies that the executable starts correctly, monitors its resource usage, and checks its application log.



\---



\# 📁 Project Structure



```text

System-Monitor/

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

├── assets/

│   ├── icon.ico

│   └── icon.png

│

├── tests/

│

├── tools/

│   ├── launch\_check.py

│   └── make\_icon.py

│

├── main.py

├── pyproject.toml

├── requirements.txt

├── requirements-dev.txt

├── system\_monitor.spec

├── run.bat

├── README.md

└── SystemMonitor-v1.0.0-Windows-x64.zip

```



\---



\# 📂 Application Data



System Monitor does not store application data next to the source code.



User-specific data is stored under:



```text

%APPDATA%\\SystemMonitor\\

│

├── settings.json

│

└── logs\\

&#x20;   └── system\_monitor.log

```



The application exposes the exact locations through the System Information page.



\---



\# 🖥️ Hardware \& Windows Dependencies



Some functionality depends on the operating system, hardware, firmware, or drivers.



| Feature                    | Requirement                    |

| -------------------------- | ------------------------------ |

| CPU temperature            | Supported sensor provider      |

| Process command line       | Sufficient process permissions |

| Ending protected processes | Administrator privileges       |

| Volume label               | Windows volume APIs            |

| Physical disk names        | Windows physical-drive APIs    |

| Disk throughput            | OS-level I/O counters          |

| Page file                  | OS-reported page file          |

| Adapter link speed         | Network driver                 |

| Start with Windows         | Windows registry               |

| System tray                | System tray support            |



When a feature is unavailable, System Monitor reports:



> \*\*Unavailable\*\*



rather than generating a plausible-looking value.



\---



\# 🔧 Extending System Monitor



Adding a new metric follows a predictable architecture.



\### 1. Add the data model



Add the new field to the appropriate dataclass in:



```text

app/models/snapshot.py

```



\### 2. Collect the value



Implement collection inside the appropriate module:



```text

app/monitoring/

```



\### 3. Handle failures



Use the existing safe-call mechanisms so a failed metric becomes `None`.



\### 4. Format the value



Add formatting logic to:



```text

app/utils/formatting.py

```



\### 5. Display it



Use the appropriate UI component:



```text

InfoGrid

MetricCard

Graph

Table

```



\### 6. Test it



Add tests covering both:



\* successful collection

\* failure/unavailable behavior



For expensive metrics, use TTL caching or page activation to avoid unnecessary work.



\---



\# 🎯 Design Principles



System Monitor follows several core principles.



\### Real data



Every displayed metric originates from the operating system or a supported hardware provider.



\### No fabricated values



Missing information is shown as unavailable.



\### Graceful degradation



One failing sensor or subsystem should not crash the application.



\### Separation of concerns



Monitoring, services, and UI remain independently testable.



\### Bounded resources



Caches and graph histories have explicit limits.



\### Responsive interface



System queries remain outside the GUI thread.



\### Hardware-aware behavior



The application adapts to what the machine actually exposes.



\---



\# 📈 Performance



Performance measurements were taken on the development machine:



\*\*Intel Core i3-1115G4 · 4 logical processors · 4 GB RAM · Windows 11 25H2\*\*



With:



\* Dashboard open

\* 1-second refresh interval

\* Normal background activity



Observed values:



| Metric          |                                   Observed |

| --------------- | -----------------------------------------: |

| Idle CPU        |                        \~1.5–5% of one core |

| Startup CPU     | \~30% of one core for the first 2–3 seconds |

| Resident memory |                                 \~50–115 MB |

| Graph memory    |                                    Bounded |



These numbers are environment-dependent and should not be interpreted as hardware-independent guarantees.



\---



\# 🚀 Release



\## v1.0.0



The first public release includes:



\* Complete eight-page monitoring interface

\* CPU monitoring

\* Memory monitoring

\* Disk monitoring

\* Network monitoring

\* Process monitoring

\* System information

\* Temperature provider chain

\* Dark/light themes

\* Windows startup support

\* System tray support

\* Configurable refresh rates

\* PyInstaller Windows build

\* 201 automated tests



\### Download



\*\*\[Download System Monitor v1.0.0 →](https://github.com/SAIYAN36/System-Monitor/releases/tag/v1.0.0)\*\*



\---



\# 🤝 Contributing



Contributions are welcome.



Before submitting a pull request:



1\. Fork the repository.

2\. Create a feature branch.

3\. Keep changes focused.

4\. Add tests for new behavior.

5\. Run the complete test suite.

6\. Document significant changes.

7\. Submit a pull request.



Example:



```powershell

python -m pytest

```



\---



\# 🐛 Issues \& Feature Requests



Found a bug or have an idea?



Open an issue:



\*\*\[Create an Issue →](https://github.com/SAIYAN36/System-Monitor/issues)\*\*



When reporting a bug, include:



\* Windows version

\* Python version if running from source

\* System Monitor version

\* Steps to reproduce

\* Relevant log output

\* Screenshots when useful



\---



\# ⭐ Support the Project



If System Monitor is useful to you:



⭐ \*\*Star the repository\*\*



🐛 \*\*Report bugs\*\*



💡 \*\*Suggest features\*\*



🔧 \*\*Contribute improvements\*\*



📢 \*\*Share the project\*\*



\---



\# 📜 License



System Monitor is released under the \*\*MIT License\*\*.



See \[`LICENSE`](LICENSE) for the complete license text.



\---



<div align="center">



\### System Monitor



\*\*Real-time monitoring. Real system data. No fabricated numbers.\*\*



Built with \*\*Python · PySide6 · psutil\*\*



\[GitHub Repository](https://github.com/SAIYAN36/System-Monitor)



</div>



