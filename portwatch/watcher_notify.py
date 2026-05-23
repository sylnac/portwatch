"""Integration glue: wires the Watcher to the Notifier.

This thin module provides :func:`run_watch_cycle`, a single function that
captures a new snapshot, diffs it against a baseline (or previous snapshot),
and dispatches any changes through a :class:`~portwatch.notify.Notifier`.

It is intentionally kept separate from *watcher.py* so that the core
watcher logic stays independent of the notification subsystem.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from portwatch.baseline import load_baseline, save_baseline
from portwatch.config import Config
from portwatch.diff import diff_snapshots
from portwatch.notify import Notifier
from portwatch.snapshot import PortSnapshot, capture_snapshot
from portwatch.watcher import Watcher

logger = logging.getLogger(__name__)


def run_watch_cycle(
    watcher: Watcher,
    notifier: Notifier,
    previous: Optional[PortSnapshot] = None,
    *,
    update_baseline: bool = False,
) -> PortSnapshot:
    """Capture a snapshot, diff it, and notify if there are changes.

    Parameters
    ----------
    watcher:
        A configured :class:`~portwatch.watcher.Watcher` used to filter
        the diff before notification.
    notifier:
        The :class:`~portwatch.notify.Notifier` that dispatches alerts.
    previous:
        The snapshot to compare against.  When *None* the persisted
        baseline (if any) is used; if no baseline exists the current
        snapshot becomes the new baseline and no alert is sent.
    update_baseline:
        When *True* the baseline on disk is overwritten with the current
        snapshot after the cycle completes.

    Returns
    -------
    PortSnapshot
        The freshly captured snapshot (useful as *previous* in the next
        call).
    """
    current = capture_snapshot()

    if previous is None:
        previous = load_baseline(watcher.config.baseline_path)

    if previous is None:
        logger.info("No baseline found — saving current snapshot as baseline.")
        save_baseline(current, watcher.config.baseline_path)
        return current

    diff = diff_snapshots(previous, current)
    filtered = watcher._filter_diff(diff)  # noqa: SLF001  (intentional internal use)

    if filtered.has_changes():
        notifier.dispatch(filtered)
    else:
        logger.debug("No unexpected port changes detected.")

    if update_baseline:
        save_baseline(current, watcher.config.baseline_path)
        logger.debug("Baseline updated at %s", watcher.config.baseline_path)

    return current
