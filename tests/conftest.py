"""Shared pytest configuration.

The project root is added to ``sys.path`` so the tests can ``import app`` no
matter which directory pytest is invoked from.
"""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def qapp():
    """A single offscreen QApplication for every GUI test.

    ``offscreen`` keeps the tests headless: they render the real widgets
    without opening a window on the developer's desktop.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
