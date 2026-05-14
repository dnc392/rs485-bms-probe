# Protocol source index

## JBD / Xiaoxiang UART-RS485

Primary open references checked on 2026-05-13:

- JBDBMS `JBD-Smart BMS RS485 PC tool box` product page:
  lists RS485 PC tooling, Xiaoxiang app support, and links to the
  `JBD communication protocol new-RS485,RS232,UART` PDF.
  https://www.jbdbms.com/products/jbd-rs485-tools
- JBDBMS smart BMS product pages:
  list UART/RS485/CAN communication support and the same downloadable JBD
  communication protocol material.
  https://www.jbdbms.com/products/up16s019
- `JBD communication protocol new-RS485,RS232,UART` PDF:
  confirms the RS485/RS232/UART frame family, 9600 BPS default, `DD A5 03 00
  FF FD 77`, `DD A5 04 00 FF FC 77`, `DD CMD STATUS LEN DATA... CHK CHK 77`
  response shape, and `status 0 == correct`.
  https://cdn-files.myshopline.com/file/store/1720492677212/JBD-communication-protocol-new-RS485%2CRS232%2CUART.pdf
- Public reverse-engineering notes:
  show JBDTools sending `DD A5 03 00 FF FD 77` and `DD A5 04 00 FF FC 77`.
  https://endless-sphere.com/sphere/threads/generic-chinese-bluetooth-bms-communication-protocol.91672/
- `syssi/esphome-jbd-bms`:
  confirms the ESPHome ecosystem monitors Xiaoxiang/JBD BMS devices over
  UART-TTL or BLE.
  https://github.com/syssi/esphome-jbd-bms

Repository policy for this source family:

- Only safe-read probes are active.
- Write/config/factory/MOS/capacity reset commands are blocked.
- Field-level decoding is deferred until real captures are validated.
