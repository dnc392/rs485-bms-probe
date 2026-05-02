# BMS Protocol Probe Tool

Safe read-only MVP utility for probing BMS communication protocols over RS485/UART-style serial links.

The project is currently focused on a verified practical target:

- Pylontech / Pylon LV RS485 ASCII
- JK BMS Pylon LV emulation / Protocol 014

The tool is intended for **diagnostics and protocol identification**, not for BMS configuration.

---

## Current status

MVP stage.

Implemented:

- CLI entry point: `bms-probe`
- serial port listing
- passive listen mode
- active safe read-only probe mode
- protocol profile registry
- Pylon LV RS485 ASCII profile
- JK Pylon LV emulation profile
- safety policy / blocklist layer
- fake serial transport for tests
- JSON / TXT / RAW report helpers
- minimal tkinter GUI scaffold
- pytest test suite

Not implemented yet:

- real CAN support
- MOS control
- parameter writing
- address changing
- calibration
- reset / shutdown commands
- full Pylon checksum validation
- production-ready GUI
- hardware validation in this recovered repository snapshot

---

## Safety model

This tool is designed as a **read-only protocol probe**.

Autodetect / scan mode must not send:

- write register commands
- write multiple register commands
- MOS control commands
- charge/discharge MOS ON/OFF
- set address
- set protocol
- calibration
- clear alarm
- factory reset
- shutdown
- sleep commands

Probe risk levels:

| Risk level | Default behavior |
|---|---|
| `safe_read` | allowed |
| `no_tx` | allowed |
| `unverified_read` | blocked unless `--include-unverified` is set |
| `write_forbidden` | always blocked |

See also:

- `SAFETY.md`
- `PROJECT_BRIEF.md`

---

## Supported MVP profiles

Show active profiles:

```bash
bms-probe --list-profiles
