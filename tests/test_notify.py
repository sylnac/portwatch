"""Tests for portwatch.notify.Notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from portwatch.alert import AlertBackend, LoggingBackend
from portwatch.diff import SnapshotDiff
from portwatch.notify import Notifier
from portwatch.snapshot import PortEntry, PortSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(port: int, proto: str = "tcp", pid: int = 1234) -> PortEntry:
    return PortEntry(port=port, proto=proto, local_addr="127.0.0.1", pid=pid, process="test")


def _diff_with_changes() -> SnapshotDiff:
    """Return a diff that has at least one added port."""
    old = PortSnapshot(entries=[], captured_at=0.0)
    new = PortSnapshot(entries=[_make_entry(8080)], captured_at=1.0)
    from portwatch.diff import diff_snapshots
    return diff_snapshots(old, new)


def _diff_no_changes() -> SnapshotDiff:
    """Return a diff with no changes."""
    snap = PortSnapshot(entries=[_make_entry(80)], captured_at=0.0)
    from portwatch.diff import diff_snapshots
    return diff_snapshots(snap, snap)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNotifier:
    def test_default_backend_is_logging(self):
        n = Notifier()
        assert len(n._backends) == 1
        assert isinstance(n._backends[0], LoggingBackend)

    def test_custom_backends_stored(self):
        b1, b2 = MagicMock(spec=AlertBackend), MagicMock(spec=AlertBackend)
        n = Notifier(backends=[b1, b2])
        assert n._backends == [b1, b2]

    def test_dispatch_calls_all_backends(self):
        b1, b2 = MagicMock(spec=AlertBackend), MagicMock(spec=AlertBackend)
        n = Notifier(backends=[b1, b2])
        diff = _diff_with_changes()
        n.dispatch(diff)
        b1.send.assert_called_once_with(diff)
        b2.send.assert_called_once_with(diff)

    def test_dispatch_skips_when_no_changes(self):
        b = MagicMock(spec=AlertBackend)
        n = Notifier(backends=[b])
        n.dispatch(_diff_no_changes())
        b.send.assert_not_called()

    def test_failing_backend_does_not_block_others(self):
        bad = MagicMock(spec=AlertBackend)
        bad.send.side_effect = RuntimeError("boom")
        good = MagicMock(spec=AlertBackend)
        n = Notifier(backends=[bad, good])
        diff = _diff_with_changes()
        n.dispatch(diff)  # should not raise
        good.send.assert_called_once_with(diff)

    def test_add_backend(self):
        n = Notifier(backends=[])
        b = MagicMock(spec=AlertBackend)
        n.add_backend(b)
        assert b in n._backends

    def test_remove_backend(self):
        b = MagicMock(spec=AlertBackend)
        n = Notifier(backends=[b])
        n.remove_backend(b)
        assert b not in n._backends

    def test_remove_backend_noop_if_missing(self):
        n = Notifier(backends=[])
        b = MagicMock(spec=AlertBackend)
        n.remove_backend(b)  # should not raise
