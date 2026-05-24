"""Write reports to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from portwatch.history import HistoryRecord, load_history
from portwatch.report import build_report


def write_report(
    records: List[HistoryRecord],
    fmt: str = "text",
    output: Optional[str] = None,
    title: str = "Port-watch Report",
) -> None:
    """Render *records* and write to *output* path or stdout.

    Args:
        records: History records to render.
        fmt: ``"text"`` or ``"json"``.
        output: Destination file path.  ``None`` writes to stdout.
        title: Heading for the text formatter.
    """
    content = build_report(records, fmt=fmt, title=title)
    if output is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    else:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_report_from_file(
    history_path: str,
    fmt: str = "text",
    output: Optional[str] = None,
    limit: Optional[int] = None,
    title: str = "Port-watch Report",
) -> None:
    """Load history from *history_path*, optionally limit to *limit* most-recent
    records, then write a report.

    Args:
        history_path: Path to the JSONL history file.
        fmt: ``"text"`` or ``"json"``.
        output: Destination file path.  ``None`` writes to stdout.
        limit: Keep only the last *limit* records when set.
        title: Heading for the text formatter.
    """
    records = load_history(history_path)
    if limit is not None and limit > 0:
        records = records[-limit:]
    write_report(records, fmt=fmt, output=output, title=title)
