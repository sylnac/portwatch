"""Periodic digest: summarise history records into a human-readable status email/log."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from portwatch.history import HistoryRecord, load_history


@dataclass
class DigestReport:
    generated_at: datetime
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    total_events: int
    added_ports: List[str] = field(default_factory=list)
    removed_ports: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.total_events == 0

    def to_text(self) -> str:
        lines = [
            f"Portwatch Digest — {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Period : {self.period_start} → {self.period_end}",
            f"Events : {self.total_events}",
        ]
        if self.added_ports:
            lines.append("Added  : " + ", ".join(self.added_ports))
        if self.removed_ports:
            lines.append("Removed: " + ", ".join(self.removed_ports))
        if self.is_empty():
            lines.append("No changes detected during this period.")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "generated_at": self.generated_at.isoformat(),
                "period_start": self.period_start.isoformat() if self.period_start else None,
                "period_end": self.period_end.isoformat() if self.period_end else None,
                "total_events": self.total_events,
                "added_ports": self.added_ports,
                "removed_ports": self.removed_ports,
            },
            indent=2,
        )


def build_digest(
    history_path: Path,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> DigestReport:
    """Load history records and aggregate them into a DigestReport."""
    records: List[HistoryRecord] = load_history(history_path)

    filtered = [
        r for r in records
        if (since is None or r.timestamp >= since)
        and (until is None or r.timestamp <= until)
    ]

    added: List[str] = []
    removed: List[str] = []
    for rec in filtered:
        for e in rec.added:
            added.append(f"{e['proto']}:{e['address']}:{e['port']}")
        for e in rec.removed:
            removed.append(f"{e['proto']}:{e['address']}:{e['port']}")

    period_start = filtered[0].timestamp if filtered else None
    period_end = filtered[-1].timestamp if filtered else None

    return DigestReport(
        generated_at=datetime.now(tz=timezone.utc),
        period_start=period_start,
        period_end=period_end,
        total_events=len(filtered),
        added_ports=added,
        removed_ports=removed,
    )
