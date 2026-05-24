"""Port filtering utilities for portwatch.

Provides filter rules that can be applied to PortEntry objects to suppress
noise from well-known or explicitly ignored ports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from portwatch.snapshot import PortEntry


@dataclass
class FilterRule:
    """A single filter rule matching ports by various criteria."""

    port: Optional[int] = None
    proto: Optional[str] = None  # 'tcp' | 'udp'
    address: Optional[str] = None
    comment: str = ""

    def matches(self, entry: PortEntry) -> bool:
        """Return True if *entry* satisfies all non-None fields."""
        if self.port is not None and entry.port != self.port:
            return False
        if self.proto is not None and entry.proto.lower() != self.proto.lower():
            return False
        if self.address is not None and entry.address != self.address:
            return False
        return True


@dataclass
class FilterSet:
    """Collection of FilterRule objects."""

    rules: List[FilterRule] = field(default_factory=list)

    def add_rule(self, rule: FilterRule) -> None:
        self.rules.append(rule)

    def is_suppressed(self, entry: PortEntry) -> bool:
        """Return True if *entry* is matched by at least one rule."""
        return any(r.matches(entry) for r in self.rules)

    def apply(self, entries: Iterable[PortEntry]) -> List[PortEntry]:
        """Return entries that are NOT suppressed by any rule."""
        return [e for e in entries if not self.is_suppressed(e)]


def build_filter_set(rules_cfg: list[dict]) -> FilterSet:
    """Build a FilterSet from a list of rule dicts (e.g. from config).

    Each dict may contain keys: port, proto, address, comment.
    """
    fs = FilterSet()
    for raw in rules_cfg:
        fs.add_rule(
            FilterRule(
                port=raw.get("port"),
                proto=raw.get("proto"),
                address=raw.get("address"),
                comment=raw.get("comment", ""),
            )
        )
    return fs
