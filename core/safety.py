from __future__ import annotations

from core.models import ProbeMessage

BLOCKLIST_TOKENS = {
    "write",
    "shutdown",
    "reset",
    "mos_control",
    "set_address",
    "calibration",
    "factory",
    "sleep",
    "clear_alarm",
    "parameter_write",
    "function_0x06",
    "function_0x10",
}

ALLOWED_RISKS = {"safe_read", "unverified_read", "no_tx"}
FORBIDDEN_RISKS = {"write_forbidden"}


def is_probe_allowed(probe: ProbeMessage, include_unverified: bool = False) -> tuple[bool, str | None]:
    # Rule 1: write_forbidden can never be sent.
    if probe.risk in FORBIDDEN_RISKS:
        return False, "Blocked by safety policy (forbidden risk)."

    # Rule 2: unknown risks are blocked by default.
    if probe.risk not in ALLOWED_RISKS:
        return False, f"Blocked by safety policy (unknown risk: {probe.risk})."

    # Rule 3: unverified reads need explicit opt-in.
    if probe.risk == "unverified_read" and not include_unverified:
        return False, "Blocked by safety policy (unverified probe disabled)."

    name = probe.name.lower()
    if any(token in name for token in BLOCKLIST_TOKENS):
        return False, "Blocked by safety policy (blocklist token)."
    return True, None
