"""Integration helper: extend the watch cycle to record diffs in history."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from portwatch.baseline import load_baseline, save_baseline
from portwatch.diff import diff_snapshots
from portwatch.history import append_record, load_history, HistoryRecord
from portwatch.notify import Notifier
from portwatch.snapshot import capture_snapshot
from portwatch.config import Config
from typing import List


def run_watch_cycle_with_history(
    config: Config,
    notifier: Notifier,
    history_path: Optional[Path] = None,
) -> bool:
    """Run a single watch cycle, dispatch alerts, and persist diff to history.

    Returns True if changes were detected, False otherwise.
    """
    baseline = load_baseline(config.baseline_path)
    if baseline is None:
        current = capture_snapshot()
        save_baseline(current, config.baseline_path)
        return False

    current = capture_snapshot()
    diff = diff_snapshots(baseline, current)

    if diff.has_changes:
        notifier.dispatch(diff)
        kwargs = {"path": history_path} if history_path else {}
        append_record(diff, **kwargs)
        save_baseline(current, config.baseline_path)

    return diff.has_changes


def get_recent_history(
    n: int = 20,
    history_path: Optional[Path] = None,
) -> List[HistoryRecord]:
    """Return the *n* most recent history records."""
    kwargs = {"path": history_path} if history_path else {}
    records = load_history(**kwargs)
    return records[-n:] if len(records) > n else records
