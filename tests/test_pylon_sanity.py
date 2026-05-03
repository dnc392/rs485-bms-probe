from pathlib import Path

import pytest

from core.scanner import run_active_probe
from protocols import get_all_profiles
from protocols.pylon_lv_rs485 import PylonLvProfile, calculate_pylon_checksum
from transport.fake_serial_transport import FakeSerialTransport


SAMPLES_DIR = Path(__file__).resolve().parent / "samples" / "hardware"


def _escaped_ascii(value: str) -> bytes:
    return value.replace("\\r", "\r").encode("ascii")


def _sample_rx(name: str) -> bytes:
    text = (SAMPLES_DIR / name).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("RX: "):
            return _escaped_ascii(line.removeprefix("RX: "))
    raise AssertionError(f"RX not found in {name}")


def _probe(profile: PylonLvProfile, name: str):
    for probe in profile.probes:
        if probe.name == name:
            return probe
    raise AssertionError(f"Probe not found: {name}")


def _replace_0x61_info(frame: bytes, offset: int, replacement: bytes) -> bytes:
    frame_data = frame[1:-5].decode("ascii")
    header = frame_data[:12]
    info = bytearray(bytes.fromhex(frame_data[12:]))
    info[offset : offset + len(replacement)] = replacement
    new_frame_data = (header + info.hex().upper()).encode("ascii")
    checksum = calculate_pylon_checksum(new_frame_data).encode("ascii")
    return b"~" + new_frame_data + checksum + b"\r"


@pytest.mark.parametrize(
    ("sample_name", "probe_name", "expected_status"),
    [
        ("pylon_0x61_analog_1.txt", "read_system_analog_data", "passed"),
        ("pylon_0x61_analog_2.txt", "read_system_analog_data", "passed"),
        ("pylon_0x61_analog_3.txt", "read_system_analog_data", "passed"),
        ("pylon_0x61_analog_4.txt", "read_system_analog_data", "passed"),
        ("pylon_0x62_alarm_status.txt", "read_system_alarm_info", "not_applicable"),
        ("pylon_0x63_charge_discharge.txt", "read_charge_discharge_management", "passed"),
    ],
)
def test_valid_hardware_captures_sanity(sample_name: str, probe_name: str, expected_status: str):
    profile = PylonLvProfile()
    result = profile.validate_response(_probe(profile, probe_name), _sample_rx(sample_name))

    assert result.ok
    assert result.decoded["parse_status"] == "partial"
    assert result.decoded["checksum_status"] == "verified"
    assert result.decoded["sanity_status"] == expected_status
    assert result.decoded["sanity_warnings"] == []


def test_impossible_cell_voltage_fails_sanity():
    profile = PylonLvProfile()
    frame = _replace_0x61_info(_sample_rx("pylon_0x61_analog_4.txt"), 11, bytes.fromhex("1770"))
    result = profile.validate_response(_probe(profile, "read_system_analog_data"), frame)

    assert not result.ok
    assert result.decoded["checksum_status"] == "verified"
    assert result.decoded["highest_cell_voltage_v"] == 6.0
    assert result.decoded["sanity_status"] == "failed"
    assert "highest_cell_voltage_v_out_of_range" in result.decoded["sanity_warnings"]
    assert "decoded_sanity_failed" in result.reasons


def test_impossible_soc_fails_sanity():
    profile = PylonLvProfile()
    frame = _replace_0x61_info(_sample_rx("pylon_0x61_analog_4.txt"), 4, bytes.fromhex("C8"))
    result = profile.validate_response(_probe(profile, "read_system_analog_data"), frame)

    assert not result.ok
    assert result.decoded["checksum_status"] == "verified"
    assert result.decoded["system_soc_percent"] == 200
    assert result.decoded["sanity_status"] == "failed"
    assert "system_soc_percent_out_of_range" in result.decoded["sanity_warnings"]


def test_impossible_temperature_fails_sanity():
    profile = PylonLvProfile()
    frame = _replace_0x61_info(_sample_rx("pylon_0x61_analog_4.txt"), 19, bytes.fromhex("127B"))
    result = profile.validate_response(_probe(profile, "read_system_analog_data"), frame)

    assert not result.ok
    assert result.decoded["checksum_status"] == "verified"
    assert result.decoded["average_cell_temperature_c"] == 200.0
    assert result.decoded["sanity_status"] == "failed"
    assert "average_cell_temperature_c_out_of_range" in result.decoded["sanity_warnings"]


def test_sanity_failed_scan_is_not_detected_confidently():
    profile = PylonLvProfile()
    bad_frame = _replace_0x61_info(_sample_rx("pylon_0x61_analog_4.txt"), 11, bytes.fromhex("1770"))
    transport = FakeSerialTransport(
        responses=[
            bad_frame,
            _sample_rx("pylon_0x62_alarm_status.txt"),
            _sample_rx("pylon_0x63_charge_discharge.txt"),
        ]
    )

    result = run_active_probe(transport, "FAKE0", profile)

    assert result.status != "detected"
    assert result.score < 80
    assert any("decoded_sanity_failed" in warning for warning in result.warnings)


def test_checksum_invalid_remains_invalid_and_not_detected():
    profile = PylonLvProfile()
    frame = b"~20024600800800000000FC23\r"
    transport = FakeSerialTransport(responses=[frame, None, None])

    result = run_active_probe(transport, "FAKE0", profile)

    assert result.status != "detected"
    assert not result.detected
    assert result.decoded["read_system_analog_data"]["checksum_status"] == "invalid"
    assert any("checksum_invalid" in warning for warning in result.warnings)


def test_active_registry_contains_only_pylon_profiles_for_sanity():
    assert {profile.id for profile in get_all_profiles()} == {
        "pylon_lv_rs485",
        "jk_pylon_lv_emulation",
    }
