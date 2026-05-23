"""Periodic scheduling for portwatch snapshot comparisons."""

import time
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class Scheduler:
    """Runs a callback at a fixed interval in a background thread."""

    def __init__(self, interval: float, callback: Callable[[], None]) -> None:
        """
        Args:
            interval: Seconds between each callback invocation.
            callback: Function to call on each tick.
        """
        if interval <= 0:
            raise ValueError(f"interval must be positive, got {interval}")
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background scheduling thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Scheduler is already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="portwatch-scheduler", daemon=True
        )
        self._thread.start()
        logger.debug("Scheduler started (interval=%.1fs)", self.interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the scheduler to stop and wait for the thread to finish."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("Scheduler thread did not stop within %.1fs", timeout)
            else:
                logger.debug("Scheduler stopped")
        self._thread = None

    @property
    def running(self) -> bool:
        """Return True if the scheduler thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Main loop executed in the background thread."""
        while not self._stop_event.is_set():
            try:
                self.callback()
            except Exception:
                logger.exception("Unhandled exception in scheduler callback")
            # Use wait() so stop() can interrupt the sleep immediately.
            self._stop_event.wait(timeout=self.interval)
