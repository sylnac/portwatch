"""CLI sub-command: portwatch digest — print a summary of recent history."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from portwatch.digest import build_digest


_DEFAULT_HISTORY = Path("portwatch_history.json")
_DEFAULT_HOURS = 24


def cmd_digest(args: argparse.Namespace) -> None:
    history_path = Path(args.history) if args.history else _DEFAULT_HISTORY

    if not history_path.exists():
        print(f"History file not found: {history_path}", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(tz=timezone.utc)
    since = now - timedelta(hours=args.hours)

    report = build_digest(history_path, since=since, until=now)

    if args.format == "json":
        print(report.to_json())
    else:
        print(report.to_text())

    if args.fail_on_changes and not report.is_empty():
        sys.exit(2)


def add_digest_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "digest",
        help="Print a summary of port-change events from the history file",
    )
    p.add_argument(
        "--history",
        metavar="FILE",
        default=None,
        help="Path to history JSON file (default: portwatch_history.json)",
    )
    p.add_argument(
        "--hours",
        type=int,
        default=_DEFAULT_HOURS,
        metavar="N",
        help=f"Look back N hours (default: {_DEFAULT_HOURS})",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-changes",
        action="store_true",
        default=False,
        help="Exit with code 2 if any changes are found (useful in CI)",
    )
    p.set_defaults(func=cmd_digest)
