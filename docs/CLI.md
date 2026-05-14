# CLI Usage

Use the project virtual environment on Windows:

```powershell
.\.venv\Scripts\bms-probe.exe --help
```

## List Profiles

Default list:

```powershell
.\.venv\Scripts\bms-probe.exe --list-profiles
```

Research/experimental profiles:

```powershell
.\.venv\Scripts\bms-probe.exe --list-profiles --include-unverified
```

## Include Unverified

`--include-unverified` allows explicitly gated unverified probes to be selected for `--single-probe`.
It does not make experimental probes participate in `--scan`.

## Single Probe

Run one reviewed probe:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile jk_rs485_modbus --probe read_cell_voltage_0_addr1 --port COM3 --baud 9600 --parity N --stopbits 1
```

## Scan Safety Note

`--scan` uses active default profiles only unless profiles are selected explicitly.
Experimental probes are blocked from scan even when `--include-unverified` is present.

## Manual TX Warning

Manual mode bypasses profile validation:

```powershell
.\.venv\Scripts\bms-probe.exe --port COM3 --baud 9600 --parity N --stopbits 1 --tx-hex "..."
```

Use manual TX only for already reviewed read-only frames.

## Transaction Logs

Single-probe and manual TX modes write JSON transaction logs to `logs/`.
The JSON log is the source of truth for TX/RX, validation reasons, decoded values, and hardware status.

## Examples

JK RS485 Modbus:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile jk_rs485_modbus --probe read_cell_voltage_0_addr1 --port COM3 --baud 9600 --parity N --stopbits 1
```

PACE basic block:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile pace_rs485_modbus_v1_3 --probe read_basic_block_0_2_addr1 --port COM3 --baud 9600 --parity N --stopbits 1
```

Growatt status block:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile growatt_bms_rs485_1xsxxp --probe read_status_block_0x0013_0x0018_addr1 --port COM3 --baud 9600 --parity N --stopbits 1
```

Voltronic source-custom cell count:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile voltronic_inverter_bms_485 --probe read_cell_count_addr1 --port COM3 --baud 9600 --parity N --stopbits 1
```

WOW experimental only:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile wow_rs485_modbus_v1_3 --probe experimental_read_basic_block_0x0000_0x0002_addr1 --port COM3 --baud 9600 --parity N --stopbits 1 --include-unverified
```
