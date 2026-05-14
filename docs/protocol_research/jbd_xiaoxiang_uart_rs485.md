# JBD / Xiaoxiang UART-RS485 safe-read profile

Status: active safe-read profile.

Confidence: medium-high for frame identity and transport shape; raw-only for
field-level interpretation until local hardware captures are collected.

## Active probes

| Probe | TX hex | Expected response prefix | Risk | Source status |
| --- | --- | --- | --- | --- |
| `read_basic_info` | `DD A5 03 00 FF FD 77` | `DD 03 00 ...` | `safe_read` | confirmed by public sources |
| `read_cell_voltages` | `DD A5 04 00 FF FC 77` | `DD 04 00 ...` | `safe_read` | confirmed by public sources |

## Primary open references

- Jiabaida/JBD product pages list smart BMS products and RS485/UART accessories,
  PC tooling, Xiaoxiang app support, and a downloadable
  `JBD communication protocol new-RS485,RS232,UART` document:
  https://www.jbdbms.com/products/jbd-rs485-tools
- The JBD protocol PDF describes a 9600 BPS RS485/RS232/UART protocol, frame
  start `0xDD`, read marker `0xA5`, write marker `0x5A`, end byte `0x77`,
  request checksum as two's complement over command/length/data bytes, response
  checksum as two's complement over length/data bytes in the public examples,
  command `0x03` as basic information/status, and command `0x04` as cell voltage
  read:
  https://cdn-files.myshopline.com/file/store/1720492677212/JBD-communication-protocol-new-RS485%2CRS232%2CUART.pdf
- Public reverse-engineering notes also show `DD A5 03 00 FF FD 77` and
  `DD A5 04 00 FF FC 77` as JBDTools read commands:
  https://endless-sphere.com/sphere/threads/generic-chinese-bluetooth-bms-communication-protocol.91672/
- The ESPHome ecosystem has an open `syssi/esphome-jbd-bms` component for
  Xiaoxiang/JBD monitoring over UART-TTL or BLE:
  https://github.com/syssi/esphome-jbd-bms

## Repository policy

- Only safe-read probes are active.
- Write/config/factory/MOS/capacity reset/calibration commands are blocked.
- Field-level decoding is deferred until real captures are validated.
- Raw-only validation still requires frame bounds, requested command echo in the
  response prefix, `status == 0x00`, declared length consistency, checksum
  validity, and a non-empty command-appropriate payload.

## Response validation model

Expected successful response shape:

```text
DD <cmd> 00 <length> <data...> <checksum_hi> <checksum_lo> 77
```

Current validation is intentionally structural, not semantic:

- `start byte == DD`
- `cmd == requested cmd`
- `status == 00`
- `length` matches the actual payload length
- checksum is valid
- `end byte == 77`
- payload length is above a minimal per-command threshold

Known open example responses used for tests:

- `DD 03 00 1B ... FB FF 77`
- `DD 04 00 1E ... F9 F9 77`

## First hardware test sequence

Run the probes one at a time. Replace `COMx` with the actual Windows serial
port.

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile jbd_xiaoxiang_uart_rs485 --probe read_basic_info --port COMx --baud 9600 --parity N --stopbits 1
```

Only after `read_basic_info` returns a structurally valid frame, run:

```powershell
.\.venv\Scripts\bms-probe.exe --single-probe --profile jbd_xiaoxiang_uart_rs485 --probe read_cell_voltages --port COMx --baud 9600 --parity N --stopbits 1
```

## Blocked command classes

- `write`
- `eeprom_write`
- `factory`
- `mos_control`
- `capacity_reset`
- `calibration`

No write/control frames are active.
