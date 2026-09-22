# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller configuration for System Monitor.

Build a standalone application bundle with:

    pyinstaller --noconfirm system_monitor.spec

The result is ``dist/SystemMonitor/SystemMonitor.exe``. A folder build is used
rather than ``--onefile`` because a single-file executable has to unpack the
whole Qt runtime into a temporary directory on every start, which adds several
seconds to launch. ``--onefile`` still works if a single file is preferred:

    pyinstaller --noconfirm --onefile --windowed --name SystemMonitor \\
        --icon assets/icon.ico --add-data "assets;assets" main.py
"""

from pathlib import Path

# Paths inside the spec file must be resolved relative to this file, because
# PyInstaller may be invoked from any working directory.
PROJECT_ROOT = Path(SPECPATH).resolve()
ASSETS = PROJECT_ROOT / "assets"

# Qt ships a large number of modules this application never imports. Dropping
# them from the bundle removes well over a hundred megabytes.
UNUSED_QT_MODULES = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
]

EXCLUDED_PACKAGES = [
    "tkinter",
    "unittest",
    "pytest",
    "numpy",
    "pandas",
    "matplotlib",
]

a = Analysis(  # noqa: F821 - provided by PyInstaller
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    # The application icon is looked up at runtime, so the assets must ship.
    datas=[(str(ASSETS), "assets")],
    hiddenimports=[
        # psutil loads its platform implementation dynamically, which
        # PyInstaller cannot always see.
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=UNUSED_QT_MODULES + EXCLUDED_PACKAGES,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)  # noqa: F821 - provided by PyInstaller

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SystemMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # No console window: this is a GUI application.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS / "icon.ico"),
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SystemMonitor",
)
