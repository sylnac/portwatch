"""Configuration loader for portwatch."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/portwatch/config.json")


@dataclass
class Config:
    """Runtime configuration for the portwatch daemon."""

    poll_interval: float = 5.0  # seconds between snapshots
    allowed_ports: List[int] = field(default_factory=list)  # ports never alerted on
    log_file: str = "/var/log/portwatch.log"
    alert_on_removal: bool = False


def load_config(path: str = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a JSON file, falling back to defaults."""
    if not os.path.exists(path):
        return Config()

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    return Config(
        poll_interval=float(data.get("poll_interval", 5.0)),
        allowed_ports=list(data.get("allowed_ports", [])),
        log_file=str(data.get("log_file", "/var/log/portwatch.log")),
        alert_on_removal=bool(data.get("alert_on_removal", False)),
    )


def save_default_config(path: str = DEFAULT_CONFIG_PATH) -> None:
    """Write a default config file to *path* if it does not already exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return
    cfg = Config()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "poll_interval": cfg.poll_interval,
                "allowed_ports": cfg.allowed_ports,
                "log_file": cfg.log_file,
                "alert_on_removal": cfg.alert_on_removal,
            },
            fh,
            indent=2,
        )
