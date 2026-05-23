"""Alert backends for portwatch notifications."""

from __future__ import annotations

import logging
import smtplib
import subprocess
from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import Optional

from portwatch.diff import SnapshotDiff

logger = logging.getLogger(__name__)


class AlertBackend(ABC):
    """Abstract base class for alert backends."""

    @abstractmethod
    def send(self, diff: SnapshotDiff) -> None:
        """Send an alert for the given diff."""
        ...


class LoggingBackend(AlertBackend):
    """Sends alerts via Python logging."""

    def __init__(self, level: int = logging.WARNING) -> None:
        self.level = level

    def send(self, diff: SnapshotDiff) -> None:
        logger.log(self.level, "portwatch alert: %s", diff.summary())


class EmailBackend(AlertBackend):
    """Sends alerts via SMTP email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        recipient: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender = sender
        self.recipient = recipient
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(self, diff: SnapshotDiff) -> None:
        msg = EmailMessage()
        msg["Subject"] = "portwatch: unexpected port binding detected"
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg.set_content(diff.summary())

        try:
            cls = smtplib.SMTP_SSL if self.use_tls else smtplib.SMTP
            with cls(self.smtp_host, self.smtp_port) as smtp:
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(msg)
            logger.info("Alert email sent to %s", self.recipient)
        except smtplib.SMTPException as exc:
            logger.error("Failed to send alert email: %s", exc)


class ExecBackend(AlertBackend):
    """Runs an external command with the alert summary as stdin."""

    def __init__(self, command: list[str]) -> None:
        self.command = command

    def send(self, diff: SnapshotDiff) -> None:
        try:
            subprocess.run(
                self.command,
                input=diff.summary(),
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.error("Alert command failed: %s", exc)


def build_backend(config: dict) -> AlertBackend:
    """Factory: construct an AlertBackend from a config dict."""
    kind = config.get("type", "logging")
    if kind == "email":
        return EmailBackend(
            smtp_host=config["smtp_host"],
            smtp_port=int(config.get("smtp_port", 465)),
            sender=config["sender"],
            recipient=config["recipient"],
            username=config.get("username"),
            password=config.get("password"),
            use_tls=bool(config.get("use_tls", True)),
        )
    if kind == "exec":
        return ExecBackend(command=config["command"])
    return LoggingBackend()
