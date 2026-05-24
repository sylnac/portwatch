"""Suppression window support: silence alerts for known ports during maintenance."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from portwatch.snapshot import PortEntry


@dataclass
class SuppressionWindow:
    """A timed suppression rule that expires after `duration_seconds`."""

    port: int
    proto: str  # "tcp" | "udp" | "*"
    reason: str
    expires_at: float  # Unix timestamp

    def is_active(self, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return now < self.expires_at

    def matches(self, entry: PortEntry) -> bool:
        port_match = self.port == entry.port
        proto_match = self.proto == "*" or self.proto == entry.proto
        return port_match and proto_match

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "proto": self.proto,
            "reason": self.reason,
            "expires_at": self.expires_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "SuppressionWindow":
        return SuppressionWindow(
            port=int(d["port"]),
            proto=str(d["proto"]),
            reason=str(d["reason"]),
            expires_at=float(d["expires_at"]),
        )


@dataclass
class SuppressionStore:
    """Collection of suppression windows, optionally persisted to disk."""

    _windows: List[SuppressionWindow] = field(default_factory=list)

    def add(self, window: SuppressionWindow) -> None:
        self._windows.append(window)

    def is_suppressed(self, entry: PortEntry, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return any(w.is_active(now) and w.matches(entry) for w in self._windows)

    def purge_expired(self, now: Optional[float] = None) -> int:
        """Remove expired windows; returns count removed."""
        now = now if now is not None else time.time()
        before = len(self._windows)
        self._windows = [w for w in self._windows if w.is_active(now)]
        return before - len(self._windows)

    def active_windows(self, now: Optional[float] = None) -> List[SuppressionWindow]:
        now = now if now is not None else time.time()
        return [w for w in self._windows if w.is_active(now)]


def save_suppressions(store: SuppressionStore, path: Path) -> None:
    data = [w.to_dict() for w in store._windows]
    path.write_text(json.dumps(data, indent=2))


def load_suppressions(path: Path) -> SuppressionStore:
    store = SuppressionStore()
    if not path.exists():
        return store
    data = json.loads(path.read_text())
    for item in data:
        store.add(SuppressionWindow.from_dict(item))
    return store
