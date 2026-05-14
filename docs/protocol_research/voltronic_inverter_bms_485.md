# Voltronic Inverter and BMS 485

## Status

active safe-read / source-custom single-probe hardware-confirmed

## BMS menu

007 Voltronic_Inverter_and_BMS_485-...

## Source

Primary source used:

- Voltronic Inverter and BMS 485 communication protocol 20201202.docx
- Public mirror: https://github.com/ardupic/voltronic-inverter-communication-protocols/blob/main/Voltronic%20Inverter%20and%20BMS%20485%20communication%20protocol%2020201202.docx

Extracted source facts:

- Serial: 9600 8N1.
- Query format: slave ID, command type, start address of data, data length, CRC.
- CRC covers all bytes before the CRC field and is sent low byte first, high byte second.
- Command type `0x03` is read data.
- Command type `0x10` is write data and is forbidden in this project.
- Normal response shape: slave ID, command type, two-byte data length, data info, CRC.
- This is Modbus-like RTU framing with CRC16, but the response is not standard Modbus RTU `addr fc byte_count data crc`.
- Source normal response uses `Data Length` as two bytes and `Data information` as `Data length * 2` bytes.
- Abnormal response shape: slave ID, command type + 128, error code, CRC.
- Common BMS node ID for RS485 is `0x01`; every BMS can respond to ID `0x01`.
- Register `0x0010`: Number of cell, unit pcs.
- Direction in source: device/UPS/inverter queries BMS address; BMS returns data. The source does not show BMS-initiated request frames for this command list.

## Active source-derived probe

Probe: `read_cell_count_addr1`

- Risk: `safe_read`
- Primary: `true`
- Source confirmed: `true`
- Hardware confirmed: `true`
- Standard Modbus confirmed: `false`
- Source custom response confirmed: `true`
- Slave ID: `0x01`
- Function code: `0x03`
- Start register: `0x0010`
- Quantity: `1`
- TX: `01 03 00 10 00 01 85 CF`
- Expected source response shape: `01 03 00 01 <2 data bytes> <crc_lo> <crc_hi>`

This first probe is intentionally bounded to one source-derived read-only register.

## Known confusion

- Do not confuse with the generic Voltronic inverter serial protocol used for PC monitoring.
- Do not confuse with Pylon low voltage RS485 ASCII.
- Do not confuse with Growatt, PACE, or JK Modbus register maps.
- This profile targets inverter/BMS 485 communication where the inverter is master and BMS responds.

## Safety limits

- No scan is required for first hardware validation.
- No register brute force.
- No guessed frames.
- No FC05, FC06, FC0F, or FC10 probes.
- No write, control, config, factory, firmware update, reset, unlock, or calibration commands.
- No wide reads until a single source-derived read is hardware-confirmed.

## Hardware test plan

1. Select BMS menu protocol: `007 Voltronic_Inverter_and_BMS_485-...`.
2. Use the confirmed RS485 adapter/port if applicable.
3. Start with 9600 8N1.
4. Send only `read_cell_count_addr1`.
5. Save the JSON transaction log.
6. Promote only after:
   - RX is present.
   - CRC OK.
   - Slave ID OK.
   - Function code OK.
   - Byte count OK.
   - Response is not echo.
   - Response is not abnormal/error response.

## Hardware observation: request-shaped RX

Date: 2026-05-14

- BMS menu: `007 Voltronic_Inverter_and_BMS_485-...`
- Serial: 9600 8N1
- COM port: COM3
- Probe: `read_cell_count_addr1`
- TX: `01 03 00 10 00 01 85 CF`
- RX: `01 03 00 01 00 08 15 CC`
- Log: `logs/single_probe_voltronic_inverter_bms_485_read_cell_count_addr1_20260514T072823Z.json`
- RX length: 8
- Frames found: 1
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - voltronic_custom_data_length_ok
  - source_response_length_ok
  - standard_modbus_request_shape_ambiguous
- Parse status: decoded
- Classification: `source_custom_response_confirmed`
- Decode status: `hardware_confirmed_single_register_source_custom`
- Decoded cell_count: `8`
- Status decision: hardware-confirmed single probe using Voltronic source-defined custom response shape

Initial standard-Modbus validation treated this as byte-count mismatch because byte 2 is `0x00`, not a one-byte byte count. Source review shows that Voltronic normal responses use a two-byte `Data Length`, so `00 01` is the source data length and `00 08` is the two-byte data information.

The same byte sequence is standard Modbus request-shaped if interpreted as `addr fc start_hi start_lo qty_hi qty_lo crc`: start `0x0001`, quantity `0x0008`. The exact RX `01 03 00 01 00 08 15 CC` was not found verbatim in the source examples, but it matches the source-defined normal response shape for a one-word read.

This confirms only `read_cell_count_addr1`: slave `0x01`, command `0x03`, register `0x0010`, quantity `1`, returned raw value `8`.

This confirms Voltronic source-defined response shape, not standard Modbus RTU response shape. Keep warnings:

- `standard_modbus_request_shape_ambiguous`
- `not_standard_modbus_response`

Do not mark the full Voltronic protocol confirmed. Do not add wide reads until each new source-derived request is reviewed and tested separately.
