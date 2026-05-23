"""Baseline management: persist and load a known-good port snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from portwatch.snapshot import PortEntry, PortSnapshot

DEFAULT_BASELINE_PATH = Path("~/.local/share/portwatch/baseline.json").expanduser()


def _entry_to_dict(entry: PortEntry) -> dict:
    return {
        "proto": entry.proto,
        "local_addr": entry.local_addr,
        "local_port": entry.local_port,
        "pid": entry.pid,
        "process": entry.process,
    }


def _entry_from_dict(data: dict) -> PortEntry:
    return PortEntry(
        proto=data["proto"],
        local_addr=data["local_addr"],
        local_port=data["local_port"],
        pid=data.get("pid"),
        process=data.get("process"),
    )


def save_baseline(snapshot: PortSnapshot, path: Path = DEFAULT_BASELINE_PATH) -> None:
    """Persist *snapshot* as the current baseline to *path*."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": snapshot.timestamp.isoformat(),
        "entries": [_entry_to_dict(e) for e in snapshot.entries],
    }
    path.write_text(json.dumps(payload, indent=2))


def load_baseline(path: Path = DEFAULT_BASELINE_PATH) -> Optional[PortSnapshot]:
    """Load a previously saved baseline from *path*.

    Returns ``None`` if the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    from datetime import datetime
    entries = [_entry_from_dict(e) for e in data.get("entries", [])]
    snapshot = PortSnapshot(entries=entries)
    snapshot.timestamp = datetime.fromisoformat(data["timestamp"])
    return snapshot


def baseline_exists(path: Path = DEFAULT_BASELINE_PATH) -> bool:
    """Return True if a baseline file exists at *path*."""
    return Path(path).exists()
