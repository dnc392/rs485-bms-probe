from core.safety import is_probe_allowed
from protocols import get_all_profiles
from protocols.jbd_jiabaida import (
    BLOCKED_ACTIONS,
    JbdXiaoxiangProfile,
    READ_COMMANDS,
    jbd_checksum,
    verify_jbd_checksum,
)


VALID_BASIC_RESPONSE = bytes.fromhex(
    "DD 03 00 1B 17 00 00 00 02 D0 03 E8 00 00 20 78 00 00 00 00 00 00 10 48 03 0F 02 0B 76 0B 82 FB FF 77"
)
VALID_CELL_RESPONSE = bytes.fromhex(
    "DD 04 00 1E 0F 66 0F 63 0F 63 0F 64 0F 3E 0F 63 0F 37 0F 5B 0F 65 0F 3B 0F 63 0F 63 0F 3C 0F 66 0F 3D F9 F9 77"
)
ZERO_LENGTH_BASIC_RESPONSE = bytes.fromhex("DD 03 00 00 00 00 77")


def test_jbd_xiaoxiang_profile_is_active_safe_read_only():
    profile = JbdXiaoxiangProfile()

    assert profile.id == "jbd_xiaoxiang_uart_rs485"
    assert profile.enabled_by_default is True
    assert profile.serial_candidates[0].baudrate == 9600
    assert profile.serial_candidates[0].parity == "N"
    assert [probe.name for probe in profile.probes] == ["read_basic_info", "read_cell_voltages"]
    assert [probe.tx for probe in profile.probes] == [
        bytes.fromhex("DD A5 03 00 FF FD 77"),
        bytes.fromhex("DD A5 04 00 FF FC 77"),
    ]
    assert [probe.expected_response for probe in profile.probes] == [
        bytes.fromhex("DD 03"),
        bytes.fromhex("DD 04"),
    ]
    assert profile.read_commands == READ_COMMANDS == (0x03, 0x04)
    assert profile.blocked_actions == BLOCKED_ACTIONS
    assert all(probe.risk == "safe_read" for probe in profile.probes)
    assert profile.id in [active.id for active in get_all_profiles()]


def test_jbd_requests_have_valid_checksums():
    profile = JbdXiaoxiangProfile()

    assert jbd_checksum(bytes.fromhex("03 00")) == 0xFFFD
    assert jbd_checksum(bytes.fromhex("04 00")) == 0xFFFC
    for probe in profile.probes:
        assert verify_jbd_checksum(probe.tx)


def test_jbd_public_sample_responses_have_valid_checksums():
    assert verify_jbd_checksum(VALID_BASIC_RESPONSE)
    assert verify_jbd_checksum(VALID_CELL_RESPONSE)


def test_jbd_split_frames_uses_declared_length():
    profile = JbdXiaoxiangProfile()
    rx = b"\x00" + VALID_BASIC_RESPONSE + b"\x99" + VALID_CELL_RESPONSE

    assert profile.split_frames(rx) == [VALID_BASIC_RESPONSE, VALID_CELL_RESPONSE]


def test_jbd_validate_accepts_valid_and_rejects_invalid_checksum():
    profile = JbdXiaoxiangProfile()
    basic_probe = profile.probes[0]
    invalid = bytearray(VALID_BASIC_RESPONSE)
    invalid[-3:-1] = b"\x00\x00"

    valid_result = profile.validate_response(basic_probe, VALID_BASIC_RESPONSE)
    invalid_result = profile.validate_response(basic_probe, bytes(invalid))

    assert valid_result.ok
    assert "checksum_ok" in valid_result.reasons
    assert valid_result.decoded["checksum_status"] == "verified"
    assert not invalid_result.ok
    assert "checksum_invalid" in invalid_result.reasons


def test_jbd_validate_requires_ok_status_and_payload_length():
    profile = JbdXiaoxiangProfile()
    basic_probe = profile.probes[0]
    non_ok_status = bytearray(VALID_BASIC_RESPONSE)
    non_ok_status[2] = 0x80
    non_ok_status[-3:-1] = (-(sum(non_ok_status[1:-3])) & 0xFFFF).to_bytes(2, "big")

    short_payload_result = profile.validate_response(basic_probe, ZERO_LENGTH_BASIC_RESPONSE)
    non_ok_status_result = profile.validate_response(basic_probe, bytes(non_ok_status))

    assert not short_payload_result.ok
    assert "payload_too_short" in short_payload_result.reasons
    assert not non_ok_status_result.ok
    assert "status_not_ok" in non_ok_status_result.reasons


def test_jbd_profile_has_no_write_or_control_probes():
    profile = JbdXiaoxiangProfile()
    blocked_terms = ("write", "calibration", "factory", "mos_control", "capacity_reset")

    for probe in profile.probes:
        allowed, reason = is_probe_allowed(probe)
        assert allowed, reason
        assert probe.tx[1] == 0xA5
        assert probe.tx[2] in (0x03, 0x04)
        assert all(term not in probe.name.lower() for term in blocked_terms)
