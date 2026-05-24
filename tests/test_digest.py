"""Tests for portwatch.digest."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from portwatch.digest import DigestReport, build_digest
from portwatch.history import HistoryRecord, append_record
from portwatch.snapshot import PortEntry
from portwatch.diff import SnapshotDiff


def _entry(port: int, proto: str = "tcp", addr: str = "0.0.0.0") -> PortEntry:
    return PortEntry(proto=proto, address=addr, port=port, pid=None, program=None)


def _make_diff(added=(), removed=()) -> SnapshotDiff:
    return SnapshotDiff(added=list(added), removed=list(removed))


# ---------------------------------------------------------------------------
# DigestReport unit tests
# ---------------------------------------------------------------------------

class TestDigestReport:
    def _report(self, total=0, added=None, removed=None) -> DigestReport:
        now = datetime.now(tz=timezone.utc)
        return DigestReport(
            generated_at=now,
            period_start=now - timedelta(hours=1),
            period_end=now,
            total_events=total,
            added_ports=added or [],
            removed_ports=removed or [],
        )

    def test_is_empty_when_no_events(self):
        assert self._report(total=0).is_empty()

    def test_not_empty_when_events_present(self):
        assert not self._report(total=3).is_empty()

    def test_to_text_contains_header(self):
        text = self._report().to_text()
        assert "Portwatch Digest" in text

    def test_to_text_lists_added_ports(self):
        r = self._report(total=1, added=["tcp:0.0.0.0:8080"])
        assert "8080" in r.to_text()

    def test_to_json_is_valid(self):
        data = json.loads(self._report(total=1, added=["tcp:0.0.0.0:9000"]).to_json())
        assert data["total_events"] == 1
        assert "tcp:0.0.0.0:9000" in data["added_ports"]


# ---------------------------------------------------------------------------
# build_digest integration tests
# ---------------------------------------------------------------------------

class TestBuildDigest:
    def test_empty_history_returns_empty_digest(self, tmp_path):
        hist = tmp_path / "h.json"
        hist.write_text("[]")
        report = build_digest(hist)
        assert report.is_empty()
        assert report.added_ports == []

    def test_counts_events_within_window(self, tmp_path):
        hist = tmp_path / "h.json"
        diff = _make_diff(added=[_entry(8080)])
        append_record(hist, diff)
        append_record(hist, diff)
        report = build_digest(hist)
        assert report.total_events == 2

    def test_added_ports_populated(self, tmp_path):
        hist = tmp_path / "h.json"
        diff = _make_diff(added=[_entry(443)])
        append_record(hist, diff)
        report = build_digest(hist)
        assert any("443" in p for p in report.added_ports)

    def test_removed_ports_populated(self, tmp_path):
        hist = tmp_path / "h.json"
        diff = _make_diff(removed=[_entry(22)])
        append_record(hist, diff)
        report = build_digest(hist)
        assert any("22" in p for p in report.removed_ports)

    def test_since_filter_excludes_old_records(self, tmp_path):
        hist = tmp_path / "h.json"
        diff = _make_diff(added=[_entry(8080)])
        append_record(hist, diff)
        future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        report = build_digest(hist, since=future)
        assert report.is_empty()
