# PACE RS485 Modbus V1.3

## Status

active safe-read / hardware-confirmed basic block / cell voltage frames confirmed but semantic decode untrusted

The active probes are limited to source-confirmed FC03 reads. Confirmed reads
cover pack voltage and the basic current/voltage/SOC block. PACE cell-voltage
requests return valid Modbus frames, but the register interpretation is not
trusted yet. This does not imply support for the full PACE register map.

PACE basic current/voltage/SOC works on the tested BMS. Do not use PACE mode
for confirmed cell-level diagnostics until the cell-voltage mapping is
cross-checked against JK native Modbus or the BMS app.

External app-log sanity evidence in
`docs/evidence/app_detail_log_sanity_20260514.md` confirms the pack was around
`26.30 V` with max/min cells around `3.288/3.287 V`, consistent with 8S
LiFePO4. That supports the PACE basic pack voltage/SOC decode, but reinforces
that PACE `0x0015..` cell-voltage semantics remain untrusted because the
returned active-cell sum does not match pack voltage.

## BMS menu

004 PACE_RS485_Modbus_V1.3

## Source

- `PACE BMS Modbus Protocol for RS485 V1.3 (2017-06-27)`.
- Serial: 9600 8N1.
- CRC: Modbus RTU CRC16.
- Read registers: FC03.
- Slave addresses: `0x01..0x10`.
- Register `0001`: Voltage of pack, R/UINT16, unit 10mV.

## Active source-derived probe

### read_pack_voltage_addr1

- Probe id: `read_pack_voltage_addr1`
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0001`
- Quantity: `1`
- Register name: `pack_voltage`
- Raw type: `UINT16`
- Unit: `10mV`
- Risk: `safe_read`
- Primary: true
- Source confirmed: true
- Hardware confirmed: true
- TX: `01 03 00 01 00 01 D5 CA`
- Expected response shape: `01 03 02 <2 data bytes> <crc_lo> <crc_hi>`

### read_core_block_0_48_addr1

- Probe id: `read_core_block_0_48_addr1`
- Description: Read PACE core read-only block registers `0x0000..0x0030`.
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0000`
- Quantity: `0x0031` / 49 registers
- Expected byte count: `0x62` / 98 data bytes
- Covered source-known registers:
  - `0x0000`: Current, INT16, unit 10mA
  - `0x0001`: Pack voltage, UINT16, unit 10mV
  - `0x0002`: SOC, conservative UINT16/raw percent
  - `0x0015..0x0030`: Cell voltages, UINT16, unit mV
- Registers `0x0003..0x0014`: raw only, no field names assigned here.
- Risk: `safe_read`
- Primary: false
- Source confirmed: true
- Hardware confirmed: false
- TX: `01 03 00 00 00 31 84 1E`
- Expected response shape: `01 03 62 <98 data bytes> <crc_lo> <crc_hi>`

### read_basic_block_0_2_addr1

- Probe id: `read_basic_block_0_2_addr1`
- Description: Read PACE basic block: current, pack voltage, SOC.
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0000`
- Quantity: `3`
- Expected byte count: `0x06` / 6 data bytes
- Registers:
  - `0x0000`: Current, INT16, unit 10mA
  - `0x0001`: Pack voltage, UINT16, unit 10mV
  - `0x0002`: SOC, conservative UINT16/raw percent
- Risk: `safe_read`
- Primary: false
- Source confirmed: true
- Hardware confirmed: true
- Semantic decode confirmed: true
- TX: `01 03 00 00 00 03 05 CB`
- Expected response shape: `01 03 06 <6 data bytes> <crc_lo> <crc_hi>`

### read_cell_voltages_0_7_addr1

- Probe id: `read_cell_voltages_0_7_addr1`
- Description: Read first 8 PACE cell voltage registers.
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0015`
- Quantity: `8`
- Expected byte count: `0x10` / 16 data bytes
- Registers: `0x0015..0x001C`, cell voltage 1..8, UINT16, unit mV
- Risk: `safe_read`
- Primary: false
- Source confirmed: true
- Hardware confirmed: true
- Modbus frame confirmed: true
- Semantic decode confirmed: false
- Decode status: `frame_valid_semantics_untrusted`
- Warning: Only first 2 values look like valid cell voltages; trailing zeros
  may be unused or mapping mismatch.
- TX: `01 03 00 15 00 08 55 C8`
- Expected response shape: `01 03 10 <16 data bytes> <crc_lo> <crc_hi>`

### read_cell_voltages_0_15_addr1

- Probe id: `read_cell_voltages_0_15_addr1`
- Description: Read first 16 PACE cell voltage registers.
- Slave id: `1`
- Function code: `0x03`
- Start register: `0x0015`
- Quantity: `16`
- Expected byte count: `0x20` / 32 data bytes
- Registers: `0x0015..0x0024`, cell voltage 1..16, UINT16, unit mV
- Risk: `safe_read`
- Primary: false
- Source confirmed: true
- Hardware confirmed: true
- Modbus frame confirmed: true
- Semantic decode confirmed: false
- Decode status: `frame_valid_semantics_untrusted`
- Warnings:
  - non_trailing_zero_cell_voltage
  - cell_voltage_out_of_expected_range
- TX: `01 03 00 15 00 10 55 C2`
- Expected response shape: `01 03 20 <32 data bytes> <crc_lo> <crc_hi>`

## Hardware confirmation

### Single register pack voltage

- Date: 2026-05-13
- BMS menu: `004 PACE_RS485_Modbus_V1.3`
- COM port: COM3
- Serial: 9600 8N1
- Probe id: `read_pack_voltage_addr1`
- TX: `01 03 00 01 00 01 D5 CA`
- RX: `01 03 02 0A 45 7F 17`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
- Response type: normal data response, not Modbus exception.
- Register `0x0001` raw: 2629
- Decoded pack voltage: 26.29 V
- Transaction log:
  `logs/single_probe_pace_rs485_modbus_v1_3_read_pack_voltage_addr1_20260513T202201Z.json`
- Status: hardware_confirmed_single_probe

### Bulk core block attempt

- Date: 2026-05-13
- BMS menu: `004 PACE_RS485_Modbus_V1.3`
- COM port: COM3
- Serial: 9600 8N1
- Probe id: `read_core_block_0_48_addr1`
- TX: `01 03 00 00 00 31 84 1E`
- RX: `01 83 02 C0 F1`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - modbus_exception_response
  - exception_code_02
- Response type: Modbus exception response, exception code `0x02`.
- Transaction log:
  `logs/single_probe_pace_rs485_modbus_v1_3_read_core_block_0_48_addr1_20260513T203845Z.json`
- Status: source_confirmed_but_hardware_exception.
- Decision: keep the probe non-primary and not hardware-confirmed; do not expand
  to larger windows from this result.

### Basic block current/voltage/SOC

- Date: 2026-05-13
- BMS menu: `004 PACE_RS485_Modbus_V1.3`
- COM port: COM3
- Serial: 9600 8N1
- Probe id: `read_basic_block_0_2_addr1`
- TX: `01 03 00 00 00 03 05 CB`
- RX: `01 03 06 00 00 0A 45 00 42 B3 49`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - decoded_basic_block_ok
- Decoded:
  - current_raw_signed: 0
  - current_a: 0.0
  - pack_voltage_raw: 2629
  - pack_voltage_v: 26.29
  - soc_percent_raw: 66
  - soc_percent: 66
- Transaction log:
  `logs/single_probe_pace_rs485_modbus_v1_3_read_basic_block_0_2_addr1_20260513T205204Z.json`
- Status: hardware_confirmed_basic_block.

### First 8 cell voltage registers

- Date: 2026-05-13
- BMS menu: `004 PACE_RS485_Modbus_V1.3`
- COM port: COM3
- Serial: 9600 8N1
- Probe id: `read_cell_voltages_0_7_addr1`
- TX: `01 03 00 15 00 08 55 C8`
- RX: `01 03 10 0C D8 0C D7 00 00 00 00 00 00 00 00 00 00 00 00 01 DC`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - cell_voltage_frame_valid_semantics_untrusted
- Decoded:
  - decode_status: `frame_valid_semantics_untrusted`
  - modbus_frame_confirmed: true
  - semantic_decode_confirmed: false
  - raw_candidate_cell_voltages_mv: `[3288, 3287, 0, 0, 0, 0, 0, 0]`
  - warning: Only first 2 values look like valid cell voltages; trailing zeros
    may be unused or mapping mismatch.
- Transaction log:
  `logs/single_probe_pace_rs485_modbus_v1_3_read_cell_voltages_0_7_addr1_20260513T205210Z.json`
- Status: Modbus frame hardware-confirmed, semantic cell-voltage decode
  untrusted.

### First 16 cell voltage registers

- Date: 2026-05-13
- BMS menu: `004 PACE_RS485_Modbus_V1.3`
- COM port: COM3
- Serial: 9600 8N1
- Probe id: `read_cell_voltages_0_15_addr1`
- TX: `01 03 00 15 00 10 55 C2`
- RX: `01 03 20 0C D7 0C D5 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 D2 00 D1 F8 30 F8 30 00 F1 00 D1 64 1A`
- Validation:
  - not_echo
  - crc_ok
  - slave_id_ok
  - function_code_ok
  - byte_count_ok
  - cell_voltage_frame_valid_semantics_untrusted
- Decoded:
  - decode_status: `frame_valid_semantics_untrusted`
  - modbus_frame_confirmed: true
  - semantic_decode_confirmed: false
  - raw_candidate_cell_voltages_mv: `[3287, 3285, 0, 0, 0, 0, 0, 0, 0, 0, 210, 209, 63536, 63536, 241, 209]`
  - decode_warnings:
    - non_trailing_zero_cell_voltage
    - cell_voltage_out_of_expected_range
- Transaction log:
  `logs/single_probe_pace_rs485_modbus_v1_3_read_cell_voltages_0_15_addr1_20260513T205218Z.json`
- Status: Modbus frame hardware-confirmed, semantic cell-voltage decode
  untrusted. Treat the tail after the zero run as not yet semantically trusted.

## Known constraints

- Do not confuse with Pylon low voltage RS485 ASCII.
- Do not confuse with PACE paceic ASCII protocol.
- Do not enable wide scans before single-probe hardware confirmation.
- Do not add write/config/control/factory commands.
- Do not add FC05, FC06, FC0F, or FC10 probes.
- Only FC03/FC04 read-only function codes are allowed by project policy.
- Decode is confirmed only for pack voltage and the basic current/voltage/SOC
  block.
- PACE cell-voltage register interpretation is not trusted yet.
- External app-log sanity evidence confirms 8S-like pack behavior around
  `26.30 V`; PACE `0x0015..` candidate cell blocks do not sum to that voltage.
- Bulk block decode is limited to source-known fields in `0x0000..0x0030`.
- The 49-register bulk read returned exception `0x02`; do not add larger read
  windows from that result.
- The 16-register cell block is frame-confirmed, but its tail includes
  non-trailing zeros and out-of-range cell voltage values.
- Do not use PACE mode for confirmed cell-level diagnostics until cross-checked
  against JK native Modbus or the BMS app.

## Hardware test plan

1. Select BMS menu protocol:
   `004 PACE_RS485_Modbus_V1.3`
2. Connect to the same confirmed RS485 adapter/port if applicable.
3. Start with 9600 8N1.
4. Send only one source-derived safe-read probe at a time.
5. Expected successful Modbus response shape:
   `<slave> <function> <byte_count> <data...> <crc_lo> <crc_hi>`
6. Save the single-probe transaction log.
7. Keep hardware_confirmed only while these checks remain true:
   - CRC OK
   - slave OK
   - function OK
   - byte count OK
   - not echo
   - response not exception

## Activation limits

- The profile is active only for source-confirmed FC03 read-only probes.
- Wide register windows remain blocked after the `0x0000..0x0030` exception.
- Write/control/config/factory/update commands remain forbidden.
- Do not add a full PACE parser from these bounded captures.
