"""System Monitor application package.

The package is deliberately layered so that the data-collection code can be
imported and tested without a running GUI:

``app.monitoring``  real metrics taken from psutil / the operating system
``app.models``      plain dataclasses describing a metrics snapshot
``app.services``    settings, logging, history buffers, the polling thread
``app.ui``          PySide6 widgets, pages and the main window
``app.utils``       formatting, ring buffers and error-handling helpers
"""

from app.config import APP_DISPLAY_NAME, APP_VERSION

__all__ = ["APP_DISPLAY_NAME", "APP_VERSION"]
