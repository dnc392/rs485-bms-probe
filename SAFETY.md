# SAFETY model

This project is a **read-only protocol probe**.

## Enforcement rules

1. `write_forbidden` probes are **always blocked**.
2. Risks outside the allow-list (`safe_read`, `unverified_read`) are blocked as unknown.
3. `unverified_read` probes are blocked unless `--include-unverified` is set.
4. Scanner output records each skipped probe and the exact blocking reason.

## Defense-in-depth

- Name-based blocklist denies common write/control keywords.
- Risk-based policy denies anything not explicitly allowed.
- Scanner logs both warnings and structured `skipped_probes` entries.

No write/control commands are supported in autodetect mode.
