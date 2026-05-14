# Support Matrix

This matrix describes current repository support. It does not imply full protocol support.

| Profile | Menu/protocol | Enabled by default | Risk class | Source confirmed | Hardware confirmed | Decode status | Notes |
|---|---|---:|---|---|---|---|---|
| `pylon_lv_rs485` | Pylontech / Pylon LV RS485 ASCII | yes | `safe_read` | yes | fixture/capture backed | minimal confirmed Pylon fields | Existing production target for Pylon-style ASCII reads. |
| `jk_pylon_lv_emulation` | JK BMS Pylon LV emulation / menu 014 | yes | `safe_read` | protocol-compatible behavior | fixture/capture backed | Pylon-compatible fields | Separate from `jk_rs485_modbus`. |
| `jbd_xiaoxiang_uart_rs485` | JBD/Xiaoxiang UART-RS485 | yes | `safe_read` | public references | hardware unverified in repo evidence | raw-only | Read-only `DD A5 03/04` probes only. |
| `daly_uart_485` | DALY UART/RS485 native | yes | `safe_read` | public frame format | hardware unverified in repo evidence | raw-only | Read-only commands `0x90..0x98`; no control writes. |
| `jk_rs485_modbus` | `013 (9600) JK BMS RS485 Modbus V1.0` | yes | `safe_read` | source/capture confirmed | hardware confirmed | confirmed cell-voltage registers only | Cell blocks confirmed; wider windows remain inactive/unverified. |
| `pace_rs485_modbus_v1_3` | `004 PACE_RS485_Modbus_V1.3` | yes | `safe_read` | source-confirmed PDF | hardware confirmed basic block | basic decode; cell semantics untrusted | Large core block returned exception `0x02`; no wide map claim. |
| `growatt_bms_rs485_1xsxxp` | `006 Growatt_BMS_RS485_Protocol_1x...` | yes | `safe_read` | source-confirmed PDF | hardware confirmed status block | status decode; cell semantics suspicious | Cell frames valid but not semantically trusted. |
| `voltronic_inverter_bms_485` | `007 Voltronic_Inverter_and_BMS_485-...` | yes | `safe_read` | source-confirmed DOCX | hardware confirmed single probe | source-custom cell-count decode | Not standard Modbus response shape. |
| `wow_rs485_modbus_v1_3` | `009 WOW_RS485_Modbus_V1.3` | no | `experimental_unverified_read` | no | experimental observations only | candidate-only; cell block semantic failed | Hidden by default; available only with `--include-unverified`; scan-blocked. |

## Status Vocabulary

- `source_confirmed`: request/shape came from a protocol source.
- `hardware_confirmed`: a bounded read was validated on real hardware.
- `hardware_unverified`: no hardware confirmation in repository evidence.
- `source_custom_confirmed`: a protocol-specific non-standard response shape is confirmed by source and capture.
- `experimental_unverified_read`: not source-confirmed; requires explicit user opt-in.
- `semantic_untrusted`: frame is valid, but decoded field meaning is not trusted.
- `frame_valid_semantics_failed`: frame is valid, but a sanity/cross-check failed.
