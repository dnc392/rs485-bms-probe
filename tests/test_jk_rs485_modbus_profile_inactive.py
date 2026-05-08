from protocols import get_all_profiles
from protocols.jk_rs485_modbus import (
    ALLOWED_FUNCTION_CODES,
    FORBIDDEN_FUNCTION_CODES,
    JkRs485ModbusProfile,
)
from protocols.modbus_rtu import verify_crc


def test_jk_rs485_modbus_profile_exists_but_is_inactive():
    profile = JkRs485ModbusProfile()
    active_ids = [profile.id for profile in get_all_profiles()]

    assert profile.id == "jk_rs485_modbus"
    assert profile.enabled_by_default is False
    assert profile.id not in active_ids


def test_active_registry_remains_exactly_pylon_profiles():
    assert [profile.id for profile in get_all_profiles()] == [
        "pylon_lv_rs485",
        "jk_pylon_lv_emulation",
    ]


def test_jk_rs485_modbus_profile_has_only_read_probes():
    profile = JkRs485ModbusProfile()

    assert profile.probes
    assert ALLOWED_FUNCTION_CODES == (0x03, 0x04)
    assert FORBIDDEN_FUNCTION_CODES == (0x05, 0x06, 0x0F, 0x10)
    for probe in profile.probes:
        assert probe.risk in {"safe_read", "unverified_read"}
        assert probe.tx[1] in ALLOWED_FUNCTION_CODES
        assert probe.tx[1] not in FORBIDDEN_FUNCTION_CODES
        assert verify_crc(probe.tx)
        assert "write" not in probe.name.lower()
        assert "control" not in probe.name.lower()
