# Protocol Profile Interface

Every protocol profile must implement:

- `split_frames(rx_buffer: bytes) -> list[bytes]`: framing parser.
- `validate_response(request, frame) -> ValidationResult`: scoring and validation.
- `decode_response(frame) -> dict`: safe best-effort decode.

## Probe safety labels

- `safe_read`: enabled by default.
- `unverified_read`: sent only with `--include-unverified`.
- `write_forbidden`: never sent by scanner.

All profiles in this repository are read-only. Write commands are intentionally not implemented.
