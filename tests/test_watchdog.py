"""Tests for portwatch.watchdog and portwatch.cli_watchdog."""

from __future__ import annotations

import argparse
import time
from unittest.mock import MagicMock

import pytest

from portwatch.watchdog import Watchdog
from portwatch.cli_watchdog import (
    add_watchdog_arguments,
    build_watchdog_from_args,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_watchdog(timeout=0.2, check_interval=0.05, on_stall=None):
    callback = on_stall or (lambda n: None)
    return Watchdog(timeout=timeout, on_stall=callback, check_interval=check_interval)


# ---------------------------------------------------------------------------
# Watchdog unit tests
# ---------------------------------------------------------------------------

class TestWatchdog:
    def test_raises_on_non_positive_timeout(self):
        with pytest.raises(ValueError, match="timeout"):
            Watchdog(timeout=0, on_stall=lambda n: None)

    def test_raises_on_non_positive_check_interval(self):
        with pytest.raises(ValueError, match="check_interval"):
            Watchdog(timeout=1, on_stall=lambda n: None, check_interval=0)

    def test_not_running_before_start(self):
        wd = _make_watchdog()
        assert not wd.running

    def test_running_after_start(self):
        wd = _make_watchdog()
        wd.start()
        try:
            assert wd.running
        finally:
            wd.stop()

    def test_not_running_after_stop(self):
        wd = _make_watchdog()
        wd.start()
        wd.stop()
        assert not wd.running

    def test_stall_callback_fired_when_no_heartbeat(self):
        fired = []
        wd = _make_watchdog(timeout=0.1, check_interval=0.05, on_stall=fired.append)
        wd.start()
        time.sleep(0.35)
        wd.stop()
        assert len(fired) >= 1
        assert fired[0] == 1

    def test_heartbeat_resets_missed_beats(self):
        fired = []
        wd = _make_watchdog(timeout=0.15, check_interval=0.05, on_stall=fired.append)
        wd.start()
        time.sleep(0.2)   # let one stall fire
        wd.heartbeat()     # reset
        pre_reset_count = len(fired)
        # After heartbeat the missed_beats counter should be 0 again
        assert wd._state.missed_beats == 0
        wd.stop()
        assert pre_reset_count >= 1

    def test_start_is_idempotent(self):
        wd = _make_watchdog()
        wd.start()
        wd.start()  # second call should not raise
        wd.stop()


# ---------------------------------------------------------------------------
# CLI watchdog helper tests
# ---------------------------------------------------------------------------

class TestBuildWatchdogFromArgs:
    def _parser(self):
        p = argparse.ArgumentParser()
        add_watchdog_arguments(p)
        return p

    def test_returns_watchdog_by_default(self):
        args = self._parser().parse_args([])
        wd = build_watchdog_from_args(args)
        assert isinstance(wd, Watchdog)

    def test_returns_none_when_disabled(self):
        args = self._parser().parse_args(["--no-watchdog"])
        wd = build_watchdog_from_args(args)
        assert wd is None

    def test_custom_timeout_applied(self):
        args = self._parser().parse_args(["--watchdog-timeout", "120"])
        wd = build_watchdog_from_args(args)
        assert wd._timeout == 120.0

    def test_custom_on_stall_used(self):
        callback = MagicMock()
        args = self._parser().parse_args([])
        wd = build_watchdog_from_args(args, on_stall=callback)
        assert wd._on_stall is callback
