"""Tests for snapshot capture helpers and diff logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from portwatch.diff import SnapshotDiff, diff_snapshots
from portwatch.snapshot import PortEntry, PortSnapshot


def _make_entry(port: int, proto: str = "tcp", pid: int = 1, name: str = "app") -> PortEntry:
    return PortEntry(pid=pid, process_name=name, local_address="0.0.0.0", local_port=port, protocol=proto)


class TestSnapshotDiff:
    def test_no_changes(self):
        snap = PortSnapshot(entries=[_make_entry(8080)])
        diff = diff_snapshots(snap, snap)
        assert not diff.has_changes

    def test_detects_added_port(self):
        before = PortSnapshot(entries=[_make_entry(8080)])
        after = PortSnapshot(entries=[_make_entry(8080), _make_entry(9090)])
        diff = diff_snapshots(before, after)
        assert diff.has_changes
        assert len(diff.added) == 1
        assert diff.added[0].local_port == 9090
        assert diff.removed == []

    def test_detects_removed_port(self):
        before = PortSnapshot(entries=[_make_entry(8080), _make_entry(9090)])
        after = PortSnapshot(entries=[_make_entry(8080)])
        diff = diff_snapshots(before, after)
        assert diff.has_changes
        assert len(diff.removed) == 1
        assert diff.removed[0].local_port == 9090
        assert diff.added == []

    def test_protocol_distinguishes_entries(self):
        before = PortSnapshot(entries=[_make_entry(53, proto="tcp")])
        after = PortSnapshot(entries=[_make_entry(53, proto="tcp"), _make_entry(53, proto="udp")])
        diff = diff_snapshots(before, after)
        assert len(diff.added) == 1
        assert diff.added[0].protocol == "udp"

    def test_summary_contains_plus_minus(self):
        diff = SnapshotDiff(
            added=[_make_entry(1234)],
            removed=[_make_entry(5678)],
        )
        summary = diff.summary()
        assert "[+]" in summary
        assert "[-]" in summary

    def test_empty_summary(self):
        diff = SnapshotDiff()
        assert "no changes" in diff.summary()


class TestCaptureSnapshot:
    def test_returns_snapshot_instance(self):
        """Smoke-test that capture_snapshot() returns a PortSnapshot."""
        from portwatch.snapshot import PortSnapshot, capture_snapshot

        fake_conn = MagicMock()
        fake_conn.laddr = MagicMock(ip="127.0.0.1", port=8080)
        fake_conn.pid = 42
        fake_conn.status = "LISTEN"

        fake_proc = MagicMock()
        fake_proc.name.return_value = "python"

        with patch("psutil.net_connections", return_value=[fake_conn]), \
             patch("psutil.Process", return_value=fake_proc):
            snap = capture_snapshot()

        assert isinstance(snap, PortSnapshot)
        assert any(e.local_port == 8080 for e in snap.entries)
