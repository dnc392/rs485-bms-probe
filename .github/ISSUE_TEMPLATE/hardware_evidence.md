---
name: Hardware evidence
about: Submit sanitized hardware evidence for an existing probe.
title: "[evidence] "
labels: hardware-evidence
assignees: ""
---

## Context

- Profile id:
- Probe id:
- BMS model:
- Selected BMS menu protocol:
- Serial settings:
- Adapter type:

## Transaction

- TX HEX:
- RX HEX:
- RX length:
- Frames found:

## Validation

- [ ] not_echo
- [ ] checksum/CRC OK
- [ ] address/slave OK
- [ ] function/command OK
- [ ] length/byte count OK
- [ ] no exception/error response

## Decoded Values

Paste only sanitized decoded values.

```json
{}
```

## Safety Confirmation

- [ ] No write/control/config/factory/update command was used.
- [ ] Test was a bounded `--single-probe`, not `--scan`.
- [ ] Raw logs are not attached.
- [ ] No local paths, serial numbers, or credentials are included.
