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
```

Expected output includes only:

```text
pylon_lv_rs485
jk_pylon_lv_emulation
```

The repository may contain inactive protocol candidate files for future work, but only profiles returned by `get_all_profiles()` are active in scan mode.

---

## Installation

Recommended: use a virtual environment.

### Windows CMD

```bat
cd C:\RS485forBMS_MVP\bms_probe
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

### Linux / macOS

```bash
cd ./bms_probe
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

---

## Run tests

```bash
python -m pytest -q
```

Expected current result:

```text
16 passed
```

---

## CLI usage

Show help:

```bash
bms-probe --help
```

List serial ports:

```bash
bms-probe --list-ports
```

List active profiles:

```bash
bms-probe --list-profiles
```

Passive listen, read-only, no TX:

```bash
bms-probe --passive --port COM3 --baud 9600 --seconds 10
```

Active safe scan:

```bash
bms-probe --scan --port COM3
```

Scan selected MVP profiles:

```bash
bms-probe --scan --port COM3 --profiles pylon_lv_rs485,jk_pylon_lv_emulation
```

Allow unverified read probes:

```bash
bms-probe --scan --port COM3 --include-unverified
```

For the current MVP, unverified profiles are not active in the default registry.

---

## JK BMS / Pylon LV bench checklist

Known working practical target from project notes:

```text
BMS: JK-B2A8S20PHC / JK-B2A8S20P-like revision
Protocol setting: 014 - PYLON_low_voltage_Protocol
Device address: 1
Serial: 9600 8N1
Interface: RS485
```

Wiring from the known bench case:

```text
USB-RS485 A -> JK yellow
USB-RS485 B -> JK white
GND         -> not used in the short bench test
```

Important:

- Close official JK-BMS-MONITOR before opening the COM port.
- Do not assume GND is never needed. The known test was a short bench cable.
- If there is no response, check A/B polarity, connector selection, BMS protocol setting, device address, power state, and COM-port ownership.

Expected Pylon LV read-only probes:

```text
~201246610000FDAA\r
~201246620000FDA9\r
~201246630000FDA8\r
```

Expected response prefix:

```text
~200246
```

---

## Reports

The scanner can save:

- JSON report
- TXT report
- RAW log

Default project folders:

```text
reports/
logs/
```

Runtime logs and generated reports should not normally be committed to git.

---

## Development notes

Project layout:

```text
bms_probe/
  PROJECT_BRIEF.md
  SAFETY.md
  README.md
  pyproject.toml
  requirements.txt
  main_cli.py
  app_gui.py

  core/
    models.py
    scanner.py
    scorer.py
    report.py
    safety.py

  protocols/
    base.py
    pylon_lv_rs485.py
    jk_pylon_lv.py

  transport/
    serial_transport.py
    fake_serial_transport.py
    port_list.py
    can_transport.py

  tests/
```

Run local checks before pushing:

```bash
python -m pytest -q
bms-probe --help
bms-probe --list-profiles
```

---

## Known limitations

Current MVP limitations:

1. Hardware validation was not performed in the recovered repository snapshot.
2. Pylon LV checksum verification is not yet production-grade.
3. GUI is minimal and not yet a full diagnostic workstation.
4. CAN transport is only a stub.
5. Non-MVP protocol files may exist as inactive candidates, but they are not active scan profiles.
6. The tool should not be used as a BMS configurator.

---

## License

Not defined yet.
