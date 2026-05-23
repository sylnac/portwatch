"""Tests for portwatch.alert backends."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from portwatch.alert import (
    EmailBackend,
    ExecBackend,
    LoggingBackend,
    build_backend,
)
from portwatch.diff import SnapshotDiff
from portwatch.snapshot import PortEntry


def _make_diff(
    added: list[PortEntry] | None = None,
    removed: list[PortEntry] | None = None,
) -> SnapshotDiff:
    return SnapshotDiff(added=added or [], removed=removed or [])


def _entry(port: int, proto: str = "tcp", pid: int = 1234) -> PortEntry:
    return PortEntry(proto=proto, local_addr="0.0.0.0", local_port=port, pid=pid, process="test")


# ---------------------------------------------------------------------------
# LoggingBackend
# ---------------------------------------------------------------------------

class TestLoggingBackend:
    def test_sends_warning_by_default(self, caplog):
        backend = LoggingBackend()
        diff = _make_diff(added=[_entry(8080)])
        with caplog.at_level(logging.WARNING, logger="portwatch.alert"):
            backend.send(diff)
        assert any("portwatch alert" in r.message for r in caplog.records)

    def test_custom_log_level(self, caplog):
        backend = LoggingBackend(level=logging.ERROR)
        diff = _make_diff(added=[_entry(9000)])
        with caplog.at_level(logging.ERROR, logger="portwatch.alert"):
            backend.send(diff)
        assert caplog.records[0].levelno == logging.ERROR


# ---------------------------------------------------------------------------
# ExecBackend
# ---------------------------------------------------------------------------

class TestExecBackend:
    def test_runs_command_with_summary(self):
        backend = ExecBackend(command=["cat"])
        diff = _make_diff(added=[_entry(3000)])
        with patch("portwatch.alert.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            backend.send(diff)
            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            assert diff.summary() in kwargs["input"]

    def test_logs_error_on_failure(self, caplog):
        import subprocess
        backend = ExecBackend(command=["false"])
        diff = _make_diff(added=[_entry(3000)])
        with patch("portwatch.alert.subprocess.run", side_effect=subprocess.CalledProcessError(1, "false")):
            with caplog.at_level(logging.ERROR, logger="portwatch.alert"):
                backend.send(diff)  # should not raise
        assert any("Alert command failed" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# build_backend factory
# ---------------------------------------------------------------------------

class TestBuildBackend:
    def test_default_returns_logging_backend(self):
        backend = build_backend({})
        assert isinstance(backend, LoggingBackend)

    def test_logging_type(self):
        backend = build_backend({"type": "logging"})
        assert isinstance(backend, LoggingBackend)

    def test_exec_type(self):
        backend = build_backend({"type": "exec", "command": ["notify-send", "alert"]})
        assert isinstance(backend, ExecBackend)
        assert backend.command == ["notify-send", "alert"]

    def test_email_type(self):
        cfg = {
            "type": "email",
            "smtp_host": "mail.example.com",
            "smtp_port": "587",
            "sender": "portwatch@example.com",
            "recipient": "admin@example.com",
        }
        backend = build_backend(cfg)
        assert isinstance(backend, EmailBackend)
        assert backend.smtp_port == 587
        assert backend.use_tls is True
