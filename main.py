"""System Monitor - application entry point.

Run with ``python main.py``. See ``README.md`` for the full instructions.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional, Sequence

from app.config import APP_DISPLAY_NAME, APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="system-monitor",
        description=f"{APP_DISPLAY_NAME} {APP_VERSION} - live system monitoring for Windows.",
    )
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="start in the notification area without showing the window",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="log at DEBUG level (verbose)",
    )
    parser.add_argument(
        "--reset-settings",
        action="store_true",
        help="ignore any saved settings and restore the defaults",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Logging first: everything below this line can be recorded.
    from app.services.logging_service import install_excepthook, setup_logging

    log_path = setup_logging(logging.DEBUG if args.debug else logging.INFO)
    install_excepthook()
    logger.info("Starting with arguments: %s", list(argv) if argv else sys.argv[1:])

    # Qt imports are deferred so that --help and --version stay instant.
    from PySide6.QtWidgets import QApplication, QMessageBox

    from app.services.settings import SettingsManager
    from app.ui.icons import application_icon
    from app.ui.main_window import MainWindow
    from app.ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    try:
        settings_manager = SettingsManager()
        if args.reset_settings:
            logger.info("Restoring default settings")
            settings_manager.reset()
        settings = settings_manager.load()

        apply_theme(app, settings.theme)
        app.setWindowIcon(application_icon())

        window = MainWindow(settings_manager, start_minimized=args.minimized)
        window.show_if_allowed()
    except Exception as exc:  # noqa: BLE001 - the last line of defence
        logger.exception("Fatal error during start-up")
        QMessageBox.critical(
            None,
            f"{APP_DISPLAY_NAME} could not start",
            f"{exc}\n\nDetails were written to:\n{log_path}",
        )
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
