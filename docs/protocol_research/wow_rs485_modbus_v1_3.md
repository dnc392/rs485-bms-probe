# WOW RS485 Modbus V1.3

## Status

inactive_research_with_experimental_read / hardware unverified / source-confirmed safe-read request still missing

## BMS menu

009 WOW_RS485_Modbus_V1.3

## Current decision

No active safe-read probe is defined. The profile remains disabled by default and must not be used by `--scan`.

Three experimental read-only FC03 probes exist for controlled, explicit hardware observations only. They are not source-confirmed and can be run only with explicit unverified permission.

Profile metadata:

- id: `wow_rs485_modbus_v1_3`
- enabled_by_default: `false`
- status: `inactive_research_with_experimental_read`
- hardware_status: `unverified_hardware`
- source_status: `missing_confirmed_safe_read_request`
- active safe-read probes: `[]`
- experimental probes: `3`

External app-log sanity evidence in
`docs/evidence/app_detail_log_sanity_20260514.md` confirms the tested pack was
around `26.30 V`, with max/min cells around `3.288/3.287 V` and derived SOC
around `65.5 %`. This supports the experimental WOW basic-block candidate
values for pack voltage and SOC, but it does not make WOW source-confirmed.

## Source discovery

Local project search:

- `docs/`
- `docs/protocol_research/`
- `protocols/`
- `tests/`
- local logs and source notes

Result: no local WOW protocol PDF/DOCX and no confirmed read-only request frame.

Public compatibility references found:

- `phinix-org/Multiple-JK-BMS-by-Modbus-RS485` lists menu option `009 - WOW_RS485_Modbus_V1.3`.
- XJ BMS product pages list `WOW RS485 Modbus V1.3` in protocol adaptation lists.
- Several battery manuals/product pages list `036-WOW RS485 Modbus V1.3-2017.06.27`.

These are compatibility lists only. They do not provide:

- exact serial settings;
- frame format;
- checksum/CRC scope;
- request direction;
- read command/function;
- expected response shape;
- register map;
- exact safe-read request bytes.

## Confusion checks

- Do not reuse PACE RS485 Modbus V1.3 register map for WOW without a source proving equivalence.
- Do not reuse Growatt, JK, Pylon, or Voltronic maps.
- Do not confuse WOW with `SRNE_LOW_Voltage_Protocol_RS485_V3.3`. Some public compatibility lists place WOW near SRNE or under SRNE inverter compatibility, but this does not prove the wire protocol is the same.
- The Voltronic precedent shows that a protocol name containing `Modbus` is not enough to assume standard Modbus RTU response shape.

## Missing evidence

Need a primary or high-confidence source for `WOW_RS485_Modbus_V1.3` containing:

- serial settings;
- master/slave direction;
- frame format;
- checksum/CRC;
- at least one read-only request frame;
- expected response shape;
- register meaning/scale for the selected first probe, if available.

## Safety policy

- No `--scan`.
- No default activation.
- No manual `--tx-hex`.
- No wide reads.
- No FC05, FC06, FC0F, FC10.
- No write/control/config/factory/update commands.
- The experimental probe is `experimental_unverified_read`, not `safe_read`.
- The experimental probe requires explicit unverified permission.
- This does not make WOW source-confirmed.
- This does not make WOW active by default.

## Experimental read-only test

Probe:

- id: `experimental_read_reg_0x0001_qty1_addr1`
- risk: `experimental_unverified_read`
- source_confirmed: `false`
- hardware_confirmed: `false`
- enabled_by_default: `false`
- requires_explicit_unverified_flag: `true`
- slave_id: `1`
- function_code: `0x03`
- start_register: `0x0001`
- quantity: `1`
- TX: `01 03 00 01 00 01 D5 CA`

Assumption for this controlled test only:

- standard Modbus RTU FC03 response shape: `01 03 02 <2 data bytes> <crc_lo> <crc_hi>`
- CRC16 Modbus
- serial: `9600 8N1`

Classification policy:

- valid standard Modbus response: `experimental_modbus_response_valid`
- Modbus exception: `experimental_modbus_exception`
- no response: `experimental_no_response`
- invalid CRC: `experimental_invalid_crc`
- request-shaped/custom response: `experimental_unexpected_shape`

This observation does not prove the WOW register map. It also does not authorize wide reads or any write/control commands.

Hardware result:

- status: `experimental_unverified_read_observed`
- date: `2026-05-14`
- BMS menu: `009 WOW_RS485_Modbus_V1.3`
- serial: `9600 8N1`
- command: `bms-probe --single-probe --profile wow_rs485_modbus_v1_3 --probe experimental_read_reg_0x0001_qty1_addr1 --port COM3 --baud 9600 --parity N --stopbits 1 --timeout-ms 2000 --include-unverified`
- log path: `logs/single_probe_wow_rs485_modbus_v1_3_experimental_read_reg_0x0001_qty1_addr1_20260514T084343Z.json`
- TX: `01 03 00 01 00 01 D5 CA`
- RX: `01 03 02 0A 46 3F 16`
- RX length: `7`
- frames_found: `1`
- validation:
  - `not_echo`
  - `crc_ok`
  - `slave_id_ok`
  - `function_code_ok`
  - `byte_count_ok`
- classification: `experimental_modbus_response_valid`
- decoded status: `raw_only`
- candidate_register_0x0001_raw: `2630`

This does not make WOW source-confirmed. This does not make WOW active by default. The value is an experimental candidate only; no WOW register semantics are confirmed.

## Experimental basic block observation

Probe:

- id: `experimental_read_basic_block_0x0000_0x0002_addr1`
- risk: `experimental_unverified_read`
- source_confirmed: `false`
- hardware_confirmed: `false`
- enabled_by_default: `false`
- requires_explicit_unverified_flag: `true`
- slave_id: `1`
- function_code: `0x03`
- start_register: `0x0000`
- quantity: `3`
- expected response shape: `01 03 06 <6 data bytes> <crc_lo> <crc_hi>`
- TX: `01 03 00 00 00 03 05 CB`

Purpose:

- bounded experimental check of registers `0x0000..0x0002`;
- hypothesis only: `0x0000` candidate current, `0x0001` candidate pack voltage, `0x0002` candidate SOC;
- all decoded values must remain `candidate_*`;
- `semantic_confirmed` must remain `false`.

Hardware result:

- status: `experimental_unverified_read_observed`
- date: `2026-05-14`
- BMS menu: `009 WOW_RS485_Modbus_V1.3`
- serial: `9600 8N1`
- command: `bms-probe --single-probe --profile wow_rs485_modbus_v1_3 --probe experimental_read_basic_block_0x0000_0x0002_addr1 --port COM3 --baud 9600 --parity N --stopbits 1 --timeout-ms 2000 --include-unverified`
- log path: `logs/single_probe_wow_rs485_modbus_v1_3_experimental_read_basic_block_0x0000_0x0002_addr1_20260514T090420Z.json`
- TX: `01 03 00 00 00 03 05 CB`
- RX: `01 03 06 00 00 0A 46 00 42 43 49`
- RX length: `11`
- frames_found: `1`
- validation:
  - `not_echo`
  - `crc_ok`
  - `slave_id_ok`
  - `function_code_ok`
  - `byte_count_ok`
- classification: `experimental_modbus_response_valid`
- decoded status: `experimental_candidate_decode`
- semantic_confirmed: `false`
- candidate_register_0x0000_raw: `0`
- candidate_register_0x0001_raw: `2630`
- candidate_register_0x0002_raw: `66`
- candidate_current_a: `0.0`
- candidate_pack_voltage_v: `26.3`
- candidate_soc_percent: `66`

This does not make WOW source-confirmed. This does not make WOW active by default. The block is bounded but still experimental and does not authorize wide reads.

## Experimental cell block observation

Probe:

- id: `experimental_read_cell_voltages_0_7_addr1`
- risk: `experimental_unverified_read`
- source_confirmed: `false`
- hardware_confirmed: `false`
- enabled_by_default: `false`
- requires_explicit_unverified_flag: `true`
- slave_id: `1`
- function_code: `0x03`
- start_register: `0x0015`
- quantity: `8`
- expected response shape: `01 03 10 <16 data bytes> <crc_lo> <crc_hi>`
- TX: `01 03 00 15 00 08 55 C8`

Purpose:

- bounded experimental check of registers `0x0015..0x001C`;
- hypothesis only: candidate cell voltages;
- all decoded values must remain `candidate_*`;
- `semantic_confirmed` must remain `false`;
- compare candidate cell sum against latest candidate pack voltage `26.30 V`.

Hardware result:

- status: `experimental_unverified_read_observed`
- date: `2026-05-14`
- BMS menu: `009 WOW_RS485_Modbus_V1.3`
- serial: `9600 8N1`
- command: `bms-probe --single-probe --profile wow_rs485_modbus_v1_3 --probe experimental_read_cell_voltages_0_7_addr1 --port COM3 --baud 9600 --parity N --stopbits 1 --timeout-ms 2000 --include-unverified`
- log path: `logs/single_probe_wow_rs485_modbus_v1_3_experimental_read_cell_voltages_0_7_addr1_20260514T111352Z.json`
- TX: `01 03 00 15 00 08 55 C8`
- RX: `01 03 10 0C D9 0C D7 00 00 00 00 00 00 00 00 00 00 00 00 C0 DC`
- RX length: `21`
- frames_found: `1`
- validation:
  - `not_echo`
  - `crc_ok`
  - `slave_id_ok`
  - `function_code_ok`
  - `byte_count_ok`
- classification: `experimental_modbus_response_valid`
- frame_valid: `true`
- decoded status: `experimental_candidate_decode`
- semantic_confirmed: `false`
- semantic_status: `frame_valid_semantics_failed`
- failure_reason: `candidate_cell_sum_mismatch_pack_voltage`
- candidate_cell_voltages_mv: `[3289, 3287, 0, 0, 0, 0, 0, 0]`
- candidate_active_cell_voltages_mv: `[3289, 3287]`
- candidate_active_cell_count: `2`
- candidate_min_cell_mv: `3287`
- candidate_max_cell_mv: `3289`
- candidate_delta_cell_mv: `2`
- candidate_cell_sum_v: `6.576`
- candidate_pack_voltage_reference_v: `26.3`
- candidate sum-vs-pack-voltage check: `candidate_cell_sum_mismatch_pack_voltage`
- decision: frame valid, cell-voltage semantics failed
- external sanity: app log confirms 8S-like pack behavior around `26.30 V`;
  the candidate active cell sum `6.576 V` is inconsistent with that pack
  voltage.
- next action: do not extend to qty=16 without a source

This does not make WOW source-confirmed. This does not make WOW active by default. The cell-voltage interpretation is candidate-only until a source or independent cross-check confirms the register map.
