# Contributing

This project is safety-first and read-only by default.

## Non-Negotiable Rules

- Do not add write/control/config/factory/update/reset/unlock/calibration commands.
- Do not add FC05, FC06, FC0F, or FC10 probes.
- Do not use guessed frames in active profiles.
- Do not promote experimental observations to source-confirmed support.
- Do not claim full protocol support from a single response.

## New Protocol Checklist

1. Perform source discovery.
2. Identify a source-derived read-only request.
3. Keep the profile inactive if no source-confirmed request exists.
4. Add only one bounded single-probe first.
5. Run hardware with `--single-probe` only when permitted.
6. Read the JSON transaction log after each hardware test.
7. Update protocol docs with TX/RX/validation/decoded/status.
8. Add regression tests for valid and invalid frames.
9. Confirm no scan/write behavior is introduced.

## Evidence

Raw `logs/` are local artifacts and are not committed.
Copy only sanitized snippets into `docs/evidence/`.

## Required Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall .
.\.venv\Scripts\bms-probe.exe --list-profiles
.\.venv\Scripts\bms-probe.exe --list-profiles --include-unverified
git diff --check
```
