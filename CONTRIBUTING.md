# Contributing

This project is safety-first and read-only by default.

## Non-Negotiable Rules

- Do not add write/control/config/factory/update/reset/unlock/calibration commands.
- Do not add FC05, FC06, FC0F, or FC10 probes.
- Do not use guessed frames in active profiles.
- Do not promote experimental observations to source-confirmed support.
- Do not claim complete protocol coverage from a single response.

## New Protocol Checklist

1. Perform source discovery.
2. Identify a source-derived read-only request.
3. If no source exists, use explicit experimental classification and keep
   `source_confirmed=false`.
4. Add a validator before any hardware claim.
5. Keep the profile inactive if no source-confirmed request exists.
6. Add only one bounded single-probe first.
7. Run hardware with `--single-probe` only when permitted.
8. Read the JSON transaction log after each hardware test.
9. Update protocol docs with TX/RX/validation/decoded/status.
10. Add regression tests from actual RX when available.
11. Confirm no scan/write behavior is introduced.

## Source Requirement

Active protocol probes require a source-confirmed read-only request or a clearly
documented hardware-confirmed safe-read boundary. Experimental observations must
remain explicitly marked and must not be promoted by inference.

## Hardware Evidence Requirement

Hardware evidence must include the selected BMS menu, serial settings, TX/RX,
validator reasons, decoded fields if any, and a status decision. Console output
alone is not enough; read the JSON transaction log.

## Evidence

Raw `logs/` are local artifacts and are not committed.
Copy only sanitized snippets into `docs/evidence/`.
Do not include raw logs, local absolute paths, adapter identifiers beyond
generic context, or large dumps in a pull request.

## Required Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall .
.\.venv\Scripts\bms-probe.exe --list-profiles
.\.venv\Scripts\bms-probe.exe --list-profiles --include-unverified
git diff --check
```
