# Safety Policy

See [docs/SAFETY.md](docs/SAFETY.md) for the full policy.

Summary:

- Default profiles are read-only.
- Write/control/config/factory/update/reset/unlock/calibration/MOS commands are blocked.
- Experimental reads require explicit `--include-unverified`.
- Experimental profiles do not participate in `--scan`.
- Manual `--tx-hex` bypasses profile validation and should only be used for reviewed read-only frames.
