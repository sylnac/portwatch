"""CLI sub-commands for managing port filter rules in portwatch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from portwatch.config import load_config
from portwatch.filter import build_filter_set
from portwatch.snapshot import capture_snapshot


def cmd_filter_list(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Print all active filter rules from config."""
    cfg = load_config(args.config)
    rules = getattr(cfg, "filter_rules", []) or []
    if not rules:
        print("No filter rules configured.")
        return
    for i, rule in enumerate(rules, 1):
        parts = [f"#{i}"]
        if rule.get("port"):
            parts.append(f"port={rule['port']}")
        if rule.get("proto"):
            parts.append(f"proto={rule['proto']}")
        if rule.get("address"):
            parts.append(f"addr={rule['address']}")
        if rule.get("comment"):
            parts.append(f"# {rule['comment']}")
        print("  ".join(parts))


def cmd_filter_test(args: argparse.Namespace) -> None:
    """Show which currently-open ports would be suppressed by active rules."""
    cfg = load_config(args.config)
    rules = getattr(cfg, "filter_rules", []) or []
    fs = build_filter_set(rules)

    snapshot = capture_snapshot()
    suppressed = [e for e in snapshot.entries if fs.is_suppressed(e)]
    visible = fs.apply(snapshot.entries)

    print(f"Total open ports : {len(snapshot.entries)}")
    print(f"Suppressed       : {len(suppressed)}")
    print(f"Visible          : {len(visible)}")

    if args.verbose and suppressed:
        print("\nSuppressed entries:")
        for e in suppressed:
            print(f"  {e}")


def add_filter_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'filter' sub-commands onto *subparsers*."""
    filter_parser = subparsers.add_parser(
        "filter", help="Manage port filter rules"
    )
    filter_sub = filter_parser.add_subparsers(dest="filter_cmd", required=True)

    # filter list
    filter_sub.add_parser("list", help="List active filter rules")

    # filter test
    test_p = filter_sub.add_parser(
        "test", help="Test rules against current port snapshot"
    )
    test_p.add_argument(
        "-v", "--verbose", action="store_true", help="Show suppressed entries"
    )

    filter_parser.set_defaults(func=_dispatch_filter)


def _dispatch_filter(args: argparse.Namespace) -> None:
    dispatch = {
        "list": cmd_filter_list,
        "test": cmd_filter_test,
    }
    handler = dispatch.get(args.filter_cmd)
    if handler:
        handler(args)
    else:
        print(f"Unknown filter sub-command: {args.filter_cmd}")
