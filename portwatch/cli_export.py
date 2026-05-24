"""CLI sub-command: portwatch export — export a live snapshot."""

from __future__ import annotations

import argparse
import sys

from portwatch.export import write_snapshot_export
from portwatch.snapshot import capture_snapshot


def cmd_export(args: argparse.Namespace) -> None:
    """Capture a live snapshot and export it in the requested format."""
    snapshot = capture_snapshot()
    fmt = args.format.lower()

    output_path: str | None = getattr(args, "output", None) or None

    try:
        content = write_snapshot_export(snapshot, fmt=fmt, path=output_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output_path is None:
        print(content, end="")
    else:
        print(f"Snapshot exported to {output_path} ({fmt})")


def add_export_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command on *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "export",
        help="Export a live snapshot to JSON or CSV",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout",
    )
    parser.set_defaults(func=cmd_export)
