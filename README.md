# portwatch

> Small daemon that monitors local port usage and alerts on unexpected bindings.

---

## Installation

```bash
pip install portwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/portwatch.git && cd portwatch && pip install .
```

---

## Usage

Start the daemon with default settings:

```bash
portwatch start
```

Specify a config file to define allowed ports and alert behavior:

```bash
portwatch start --config /etc/portwatch/config.yaml
```

Example `config.yaml`:

```yaml
allowed_ports:
  - 22
  - 80
  - 443
alert:
  method: log
  log_path: /var/log/portwatch.log
interval: 10  # seconds between scans
```

When an unexpected binding is detected, portwatch logs an alert:

```
[ALERT] Unexpected binding detected: 0.0.0.0:8888 (PID 4521 - python3)
```

Stop the running daemon:

```bash
portwatch stop
```

---

## Options

| Flag | Description |
|------|-------------|
| `--config` | Path to configuration file |
| `--interval` | Scan interval in seconds (default: 10) |
| `--verbose` | Enable verbose logging |

---

## License

MIT © 2024 youruser