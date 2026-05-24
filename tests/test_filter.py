"""Tests for portwatch.filter."""

from __future__ import annotations

import pytest

from portwatch.filter import FilterRule, FilterSet, build_filter_set
from portwatch.snapshot import PortEntry


def _entry(port: int = 8080, proto: str = "tcp", address: str = "0.0.0.0") -> PortEntry:
    return PortEntry(port=port, proto=proto, address=address, pid=1, process="test")


class TestFilterRule:
    def test_matches_by_port(self):
        rule = FilterRule(port=8080)
        assert rule.matches(_entry(port=8080))
        assert not rule.matches(_entry(port=9090))

    def test_matches_by_proto(self):
        rule = FilterRule(proto="udp")
        assert rule.matches(_entry(proto="udp"))
        assert not rule.matches(_entry(proto="tcp"))

    def test_matches_by_address(self):
        rule = FilterRule(address="127.0.0.1")
        assert rule.matches(_entry(address="127.0.0.1"))
        assert not rule.matches(_entry(address="0.0.0.0"))

    def test_matches_all_fields(self):
        rule = FilterRule(port=443, proto="tcp", address="0.0.0.0")
        assert rule.matches(_entry(port=443, proto="tcp", address="0.0.0.0"))
        assert not rule.matches(_entry(port=443, proto="udp", address="0.0.0.0"))

    def test_empty_rule_matches_everything(self):
        rule = FilterRule()
        assert rule.matches(_entry())

    def test_proto_comparison_is_case_insensitive(self):
        rule = FilterRule(proto="TCP")
        assert rule.matches(_entry(proto="tcp"))


class TestFilterSet:
    def test_not_suppressed_when_no_rules(self):
        fs = FilterSet()
        assert not fs.is_suppressed(_entry())

    def test_suppressed_when_rule_matches(self):
        fs = FilterSet()
        fs.add_rule(FilterRule(port=8080))
        assert fs.is_suppressed(_entry(port=8080))

    def test_not_suppressed_when_no_rule_matches(self):
        fs = FilterSet()
        fs.add_rule(FilterRule(port=9090))
        assert not fs.is_suppressed(_entry(port=8080))

    def test_apply_removes_suppressed_entries(self):
        fs = FilterSet()
        fs.add_rule(FilterRule(port=80))
        entries = [_entry(port=80), _entry(port=443), _entry(port=8080)]
        result = fs.apply(entries)
        assert len(result) == 2
        assert all(e.port != 80 for e in result)

    def test_apply_returns_all_when_no_rules(self):
        fs = FilterSet()
        entries = [_entry(port=80), _entry(port=443)]
        assert fs.apply(entries) == entries


class TestBuildFilterSet:
    def test_builds_from_dict_list(self):
        cfg = [
            {"port": 22, "proto": "tcp", "comment": "SSH"},
            {"port": 53, "proto": "udp"},
        ]
        fs = build_filter_set(cfg)
        assert len(fs.rules) == 2
        assert fs.is_suppressed(_entry(port=22, proto="tcp"))
        assert fs.is_suppressed(_entry(port=53, proto="udp"))
        assert not fs.is_suppressed(_entry(port=80, proto="tcp"))

    def test_empty_list_yields_empty_filter_set(self):
        fs = build_filter_set([])
        assert len(fs.rules) == 0
