"""Generate human-readable and machine-readable reports from history records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from portwatch.history import HistoryRecord


def _fmt_ts(ts: float) -> str:
    """Format a UTC timestamp as an ISO-8601 string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def records_to_text(records: List[HistoryRecord], title: str = "Port-watch Report") -> str:
    """Return a plain-text summary of *records*."""
    lines: List[str] = [title, "=" * len(title), ""]
    if not records:
        lines.append("No changes recorded.")
        return "\n".join(lines)

    for rec in records:
        lines.append(f"[{_fmt_ts(rec.timestamp)}]")
        for entry in rec.added:
            lines.append(f"  + {entry.proto:<4} {entry.host}:{entry.port}  (pid={entry.pid})")
        for entry in rec.removed:
            lines.append(f"  - {entry.proto:<4} {entry.host}:{entry.port}  (pid={entry.pid})")
        lines.append("")
    return "\n".join(lines)


def records_to_json(records: List[HistoryRecord], indent: int = 2) -> str:
    """Serialise *records* to a JSON string."""

    def _entry(e):
        return {"proto": e.proto, "host": e.host, "port": e.port, "pid": e.pid}

    payload = [
        {
            "timestamp": rec.timestamp,
            "timestamp_iso": _fmt_ts(rec.timestamp),
            "added": [_entry(e) for e in rec.added],
            "removed": [_entry(e) for e in rec.removed],
        }
        for rec in records
    ]
    return json.dumps(payload, indent=indent)


def build_report(
    records: List[HistoryRecord],
    fmt: str = "text",
    title: str = "Port-watch Report",
) -> str:
    """Dispatch to the appropriate formatter.

    Args:
        records: History records to include.
        fmt: ``"text"`` or ``"json"``.
        title: Heading used by the text formatter.

    Returns:
        Formatted report string.

    Raises:
        ValueError: If *fmt* is not recognised.
    """
    if fmt == "text":
        return records_to_text(records, title=title)
    if fmt == "json":
        return records_to_json(records)
    raise ValueError(f"Unknown report format: {fmt!r}. Choose 'text' or 'json'.")
