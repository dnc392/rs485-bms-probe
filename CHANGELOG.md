# Changelog

## 0.1.1 - 2026-05-14

### Added

- Read-only protocol probe framework.
- Pylon LV RS485 ASCII profile.
- JK Pylon emulation profile.
- JBD/Xiaoxiang safe-read profile.
- DALY UART/485 safe-read profile.
- JK RS485 Modbus hardware-confirmed reads.
- PACE RS485 Modbus V1.3 bounded reads.
- Growatt BMS RS485 hardware-confirmed blocks.
- Voltronic source-custom single-probe confirmation.
- WOW experimental unverified observations.
- Sanitized evidence snippets under `docs/evidence/`.
- GitHub Actions test workflow.

### Safety

- No write/control commands.
- Explicit experimental gate via `--include-unverified`.
- No scan for experimental profiles.
- JSON transaction logs for hardware observations.

### Known Limitations

- Not full protocol support.
- Some cell-voltage mappings are semantically untrusted or failed.
- Hardware coverage is limited to the available BMS/test setup.
- No production certification.
