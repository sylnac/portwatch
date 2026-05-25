"""CLI integration: add watchdog options to the watch command."""

from __future__ import annotations

import argparse
import logging
from typing import Optional

from portwatch.watchdog import Watchdog

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 60.0
_DEFAULT_CHECK_INTERVAL = 10.0


def _stall_handler(missed: int) -> None:
    """Default stall callback — logs a warning each missed beat."""
    logger.warning(
        "[watchdog] watch cycle stalled — %d consecutive missed heartbeat(s)",
        missed,
    )


def build_watchdog_from_args(
    args: argparse.Namespace,
    on_stall=None,
) -> Optional[Watchdog]:
    """Construct a :class:`Watchdog` from parsed CLI arguments.

    Returns *None* when the watchdog is disabled via ``--no-watchdog``.
    """
    if getattr(args, "no_watchdog", False):
        return None

    timeout: float = getattr(args, "watchdog_timeout", _DEFAULT_TIMEOUT)
    check_interval: float = getattr(
        args, "watchdog_check_interval", _DEFAULT_CHECK_INTERVAL
    )
    callback = on_stall if on_stall is not None else _stall_handler
    return Watchdog(
        timeout=timeout,
        on_stall=callback,
        check_interval=check_interval,
    )


def add_watchdog_arguments(parser: argparse.ArgumentParser) -> None:
    """Register watchdog-related flags on *parser*."""
    grp = parser.add_argument_group("watchdog")
    grp.add_argument(
        "--no-watchdog",
        action="store_true",
        default=False,
        help="Disable the watchdog (not recommended for long-running daemons).",
    )
    grp.add_argument(
        "--watchdog-timeout",
        type=float,
        default=_DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=(
            "Seconds without a heartbeat before the cycle is considered stalled "
            f"(default: {_DEFAULT_TIMEOUT})."
        ),
    )
    grp.add_argument(
        "--watchdog-check-interval",
        type=float,
        default=_DEFAULT_CHECK_INTERVAL,
        metavar="SECONDS",
        help=(
            "How often the watchdog polls for a missed heartbeat "
            f"(default: {_DEFAULT_CHECK_INTERVAL})."
        ),
    )
