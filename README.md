# rs485-bms-probe

Read-only RS485 BMS protocol probe tool.
It is designed for safe protocol identification and bounded read-only validation.

> [!WARNING]
> This is a research tool for controlled read-only BMS protocol probing.
> Default profiles are read-only. Experimental probes require explicit opt-in
> and are excluded from default scans.
> Do not use this project for write/config/factory/update commands.

## What This Is

- CLI tool for controlled BMS protocol probing.
- Supports source-confirmed safe-read profiles and explicitly gated experimental reads.
- Saves JSON transaction logs for each single-probe/manual transaction.
- Includes tests for validators, safety gates, scan behavior, and selected hardware captures.

## What This Is Not

- Not a BMS flasher.
- Not a brute-force scanner.
- Not a write/config tool.
- Not a complete decoder.
- Not certified for production use.
- Not safe for arbitrary unknown devices without protocol review.

## Safety Model

- Safe-read profiles only by default.
- Write/control/factory/update commands are forbidden.
- Experimental probes require explicit opt-in with `--include-unverified`.
- Experimental probes do not participate in `--scan`.
- No guessed frames are active by default.
- JSON transaction logs are the source of truth for hardware observations.

See [docs/SAFETY.md](docs/SAFETY.md).

## Supported Profile Matrix

| Profile id | Protocol/menu | Default enabled | Status | Hardware evidence | Decode level | Notes |
|---|---|---:|---|---|---|---|
| `pylon_lv_rs485` | Pylontech / Pylon LV RS485 ASCII | yes | active safe-read | hardware sample fixtures | minimal Pylon decode | Not a write/config profile. |
| `jk_pylon_lv_emulation` | JK BMS Pylon LV emulation / menu 014 | yes | active safe-read | Pylon-compatible captures | Pylon-compatible decode | Separate from native JK Modbus. |
| `jbd_xiaoxiang_uart_rs485` | JBD/Xiaoxiang UART-RS485 | yes | active safe-read | unit/fake-transport coverage | raw-only | Hardware capture not claimed here. |
| `daly_uart_485` | DALY UART/RS485 native | yes | active safe-read | unit/fake-transport coverage | raw-only | Read-only commands `0x90..0x98`. |
| `jk_rs485_modbus` | `013 (9600) JK BMS RS485 Modbus V1.0` | yes | active safe-read, hardware-confirmed | single register and bounded cell blocks | confirmed cell-voltage decode only | No FC05/FC06/FC0F/FC10. |
| `pace_rs485_modbus_v1_3` | `004 PACE_RS485_Modbus_V1.3` | yes | active safe-read, basic block hardware-confirmed | pack/basic blocks confirmed; large block exception | basic decode; cell semantics untrusted | Full map not confirmed. |
| `growatt_bms_rs485_1xsxxp` | `006 Growatt_BMS_RS485_Protocol_1x...` | yes | active safe-read, status block hardware-confirmed | SOC/status/cell frame captures | status decode; cell semantics suspicious | Do not use inverter Modbus map as BMS map. |
| `voltronic_inverter_bms_485` | `007 Voltronic_Inverter_and_BMS_485-...` | yes | active safe-read, source-custom single-probe confirmed | cell-count capture | source-custom decode | Not standard Modbus response shape. |
| `wow_rs485_modbus_v1_3` | `009 WOW_RS485_Modbus_V1.3` | no | inactive research with experimental reads | experimental observations only | candidate-only | Not source-confirmed; not active safe-read. |

More detail: [docs/SUPPORT_MATRIX.md](docs/SUPPORT_MATRIX.md).

## Install

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Development tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Basic Commands

```powershell
.\.venv\Scripts\bms-probe.exe --list-profiles
.\.venv\Scripts\bms-probe.exe --list-profiles --include-unverified
.\.venv\Scripts\bms-probe.exe --list-ports
.\.venv\Scripts\bms-probe.exe --doctor --port COMx --baud 9600 --parity N --stopbits 1
```

## Single Probe Example

JK RS485 Modbus confirmed single-register read:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile jk_rs485_modbus --probe read_cell_voltage_0_addr1 --port COMx --baud 9600 --parity N --stopbits 1
```

WOW remains experimental-only:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile wow_rs485_modbus_v1_3 --probe experimental_read_basic_block_0x0000_0x0002_addr1 --port COMx --baud 9600 --parity N --stopbits 1 --include-unverified
```

Replace `COMx` with the selected local serial port before running a hardware
probe. Do not run experimental probes without reviewing the protocol note first.

## Logs

- JSON logs are written to `logs/`.
- `logs/` is gitignored.
- Sanitized evidence snippets may be placed in `docs/evidence/`.
- Raw logs should not be committed.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall .
git diff --check
```

## Project Status

MVP / research tool / read-only. It is useful for controlled protocol
validation, but it does not implement complete protocol maps and is not
certified for production use.

## License

MIT License. See [LICENSE](LICENSE).
