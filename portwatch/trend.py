"""Trend analysis over historical PortWatch records."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from portwatch.history import HistoryRecord


@dataclass
class TrendReport:
    """Aggregated trend statistics derived from a sequence of history records."""

    total_events: int = 0
    # port -> number of times it appeared as added
    most_added: Dict[int, int] = field(default_factory=dict)
    # port -> number of times it appeared as removed
    most_removed: Dict[int, int] = field(default_factory=dict)
    # proto -> event count
    by_proto: Dict[str, int] = field(default_factory=dict)
    # address -> event count
    by_address: Dict[str, int] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return self.total_events == 0

    def to_text(self, top_n: int = 5) -> str:
        if self.is_empty():
            return "No trend data available."
        lines: List[str] = [f"Total change events : {self.total_events}"]
        if self.most_added:
            top = sorted(self.most_added.items(), key=lambda x: x[1], reverse=True)[:top_n]
            lines.append("Most added ports     : " + ", ".join(f"{p}({c})" for p, c in top))
        if self.most_removed:
            top = sorted(self.most_removed.items(), key=lambda x: x[1], reverse=True)[:top_n]
            lines.append("Most removed ports   : " + ", ".join(f"{p}({c})" for p, c in top))
        if self.by_proto:
            lines.append("By protocol          : " + ", ".join(f"{k}={v}" for k, v in self.by_proto.items()))
        if self.by_address:
            top = sorted(self.by_address.items(), key=lambda x: x[1], reverse=True)[:top_n]
            lines.append("By address           : " + ", ".join(f"{a}({c})" for a, c in top))
        return "\n".join(lines)


def build_trend(records: List[HistoryRecord]) -> TrendReport:
    """Compute a TrendReport from a list of HistoryRecord objects."""
    added_counter: Counter = Counter()
    removed_counter: Counter = Counter()
    proto_counter: Counter = Counter()
    addr_counter: Counter = Counter()
    total = 0

    for record in records:
        for entry in record.added:
            added_counter[entry.port] += 1
            proto_counter[entry.proto] += 1
            addr_counter[entry.address] += 1
            total += 1
        for entry in record.removed:
            removed_counter[entry.port] += 1
            proto_counter[entry.proto] += 1
            addr_counter[entry.address] += 1
            total += 1

    return TrendReport(
        total_events=total,
        most_added=dict(added_counter),
        most_removed=dict(removed_counter),
        by_proto=dict(proto_counter),
        by_address=dict(addr_counter),
    )
