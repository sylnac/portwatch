"""Core watcher loop: polls ports and emits alerts on unexpected changes."""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from portwatch.config import Config
from portwatch.diff import SnapshotDiff, diff_snapshots
from portwatch.snapshot import PortSnapshot, capture_snapshot

logger = logging.getLogger("portwatch")

AlertCallback = Callable[[SnapshotDiff], None]


def _default_alert(diff: SnapshotDiff) -> None:
    logger.warning("Port changes detected:\n%s", diff.summary())


class Watcher:
    """Polls port state and fires *alert_callback* when changes occur."""

    def __init__(
        self,
        config: Config,
        alert_callback: Optional[AlertCallback] = None,
    ) -> None:
        self.config = config
        self.alert_callback: AlertCallback = alert_callback or _default_alert
        self._running = False
        self._last_snapshot: Optional[PortSnapshot] = None

    def _is_allowed(self, port: int) -> bool:
        return port in self.config.allowed_ports

    def _filter_diff(self, diff: SnapshotDiff) -> SnapshotDiff:
        from portwatch.diff import SnapshotDiff as SD

        filtered = SD(
            added=[e for e in diff.added if not self._is_allowed(e.local_port)],
            removed=(
                [e for e in diff.removed if not self._is_allowed(e.local_port)]
                if self.config.alert_on_removal
                else []
            ),
        )
        return filtered

    def tick(self) -> Optional[SnapshotDiff]:
        """Perform a single poll cycle. Returns a diff if changes were found."""
        try:
            current = capture_snapshot()
        except Exception:
            logger.exception("Failed to capture port snapshot; skipping cycle.")
            return None

        if self._last_snapshot is None:
            self._last_snapshot = current
            logger.info("Initial snapshot captured (%d entries).", len(current.entries))
            return None

        diff = diff_snapshots(self._last_snapshot, current)
        self._last_snapshot = current

        filtered = self._filter_diff(diff)
        if filtered.has_changes:
            self.alert_callback(filtered)
            return filtered
        return None

    def run(self) -> None:
        """Block and poll indefinitely until stopped."""
        self._running = True
        logger.info("portwatch started (interval=%.1fs)", self.config.poll_interval)
        while self._running:
            self.tick()
            time.sleep(self.config.poll_interval)

    def stop(self) -> None:
        self._running = False
        logger.info("portwatch stopped.")
