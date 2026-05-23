"""Port snapshot module: captures current listening ports on the system."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import psutil


@dataclass(frozen=True)
class PortEntry:
    """Represents a single listening port binding."""

    pid: int
    process_name: str
    local_address: str
    local_port: int
    protocol: str  # 'tcp' or 'udp'

    def __str__(self) -> str:
        return (
            f"{self.protocol.upper()} {self.local_address}:{self.local_port} "
            f"(pid={self.pid}, name={self.process_name})"
        )


@dataclass
class PortSnapshot:
    """A point-in-time snapshot of all listening ports."""

    timestamp: float = field(default_factory=time.time)
    entries: List[PortEntry] = field(default_factory=list)

    @property
    def port_set(self) -> set:
        """Return a set of (protocol, local_address, local_port) tuples."""
        return {(e.protocol, e.local_address, e.local_port) for e in self.entries}


def capture_snapshot() -> PortSnapshot:
    """Capture the current listening ports from the OS."""
    snapshot = PortSnapshot()

    for proto, kind in (("tcp", psutil.AF_INET), ("udp", psutil.AF_INET)):
        for conn in psutil.net_connections(kind=proto):
            if conn.status not in ("LISTEN", "") and proto == "tcp":
                continue
            if conn.laddr:
                try:
                    proc = psutil.Process(conn.pid) if conn.pid else None
                    name = proc.name() if proc else "unknown"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    name = "unknown"
                entry = PortEntry(
                    pid=conn.pid or -1,
                    process_name=name,
                    local_address=conn.laddr.ip,
                    local_port=conn.laddr.port,
                    protocol=proto,
                )
                snapshot.entries.append(entry)

    return snapshot
