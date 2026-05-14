# Safety Policy

The project is a read-only protocol probe. It is not a BMS configuration tool.

## Allowed By Default

- Source-confirmed read-only requests.
- Bounded single-probe operations.
- Validators and checksum/CRC checks.
- JSON transaction logging.
- Passive listening.

## Blocked

The following command types and risk tokens must not be active probes:

- FC05
- FC06
- FC0F
- FC10
- write
- control
- config
- factory
- firmware update
- firmware_update
- reset
- unlock
- calibration
- parameter_set
- mos_control

## Experimental Mode

- Requires explicit `--include-unverified` or an equivalent explicit flag.
- Never participates in `--scan`.
- Is not source-confirmed.
- Is not active by default.
- Must be documented and tested.
- Must not be promoted to `safe_read` without a protocol source and hardware evidence.
- Must keep `source_confirmed=false` unless a real source is found and reviewed.

## Hardware Testing Checklist

1. Select the correct BMS menu protocol.
2. Confirm the correct serial port.
3. Confirm baud/parity/stopbits.
4. Run one bounded probe at a time.
5. Read the JSON transaction log after each test.
6. Do not infer a full register map from one response.
7. Do not expand to wider windows without source or prior bounded evidence.

## Manual TX Warning

Manual `--tx-hex` mode bypasses profile validation. Use it only for already reviewed read-only frames.
