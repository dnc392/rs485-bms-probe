# Pylon LV RS485 checksum

Status: implemented for read-only Pylon LV / JK Protocol 014 compatible frames.

## Sources

- Pylon LV RS485 protocol PDF: `RS485-protocol-pylon-low-voltage-V3.3-20180821.pdf`.
- Donor reference, used only as research cross-check: Frankkkkk/python-pylontech
  (`Pylontech.get_frame_checksum`, MIT licensed).
- Local hardware captures in `tests/samples/hardware/*.txt`.

`docs/protocol_research/pylon_lv_rs485.md` was not present in this workspace when
this note was written.

## Frame fields

Pylon LV frames are:

```text
SOI VER ADR CID1 CID2/RTN LENGTH INFO CHKSUM EOI
```

- `SOI` is raw `~` (`0x7E`).
- `EOI` is raw carriage return (`0x0D`).
- All fields between `SOI` and `EOI` are uppercase HEX represented as ASCII.
- `CHKSUM` is the last four ASCII HEX characters before `EOI`.

Checksum input is the ASCII byte sequence between `SOI` and `CHKSUM`.
It excludes `SOI`, `CHKSUM`, and `EOI`.

## Algorithm

1. Take `frame_data = frame[1:-5]`.
2. Sum every ASCII byte in `frame_data`.
3. Keep the result modulo `65536`.
4. Invert the 16-bit value and add one.
5. Format the result as four uppercase HEX characters.

Equivalent expression:

```text
checksum = ((~sum(frame_data)) + 1) & 0xFFFF
```

## Worked example

Captured frame:

```text
~20024600800800000000FC22\r
```

Fields:

- `frame_data`: `20024600800800000000`
- received checksum: `FC22`
- sum of ASCII bytes in `frame_data`: `0x03DE`
- 16-bit inverse: `0xFC21`
- plus one: `0xFC22`

Expected checksum result: `FC22`.

## Edge cases

- Missing `~` or missing `\r`: do not verify checksum; fail framing first.
- Fewer than four checksum characters before `\r`: do not verify checksum.
- Non-uppercase-HEX frame body: fail payload validation before trusting decoded fields.
- Checksum mismatch: mark `checksum_invalid` and do not report protocol detection.
- Echoed request frames are invalid even if they are structurally well-formed.
