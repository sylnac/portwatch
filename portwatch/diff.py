"""Diff module: compares two port snapshots and reports changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from portwatch.snapshot import PortEntry, PortSnapshot


@dataclass
class SnapshotDiff:
    """Result of comparing two port snapshots."""

    added: List[PortEntry] = field(default_factory=list)
    removed: List[PortEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def summary(self) -> str:
        lines = []
        for entry in self.added:
            lines.append(f"  [+] {entry}")
        for entry in self.removed:
            lines.append(f"  [-] {entry}")
        return "\n".join(lines) if lines else "  (no changes)"


def diff_snapshots(before: PortSnapshot, after: PortSnapshot) -> SnapshotDiff:
    """Compare two snapshots and return what was added or removed."""
    before_keys = {(e.protocol, e.local_address, e.local_port): e for e in before.entries}
    after_keys = {(e.protocol, e.local_address, e.local_port): e for e in after.entries}

    added_keys = set(after_keys) - set(before_keys)
    removed_keys = set(before_keys) - set(after_keys)

    return SnapshotDiff(
        added=[after_keys[k] for k in added_keys],
        removed=[before_keys[k] for k in removed_keys],
    )
