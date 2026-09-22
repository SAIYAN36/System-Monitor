\# System Monitor



> A lightweight, real-time Windows system monitoring desktop application built with Python, PySide6, and psutil.





```text

┌──────────────────────────────────────────────────────────────────────────────┐

│  SYSTEM MONITOR                                      ● Monitoring            │

│  v1.0.0                                                                      │

├───────────────┬──────────────────────────────────────────────────────────────┤

│               │  Dashboard                                                   │

│  ◈ Dashboard  │                                                              │

│               │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │

│  ◉ CPU        │  │ CPU            │ │ MEMORY         │ │ DISK           │   │

│               │  │                │ │                │ │                │   │

│  ▣ Memory     │  │    12.4%       │ │    3.1 / 3.9GB │ │     41.7%      │   │

│               │  │   ▂▃▅▃▂        │ │   ▆▇▆▅▇▆       │ │    ▂▃▄▅▃       │   │

│  ◫ Disk       │  └────────────────┘ └────────────────┘ └────────────────┘   │

│               │                                                              │

│  ◇ Network    │  CPU HISTORY                                                │

│               │  100% ┤                                                     │

│  ☰ Processes  │   75% ┤       ╭╮                                            │

│               │   50% ┤  ╭────╯╰──╮      ╭──╮                              │

│  ⓘ System     │   25% ┤──╯          ╰────╯  ╰──                             │

│               │    0% └──────────────────────────────────                   │

│  ⚙ Settings   │                                                              │

│               │  NETWORK                 UPTIME                              │

│               │  ↓ 2.4 MB/s              04:32:17                           │

│               │  ↑ 512 KB/s                                                  │

└───────────────┴──────────────────────────────────────────────────────────────┘

```



\---



\## ✨ Features



\### 📊 Dashboard



\* CPU utilization

\* RAM utilization

\* Aggregate disk usage

\* Network upload/download speed

\* System uptime

\* CPU temperature when available

\* Running process information

\* Current time

\* Live CPU, memory, network, and disk graphs



\### 🧠 CPU



\* Overall CPU utilization

\* Per-core utilization

\* Processor model

\* Physical cores

\* Logical processors

\* Current and maximum clock speed

\* Architecture

\* Load average

\* Temperature and sensor provider

\* Usage history



\### 💾 Memory



\* Total RAM

\* Used RAM

\* Available RAM

\* Memory utilization

\* Page file / swap information

\* Memory history



\### 💿 Disk



\* All mounted volumes

\* Capacity, used and free space

\* Usage percentage

\* File system

\* Drive type

\* Windows volume labels

\* Read/write throughput

\* Cumulative I/O counters

\* Disk activity graph



\### 🌐 Network



\* Upload/download speed

\* Cumulative network traffic

\* Primary IPv4 address

\* Adapter status

\* MAC addresses

\* Link speed

\* Per-adapter traffic

\* Network traffic graph



\### ⚙️ Processes



\* Running process list

\* PID

\* CPU usage

\* Memory usage

\* Thread count

\* Process status

\* Search/filter

\* Process details

\* Protected-process handling

\* Confirmed \*\*End Task\*\* action



Process enumeration is only enabled while the Processes page is open to avoid unnecessary system overhead.



\### 🖥️ System Information



Displays:



\* Windows edition and build

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



\### 🎨 Settings



\* Refresh interval

\* Graph history length

\* CPU temperature interval

\* Start minimized

\* Start with Windows

\* System tray behavior

\* Process termination confirmation

\* Dark/light theme

\* Dashboard cards

\* Dashboard graphs



\---



\# 🚀 Download



\## Windows



Download the latest Windows build from the Releases page:



\*\*\[⬇️ Download System Monitor v1.0.0](https://github.com/SAIYAN36/System-Monitor/releases/tag/v1.0.0)\*\*



The release contains a ready-to-run Windows build.



No Python installation is required when using the packaged executable.



\### Manual download



The repository also contains the Windows package:



`SystemMonitor-v1.0.0-Windows-x64.zip`



Extract the ZIP and run:



`SystemMonitor\\SystemMonitor.exe`



\---



\# 🛠️ Installation from Source



\## Requirements



\* Windows

\* Python 3.10+

\* Python 3.11.9 recommended for development



Clone the repository:



```bash

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



Run:



```powershell

.venv\\Scripts\\python.exe main.py

```



\### PowerShell



Alternatively:



```powershell

.venv\\Scripts\\Activate.ps1

python main.py

```



\---



\# 🎛️ Command-Line Options



| Option             | Description                    |

| ------------------ | ------------------------------ |

| `--minimized`      | Start in the notification area |

| `--debug`          | Enable DEBUG logging           |

| `--reset-settings` | Restore default settings       |

| `--version`        | Display application version    |



Example:



```powershell

python main.py --debug

```



\---



\# 🏗️ Architecture



System Monitor separates data collection, application services, and the graphical interface.



```text

&#x20;                   ┌─────────────────────┐

&#x20;                   │      PySide6 UI     │

&#x20;                   │                     │

&#x20;                   │ Dashboard           │

&#x20;                   │ CPU                 │

&#x20;                   │ Memory              │

&#x20;                   │ Disk                │

&#x20;                   │ Network             │

&#x20;                   │ Processes           │

&#x20;                   │ System Info         │

&#x20;                   │ Settings            │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                        MetricsUpdate

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │   MonitorWorker     │

&#x20;                   │      QThread        │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                   ┌──────────▼──────────┐

&#x20;                   │ SystemMonitor       │

&#x20;                   │                     │

&#x20;                   │ CPU                 │

&#x20;                   │ Memory              │

&#x20;                   │ Disk                │

&#x20;                   │ Network             │

&#x20;                   │ Processes           │

&#x20;                   │ System              │

&#x20;                   │ Sensors             │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                        ┌─────▼─────┐

&#x20;                        │   psutil  │

&#x20;                        │  Windows  │

&#x20;                        │  Sensors  │

&#x20;                        └───────────┘

```



The monitoring layer does not depend on Qt widgets, which allows it to be tested independently.



The UI does not call psutil directly.



\---



\# ⚡ Performance Design



Performance was considered part of the architecture rather than something added later.



\### Background monitoring



All psutil calls run on a worker thread rather than the GUI thread.



This prevents slow system queries from freezing the interface.



\### Lazy page creation



Pages are created when first opened instead of constructing every page during startup.



\### Visible-page updates



Only the currently visible page receives UI updates.



\### Process enumeration



The process table is collected only while the Processes page is active.



\### Cached information



Information that rarely changes uses TTL-based caching:



\* Volume information

\* Network adapter information

\* Operating-system information

\* Temperature readings



\### Fixed graph history



Graphs use bounded history buffers.



Old samples are discarded automatically, preventing unlimited memory growth.



\---



\# 🌡️ Temperature Monitoring



Windows does not provide a universal CPU-temperature API for normal applications.



System Monitor therefore uses a provider chain:



1\. `psutil.sensors\_temperatures()`

2\. LibreHardwareMonitor / OpenHardwareMonitor

3\. Windows ACPI thermal zones



When a temperature cannot be obtained, System Monitor displays:



> \*\*Unavailable\*\*



It does not generate fake temperature values.



\---



\# 🛡️ Error Handling



A hardware-monitoring application should continue working even when individual sensors or system calls fail.



System Monitor therefore treats individual failures as isolated events.



Examples:



\* Missing temperature sensor → `Unavailable`

\* Disconnected volume → skipped

\* Protected process → readable fields remain available

\* Permission error → marked as access denied

\* Failed subsystem → other monitoring continues



The monitoring layer uses safe-call helpers so an individual failing metric does not crash the entire application.



\---



\# 🧪 Testing



The project currently contains:



\*\*201 tests\*\*



Run the test suite with:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

.venv\\Scripts\\python.exe -m pytest

```



The tests cover:



| Test                 | Coverage                                  |

| -------------------- | ----------------------------------------- |

| `test\_formatting.py` | Formatting and edge cases                 |

| `test\_ringbuffer.py` | Fixed-capacity history                    |

| `test\_rate.py`       | Counter-to-rate conversion                |

| `test\_settings.py`   | Settings validation and persistence       |

| `test\_history.py`    | Graph history                             |

| `test\_monitoring.py` | Real system monitoring + failure handling |

| `test\_sensors.py`    | Temperature providers                     |

| `test\_processes.py`  | Process enumeration and termination       |

| `test\_config.py`     | Paths and platform detection              |

| `test\_ui\_smoke.py`   | All eight UI pages and rendering          |



The monitoring tests verify properties rather than expecting fixed hardware values.



For example:



\* CPU percentage stays within valid bounds

\* Memory totals remain consistent

\* Every logical processor is represented

\* Failed psutil calls are handled safely



GUI tests use Qt's offscreen platform, allowing them to run without opening windows.



\---



\# 📦 Building the Windows Executable



Install development dependencies:



```powershell

.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt

```



Build:



```powershell

.venv\\Scripts\\python.exe -m PyInstaller --noconfirm system\_monitor.spec

```



The result is:



```text

dist\\

└── SystemMonitor\\

&#x20;   ├── SystemMonitor.exe

&#x20;   └── \_internal\\

```



Run the executable:



```powershell

dist\\SystemMonitor\\SystemMonitor.exe

```



Verify the packaged build:



```powershell

.venv\\Scripts\\python.exe tools\\launch\_check.py --exe dist\\SystemMonitor\\SystemMonitor.exe

```



The project intentionally uses a folder-based PyInstaller build.



This avoids unpacking the entire Qt runtime into a temporary directory every time the application starts.



\---



\# 📁 Project Structure



```text

System-Monitor/

│

├── app/

│   ├── models/

│   ├── monitoring/

│   ├── services/

│   ├── ui/

│   │   ├── pages/

│   │   └── widgets/

│   └── utils/

│

├── assets/

│   ├── icon.ico

│   └── icon.png

│

├── tests/

├── tools/

│

├── main.py

├── pyproject.toml

├── requirements.txt

├── requirements-dev.txt

├── system\_monitor.spec

├── run.bat

├── README.md

│

└── SystemMonitor-v1.0.0-Windows-x64.zip

```



\---



\# 📂 Application Data



System Monitor does not write configuration files next to the source code.



User data is stored under:



```text

%APPDATA%\\SystemMonitor\\

├── settings.json

└── logs\\

&#x20;   └── system\_monitor.log

```



The application provides the exact paths through the System Information page.



\---



\# 📈 Performance



Measured on the development machine:



\*\*Intel Core i3-1115G4 · 4 logical processors · 4 GB RAM · Windows 11 25H2\*\*



With a 1-second refresh interval and Dashboard open:



| Metric          | Observed                                   |

| --------------- | ------------------------------------------ |

| Idle CPU        | \~1.5–5% of one core                        |

| Startup CPU     | \~30% of one core for the first 2–3 seconds |

| Resident memory | \~50–115 MB                                 |

| Graph history   | Fixed/bounded                              |



These measurements are environment-dependent and should not be treated as hardware-independent guarantees.



\---



\# 🔧 Extending the Project



To add a new metric:



1\. Add the field to the appropriate dataclass in `app/models/snapshot.py`.

2\. Collect it inside the appropriate monitoring module.

3\. Wrap potentially failing calls with the project's safe-call helpers.

4\. Add formatting if necessary.

5\. Display it in the relevant UI page.

6\. Add tests.



For expensive metrics, use the existing TTL-cache or page-activation architecture.



\---



\# 🖥️ Windows-Specific Features



Some features depend on the hardware, drivers, firmware, or Windows APIs.



| Feature                    | Dependency                  |

| -------------------------- | --------------------------- |

| CPU temperature            | Available sensor provider   |

| Process command line       | Process permissions         |

| Ending protected processes | Administrator privileges    |

| Volume labels              | Windows volume APIs         |

| Physical disk names        | Windows physical-drive APIs |

| Adapter link speed         | Network driver              |

| Start with Windows         | Windows registry            |

| System tray                | Available system tray       |



When a dependency is unavailable, the application reports the value as unavailable instead of fabricating data.



\---



\# 🔒 Design Principles



System Monitor follows several principles:



\*\*Real data\*\*

Values come from the machine at runtime.



\*\*No fake metrics\*\*

Unavailable hardware information is never replaced with random or hard-coded values.



\*\*Graceful failure\*\*

One broken subsystem should not bring down the application.



\*\*Separation of concerns\*\*

Monitoring, services, and UI remain independently testable.



\*\*Bounded resources\*\*

Graph history and caches have explicit limits.



\*\*Responsive UI\*\*

System queries are kept away from the GUI thread.



\---



\# 🤝 Contributing



Contributions are welcome.



Before submitting a pull request:



1\. Create a branch for your change.

2\. Keep monitoring logic independent from the UI.

3\. Add tests for new functionality.

4\. Run the complete test suite.

5\. Keep changes focused and documented.



```powershell

python -m pytest

```



\---



\# 📜 License



This project is released under the \*\*MIT License\*\*.



See \[`LICENSE`](LICENSE) for the full license text.



\---



\# ⭐ Support the Project



If you find System Monitor useful:



\* ⭐ Star the repository

\* 🐛 Report bugs

\* 💡 Suggest improvements

\* 🔧 Contribute code

\* 📢 Share the project



\*\*GitHub:\*\*

https://github.com/SAIYAN36/System-Monitor



\---



\## System Monitor v1.0.0



Built with \*\*Python · PySide6 · psutil\*\*



Real-time monitoring.

No fake numbers.

No unnecessary overhead.



