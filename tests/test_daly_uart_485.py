from core.scanner import run_active_probe
from core.safety import is_probe_allowed
from protocols import get_all_profiles
from protocols.daly_uart_485 import (
    BLOCKED_ACTIONS,
    DATA_LENGTH,
    FRAME_START,
    READ_COMMANDS,
    RESPONSE_ADDRESSES,
    DalyUart485Profile,
    build_daly_read_request,
    daly_checksum,
    verify_daly_checksum,
)
from transport.fake_serial_transport import FakeSerialTransport


def build_daly_response(command: int, address: int = 0x01, data: bytes | None = None) -> bytes:
    if data is None:
        data = bytes(range(1, DATA_LENGTH + 1))
    frame = bytes([FRAME_START, address, command, DATA_LENGTH]) + data
    return frame + bytes([daly_checksum(frame)])


def test_daly_checksum_calculation():
    frame_without_checksum = bytes.fromhex("A5 40 90 08 00 00 00 00 00 00 00 00")

    assert daly_checksum(frame_without_checksum) == 0x7D
    assert build_daly_read_request(0x90) == bytes.fromhex("A5 40 90 08 00 00 00 00 00 00 00 00 7D")


def test_daly_all_probe_frames_have_valid_checksum():
    profile = DalyUart485Profile()

    assert len(profile.probes) == 9
    assert [probe.tx[2] for probe in profile.probes] == list(READ_COMMANDS)
    for probe in profile.probes:
        assert verify_daly_checksum(probe.tx)


def test_daly_profile_is_active():
    active_ids = [profile.id for profile in get_all_profiles()]

    assert "daly_uart_485" in active_ids


def test_daly_profile_has_only_safe_read_probes():
    profile = DalyUart485Profile()

    assert profile.enabled_by_default is True
    assert profile.read_commands == READ_COMMANDS
    assert profile.blocked_actions == BLOCKED_ACTIONS
    for probe in profile.probes:
        allowed, reason = is_probe_allowed(probe)
        assert allowed, reason
        assert probe.risk == "safe_read"
        assert probe.tx[0] == FRAME_START
        assert probe.tx[1] == 0x40
        assert probe.tx[2] in READ_COMMANDS
        assert probe.tx[3] == DATA_LENGTH


def test_daly_profile_has_no_write_or_control_probes():
    profile = DalyUart485Profile()
    blocked_terms = (
        "write",
        "mos_control",
        "charging_mos_control",
        "discharging_mos_control",
        "calibration",
        "parameter_set",
        "factory",
        "firmware_update",
        "reset",
    )

    assert RESPONSE_ADDRESSES == (0x01, 0x40)
    for probe in profile.probes:
        assert all(term not in probe.name.lower() for term in blocked_terms)


def test_daly_fake_transport_positive_response():
    profile = DalyUart485Profile()
    profile.probes = [profile.probes[0]]
    response = build_daly_response(command=0x90)
    transport = FakeSerialTransport([response])

    result = run_active_probe(transport, "FAKE0", profile)

    assert transport.writes == [build_daly_read_request(0x90)]
    assert result.detected
    assert result.decoded["read_0x90"]["checksum_status"] == "verified"


def test_daly_corrupted_checksum_rejected():
    profile = DalyUart485Profile()
    probe = profile.probes[0]
    corrupted = bytearray(build_daly_response(command=0x90))
    corrupted[-1] ^= 0xFF

    result = profile.validate_response(probe, bytes(corrupted))

    assert not result.ok
    assert "checksum_invalid" in result.reasons


def test_daly_wrong_cmd_in_response_rejected():
    profile = DalyUart485Profile()
    probe = profile.probes[0]
    wrong_command = build_daly_response(command=0x91)

    result = profile.validate_response(probe, wrong_command)

    assert not result.ok
    assert "command_mismatch" in result.reasons
