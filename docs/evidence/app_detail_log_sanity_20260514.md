# App Detail Log Sanity Evidence - 2026-05-14

## Source

- Source artifact: `detaillogs-20260514145011.txt`
- Type: BMS app-exported detail log
- Repository handling: raw app log is not committed; this file is a sanitized
  summary.
- Purpose: external sanity evidence for decoded protocol values.

## Selected app-log row

The latest relevant app rows are:

- `2026-05-14 14:46:23`
- `2026-05-14 14:46:24`

Both rows report the same values:

- Max cell voltage: `3.288 V`
- Min cell voltage: `3.287 V`
- Battery voltage: `26.30 V`
- Battery current: `0.0 A`
- Remaining capacity: `131.0 Ah`
- Full charge capacity: `200.0 Ah`
- Max/min temperature: `21 C / 21 C`
- MOS temperature: `24 C`

## Derived checks

- Derived SOC: `131.0 Ah / 200.0 Ah * 100 = 65.5 %`
- Protocol SOC values around `66 %` are consistent with the app log.
- Pack topology is consistent with 8S LiFePO4:
  `26.30 V / 8 = 3.2875 V`
- The app log supports the expectation that a valid 8-cell voltage list should
  sum near `26.30 V`, not near `6.57 V` or `23.03 V`.

## Protocol cross-check

| Source | Protocol value | App-log reference | Decision |
| --- | ---: | ---: | --- |
| PACE `read_basic_block_0_2_addr1` | pack voltage `26.29 V` | battery voltage `26.30 V` | OK |
| WOW `experimental_read_basic_block_0x0000_0x0002_addr1` | candidate pack voltage `26.30 V` | battery voltage `26.30 V` | OK, still experimental |
| Growatt `read_status_block_0x0013_0x0018_addr1` | pack voltage `26.31 V` | battery voltage `26.30 V` | OK |
| PACE basic block | SOC `66 %` | derived SOC `65.5 %` | OK |
| Growatt status block | SOC `66 %` | derived SOC `65.5 %` | OK |
| WOW basic block | candidate SOC `66 %` | derived SOC `65.5 %` | OK, still experimental |

## Cell block semantic decisions

PACE cell block `0x0015..`:

- Frame status: valid Modbus frame.
- Semantic status: untrusted.
- Reason: candidate active cell sum from the returned `0x0015..` block does not
  match the `26.30 V` pack voltage implied by the app log.
- Decision: keep PACE cell-level diagnostics unconfirmed until cross-checked
  against a trusted register source, JK native Modbus, or app-level per-cell
  values.

WOW experimental cell block `0x0015..`:

- Frame status: valid experimental Modbus response.
- Semantic status: failed/untrusted.
- Reason: candidate active cells `[3289, 3287]` sum to `6.576 V`, while the app
  log confirms the pack behaves like 8S at about `26.30 V`.
- Decision: do not extend WOW to a 16-cell block without a source. WOW remains
  `experimental_unverified_read`, disabled by default, and not
  `source_confirmed`.

## Status boundaries

- This evidence does not activate any protocol.
- This evidence does not make WOW source-confirmed.
- This evidence does not validate a full register map.
- This evidence does not authorize wider reads or write/control commands.
- It is only an external sanity cross-check for already captured decoded values.
