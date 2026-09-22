"""Error-containment helpers.

Sensor and process queries fail routinely and benignly on Windows (permission
denied, process exited mid-read, unsupported WMI sensor). These helpers keep
such failures local to the single metric they belong to.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator, Optional

logger = logging.getLogger(__name__)


def safe_call(
    func: Callable[..., Any],
    *args: Any,
    default: Any = None,
    context: str = "",
    **kwargs: Any,
) -> Any:
    """Call ``func`` and return ``default`` if it raises anything."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all
        logger.debug("%s failed: %r", context or getattr(func, "__name__", "call"), exc)
        return default


def safe(default: Any = None, context: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator form of :func:`safe_call` for collectors."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        label = context or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return safe_call(func, *args, default=default, context=label, **kwargs)

        return wrapper

    return decorator


@contextmanager
def ignore_errors(context: str = "", default: Optional[Any] = None) -> Iterator[None]:
    """Context manager that swallows exceptions from a monitoring probe."""
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all
        logger.debug("%s failed: %r", context or "block", exc)
