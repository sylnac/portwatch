"""Tests for portwatch.anomaly scoring module."""

from __future__ import annotations

import pytest

from portwatch.anomaly import (
    AnomalyScore,
    score_diff,
    score_entry,
    _SCORE_PRIVILEGED_PORT,
    _SCORE_WILDCARD_ADDRESS,
    _SCORE_UNKNOWN_PROTOCOL,
)
from portwatch.diff import SnapshotDiff
from portwatch.snapshot import PortEntry


def _entry(
    port: int = 8080,
    proto: str = "tcp",
    address: str = "127.0.0.1",
    pid: int = 1234,
    process: str = "test",
) -> PortEntry:
    return PortEntry(port=port, proto=proto, address=address, pid=pid, process=process)


class TestScoreEntry:
    def test_high_port_no_wildcard_low_severity(self):
        result = score_entry(_entry(port=8080))
        assert result.severity == "LOW"
        assert result.score == 0

    def test_privileged_port_increases_score(self):
        result = score_entry(_entry(port=80))
        assert result.score >= _SCORE_PRIVILEGED_PORT

    def test_wildcard_address_increases_score(self):
        result = score_entry(_entry(address="0.0.0.0"))
        assert result.score >= _SCORE_WILDCARD_ADDRESS

    def test_ipv6_wildcard_address_increases_score(self):
        result = score_entry(_entry(address="::"))
        assert result.score >= _SCORE_WILDCARD_ADDRESS

    def test_unknown_protocol_increases_score(self):
        result = score_entry(_entry(proto="sctp"))
        assert result.score >= _SCORE_UNKNOWN_PROTOCOL

    def test_all_heuristics_combine_additively(self):
        entry = _entry(port=22, proto="sctp", address="0.0.0.0")
        result = score_entry(entry)
        expected = _SCORE_PRIVILEGED_PORT + _SCORE_WILDCARD_ADDRESS + _SCORE_UNKNOWN_PROTOCOL
        assert result.score == expected

    def test_high_severity_threshold(self):
        entry = _entry(port=22, address="0.0.0.0")
        result = score_entry(entry)
        assert result.severity == "HIGH"

    def test_medium_severity_threshold(self):
        entry = _entry(port=8080, address="0.0.0.0")
        result = score_entry(entry)
        assert result.severity == "MEDIUM"

    def test_reasons_populated(self):
        result = score_entry(_entry(port=443))
        assert any("privileged" in r for r in result.reasons)

    def test_no_concerns_reason_when_benign(self):
        result = score_entry(_entry(port=9000))
        assert result.reasons == ["no specific concerns"]

    def test_str_includes_severity(self):
        result = score_entry(_entry(port=22, address="0.0.0.0"))
        assert "HIGH" in str(result)


class TestScoreDiff:
    def _diff(self, added=None, removed=None):
        return SnapshotDiff(added=added or [], removed=removed or [])

    def test_empty_diff_returns_empty_list(self):
        assert score_diff(self._diff()) == []

    def test_scores_added_entries(self):
        diff = self._diff(added=[_entry(port=80), _entry(port=443)])
        results = score_diff(diff)
        assert len(results) == 2

    def test_removed_entries_not_scored(self):
        diff = self._diff(removed=[_entry(port=22)])
        assert score_diff(diff) == []

    def test_returns_anomaly_score_instances(self):
        diff = self._diff(added=[_entry()])
        results = score_diff(diff)
        assert all(isinstance(r, AnomalyScore) for r in results)
