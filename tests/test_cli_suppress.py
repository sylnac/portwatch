"""Tests for portwatch.cli_suppress CLI sub-commands."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from portwatch.cli_suppress import (
    cmd_suppress_add,
    cmd_suppress_list,
    cmd_suppress_purge,
)
from portwatch.suppress import SuppressionWindow, SuppressionStore, save_suppressions, load_suppressions


def _args(**kwargs):
    defaults = {
        "port": 8080,
        "proto": "tcp",
        "duration": 30,
        "reason": "maintenance",
        "suppress_file": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestCmdSuppressAdd:
    def test_creates_suppression_file(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        args = _args(suppress_file=str(path))
        cmd_suppress_add(args)
        assert path.exists()

    def test_output_confirms_port(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        args = _args(port=9090, suppress_file=str(path))
        cmd_suppress_add(args)
        out = capsys.readouterr().out
        assert "9090" in out

    def test_window_is_active_after_add(self, tmp_path: Path):
        path = tmp_path / "s.json"
        args = _args(port=443, proto="tcp", duration=60, suppress_file=str(path))
        cmd_suppress_add(args)
        store = load_suppressions(path)
        assert len(store.active_windows()) == 1
        assert store.active_windows()[0].port == 443


class TestCmdSuppressList:
    def test_prints_no_active_when_empty(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        cmd_suppress_list(_args(suppress_file=str(path)))
        out = capsys.readouterr().out
        assert "No active" in out

    def test_lists_active_window(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        store = SuppressionStore()
        store.add(SuppressionWindow(port=8080, proto="tcp", reason="deploy", expires_at=time.time() + 300))
        save_suppressions(store, path)
        cmd_suppress_list(_args(suppress_file=str(path)))
        out = capsys.readouterr().out
        assert "8080" in out
        assert "deploy" in out


class TestCmdSuppressPurge:
    def test_purges_expired_windows(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        store = SuppressionStore()
        store.add(SuppressionWindow(port=1234, proto="*", reason="old", expires_at=time.time() - 1))
        save_suppressions(store, path)
        cmd_suppress_purge(_args(suppress_file=str(path)))
        out = capsys.readouterr().out
        assert "1" in out
        reloaded = load_suppressions(path)
        assert reloaded.active_windows() == []

    def test_purge_zero_when_none_expired(self, tmp_path: Path, capsys):
        path = tmp_path / "s.json"
        store = SuppressionStore()
        store.add(SuppressionWindow(port=80, proto="tcp", reason="ok", expires_at=time.time() + 999))
        save_suppressions(store, path)
        cmd_suppress_purge(_args(suppress_file=str(path)))
        out = capsys.readouterr().out
        assert "0" in out
