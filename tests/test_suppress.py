"""Tests for portwatch.suppress."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from portwatch.snapshot import PortEntry
from portwatch.suppress import (
    SuppressionStore,
    SuppressionWindow,
    load_suppressions,
    save_suppressions,
)


def _entry(port: int = 8080, proto: str = "tcp") -> PortEntry:
    return PortEntry(proto=proto, local_address="0.0.0.0", port=port, pid=1, process="test")


def _window(port: int = 8080, proto: str = "*", offset: float = 300.0) -> SuppressionWindow:
    return SuppressionWindow(
        port=port, proto=proto, reason="test", expires_at=time.time() + offset
    )


class TestSuppressionWindow:
    def test_active_when_not_expired(self):
        w = _window(offset=60)
        assert w.is_active()

    def test_inactive_when_expired(self):
        w = _window(offset=-1)
        assert not w.is_active()

    def test_matches_by_port_and_wildcard_proto(self):
        w = _window(port=9000, proto="*")
        assert w.matches(_entry(port=9000, proto="tcp"))
        assert w.matches(_entry(port=9000, proto="udp"))

    def test_does_not_match_different_port(self):
        w = _window(port=9000)
        assert not w.matches(_entry(port=8080))

    def test_matches_specific_proto(self):
        w = _window(port=8080, proto="udp")
        assert w.matches(_entry(port=8080, proto="udp"))
        assert not w.matches(_entry(port=8080, proto="tcp"))


class TestSuppressionStore:
    def test_not_suppressed_when_empty(self):
        store = SuppressionStore()
        assert not store.is_suppressed(_entry())

    def test_suppresses_matching_active_window(self):
        store = SuppressionStore()
        store.add(_window(port=8080))
        assert store.is_suppressed(_entry(port=8080))

    def test_does_not_suppress_expired_window(self):
        store = SuppressionStore()
        store.add(_window(port=8080, offset=-1))
        assert not store.is_suppressed(_entry(port=8080))

    def test_purge_removes_expired(self):
        store = SuppressionStore()
        store.add(_window(offset=-1))
        store.add(_window(offset=300))
        removed = store.purge_expired()
        assert removed == 1
        assert len(store.active_windows()) == 1

    def test_active_windows_excludes_expired(self):
        store = SuppressionStore()
        store.add(_window(offset=-5))
        store.add(_window(port=9000, offset=120))
        active = store.active_windows()
        assert len(active) == 1
        assert active[0].port == 9000


class TestPersistence:
    def test_round_trip(self, tmp_path: Path):
        path = tmp_path / "suppressions.json"
        store = SuppressionStore()
        store.add(_window(port=443, proto="tcp"))
        save_suppressions(store, path)
        loaded = load_suppressions(path)
        assert len(loaded.active_windows()) == 1
        assert loaded.active_windows()[0].port == 443

    def test_returns_empty_store_when_file_missing(self, tmp_path: Path):
        store = load_suppressions(tmp_path / "nope.json")
        assert store.active_windows() == []

    def test_saved_json_is_valid(self, tmp_path: Path):
        path = tmp_path / "s.json"
        store = SuppressionStore()
        store.add(_window())
        save_suppressions(store, path)
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert data[0]["port"] == 8080
