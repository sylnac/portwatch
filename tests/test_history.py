"""Tests for portwatch.history module."""

import json
import pytest
from pathlib import Path

from portwatch.snapshot import PortEntry, PortSnapshot
from portwatch.diff import SnapshotDiff
from portwatch.history import append_record, load_history, HistoryRecord


def _make_entry(port: int, proto: str = "tcp", process: str = "svc") -> PortEntry:
    return PortEntry(
        proto=proto,
        local_addr="0.0.0.0",
        local_port=port,
        pid=1000 + port,
        process=process,
    )


def _make_diff(added=(), removed=()) -> SnapshotDiff:
    import time
    ts = time.time()
    before = PortSnapshot(timestamp=ts, entries=list(removed))
    after = PortSnapshot(timestamp=ts + 1, entries=list(added))
    return SnapshotDiff(added=list(added), removed=list(removed))


class TestAppendRecord:
    def test_no_write_when_no_changes(self, tmp_path):
        hist_file = tmp_path / "history.json"
        diff = _make_diff()
        append_record(diff, path=hist_file)
        assert not hist_file.exists()

    def test_creates_file_on_first_change(self, tmp_path):
        hist_file = tmp_path / "history.json"
        diff = _make_diff(added=[_make_entry(8080)])
        append_record(diff, path=hist_file)
        assert hist_file.exists()

    def test_record_contains_added_port(self, tmp_path):
        hist_file = tmp_path / "history.json"
        diff = _make_diff(added=[_make_entry(9000)])
        append_record(diff, path=hist_file)
        records = load_history(hist_file)
        assert len(records) == 1
        assert records[0].added[0]["local_port"] == 9000

    def test_record_contains_removed_port(self, tmp_path):
        hist_file = tmp_path / "history.json"
        diff = _make_diff(removed=[_make_entry(3306)])
        append_record(diff, path=hist_file)
        records = load_history(hist_file)
        assert records[0].removed[0]["local_port"] == 3306

    def test_multiple_appends(self, tmp_path):
        hist_file = tmp_path / "history.json"
        for port in (80, 443, 8080):
            diff = _make_diff(added=[_make_entry(port)])
            append_record(diff, path=hist_file)
        records = load_history(hist_file)
        assert len(records) == 3

    def test_prunes_old_entries(self, tmp_path):
        hist_file = tmp_path / "history.json"
        for port in range(200):
            diff = _make_diff(added=[_make_entry(port + 1024)])
            append_record(diff, path=hist_file, max_entries=50)
        records = load_history(hist_file)
        assert len(records) == 50

    def test_record_has_timestamp(self, tmp_path):
        hist_file = tmp_path / "history.json"
        diff = _make_diff(added=[_make_entry(22)])
        append_record(diff, path=hist_file)
        records = load_history(hist_file)
        assert records[0].timestamp  # non-empty string


class TestLoadHistory:
    def test_returns_empty_list_when_missing(self, tmp_path):
        result = load_history(tmp_path / "nonexistent.json")
        assert result == []

    def test_returns_empty_list_on_corrupt_file(self, tmp_path):
        bad = tmp_path / "history.json"
        bad.write_text("not valid json")
        result = load_history(bad)
        assert result == []
