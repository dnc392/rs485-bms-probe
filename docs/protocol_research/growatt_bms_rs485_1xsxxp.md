# Growatt BMS RS485 1xSxxP ESS

## Status

active safe-read / hardware-confirmed status block / cell-voltage Modbus
frames confirmed but semantic decode suspicious

This profile is for BMS menu:

`006 Growatt_BMS_RS485_Protocol_1x...`

The active scope is one source-derived FC03 read-only request. It is not a wide
scan and does not imply support for the full Growatt BMS register map.

The status block decode is hardware-confirmed for SOC, pack voltage, current,
and temperature. The cell-voltage block Modbus frames are hardware-confirmed,
but their semantic mapping is not trusted yet because the candidate cell sum
does not match the confirmed pack voltage.

## Source

- `Growatt_BMS_RS485_Protocol_1xSxxP_ESS_Rev2.01 / V2.02`.
- Public PDF:
  `https://www.amosplanet.org/wp-content/uploads/2022/04/Growatt_BMS_RS485_protocal_1xSxxP_ESS_V2.02-1.pdf`
- Protocol class: Modbus RTU.
- Serial: 9600 8N1.
- CRC: Modbus RTU CRC16, CRC low byte then high byte.
- Read holding registers: FC03.
- Slave address `0x01`: box report standalone / parallel battery address.
- Register `0x0015`: SOC, read-only status query field, percent.
- Registers `0x0013..0x0018`: status, error, SOC, total voltage, current,
  temperature.
- Registers `0x0071..0x0080`: cell 1..16 voltage, unit 1 mV.

## Active source-derived probe

- Probe id: `read_soc_addr1`
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0015`
- Quantity: `1`
- Register name: `soc`
- Raw type: `UINT16`
- Unit: `%`
- Risk: `safe_read`
- Primary: true
- Source confirmed: true
- Hardware confirmed: true
- TX: `01 03 00 15 00 01 95 CE`
- Expected response shape: `01 03 02 <2 data bytes> <crc_lo> <crc_hi>`

## Active source-derived bounded block probes

These probes are still bounded `safe_read` FC03 requests. They are not a wide
map scan and do not use the Growatt inverter Modbus map.

### read_status_block_0x0013_0x0018_addr1

- Source registers: `0x0013..0x0018`
- Quantity: `6`
- Expected byte count: `12`
- Source fields:
  - `0x0013`: status bits
  - `0x0014`: error code
  - `0x0015`: SOC, percent
  - `0x0016`: voltage, unit 10 mV
  - `0x0017`: current, unit 10 mA
  - `0x0018`: temperature, unit deg C
- Risk: `safe_read`
- Source confirmed: true
- Hardware confirmed: true
- TX: `01 03 00 13 00 06 34 0D`
- Expected response shape: `01 03 0C <12 data bytes> <crc_lo> <crc_hi>`

### read_cell_voltages_1_8_addr1

- Source registers: `0x0071..0x0078`
- Quantity: `8`
- Expected byte count: `16`
- Source fields: cell 1..8 voltage, unit 1 mV
- Risk: `safe_read`
- Source confirmed: true
- Modbus frame hardware confirmed: true
- Semantic decode confirmed: false
- TX: `01 03 00 71 00 08 14 17`
- Expected response shape: `01 03 10 <16 data bytes> <crc_lo> <crc_hi>`

### read_cell_voltages_1_16_addr1

- Source registers: `0x0071..0x0080`
- Quantity: `16`
- Expected byte count: `32`
- Source fields: cell 1..16 voltage, unit 1 mV
- Risk: `safe_read`
- Source confirmed: true
- Modbus frame hardware confirmed: true
- Semantic decode confirmed: false
- TX: `01 03 00 71 00 10 14 1D`
- Expected response shape: `01 03 20 <32 data bytes> <crc_lo> <crc_hi>`

## Known confusion

- Do not confuse with Growatt Inverter Modbus RTU Protocol. The inverter
  register map is not enough to define this BMS-side request by itself.
- Do not confuse with Growatt BMS CAN protocol.
- Do not confuse with Pylon/Growatt compatibility mode.
- Do not use generic candidate frames from `growatt_ess_rs485_candidate`.

## Forbidden actions

- No write/config/control/factory/update commands.
- No FC05, FC06, FC0F, or FC10 probes.
- No wide reads before single-probe hardware confirmation.
- No full parser before hardware captures.

## Hardware test plan

1. Select BMS menu protocol:
   `006 Growatt_BMS_RS485_Protocol_1x...`
2. Use COM3 with 9600 8N1.
3. Send only `read_soc_addr1`.
4. Expected successful Modbus response shape:
   `<slave> <function> <byte_count> <data...> <crc_lo> <crc_hi>`
5. Save and inspect the JSON transaction log.
6. Promote only after:
   - CRC OK
   - slave OK
   - function OK
   - byte count OK
   - not echo
   - response not exception

## Hardware confirmation

- Date: 2026-05-14
- BMS menu protocol: `006 Growatt_BMS_RS485_Protocol_1x...`
- COM port: `COM3`
- Serial: `9600 8N1`
- Probe: `read_soc_addr1`
- TX: `01 03 00 15 00 01 95 CE`
- RX: `01 03 02 00 42 38 75`
- CRC: OK
- Slave ID: OK
- Function code: OK
- Byte count: OK
- Not echo: OK
- Register `0x0015` raw: `66`
- Decoded SOC: `66 %`
- Transaction log:
  `logs/single_probe_growatt_bms_rs485_1xsxxp_read_soc_addr1_20260514T055540Z.json`
- Status: hardware-confirmed single read-only probe

## Decoder confirmation

- Date: 2026-05-14
- Probe: `read_soc_addr1`
- TX: `01 03 00 15 00 01 95 CE`
- RX: `01 03 02 00 42 38 75`
- Transaction log:
  `logs/single_probe_growatt_bms_rs485_1xsxxp_read_soc_addr1_20260514T061543Z.json`
- JSON decoded status: `hardware_confirmed_single_register`
- JSON decoded register `0x0015` raw: `66`
- JSON decoded SOC raw: `66`
- JSON decoded SOC percent: `66`

## Bounded block hardware confirmation

### Status block

- Date: 2026-05-14
- Probe: `read_status_block_0x0013_0x0018_addr1`
- TX: `01 03 00 13 00 06 34 0D`
- RX: `01 03 0C 04 69 00 00 00 42 0A 47 00 00 00 14 64 8C`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - decoded_status_block_ok
- JSON decoded:
  - decode_status: `source_confirmed_status_block`
  - status_raw: `1129`
  - error_raw: `0`
  - soc_percent: `66`
  - pack_voltage_v: `26.31`
  - current_a: `0.0`
  - temperature_c: `20`
- Transaction log:
  `logs/single_probe_growatt_bms_rs485_1xsxxp_read_status_block_0x0013_0x0018_addr1_20260514T062546Z.json`
- Status: hardware_confirmed

### Cell voltage block 1..8

- Date: 2026-05-14
- Probe: `read_cell_voltages_1_8_addr1`
- TX: `01 03 00 71 00 08 14 17`
- RX: `01 03 10 0C D9 0C D9 0C DA 0C DA 0C D9 0C DA 0C DA 00 00 5F 2F`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - cell_voltage_frame_valid_semantics_suspicious (current decoder classification)
- Current decoder classification for captured RX:
  - decode_status: `frame_valid_semantics_suspicious`
  - semantic_decode_confirmed: `false`
  - raw_candidate_cell_voltages_mv: `[3289, 3289, 3290, 3290, 3289, 3290, 3290, 0]`
  - raw_candidate_active_cell_count: `7`
  - raw_candidate_cell_sum_v: `23.027`
  - reference_pack_voltage_v: `26.31`
  - expected_cell_count_from_pack_voltage: `8`
  - warnings:
    - `cell_sum_mismatch_pack_voltage`
    - `active_cell_count_mismatch_pack_voltage`
- Transaction log:
  `logs/single_probe_growatt_bms_rs485_1xsxxp_read_cell_voltages_1_8_addr1_20260514T062602Z.json`
- Status: Modbus frame hardware_confirmed, semantic decode suspicious/untrusted

### Cell voltage block 1..16

- Date: 2026-05-14
- Probe: `read_cell_voltages_1_16_addr1`
- TX: `01 03 00 71 00 10 14 1D`
- RX: `01 03 20 0C D9 0C DA 0C DA 0C D9 0C D9 0C DA 0C DA 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 E9 96`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - cell_voltage_frame_valid_semantics_suspicious (current decoder classification)
- Current decoder classification for captured RX:
  - decode_status: `frame_valid_semantics_suspicious`
  - semantic_decode_confirmed: `false`
  - raw_candidate_cell_voltages_mv: `[3289, 3290, 3290, 3289, 3289, 3290, 3290, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
  - raw_candidate_active_cell_count: `7`
  - raw_candidate_cell_sum_v: `23.027`
  - reference_pack_voltage_v: `26.31`
  - expected_cell_count_from_pack_voltage: `8`
  - warnings:
    - `cell_sum_mismatch_pack_voltage`
    - `active_cell_count_mismatch_pack_voltage`
- Transaction log:
  `logs/single_probe_growatt_bms_rs485_1xsxxp_read_cell_voltages_1_16_addr1_20260514T062620Z.json`
- Status: Modbus frame hardware_confirmed, semantic decode suspicious/untrusted

## Cell Voltage Semantic Risk

- Confirmed status-block pack voltage is `26.31 V`.
- The current cell-voltage candidates contain only 7 nonzero values around
  `3289..3290 mV`.
- Sum of 7 candidate cells is about `23.027 V`, not `26.31 V`.
- This suggests a possible off-by-one register-map mismatch, profile-mode
  mismatch, or another interpretation gap.
- Do not use Growatt cell-voltage blocks as confirmed cell-level diagnostics
  until cross-checked against another trusted source or capture.
- Do not add guessed alternative cell registers without source confirmation.

## Limits

- This confirms only slave `1`, FC03, register `0x0015`, status block
  `0x0013..0x0018`, and cell-voltage blocks `0x0071..0x0078` and
  `0x0071..0x0080`.
- It does not confirm the full Growatt BMS register map.
- Do not add wide reads before separate source review and hardware validation.
- No write/control/config/factory/update commands are allowed.
