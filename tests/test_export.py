"""Tests for portwatch.export."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from portwatch.export import snapshot_to_csv, snapshot_to_json, write_snapshot_export
from portwatch.snapshot import PortEntry, PortSnapshot


def _make_snapshot(*entries: PortEntry) -> PortSnapshot:
    return PortSnapshot(timestamp=1_700_000_000.0, entries=list(entries))


def _entry(proto="tcp", address="0.0.0.0", port=8080, pid=42, process="python") -> PortEntry:
    return PortEntry(proto=proto, address=address, port=port, pid=pid, process=process)


class TestSnapshotToCsv:
    def test_header_present(self):
        snap = _make_snapshot(_entry())
        csv = snapshot_to_csv(snap)
        assert csv.splitlines()[0] == "proto,address,port,pid,process"

    def test_entry_row(self):
        snap = _make_snapshot(_entry(port=9000, process="nginx", pid=10))
        lines = snapshot_to_csv(snap).splitlines()
        assert any("9000" in line and "nginx" in line for line in lines)

    def test_none_pid_becomes_empty_string(self):
        snap = _make_snapshot(_entry(pid=None, process=None))
        csv = snapshot_to_csv(snap)
        # two consecutive commas for empty pid and process
        assert ",," in csv

    def test_sorted_by_proto_then_port(self):
        snap = _make_snapshot(
            _entry(proto="udp", port=53),
            _entry(proto="tcp", port=22),
            _entry(proto="tcp", port=80),
        )
        rows = snapshot_to_csv(snap).splitlines()[1:]  # skip header
        protos = [r.split(",")[0] for r in rows]
        ports = [int(r.split(",")[2]) for r in rows]
        assert protos == ["tcp", "tcp", "udp"]
        assert ports[:2] == [22, 80]


class TestSnapshotToJson:
    def test_returns_valid_json(self):
        snap = _make_snapshot(_entry())
        data = json.loads(snapshot_to_json(snap))
        assert "entries" in data
        assert "timestamp" in data

    def test_timestamp_preserved(self):
        snap = _make_snapshot(_entry())
        data = json.loads(snapshot_to_json(snap))
        assert data["timestamp"] == pytest.approx(1_700_000_000.0)

    def test_entry_fields(self):
        snap = _make_snapshot(_entry(port=443, process="nginx", pid=5))
        data = json.loads(snapshot_to_json(snap))
        entry = data["entries"][0]
        assert entry["port"] == 443
        assert entry["process"] == "nginx"
        assert entry["pid"] == 5


class TestWriteSnapshotExport:
    def test_returns_string_when_no_path(self):
        snap = _make_snapshot(_entry())
        result = write_snapshot_export(snap, fmt="json", path=None)
        assert isinstance(result, str)
        json.loads(result)  # must be valid JSON

    def test_writes_file(self, tmp_path: Path):
        snap = _make_snapshot(_entry())
        dest = str(tmp_path / "out.json")
        write_snapshot_export(snap, fmt="json", path=dest)
        assert os.path.exists(dest)
        with open(dest) as fh:
            data = json.load(fh)
        assert "entries" in data

    def test_csv_file(self, tmp_path: Path):
        snap = _make_snapshot(_entry())
        dest = str(tmp_path / "out.csv")
        write_snapshot_export(snap, fmt="csv", path=dest)
        with open(dest) as fh:
            header = fh.readline().strip()
        assert header == "proto,address,port,pid,process"

    def test_invalid_format_raises(self):
        snap = _make_snapshot(_entry())
        with pytest.raises(ValueError, match="Unsupported export format"):
            write_snapshot_export(snap, fmt="xml")
