"""Watchdog: detects stale or hung watch cycles and emits alerts."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class WatchdogState:
    """Mutable state tracked by the watchdog."""

    last_heartbeat: float = field(default_factory=time.monotonic)
    missed_beats: int = 0


class Watchdog:
    """Monitors a watch cycle and fires *on_stall* when heartbeats stop.

    Parameters
    ----------
    timeout:
        Seconds without a heartbeat before the cycle is considered stalled.
    on_stall:
        Callable invoked with the number of consecutive missed beats.
    check_interval:
        How often (seconds) the watchdog polls for a missed heartbeat.
    """

    def __init__(
        self,
        timeout: float,
        on_stall: Callable[[int], None],
        check_interval: float = 5.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if check_interval <= 0:
            raise ValueError("check_interval must be positive")
        self._timeout = timeout
        self._on_stall = on_stall
        self._check_interval = check_interval
        self._state = WatchdogState()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def heartbeat(self) -> None:
        """Signal that the watched cycle is still alive."""
        self._state.last_heartbeat = time.monotonic()
        self._state.missed_beats = 0

    def start(self) -> None:
        """Start the background watchdog thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="portwatch-watchdog"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background watchdog thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._check_interval + 1)

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.wait(timeout=self._check_interval):
            elapsed = time.monotonic() - self._state.last_heartbeat
            if elapsed >= self._timeout:
                self._state.missed_beats += 1
                self._on_stall(self._state.missed_beats)
