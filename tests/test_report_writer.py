"""Tests for portwatch.report_writer."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from portwatch.report_writer import write_report, write_report_from_file
from portwatch.history import HistoryRecord
from portwatch.snapshot import PortEntry


def _entry(port=8080):
    return PortEntry(proto="tcp", host="127.0.0.1", port=port, pid=999)


def _record(added=(), removed=(), ts=1_700_000_000.0):
    rec = MagicMock(spec=HistoryRecord)
    rec.timestamp = ts
    rec.added = list(added)
    rec.removed = list(removed)
    return rec


class TestWriteReport:
    def test_writes_to_stdout(self, capsys):
        write_report([], fmt="text")
        captured = capsys.readouterr()
        assert "No changes recorded" in captured.out

    def test_writes_to_file(self, tmp_path):
        dest = tmp_path / "report.txt"
        write_report([_record(added=[_entry()])], fmt="text", output=str(dest))
        assert dest.exists()
        assert "tcp" in dest.read_text()

    def test_creates_parent_dirs(self, tmp_path):
        dest = tmp_path / "sub" / "dir" / "report.json"
        write_report([], fmt="json", output=str(dest))
        assert dest.exists()

    def test_json_file_is_valid(self, tmp_path):
        dest = tmp_path / "out.json"
        write_report([_record(added=[_entry(port=22)])], fmt="json", output=str(dest))
        data = json.loads(dest.read_text())
        assert data[0]["added"][0]["port"] == 22


class TestWriteReportFromFile:
    def _make_history_file(self, tmp_path, records):
        """Write a minimal JSONL history file."""
        path = tmp_path / "history.jsonl"
        lines = [
            json.dumps(
                {
                    "timestamp": r.timestamp,
                    "added": [{"proto": e.proto, "host": e.host, "port": e.port, "pid": e.pid} for e in r.added],
                    "removed": [{"proto": e.proto, "host": e.host, "port": e.port, "pid": e.pid} for e in r.removed],
                }
            )
            for r in records
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    def test_loads_and_renders(self, tmp_path, capsys):
        rec = _record(added=[_entry(port=3000)])
        hp = self._make_history_file(tmp_path, [rec])
        write_report_from_file(hp, fmt="text")
        out = capsys.readouterr().out
        assert "3000" in out

    def test_limit_applied(self, tmp_path, capsys):
        records = [_record(added=[_entry(port=p)], ts=float(p)) for p in range(5000, 5010)]
        hp = self._make_history_file(tmp_path, records)
        write_report_from_file(hp, fmt="text", limit=3)
        out = capsys.readouterr().out
        # Only the last 3 ports (5007, 5008, 5009) should appear
        assert "5009" in out
        assert "5000" not in out
