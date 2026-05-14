# Pylon LV RS485 ASCII

## Status

active safe-read / bounded Pylon LV ASCII requests / fixture-backed decode tests

## Profile

- id: `pylon_lv_rs485`
- enabled_by_default: `true`
- transport: `rs485`
- risk: `safe_read`

## Scope

This profile sends read-only Pylon LV ASCII commands and validates ASCII frame shape/checksum behavior.

## Limits

- No write/control/config/factory commands.
- Pylon behavior must not be changed to support unrelated protocols.
- Hardware coverage is represented by tests and sample captures in this repository; full Pylon protocol coverage is not claimed.
