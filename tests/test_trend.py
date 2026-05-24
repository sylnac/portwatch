"""Tests for portwatch.trend."""
from __future__ import annotations

import datetime
from typing import List

import pytest

from portwatch.snapshot import PortEntry
from portwatch.history import HistoryRecord
from portwatch.trend import TrendReport, build_trend


def _entry(port: int, proto: str = "tcp", address: str = "0.0.0.0") -> PortEntry:
    return PortEntry(port=port, proto=proto, address=address, pid=None, program=None)


def _record(
    added: List[PortEntry] | None = None,
    removed: List[PortEntry] | None = None,
) -> HistoryRecord:
    return HistoryRecord(
        timestamp=datetime.datetime.utcnow().isoformat(),
        added=added or [],
        removed=removed or [],
    )


class TestBuildTrend:
    def test_empty_records_returns_empty_report(self):
        report = build_trend([])
        assert report.is_empty()
        assert report.total_events == 0

    def test_counts_added_entries(self):
        records = [
            _record(added=[_entry(80), _entry(443)]),
            _record(added=[_entry(80)]),
        ]
        report = build_trend(records)
        assert report.most_added[80] == 2
        assert report.most_added[443] == 1

    def test_counts_removed_entries(self):
        records = [_record(removed=[_entry(8080), _entry(8080)])]
        report = build_trend(records)
        assert report.most_removed[8080] == 2

    def test_total_events_includes_both_added_and_removed(self):
        records = [
            _record(added=[_entry(22)], removed=[_entry(9000)]),
        ]
        report = build_trend(records)
        assert report.total_events == 2

    def test_by_proto_aggregation(self):
        records = [
            _record(added=[_entry(80, proto="tcp"), _entry(53, proto="udp")]),
            _record(added=[_entry(443, proto="tcp")]),
        ]
        report = build_trend(records)
        assert report.by_proto["tcp"] == 2
        assert report.by_proto["udp"] == 1

    def test_by_address_aggregation(self):
        records = [
            _record(added=[_entry(80, address="0.0.0.0"), _entry(443, address="127.0.0.1")]),
            _record(added=[_entry(8080, address="0.0.0.0")]),
        ]
        report = build_trend(records)
        assert report.by_address["0.0.0.0"] == 2
        assert report.by_address["127.0.0.1"] == 1

    def test_to_text_non_empty(self):
        records = [_record(added=[_entry(80)])]
        report = build_trend(records)
        text = report.to_text()
        assert "Total change events" in text
        assert "80" in text

    def test_to_text_empty(self):
        report = build_trend([])
        assert report.to_text() == "No trend data available."

    def test_is_empty_false_when_events_present(self):
        records = [_record(added=[_entry(22)])]
        report = build_trend(records)
        assert not report.is_empty()
