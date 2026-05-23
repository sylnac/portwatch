"""Configuration loading and defaults for portwatch."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("/etc/portwatch/config.toml")

DEFAULT_TOML = """\
[portwatch]
interval = 30          # seconds between snapshots
baseline_file = "/var/lib/portwatch/baseline.json"

[portwatch.allowed]
# List allowed bindings as [[proto, port]] pairs, e.g.:
# ports = [["tcp", 22], ["tcp", 80], ["tcp", 443]]
ports = []

[portwatch.alert]
# type = "logging"   # options: logging | email | exec
type = "logging"

# --- email example ---
# type = "email"
# smtp_host = "mail.example.com"
# smtp_port = 465
# sender = "portwatch@example.com"
# recipient = "admin@example.com"
# use_tls = true

# --- exec example ---
# type = "exec"
# command = ["notify-send", "portwatch alert"]
"""


@dataclass
class Config:
    interval: int = 30
    baseline_file: Path = Path("/var/lib/portwatch/baseline.json")
    allowed_ports: list[tuple[str, int]] = field(default_factory=list)
    alert: dict[str, Any] = field(default_factory=lambda: {"type": "logging"})


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a TOML file."""
    if not path.exists():
        return Config()

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    pw = data.get("portwatch", {})
    allowed_raw = pw.get("allowed", {}).get("ports", [])
    allowed_ports = [(proto, int(port)) for proto, port in allowed_raw]

    return Config(
        interval=int(pw.get("interval", 30)),
        baseline_file=Path(pw.get("baseline_file", "/var/lib/portwatch/baseline.json")),
        allowed_ports=allowed_ports,
        alert=pw.get("alert", {"type": "logging"}),
    )


def save_default_config(path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Write the default TOML config to *path* (creates parent dirs)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_TOML, encoding="utf-8")
