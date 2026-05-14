# DALY UART/RS485 Native Safe-Read

## Status

active safe-read / hardware unverified in repository evidence / raw-only decode

## Profile

- id: `daly_uart_485`
- enabled_by_default: `true`
- transport: `uart/rs485`
- serial: `9600 8N1`
- risk: `safe_read`

## Read-Only Commands

The active profile uses read-only command ids `0x90..0x98`.

## Limits

- Decode remains conservative raw-only.
- No write/control/config/factory/update commands.
- No MOS control.
- No calibration/reset operations.
