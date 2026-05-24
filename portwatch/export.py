"""Export snapshot data to CSV or JSON for external consumption."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable

from portwatch.snapshot import PortEntry, PortSnapshot


def _entry_to_row(entry: PortEntry) -> dict:
    return {
        "proto": entry.proto,
        "address": entry.address,
        "port": entry.port,
        "pid": entry.pid if entry.pid is not None else "",
        "process": entry.process if entry.process is not None else "",
    }


def snapshot_to_csv(snapshot: PortSnapshot) -> str:
    """Serialise a snapshot to a CSV string."""
    output = io.StringIO()
    fieldnames = ["proto", "address", "port", "pid", "process"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for entry in sorted(snapshot.entries, key=lambda e: (e.proto, e.port)):
        writer.writerow(_entry_to_row(entry))
    return output.getvalue()


def snapshot_to_json(snapshot: PortSnapshot) -> str:
    """Serialise a snapshot to a JSON string."""
    data = {
        "timestamp": snapshot.timestamp,
        "entries": [_entry_to_row(e) for e in
                    sorted(snapshot.entries, key=lambda e: (e.proto, e.port))],
    }
    return json.dumps(data, indent=2)


def write_snapshot_export(
    snapshot: PortSnapshot,
    fmt: str = "json",
    path: str | None = None,
) -> str:
    """Write snapshot export to *path* (or return as string if path is None).

    Args:
        snapshot: The snapshot to export.
        fmt: ``"json"`` or ``"csv"``.
        path: Destination file path.  Pass ``None`` to return the string.

    Returns:
        The serialised content string.
    """
    if fmt == "csv":
        content = snapshot_to_csv(snapshot)
    elif fmt == "json":
        content = snapshot_to_json(snapshot)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")

    if path is not None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    return content
