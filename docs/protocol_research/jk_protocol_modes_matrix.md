# JK BMS selectable protocol modes test matrix

Status: research-only documentation. This matrix does not define active probe
profiles and must not be used as a generic scan list.

## Safety rules

1. Each BMS menu mode must be tested only with protocol-specific confirmed
   read-only requests.
2. If no confirmed request exists, mark TX as `TBD` and do not test.
3. Do not test non-Pylon modes with Pylon requests.
4. Pylon request `~201246620000FDA9\r` is valid only for Pylon LV / JK Pylon
   emulation mode.
5. For Growatt mode, require a Growatt BMS RS485 Protocol 1xSxxP_ESS Rev2.xx
   source before defining TX.
6. For PACE mode, require the exact Modbus read register map before defining TX.
7. For Daly mode, split protocol families before defining TX:
   - 0xA5 family
   - 0xD2/Modbus-like family
8. CAN modes must not be treated as serial RS485 tests.
9. Record physical interface separately:
   - RS485
   - UART TTL
   - RS232
   - CAN
   - unknown
10. Record serial settings separately:
    - baudrate
    - parity
    - stopbits
    - address
11. Record source quality:
    - official manual
    - manufacturer PDF
    - donor source code
    - forum claim
    - own capture
    - unknown

Unknown, unverified, write-capable, or state-changing commands must not be marked
as safe read requests. Do not invent master requests, registers, checksums,
addresses, or protocol framing.

## Initial matrix

| JK BMS menu mode | Source / source quality | Physical interface | Serial settings | Confirmed read-only TX | Expected RX | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pylon LV / JK Protocol 014 | Existing project notes + Pylon LV RS485 V3.3 PDF / existing notes + manufacturer PDF | RS485 | baudrate: 9600; parity: N; stopbits: 1; address: protocol-specific Pylon address in frame | `~201246610000FDAA\r`<br>`~201246620000FDA9\r`<br>`~201246630000FDA8\r` | prefix: `~200246` | `ready_for_single_probe` | Valid only for Pylon LV / JK Pylon emulation mode. |
| Growatt BMS RS485 Protocol 1xSxxP_ESS Rev2 | required / unknown | RS485, verify | baudrate: `TBD`; parity: `TBD`; stopbits: `TBD`; address: `TBD` | `TBD` | `TBD` | `research_required` | Do not test with Pylon requests. Require Growatt BMS RS485 Protocol 1xSxxP_ESS Rev2.xx source before defining TX. |
| PACE RS485 Modbus | required / unknown | RS485 | baudrate: `TBD`, likely 9600; parity: `TBD`, likely N; stopbits: `TBD`, likely 1; address: `TBD`; all likely values must be verified | `TBD` | `TBD` | `research_required` | Only FC03/FC04 read-only candidates may be considered. FC06/FC10 forbidden. Require exact Modbus read register map before defining TX. |
| Daly | required / unknown | UART/RS485, verify | baudrate: `TBD`; parity: `TBD`; stopbits: `TBD`; address: `TBD` | `TBD` | `TBD` | `research_required` | Must split by Daly protocol family before testing: 0xA5 family vs 0xD2/Modbus-like family. |
| Seplos | required / unknown | UART/RS485/CAN depending on model | baudrate: `TBD`; parity: `TBD`; stopbits: `TBD`; address: `TBD` | `TBD` | `TBD` | `research_required` | Interface and serial/CAN transport must be verified per model. |
| JK native | required / unknown | RS485/UART TTL depending on port | baudrate: `TBD`; parity: `TBD`; stopbits: `TBD`; address: `TBD` | `TBD` | `TBD` | `research_required` | Do not confuse JK native UART/RS485 with JK Pylon LV emulation. |

## Current allowed conclusion

Only the Pylon LV / JK Protocol 014 row is ready for a single protocol-specific
probe, and only when the selected BMS menu mode is Pylon LV / JK Pylon emulation.
All other rows remain `research_required` until source-backed read-only requests,
framing, checksum/CRC rules, interface, serial settings, and address semantics are
confirmed.
