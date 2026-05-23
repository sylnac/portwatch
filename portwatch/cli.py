"""Command-line interface for portwatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portwatch.baseline import (
    DEFAULT_BASELINE_PATH,
    baseline_exists,
    load_baseline,
    save_baseline,
)
from portwatch.config import load_config
from portwatch.diff import diff_snapshots
from portwatch.snapshot import capture_snapshot


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Save the current port state as the baseline."""
    snapshot = capture_snapshot()
    path = Path(args.baseline)
    save_baseline(snapshot, path)
    print(f"Baseline saved to {path} ({len(snapshot.entries)} entries).")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Compare current ports against the saved baseline."""
    path = Path(args.baseline)
    if not baseline_exists(path):
        print(
            f"No baseline found at {path}. Run 'portwatch snapshot' first.",
            file=sys.stderr,
        )
        return 2

    baseline = load_baseline(path)
    current = capture_snapshot()
    diff = diff_snapshots(baseline, current)

    if not diff.has_changes():
        print("No changes detected.")
        return 0

    print(diff.summary())
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portwatch",
        description="Monitor local port usage and alert on unexpected bindings.",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE_PATH),
        metavar="FILE",
        help="Path to the baseline snapshot file.",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="FILE",
        help="Path to the configuration file.",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot", help="Record current ports as the baseline.")
    sub.add_parser("check", help="Check current ports against the baseline.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "snapshot":
        return cmd_snapshot(args)
    if args.command == "check":
        return cmd_check(args)

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
