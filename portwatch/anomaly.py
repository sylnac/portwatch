"""Anomaly scoring: assign a severity score to snapshot diffs based on
heuristics such as well-known privileged ports, unexpected protocols, and
bindings on all-interfaces addresses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from portwatch.diff import SnapshotDiff
from portwatch.snapshot import PortEntry

# Ports below this threshold are considered privileged
_PRIVILEGED_PORT_MAX = 1024

# Addresses that expose a service to all network interfaces
_WILDCARD_ADDRESSES = {"0.0.0.0", "::", "*"}

# Scores assigned per heuristic (additive)
_SCORE_PRIVILEGED_PORT = 30
_SCORE_WILDCARD_ADDRESS = 20
_SCORE_UNKNOWN_PROTOCOL = 10
_KNOWN_PROTOCOLS = {"tcp", "tcp6", "udp", "udp6"}


@dataclass
class AnomalyScore:
    """Holds the computed anomaly score for a single added port entry."""

    entry: PortEntry
    score: int
    reasons: List[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        if self.score >= 50:
            return "HIGH"
        if self.score >= 20:
            return "MEDIUM"
        return "LOW"

    def __str__(self) -> str:
        return (
            f"{self.severity} (score={self.score}) "
            f"{self.entry} — {'; '.join(self.reasons)}"
        )


def score_entry(entry: PortEntry) -> AnomalyScore:
    """Compute an anomaly score for a single PortEntry."""
    score = 0
    reasons: List[str] = []

    if entry.port < _PRIVILEGED_PORT_MAX:
        score += _SCORE_PRIVILEGED_PORT
        reasons.append(f"privileged port ({entry.port})")

    if entry.address in _WILDCARD_ADDRESSES:
        score += _SCORE_WILDCARD_ADDRESS
        reasons.append(f"wildcard address ({entry.address})")

    if entry.proto.lower() not in _KNOWN_PROTOCOLS:
        score += _SCORE_UNKNOWN_PROTOCOL
        reasons.append(f"unknown protocol ({entry.proto})")

    if not reasons:
        reasons.append("no specific concerns")

    return AnomalyScore(entry=entry, score=score, reasons=reasons)


def score_diff(diff: SnapshotDiff) -> List[AnomalyScore]:
    """Return anomaly scores for every *added* entry in a diff.

    Only newly added ports are scored — removed ports are not considered
    anomalous from a security perspective.
    """
    return [score_entry(e) for e in diff.added]
