from __future__ import annotations

from core.models import ProbeMessage

BLOCKLIST_TOKENS = {
    "write",
    "control",
    "shutdown",
    "reset",
    "unlock",
    "mos_control",
    "charging_mos_control",
    "discharging_mos_control",
    "set_address",
    "calibrate",
    "calibration",
    "capacity_reset",
    "factory",
    "firmware_update",
    "sleep",
    "clear_alarm",
    "parameter_set",
    "parameter_write",
    "function_0x05",
    "function_0x06",
    "function_0x0f",
    "function_0x10",
}

ALLOWED_RISKS = {"safe_read", "unverified_read", "experimental_unverified_read", "no_tx"}
FORBIDDEN_RISKS = {"write_forbidden"}


def is_probe_allowed(probe: ProbeMessage, include_unverified: bool = False) -> tuple[bool, str | None]:
    # Rule 1: write_forbidden can never be sent.
    if probe.risk in FORBIDDEN_RISKS:
        return False, "Blocked by safety policy (forbidden risk)."

    # Rule 2: unknown risks are blocked by default.
    if probe.risk not in ALLOWED_RISKS:
        return False, f"Blocked by safety policy (unknown risk: {probe.risk})."

    # Rule 3: unverified reads need explicit opt-in.
    if probe.risk in {"unverified_read", "experimental_unverified_read"} and not include_unverified:
        return False, "Blocked by safety policy (unverified probe disabled)."

    name = probe.name.lower()
    if any(token in name for token in BLOCKLIST_TOKENS):
        return False, "Blocked by safety policy (blocklist token)."
    return True, None
