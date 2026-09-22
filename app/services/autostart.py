"""Start-with-Windows support via the current user's Run registry key.

Only the per-user key (``HKCU``) is used, so no administrator rights are needed
and nothing outside the current user's profile is modified.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from app.config import APP_NAME, is_frozen, is_windows, project_root

logger = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = APP_NAME


class AutostartError(RuntimeError):
    """Raised when the autostart entry could not be changed."""


def is_supported() -> bool:
    """Autostart is only implemented on Windows."""
    return is_windows()


def command_line() -> str:
    """The command Windows should launch at sign-in."""
    if is_frozen():
        executable = Path(sys.executable)
        return f'"{executable}" --minimized'

    # Running from source: use pythonw.exe so no console window appears.
    interpreter = Path(sys.executable)
    windowed = interpreter.with_name("pythonw.exe")
    if windowed.exists():
        interpreter = windowed
    entry_point = project_root() / "main.py"
    return f'"{interpreter}" "{entry_point}" --minimized'


def is_enabled() -> bool:
    """Whether an autostart entry exists for this application."""
    if not is_supported():
        return False
    try:
        import winreg  # noqa: PLC0415 - Windows-only import

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            try:
                winreg.QueryValueEx(key, _VALUE_NAME)
            except FileNotFoundError:
                return False
        return True
    except OSError as exc:
        logger.debug("Autostart state could not be read: %r", exc)
        return False


def set_enabled(enabled: bool) -> None:
    """Create or remove the autostart entry, raising on failure."""
    if not is_supported():
        raise AutostartError("Starting with the operating system is only supported on Windows.")

    try:
        import winreg  # noqa: PLC0415 - Windows-only import

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                value = command_line()
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, value)
                logger.info("Autostart enabled: %s", value)
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                    logger.info("Autostart disabled")
                except FileNotFoundError:
                    # Already absent, which is the requested state.
                    pass
    except OSError as exc:
        raise AutostartError(f"Could not update the Windows startup entry: {exc}") from exc


def current_entry() -> Optional[str]:
    """The registered command line, or ``None`` when autostart is off."""
    if not is_supported():
        return None
    try:
        import winreg  # noqa: PLC0415 - Windows-only import

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
        return str(value)
    except OSError:
        return None
