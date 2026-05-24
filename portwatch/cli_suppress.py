"""CLI sub-commands for managing suppression windows."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from portwatch.suppress import (
    SuppressionWindow,
    load_suppressions,
    save_suppressions,
)

DEFAULT_SUPPRESS_FILE = Path("portwatch_suppressions.json")


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "suppress_file", None) or DEFAULT_SUPPRESS_FILE)


def cmd_suppress_add(args: argparse.Namespace) -> None:
    path = _resolve_path(args)
    store = load_suppressions(path)
    expires_at = time.time() + args.duration * 60
    window = SuppressionWindow(
        port=args.port,
        proto=args.proto,
        reason=args.reason,
        expires_at=expires_at,
    )
    store.add(window)
    save_suppressions(store, path)
    print(
        f"Suppressed {args.proto}:{args.port} for {args.duration} minute(s). "
        f"Reason: {args.reason}"
    )


def cmd_suppress_list(args: argparse.Namespace) -> None:
    path = _resolve_path(args)
    store = load_suppressions(path)
    active = store.active_windows()
    if not active:
        print("No active suppression windows.")
        return
    now = time.time()
    for w in active:
        remaining = max(0, w.expires_at - now)
        print(
            f"  {w.proto}:{w.port}  expires in {remaining:.0f}s  reason={w.reason!r}"
        )


def cmd_suppress_purge(args: argparse.Namespace) -> None:
    path = _resolve_path(args)
    store = load_suppressions(path)
    removed = store.purge_expired()
    save_suppressions(store, path)
    print(f"Purged {removed} expired suppression window(s).")


def add_suppress_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("suppress", help="Manage suppression windows")
    sp = p.add_subparsers(dest="suppress_cmd", required=True)

    add_p = sp.add_parser("add", help="Add a suppression window")
    add_p.add_argument("port", type=int, help="Port number to suppress")
    add_p.add_argument("--proto", default="*", choices=["tcp", "udp", "*"])
    add_p.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    add_p.add_argument("--reason", default="maintenance")
    add_p.add_argument("--suppress-file", default=None)
    add_p.set_defaults(func=cmd_suppress_add)

    list_p = sp.add_parser("list", help="List active suppression windows")
    list_p.add_argument("--suppress-file", default=None)
    list_p.set_defaults(func=cmd_suppress_list)

    purge_p = sp.add_parser("purge", help="Remove expired suppression windows")
    purge_p.add_argument("--suppress-file", default=None)
    purge_p.set_defaults(func=cmd_suppress_purge)
