import pytest

from core.scanner import run_active_probe
from protocols import get_all_profiles
from transport.fake_serial_transport import FakeSerialTransport

RESPONSES = {
    "pylon_lv_rs485": b"~20024600800800000000FC22\r",
    "jk_pylon_lv_emulation": b"~20024600800800000000FC22\r",
    "jbd_jiabaida_uart_rs485": b"\xDD\x03\x00\x01w",
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
