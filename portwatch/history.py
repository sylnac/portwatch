"""Persistent history of snapshot diffs for trend analysis and auditing."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from portwatch.diff import SnapshotDiff
from portwatch.snapshot import PortEntry

_DEFAULT_HISTORY_PATH = Path("~/.portwatch/history.json").expanduser()
_MAX_ENTRIES = 500


@dataclass
class HistoryRecord:
    timestamp: str
    added: List[dict]
    removed: List[dict]

    @classmethod
    def from_diff(cls, diff: SnapshotDiff) -> "HistoryRecord":
        ts = datetime.now(timezone.utc).isoformat()
        return cls(
            timestamp=ts,
            added=[_entry_to_dict(e) for e in diff.added],
            removed=[_entry_to_dict(e) for e in diff.removed],
        )


def _entry_to_dict(entry: PortEntry) -> dict:
    return {
        "proto": entry.proto,
        "local_addr": entry.local_addr,
        "local_port": entry.local_port,
        "pid": entry.pid,
        "process": entry.process,
    }


def append_record(
    diff: SnapshotDiff,
    path: Path = _DEFAULT_HISTORY_PATH,
    max_entries: int = _MAX_ENTRIES,
) -> None:
    """Append a diff as a history record, pruning old entries if needed."""
    if not diff.has_changes:
        return

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    records: List[dict] = []
    if path.exists():
        try:
            with path.open() as fh:
                records = json.load(fh)
        except (json.JSONDecodeError, OSError):
            records = []

    record = HistoryRecord.from_diff(diff)
    records.append(asdict(record))

    if len(records) > max_entries:
        records = records[-max_entries:]

    with path.open("w") as fh:
        json.dump(records, fh, indent=2)


def load_history(path: Path = _DEFAULT_HISTORY_PATH) -> List[HistoryRecord]:
    """Load all history records from disk."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        with path.open() as fh:
            raw = json.load(fh)
        return [HistoryRecord(**r) for r in raw]
    except (json.JSONDecodeError, OSError, TypeError):
        return []
