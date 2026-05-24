"""CLI sub-command ``portwatch report`` — generate reports from history."""

from __future__ import annotations

import argparse
from pathlib import Path

from portwatch.config import load_config
from portwatch.report_writer import write_report_from_file

_DEFAULT_HISTORY = "portwatch_history.jsonl"


def cmd_report(args: argparse.Namespace) -> None:
    """Entry-point for the ``report`` sub-command."""
    cfg = load_config(args.config) if args.config else None
    history_path = args.history or (
        cfg.get("history_path", _DEFAULT_HISTORY) if cfg else _DEFAULT_HISTORY
    )

    if not Path(history_path).exists():
        print(f"No history file found at {history_path!r}. Run the watcher first.")
        return

    write_report_from_file(
        history_path=history_path,
        fmt=args.format,
        output=args.output,
        limit=args.limit,
        title=args.title,
    )


def add_report_subcommand(subparsers) -> None:
    """Register the ``report`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "report",
        help="Generate a report from the port-change history.",
    )
    p.add_argument(
        "--history",
        metavar="FILE",
        default=None,
        help="Path to the history JSONL file (overrides config).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write report to FILE instead of stdout.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Include only the N most-recent history records.",
    )
    p.add_argument(
        "--title",
        default="Port-watch Report",
        help="Report heading (text format only).",
    )
    p.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to portwatch config file.",
    )
    p.set_defaults(func=cmd_report)
