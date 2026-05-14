import pytest

from core.scanner import run_active_probe
from protocols import get_all_profiles
from transport.fake_serial_transport import FakeSerialTransport

RESPONSES = {
    "pylon_lv_rs485": b"~20024600800800000000FC22\r",
    "jk_pylon_lv_emulation": b"~20024600800800000000FC22\r",
    "jbd_xiaoxiang_uart_rs485": bytes.fromhex("DD 03 00 00 FF FD 77"),
    "daly_uart_485": bytes.fromhex("A5 01 90 08 01 02 03 04 05 06 07 08 62"),
    "jk_rs485_modbus": bytes.fromhex("01 03 02 0C D8 BD 1E"),
    "pace_rs485_modbus_v1_3": bytes.fromhex("01 03 02 14 50 B7 78"),
    "growatt_bms_rs485_1xsxxp": bytes.fromhex("01 03 02 00 42 38 75"),
    "voltronic_inverter_bms_485": bytes.fromhex("01 03 00 01 00 08 15 CC"),
    "daly_uart_485_native": b"\xA5\x01\x02\x03",
    "seplos_rs485_ascii": b"~OK\r",
    "pace_rs485_modbus_rtu": b"\x00\x03\x02\x00\x01",
    "daly_rs485_modbus_rtu_candidate": b"\x01\x03\x02\x00\x01",
    "seplos_xzh_modbus_rtu_candidate": b"\x01\x03\x02\x00\x01",
    "jk_native_rs485_v2_placeholder": b"\x55\xAA\x10",
    "growatt_ess_rs485_candidate": b"\x01\x03\x02\x00\x01",
}

@pytest.mark.parametrize("profile", get_all_profiles(), ids=lambda p: p.id)
def test_profile_has_framing_scoring_and_runs_with_fake_transport(profile):
    response = RESPONSES[profile.id]
    transport = FakeSerialTransport([response] * max(1, len(profile.probes)))
    result = run_active_probe(transport, "FAKE0", profile, include_unverified=True)
    assert isinstance(profile.split_frames(response), list)
    assert result.protocol_id == profile.id
    assert result.score != 0 or result.reasons or result.warnings
