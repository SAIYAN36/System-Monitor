"""Application logging.

Logs are written to a rotating file inside the per-user application data
directory so that running from source never litters the project folder:

    %APPDATA%\\SystemMonitor\\logs\\system_monitor.log
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
import threading
from pathlib import Path
from typing import Optional

from app.config import APP_DISPLAY_NAME, APP_VERSION, ensure_directories, log_file_path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3


class _MaxLevelFilter(logging.Filter):
    """Lets a handler accept records up to (and including) a level."""

    def __init__(self, maximum: int) -> None:
        super().__init__()
        self.maximum = maximum

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.maximum


_configured_path: Optional[Path] = None


def setup_logging(level: int = logging.INFO, *, console: bool = True) -> Path:
    """Configure root logging once and return the log file path."""
    global _configured_path
    if _configured_path is not None:
        return _configured_path

    try:
        ensure_directories()
        path = log_file_path()
    except OSError:
        # Extremely unlikely, but logging must not be the thing that crashes
        # start-up: fall back to the console only.
        path = Path("system_monitor.log")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(_LOG_FORMAT)

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root.addHandler(file_handler)
    except OSError:
        logging.getLogger(__name__).warning("File logging is unavailable; using console only")

    if console and sys.stderr is not None:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root.addHandler(console_handler)

    # Qt and psutil are chatty at DEBUG level; keep our own logs readable.
    for noisy in ("PySide6", "psutil", "app.monitoring.rate"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "%s %s starting (log file: %s)", APP_DISPLAY_NAME, APP_VERSION, path
    )
    _configured_path = path
    return path


def log_file() -> Optional[Path]:
    """Path of the active log file, if logging has been set up."""
    return _configured_path


def install_excepthook() -> None:
    """Log uncaught exceptions instead of losing them to a dead terminal."""
    logger = logging.getLogger("app.crash")

    def _hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = _hook

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        if issubclass(args.exc_type, SystemExit):
            return
        logger.critical(
            "Uncaught exception in thread %s",
            getattr(args.thread, "name", "?"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    threading.excepthook = _thread_hook
