from core.models import ProbeMessage
from core.safety import is_probe_allowed


def test_forbidden_risk_blocked():
    p = ProbeMessage("set_address", b"00", None, 100, "write_forbidden")
    ok, _ = is_probe_allowed(p)
    assert not ok


def test_write_control_name_tokens_blocked():
    blocked_names = [
        "write_config",
        "control_command",
        "factory_mode",
        "unlock_pack",
        "calibrate_pack",
        "calibration_mode",
        "reset_bms",
        "firmware_update",
        "parameter_set",
        "mos_control",
        "function_0x05",
        "function_0x06",
        "function_0x0f",
        "function_0x10",
    ]

    for name in blocked_names:
        ok, reason = is_probe_allowed(ProbeMessage(name, b"00", None, 100, "safe_read"))
        assert not ok, name
        assert reason == "Blocked by safety policy (blocklist token)."
