"""Tests for portwatch.report."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from portwatch.report import build_report, records_to_json, records_to_text
from portwatch.snapshot import PortEntry
from portwatch.history import HistoryRecord


def _entry(proto="tcp", host="0.0.0.0", port=8080, pid=1234):
    return PortEntry(proto=proto, host=host, port=port, pid=pid)


def _record(added=(), removed=(), ts=1_700_000_000.0):
    rec = MagicMock(spec=HistoryRecord)
    rec.timestamp = ts
    rec.added = list(added)
    rec.removed = list(removed)
    return rec


class TestRecordsToText:
    def test_empty_returns_no_changes(self):
        out = records_to_text([])
        assert "No changes recorded" in out

    def test_added_entry_shown_with_plus(self):
        rec = _record(added=[_entry(port=9000)])
        out = records_to_text([rec])
        assert "+ tcp" in out
        assert "9000" in out

    def test_removed_entry_shown_with_minus(self):
        rec = _record(removed=[_entry(port=22)])
        out = records_to_text([rec])
        assert "- tcp" in out
        assert "22" in out

    def test_custom_title_appears(self):
        out = records_to_text([], title="My Report")
        assert "My Report" in out

    def test_timestamp_iso_format_present(self):
        rec = _record(added=[_entry()], ts=1_700_000_000.0)
        out = records_to_text([rec])
        assert "2023-" in out  # UTC year for that epoch value


class TestRecordsToJson:
    def test_returns_valid_json(self):
        rec = _record(added=[_entry()])
        data = json.loads(records_to_json([rec]))
        assert isinstance(data, list)
        assert len(data) == 1

    def test_added_field_present(self):
        rec = _record(added=[_entry(port=443)])
        data = json.loads(records_to_json([rec]))
        assert data[0]["added"][0]["port"] == 443

    def test_removed_field_present(self):
        rec = _record(removed=[_entry(port=80)])
        data = json.loads(records_to_json([rec]))
        assert data[0]["removed"][0]["port"] == 80

    def test_empty_records_gives_empty_list(self):
        data = json.loads(records_to_json([]))
        assert data == []


class TestBuildReport:
    def test_text_format(self):
        out = build_report([], fmt="text")
        assert "No changes recorded" in out

    def test_json_format(self):
        out = build_report([], fmt="json")
        assert json.loads(out) == []

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown report format"):
            build_report([], fmt="csv")
