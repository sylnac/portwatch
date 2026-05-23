"""Tests for portwatch.baseline and the CLI snapshot/check commands."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from portwatch.baseline import (
    baseline_exists,
    load_baseline,
    save_baseline,
)
from portwatch.cli import main
from portwatch.snapshot import PortEntry, PortSnapshot


def _make_snapshot(*ports: int) -> PortSnapshot:
    entries = [
        PortEntry(proto="tcp", local_addr="0.0.0.0", local_port=p, pid=1, process="svc")
        for p in ports
    ]
    snap = PortSnapshot(entries=entries)
    snap.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return snap


class TestSaveLoadBaseline:
    def test_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        original = _make_snapshot(80, 443)
        save_baseline(original, path)
        loaded = load_baseline(path)
        assert loaded is not None
        assert {e.local_port for e in loaded.entries} == {80, 443}

    def test_timestamp_preserved(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        original = _make_snapshot(22)
        save_baseline(original, path)
        loaded = load_baseline(path)
        assert loaded.timestamp == original.timestamp

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        assert load_baseline(tmp_path / "no_such_file.json") is None

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "deep" / "dir" / "baseline.json"
        save_baseline(_make_snapshot(8080), path)
        assert path.exists()

    def test_baseline_exists(self, tmp_path: Path) -> None:
        path = tmp_path / "b.json"
        assert not baseline_exists(path)
        save_baseline(_make_snapshot(9000), path)
        assert baseline_exists(path)


class TestCLI:
    def test_snapshot_command(self, tmp_path: Path) -> None:
        snap = _make_snapshot(80)
        with patch("portwatch.cli.capture_snapshot", return_value=snap):
            rc = main(["--baseline", str(tmp_path / "b.json"), "snapshot"])
        assert rc == 0
        assert (tmp_path / "b.json").exists()

    def test_check_no_baseline(self, tmp_path: Path) -> None:
        rc = main(["--baseline", str(tmp_path / "missing.json"), "check"])
        assert rc == 2

    def test_check_no_changes(self, tmp_path: Path) -> None:
        path = tmp_path / "b.json"
        snap = _make_snapshot(80, 443)
        save_baseline(snap, path)
        with patch("portwatch.cli.capture_snapshot", return_value=snap):
            rc = main(["--baseline", str(path), "check"])
        assert rc == 0

    def test_check_detects_new_port(self, tmp_path: Path) -> None:
        path = tmp_path / "b.json"
        baseline = _make_snapshot(80)
        current = _make_snapshot(80, 9999)
        save_baseline(baseline, path)
        with patch("portwatch.cli.capture_snapshot", return_value=current):
            rc = main(["--baseline", str(path), "check"])
        assert rc == 1
