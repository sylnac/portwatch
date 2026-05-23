"""Notification dispatcher: routes alerts to one or more backends."""

from __future__ import annotations

import logging
from typing import List, Optional

from portwatch.alert import AlertBackend, LoggingBackend
from portwatch.diff import SnapshotDiff

logger = logging.getLogger(__name__)


class Notifier:
    """Dispatches a SnapshotDiff to a collection of AlertBackends.

    Parameters
    ----------
    backends:
        One or more :class:`~portwatch.alert.AlertBackend` instances.
        If *None* or an empty list is supplied a :class:`~portwatch.alert.LoggingBackend`
        is used as a sensible default.
    """

    def __init__(self, backends: Optional[List[AlertBackend]] = None) -> None:
        if backends:
            self._backends: List[AlertBackend] = list(backends)
        else:
            self._backends = [LoggingBackend()]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_backend(self, backend: AlertBackend) -> None:
        """Register an additional backend at runtime."""
        self._backends.append(backend)

    def remove_backend(self, backend: AlertBackend) -> None:
        """Unregister a backend (no-op if not present)."""
        try:
            self._backends.remove(backend)
        except ValueError:
            pass

    def dispatch(self, diff: SnapshotDiff) -> None:
        """Send *diff* to every registered backend.

        Errors raised by individual backends are caught and logged so that
        a failing backend cannot prevent others from being notified.
        """
        if not diff.has_changes():
            return

        for backend in self._backends:
            try:
                backend.send(diff)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Backend %s raised an exception while sending alert",
                    type(backend).__name__,
                )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        names = ", ".join(type(b).__name__ for b in self._backends)
        return f"Notifier(backends=[{names}])"
